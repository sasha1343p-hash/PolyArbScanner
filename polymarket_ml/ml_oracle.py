"""
ML Oracle для предиктивных рынков Polymarket.

CLI-интерфейс для обучения, оценки и инференса ML-моделей.

Использование:
    python ml_oracle.py train              # Обучение модели
    python ml_oracle.py evaluate           # Оценка на отложенной выборке
    python ml_oracle.py predict <market_id>  # Предсказание для рынка
    python ml_oracle.py drift-check        # Проверка дрейфа
    python ml_oracle.py feature-importance # Важность признаков
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import yaml

from ml_oracle import FeatureExtractor, MLOracle, ModelMonitor, OracleEnsemble
from ml_oracle.feature_extractor import FeatureConfig
from ml_oracle.model import TrainingConfig
from ml_oracle.monitor import MonitorConfig
from ml_oracle.ensemble import EnsembleConfig

# Создаём необходимые директории ДО настройки логирования
os.makedirs('logs', exist_ok=True)
os.makedirs('artifacts', exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/ml_oracle.log', encoding='utf-8'),
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = 'configs/oracle_config.yaml') -> dict:
    """Загружает конфигурацию из YAML."""
    if not os.path.exists(config_path):
        logger.warning(f"Конфиг не найден: {config_path}, используем дефолты")
        return {}
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config or {}


def load_data(db_path: str) -> tuple:
    """
    Загружает данные из SQLite БД.
    
    Returns:
        (metadata_df, price_df)
    """
    import sqlite3
    
    if not os.path.exists(db_path):
        logger.error(f"База данных не найдена: {db_path}")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    
    # Загружаем метаданные
    metadata_df = pd.read_sql_query("""
        SELECT id, question, end_date, resolution, created_at
        FROM market_metadata
        WHERE resolution IS NOT NULL
    """, conn)
    
    # Загружаем цены
    price_df = pd.read_sql_query("""
        SELECT market_id, timestamp, yes_price, volume, liquidity
        FROM price_history
    """, conn)
    
    conn.close()
    
    logger.info(f"Загружено {len(metadata_df)} рынков, {len(price_df)} записей цен")
    
    return metadata_df, price_df


def cmd_train(args):
    """Команда обучения модели."""
    logger.info("=" * 60)
    logger.info("НАЧАЛО ОБУЧЕНИЯ МОДЕЛИ")
    logger.info("=" * 60)
    
    # Загружаем конфиг
    config = load_config(args.config)
    
    # Загружаем данные
    metadata_df, price_df = load_data(config.get('paths', {}).get('database', 'polymarket_history.db'))
    
    if len(metadata_df) < 100:
        logger.error(f"Недостаточно данных для обучения: {len(metadata_df)} < 100")
        sys.exit(1)
    
    # Создаём target variable
    metadata_df['target'] = (metadata_df['resolution'] == 'YES').astype(int)
    
    # Извлекаем признаки
    feature_config = FeatureConfig(**config.get('features', {}))
    extractor = FeatureExtractor(feature_config)
    
    logger.info("Извлечение признаков...")
    X = extractor.extract_features_batch(metadata_df, price_df)
    y = metadata_df.set_index('id')['target']
    
    #Align indices
    common_idx = X.index.intersection(y.index)
    X = X.loc[common_idx]
    y = y.loc[common_idx]
    
    logger.info(f"Признаки: {X.shape[1]}, Примеры: {len(X)}")
    
    # Обучаем модель
    training_config = TrainingConfig(**config.get('training', {}))
    model = MLOracle(training_config)
    
    logger.info("Обучение модели...")
    metrics = model.train(X, y, feature_names=extractor.get_feature_names())
    
    # Выводим метрики
    logger.info("=" * 60)
    logger.info("МЕТРИКИ КАЧЕСТВА")
    logger.info("=" * 60)
    logger.info(f"Accuracy:    {metrics.accuracy:.4f}")
    logger.info(f"Precision:   {metrics.precision:.4f}")
    logger.info(f"Recall:      {metrics.recall:.4f}")
    logger.info(f"F1 Score:    {metrics.f1:.4f}")
    logger.info(f"AUC-ROC:     {metrics.auc_roc:.4f}")
    logger.info(f"Brier Score: {metrics.brier_score:.4f}")
    logger.info(f"Samples:     {metrics.n_samples} (YES={metrics.n_positive}, NO={metrics.n_negative})")
    
    # Проверяем пороги
    if metrics.auc_roc < 0.65:
        logger.warning("⚠️  AUC-ROC ниже порога 0.65. Модель может быть недостаточно точной.")
    
    if metrics.brier_score > 0.25:
        logger.warning("⚠️  Brier Score выше порога 0.25. Калибровка вероятностей может быть плохой.")
    
    # Сохраняем модель
    model_path = config.get('paths', {}).get('model_bundle', 'artifacts/ml_oracle_bundle.pkl')
    model.save(model_path)
    
    # Сохраняем scaler
    scaler_path = model_path.replace('.pkl', '_scaler.pkl')
    extractor.save_scaler(scaler_path)
    
    # Инициализируем мониторинг
    monitor = ModelMonitor(MonitorConfig(**config.get('monitoring', {})))
    monitor.initialize_from_train_data(X)
    
    stats_path = config.get('paths', {}).get('train_stats', 'artifacts/train_stats.json')
    monitor.save_train_stats(stats_path)
    
    logger.info("=" * 60)
    logger.info("✅ ОБУЧЕНИЕ ЗАВЕРШЕНО УСПЕШНО")
    logger.info("=" * 60)


def cmd_evaluate(args):
    """Команда оценки модели."""
    logger.info("Оценка модели на отложенной выборке")
    
    config = load_config(args.config)
    
    # Загружаем модель
    model = MLOracle()
    model_path = config.get('paths', {}).get('model_bundle', 'artifacts/ml_oracle_bundle.pkl')
    
    if not model.load(model_path):
        logger.error("Не удалось загрузить модель. Сначала выполните: python ml_oracle.py train")
        sys.exit(1)
    
    # Загружаем данные
    metadata_df, price_df = load_data(config.get('paths', {}).get('database', 'polymarket_history.db'))
    metadata_df['target'] = (metadata_df['resolution'] == 'YES').astype(int)
    
    # Извлекаем признаки
    extractor = FeatureExtractor()
    scaler_path = model_path.replace('.pkl', '_scaler.pkl')
    extractor.load_scaler(scaler_path)
    
    X = extractor.extract_features_batch(metadata_df, price_df)
    y = metadata_df.set_index('id')['target']
    
    # Предсказания
    y_pred_proba = []
    for idx in X.index:
        features = X.loc[idx]
        proba = model.predict(features)
        y_pred_proba.append(proba if proba is not None else 0.5)
    
    y_pred_proba = pd.Series(y_pred_proba, index=X.index)
    
    # Метрики
    from sklearn.metrics import roc_auc_score, brier_score_loss
    
    auc = roc_auc_score(y, y_pred_proba)
    brier = brier_score_loss(y, y_pred_proba)
    
    logger.info(f"AUC-ROC: {auc:.4f}")
    logger.info(f"Brier Score: {brier:.4f}")


def cmd_predict(args):
    """Команда предсказания для конкретного рынка."""
    market_id = args.market_id
    
    logger.info(f"Предсказание для рынка: {market_id}")
    
    config = load_config(args.config)
    
    # Загружаем модель
    model = MLOracle()
    model_path = config.get('paths', {}).get('model_bundle', 'artifacts/ml_oracle_bundle.pkl')
    
    if not model.load(model_path):
        logger.error("Модель не загружена. Сначала: python ml_oracle.py train")
        sys.exit(1)
    
    # Загружаем данные для этого рынка
    import sqlite3
    db_path = config.get('paths', {}).get('database', 'polymarket_history.db')
    conn = sqlite3.connect(db_path)
    
    metadata_df = pd.read_sql_query(
        f"SELECT * FROM market_metadata WHERE id = '{market_id}'",
        conn
    )
    price_df = pd.read_sql_query(
        f"SELECT * FROM price_history WHERE market_id = '{market_id}'",
        conn
    )
    conn.close()
    
    if metadata_df.empty:
        logger.error(f"Рынок не найден: {market_id}")
        sys.exit(1)
    
    # Извлекаем признаки
    from ml_oracle.feature_extractor import MarketMetadata
    extractor = FeatureExtractor()
    
    metadata = MarketMetadata(
        id=market_id,
        question=metadata_df.iloc[0]['question'],
        end_date=pd.to_datetime(metadata_df.iloc[0]['end_date']) if pd.notna(metadata_df.iloc[0].get('end_date')) else None,
    )
    
    features = extractor.extract_features(market_id, price_df, metadata)
    
    # Предсказание
    proba, confidence = model.predict_with_confidence(features)
    
    if proba is None:
        logger.error("Не удалось получить предсказание")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info(f"РЫНОК: {metadata_df.iloc[0]['question']}")
    logger.info("=" * 60)
    logger.info(f"Вероятность YES: {proba:.2%}")
    logger.info(f"Уверенность:     {confidence:.2%}")
    logger.info(f"Рекомендация:    {'BUY YES' if proba > 0.5 else 'BUY NO'}")
    logger.info("=" * 60)


def cmd_drift_check(args):
    """Команда проверки дрейфа."""
    logger.info("Проверка дрейфа модели")
    
    config = load_config(args.config)
    
    # Загружаем мониторинг
    monitor = ModelMonitor()
    stats_path = config.get('paths', {}).get('train_stats', 'artifacts/train_stats.json')
    
    if not monitor.load_train_stats(stats_path):
        logger.error("Статистика не загружена. Сначала: python ml_oracle.py train")
        sys.exit(1)
    
    # Загружаем новые данные
    metadata_df, price_df = load_data(config.get('paths', {}).get('database', 'polymarket_history.db'))
    
    # Извлекаем признаки
    extractor = FeatureExtractor()
    X_new = extractor.extract_features_batch(metadata_df, price_df)
    
    # Проверяем дрейф
    report = monitor.check_drift(X_new)
    
    logger.info("=" * 60)
    logger.info("ОТЧЁТ О ДРЕЙФЕ")
    logger.info("=" * 60)
    logger.info(f"Дрейф обнаружен: {'ДА' if report.has_drift else 'НЕТ'}")
    logger.info(f"Дрейфующие признаки: {len(report.drifted_features)}")
    
    if report.drifted_features:
        logger.info("\nДрейфующие признаки:")
        for feature in report.drifted_features:
            psi = report.psi_values.get(feature, 0)
            ks = report.ks_values.get(feature, 0)
            logger.info(f"  - {feature}: PSI={psi:.4f}, KS={ks:.4f}")
    
    logger.info(f"\nРекомендация: {report.recommendation}")
    logger.info("=" * 60)


def cmd_feature_importance(args):
    """Команда вывода важности признаков."""
    logger.info("Важность признаков")
    
    config = load_config(args.config)
    
    # Загружаем модель
    model = MLOracle()
    model_path = config.get('paths', {}).get('model_bundle', 'artifacts/ml_oracle_bundle.pkl')
    
    if not model.load(model_path):
        logger.error("Модель не загружена")
        sys.exit(1)
    
    # Получаем важность
    importance = model.get_feature_importance(top_n=20)
    
    if not importance:
        logger.error("Не удалось получить важность признаков")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("ТОП-20 ВАЖНЫХ ПРИЗНАКОВ")
    logger.info("=" * 60)
    
    for i, (feature, score) in enumerate(importance, 1):
        bar = "█" * int(score * 50)
        logger.info(f"{i:2d}. {feature:30s} {score:.4f} {bar}")
    
    logger.info("=" * 60)


def main():
    """Главная функция CLI."""
    parser = argparse.ArgumentParser(
        description="ML Oracle для предиктивных рынков Polymarket"
    )
    parser.add_argument(
        '--config',
        default='configs/oracle_config.yaml',
        help='Путь к конфигурационному файлу'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Команды')
    
    # train
    subparsers.add_parser('train', help='Обучение модели')
    
    # evaluate
    subparsers.add_parser('evaluate', help='Оценка модели')
    
    # predict
    predict_parser = subparsers.add_parser('predict', help='Предсказание для рынка')
    predict_parser.add_argument('market_id', help='ID рынка')
    
    # drift-check
    subparsers.add_parser('drift-check', help='Проверка дрейфа')
    
    # feature-importance
    subparsers.add_parser('feature-importance', help='Важность признаков')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Создаём директории
    os.makedirs('logs', exist_ok=True)
    os.makedirs('artifacts', exist_ok=True)
    
    # Выполняем команду
    commands = {
        'train': cmd_train,
        'evaluate': cmd_evaluate,
        'predict': cmd_predict,
        'drift-check': cmd_drift_check,
        'feature-importance': cmd_feature_importance,
    }
    
    commands[args.command](args)


if __name__ == '__main__':
    main()
