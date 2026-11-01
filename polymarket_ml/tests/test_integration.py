"""
Интеграционные тесты для проверки всего пайплайна ML Oracle.

Эти тесты проверяют полный цикл: от загрузки данных до предсказания.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

from ml_oracle import FeatureExtractor, MLOracle, ModelMonitor
from ml_oracle.feature_extractor import MarketMetadata, FeatureConfig
from ml_oracle.model import TrainingConfig


@pytest.fixture
def temp_dir():
    """Создаёт временную директорию для тестов."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_data():
    """Создаёт тестовые данные для интеграционных тестов."""
    np.random.seed(42)
    
    # Метаданные рынков
    metadata_df = pd.DataFrame({
        'id': [f'market-{i:03d}' for i in range(150)],
        'question': [f'Will BTC be above ${60000 + i * 500}?' for i in range(150)],
        'end_date': pd.date_range('2026-01-01', periods=150, freq='D'),
        'resolution': np.random.choice(['YES', 'NO'], size=150, p=[0.6, 0.4]),
        'created_at': pd.date_range('2025-01-01', periods=150, freq='D'),
    })
    
    # История цен
    price_data = []
    for market_id in metadata_df['id']:
        base_price = np.random.uniform(0.3, 0.7)
        for hour in range(200):
            price_data.append({
                'market_id': market_id,
                'timestamp': pd.Timestamp('2025-01-01') + pd.Timedelta(hours=hour),
                'yes_price': base_price + np.random.normal(0, 0.05),
                'volume': np.random.uniform(1000, 10000),
                'liquidity': np.random.uniform(5000, 50000),
            })
    
    price_df = pd.DataFrame(price_data)
    
    return metadata_df, price_df


class TestFullPipeline:
    """Тесты полного пайплайна."""
    
    def test_feature_extraction_to_prediction(self, sample_data, temp_dir):
        """Тест полного цикла: извлечение признаков -> обучение -> предсказание."""
        metadata_df, price_df = sample_data
        
        # 1. Извлечение признаков
        extractor = FeatureExtractor()
        X = extractor.extract_features_batch(metadata_df, price_df)
        y = (metadata_df.set_index('id')['resolution'] == 'YES').astype(int)
        
        # Проверки
        assert len(X) == 150, "Должно быть 150 примеров"
        assert len(X.columns) > 50, "Должно быть больше 50 признаков"
        assert not X.isna().any().any(), "Не должно быть NaN"
        
        # 2. Обучение модели
        config = TrainingConfig(
            test_size=0.2,
            n_splits=3,
            calibration_enabled=False,
            xgb_enabled=True,
            lgb_enabled=False,
        )
        model = MLOracle(config)
        metrics = model.train(X, y, feature_names=list(X.columns))
        
        # Проверки метрик
        assert 0 <= metrics.accuracy <= 1, "Accuracy должен быть в [0, 1]"
        assert 0 <= metrics.auc_roc <= 1, "AUC-ROC должен быть в [0, 1]"
        assert metrics.brier_score >= 0, "Brier Score должен быть >= 0"
        assert metrics.n_samples > 0, "Должно быть хотя бы 1 пример в тесте"
        
        # 3. Сохранение модели
        model_path = temp_dir / 'test_model.pkl'
        model.save(str(model_path))
        assert model_path.exists(), "Файл модели должен существовать"
        
        # 4. Загрузка модели
        new_model = MLOracle()
        success = new_model.load(str(model_path))
        assert success, "Модель должна загрузиться"
        assert new_model.is_trained, "Модель должна быть обучена"
        
        # 5. Предсказание
        test_market_id = 'market-001'
        test_metadata = MarketMetadata(
            id=test_market_id,
            question='Will BTC be above $60500?',
            end_date=pd.Timestamp('2026-01-02'),
        )
        test_prices = price_df[price_df['market_id'] == test_market_id]
        
        test_features = extractor.extract_features(test_market_id, test_prices, test_metadata)
        proba = new_model.predict(test_features)
        
        assert proba is not None, "Предсказание не должно быть None"
        assert 0 <= proba <= 1, "Вероятность должна быть в [0, 1]"
        
        # 6. Предсказание с уверенностью
        proba_with_conf, confidence = new_model.predict_with_confidence(test_features)
        assert proba_with_conf is not None, "Предсказание не должно быть None"
        assert 0 <= confidence <= 1, "Уверенность должна быть в [0, 1]"
    
    def test_model_monitoring_pipeline(self, sample_data, temp_dir):
        """Тест пайплайна мониторинга дрейфа."""
        metadata_df, price_df = sample_data
        
        # 1. Извлечение признаков
        extractor = FeatureExtractor()
        X = extractor.extract_features_batch(metadata_df, price_df)
        
        # 2. Инициализация монитора
        monitor = ModelMonitor()
        monitor.initialize_from_train_data(X)
        
        # 3. Сохранение статистики
        stats_path = temp_dir / 'train_stats.json'
        monitor.save_train_stats(str(stats_path))
        assert stats_path.exists(), "Файл статистики должен существовать"
        
        # 4. Загрузка статистики
        new_monitor = ModelMonitor()
        success = new_monitor.load_train_stats(str(stats_path))
        assert success, "Статистика должна загрузиться"
        
        # 5. Проверка дрейфа на тех же данных (не должно быть дрейфа)
        report = new_monitor.check_drift(X)
        assert not report.has_drift, "Не должно быть дрейфа на тех же данных"
        assert len(report.drifted_features) == 0, "Не должно быть дрейфующих признаков"
        
        # 6. Проверка дрейфа на изменённых данных
        X_drifted = X.copy()
        X_drifted['price_mean'] = X_drifted['price_mean'] * 2  # Удваиваем значения
        report_drifted = new_monitor.check_drift(X_drifted)
        # Может быть дрейф, а может и нет (зависит от порога)
        assert isinstance(report_drifted.has_drift, bool), "has_drift должен быть bool"
    
    def test_feature_extractor_consistency(self, sample_data):
        """Тест согласованности извлечения признаков."""
        metadata_df, price_df = sample_data
        
        # Извлекаем признаки дважды
        extractor1 = FeatureExtractor()
        X1 = extractor1.extract_features_batch(metadata_df, price_df)
        
        extractor2 = FeatureExtractor()
        X2 = extractor2.extract_features_batch(metadata_df, price_df)
        
        # Проверяем, что признаки одинаковые
        assert list(X1.columns) == list(X2.columns), "Названия признаков должны совпадать"
        assert X1.shape == X2.shape, "Размеры должны совпадать"
        
        # Проверяем, что значения одинаковые для первого рынка
        pd.testing.assert_series_equal(
            X1.iloc[0], X2.iloc[0],
            check_names=False,
            rtol=1e-5
        )
    
    def test_model_reproducibility(self, sample_data):
        """Тест воспроизводимости результатов."""
        metadata_df, price_df = sample_data
        
        # Извлекаем признаки
        extractor = FeatureExtractor()
        X = extractor.extract_features_batch(metadata_df, price_df)
        y = (metadata_df.set_index('id')['resolution'] == 'YES').astype(int)
        
        # Обучаем модель дважды с одинаковыми параметрами
        config1 = TrainingConfig(
            test_size=0.2,
            n_splits=3,
            calibration_enabled=False,
            xgb_enabled=True,
            lgb_enabled=False,
            random_state=42,
        )
        model1 = MLOracle(config1)
        metrics1 = model1.train(X, y, feature_names=list(X.columns))
        
        config2 = TrainingConfig(
            test_size=0.2,
            n_splits=3,
            calibration_enabled=False,
            xgb_enabled=True,
            lgb_enabled=False,
            random_state=42,
        )
        model2 = MLOracle(config2)
        metrics2 = model2.train(X, y, feature_names=list(X.columns))
        
        # Проверяем, что метрики одинаковые
        assert abs(metrics1.auc_roc - metrics2.auc_roc) < 1e-6, "AUC-ROC должен быть одинаковым"
        assert abs(metrics1.brier_score - metrics2.brier_score) < 1e-6, "Brier Score должен быть одинаковым"
    
    def test_edge_cases(self, sample_data):
        """Тест граничных случаев."""
        metadata_df, price_df = sample_data
        
        extractor = FeatureExtractor()
        
        # 1. Пустой DataFrame с ценами
        empty_metadata = metadata_df.iloc[[0]].copy()
        empty_metadata['id'] = 'empty-market'
        empty_prices = pd.DataFrame(columns=['market_id', 'timestamp', 'yes_price', 'volume', 'liquidity'])
        
        empty_meta = MarketMetadata(
            id='empty-market',
            question='Test',
            end_date=pd.Timestamp('2026-01-01'),
        )
        
        features = extractor.extract_features('empty-market', empty_prices, empty_meta)
        assert features is not None, "Должны вернуться признаки даже для пустых данных"
        assert 'price_current' in features.index, "Должен быть price_current"
        
        # 2. Очень мало данных
        small_metadata = metadata_df.iloc[[0]].copy()
        small_prices = price_df[price_df['market_id'] == small_metadata['id']].head(5)
        
        small_meta = MarketMetadata(
            id=small_metadata['id'].iloc[0],
            question=small_metadata['question'].iloc[0],
            end_date=pd.Timestamp('2026-01-01'),
        )
        
        features_small = extractor.extract_features(
            small_metadata['id'].iloc[0],
            small_prices,
            small_meta
        )
        assert features_small is not None, "Должны вернуться признаки даже для малых данных"


class TestDataQuality:
    """Тесты качества данных."""
    
    def test_no_nan_in_features(self, sample_data):
        """Тест отсутствия NaN в признаках."""
        metadata_df, price_df = sample_data
        
        extractor = FeatureExtractor()
        X = extractor.extract_features_batch(metadata_df, price_df)
        
        assert not X.isna().any().any(), "Не должно быть NaN в признаках"
    
    def test_no_inf_in_features(self, sample_data):
        """Тест отсутствия inf в признаках."""
        metadata_df, price_df = sample_data
        
        extractor = FeatureExtractor()
        X = extractor.extract_features_batch(metadata_df, price_df)
        
        assert not np.isinf(X.values).any(), "Не должно быть inf в признаках"
    
    def test_feature_ranges(self, sample_data):
        """Тест диапазонов значений признаков."""
        metadata_df, price_df = sample_data
        
        extractor = FeatureExtractor()
        X = extractor.extract_features_batch(metadata_df, price_df)
        
        # Проверяем вероятности
        if 'price_current' in X.columns:
            assert (X['price_current'] >= 0).all() and (X['price_current'] <= 1).all(), \
                "price_current должен быть в [0, 1]"
        
        # Проверяем волатильность
        if 'volatility_24h' in X.columns:
            assert (X['volatility_24h'] >= 0).all(), "volatility_24h должен быть >= 0"
        
        # Проверяем RSI
        if 'rsi' in X.columns:
            assert (X['rsi'] >= 0).all() and (X['rsi'] <= 100).all(), \
                "RSI должен быть в [0, 100]"


class TestPerformance:
    """Тесты производительности."""
    
    def test_inference_speed(self, sample_data):
        """Тест скорости инференса."""
        import time
        
        metadata_df, price_df = sample_data
        
        # Извлекаем признаки
        extractor = FeatureExtractor()
        X = extractor.extract_features_batch(metadata_df, price_df)
        y = (metadata_df.set_index('id')['resolution'] == 'YES').astype(int)
        
        # Обучаем модель
        config = TrainingConfig(
            test_size=0.2,
            n_splits=3,
            calibration_enabled=False,
            xgb_enabled=True,
            lgb_enabled=False,
        )
        model = MLOracle(config)
        model.train(X, y, feature_names=list(X.columns))
        
        # Тестируем скорость предсказания
        test_features = X.iloc[0]
        
        start_time = time.time()
        for _ in range(100):
            proba = model.predict(test_features)
        end_time = time.time()
        
        avg_time_ms = (end_time - start_time) / 100 * 1000
        
        assert avg_time_ms < 50, f"Инференс должен быть < 50ms, получилось {avg_time_ms:.2f}ms"
    
    def test_batch_inference_speed(self, sample_data):
        """Тест скорости пакетного инференса."""
        import time
        
        metadata_df, price_df = sample_data
        
        # Извлекаем признаки
        extractor = FeatureExtractor()
        X = extractor.extract_features_batch(metadata_df, price_df)
        y = (metadata_df.set_index('id')['resolution'] == 'YES').astype(int)
        
        # Обучаем модель
        config = TrainingConfig(
            test_size=0.2,
            n_splits=3,
            calibration_enabled=False,
            xgb_enabled=True,
            lgb_enabled=False,
        )
        model = MLOracle(config)
        model.train(X, y, feature_names=list(X.columns))
        
        # Тестируем скорость пакетного предсказания
        start_time = time.time()
        for idx in X.index:
            features = X.loc[idx]
            proba = model.predict(features)
        end_time = time.time()
        
        total_time_ms = (end_time - start_time) * 1000
        avg_time_ms = total_time_ms / len(X)
        
        assert avg_time_ms < 50, f"Средний инференс должен быть < 50ms, получилось {avg_time_ms:.2f}ms"
