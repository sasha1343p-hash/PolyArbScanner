import sqlite3
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, brier_score_loss, classification_report,
    roc_curve, precision_recall_curve
)
from datetime import datetime
import logging
import os

# Опциональные библиотеки для визуализации
try:
    import matplotlib
    matplotlib.use('Agg')  # Не требует GUI
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️  matplotlib/seaborn не установлены. Графики не будут построены.")
    print("   Для графиков выполните: pip install matplotlib seaborn")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ModelEvaluator:
    def __init__(self, db_path='../polymarket_history.db', model_path='artifacts/ml_oracle_bundle.pkl'):
        self.db_path = db_path
        self.model_path = model_path
        self.model_bundle = None
        self.model = None
        self.scaler = None
        
    def load_model(self):
        """Загружает обученную модель и scaler"""
        try:
            # Загружаем модель
            self.model_bundle = joblib.load(self.model_path)
            self.model = self.model_bundle['model']
            logging.info(f"✅ Модель загружена из {self.model_path}")
            
            # Загружаем scaler из отдельного файла
            scaler_path = self.model_path.replace('.pkl', '_scaler.pkl')
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                logging.info(f"✅ Scaler загружен из {scaler_path}")
            else:
                logging.warning(f"⚠️  Scaler не найден: {scaler_path}")
                logging.warning("   Признаки не будут нормализованы")
                self.scaler = None
            
            return True
        except Exception as e:
            logging.error(f"❌ Ошибка загрузки модели: {e}")
            return False
    
    def load_test_data(self):
        """Загружает тестовые данные (последние 20% по времени)"""
        conn = sqlite3.connect(self.db_path)
        
        # Загружаем метаданные
        metadata_df = pd.read_sql_query('''
            SELECT id, question, end_date, resolution, created_at
            FROM market_metadata 
            WHERE resolution IS NOT NULL
            ORDER BY created_at
        ''', conn)
        
        # Загружаем историю цен
        price_df = pd.read_sql_query('''
            SELECT market_id, timestamp, yes_price, volume, liquidity
            FROM price_history
            ORDER BY market_id, timestamp
        ''', conn)
        
        conn.close()
        
        if metadata_df.empty or price_df.empty:
            logging.error("Нет данных для оценки")
            return None, None
        
        # Разделяем на train/test по времени (последние 20%)
        split_idx = int(len(metadata_df) * 0.8)
        test_metadata = metadata_df.iloc[split_idx:]
        
        logging.info(f"Тестовая выборка: {len(test_metadata)} рынков")
        
        return test_metadata, price_df
    
    def extract_features(self, metadata_df, price_df):
        """Извлекает фичи для тестовых данных"""
        from ml_oracle.feature_extractor import FeatureExtractor
        
        extractor = FeatureExtractor()
        features_df = extractor.extract_features_batch(metadata_df, price_df)
        
        # Добавляем market_id и resolution
        features_df['market_id'] = metadata_df['id'].values
        features_df['resolution'] = (metadata_df['resolution'] == 'YES').astype(int).values
        
        return features_df
    
    def evaluate(self, features_df):
        """Проводит полную оценку модели"""
        if features_df.empty:
            logging.error("Нет фич для оценки")
            return None
        
        # Разделяем фичи и целевую переменную
        X = features_df.drop(['market_id', 'resolution'], axis=1).copy()
        y = features_df['resolution'].copy()
        
        # Сбрасываем индексы для безопасности
        X = X.reset_index(drop=True)
        y = y.reset_index(drop=True)
        
        # Получаем список признаков, которые ожидает модель
        if hasattr(self.model, 'feature_names_in_'):
            expected_features = list(self.model.feature_names_in_)
        elif isinstance(self.model_bundle, dict) and 'feature_names' in self.model_bundle:
            expected_features = self.model_bundle['feature_names']
        else:
            # Если не можем определить, используем все признаки
            expected_features = X.columns.tolist()
            logging.warning("⚠️  Не удалось определить ожидаемые признаки модели")
        
        # Фильтруем и упорядочиваем признаки
        missing_features = set(expected_features) - set(X.columns)
        extra_features = set(X.columns) - set(expected_features)
        
        if missing_features:
            logging.warning(f"⚠️  Отсутствуют {len(missing_features)} признаков: {list(missing_features)[:5]}...")
            # Добавляем нулевые значения для отсутствующих признаков
            for feat in missing_features:
                X[feat] = 0
        
        if extra_features:
            logging.info(f"ℹ️  Игнорируем {len(extra_features)} лишних признаков")
        
        # Упорядочиваем признаки в правильном порядке
        X = X[expected_features]
        
        # Масштабируем фичи (если scaler загружен)
        if self.scaler is not None:
            X_scaled = self.scaler.transform(X)
        else:
            logging.warning("⚠️  Scaler не загружен, используем ненормализованные данные")
            X_scaled = X
        
        # Проверяем, что в выборке есть оба класса
        unique_classes = np.unique(y)
        if len(unique_classes) < 2:
            logging.error(f"❌ В тестовой выборке только один класс: {unique_classes[0]}")
            logging.error("   Невозможно вычислить все метрики")
            return None
        
        # Предсказания
        y_pred = self.model.predict(X_scaled)
        
        # Получаем вероятности (обрабатываем разные форматы вывода)
        proba_raw = self.model.predict_proba(X_scaled)
        if proba_raw.ndim == 1:
            y_pred_proba = proba_raw
        else:
            y_pred_proba = proba_raw[:, 1]
        
        # Метрики
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, zero_division=0),
            'recall': recall_score(y, y_pred, zero_division=0),
            'f1': f1_score(y, y_pred, zero_division=0),
            'auc_roc': roc_auc_score(y, y_pred_proba),
            'brier_score': brier_score_loss(y, y_pred_proba)
        }
        
        return metrics, y, y_pred, y_pred_proba
    
    def plot_results(self, y, y_pred_proba):
        """Строит графики для визуализации качества"""
        if not HAS_MATPLOTLIB:
            logging.warning("⚠️  matplotlib не установлен, пропускаем построение графиков")
            return
        
        # Преобразуем в numpy arrays для безопасности
        y = np.array(y)
        y_pred_proba = np.array(y_pred_proba)
        
        # Удаляем NaN и inf
        valid_mask = ~(np.isnan(y_pred_proba) | np.isinf(y_pred_proba))
        if not valid_mask.all():
            logging.warning(f"⚠️  Удалено {sum(~valid_mask)} предсказаний с NaN/inf")
            y = y[valid_mask]
            y_pred_proba = y_pred_proba[valid_mask]
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. ROC Curve
        fpr, tpr, _ = roc_curve(y, y_pred_proba)
        axes[0, 0].plot(fpr, tpr, label=f'AUC = {roc_auc_score(y, y_pred_proba):.3f}')
        axes[0, 0].plot([0, 1], [0, 1], 'k--')
        axes[0, 0].set_xlabel('False Positive Rate')
        axes[0, 0].set_ylabel('True Positive Rate')
        axes[0, 0].set_title('ROC Curve')
        axes[0, 0].legend()
        
        # 2. Precision-Recall Curve
        precision, recall, _ = precision_recall_curve(y, y_pred_proba)
        axes[0, 1].plot(recall, precision)
        axes[0, 1].set_xlabel('Recall')
        axes[0, 1].set_ylabel('Precision')
        axes[0, 1].set_title('Precision-Recall Curve')
        
        # 3. Calibration Plot
        # Разбиваем предсказания на бины
        bins = np.linspace(0, 1, 11)
        bin_indices = np.digitize(y_pred_proba, bins) - 1
        bin_indices = np.clip(bin_indices, 0, 9)
        
        bin_means = []
        bin_true_means = []
        for i in range(10):
            mask = bin_indices == i
            if mask.sum() > 0:
                bin_means.append(y_pred_proba[mask].mean())
                bin_true_means.append(y[mask].mean())
        
        # Строим график только если есть данные
        if len(bin_means) > 0:
            axes[1, 0].plot(bin_means, bin_true_means, 'o-')
            axes[1, 0].plot([0, 1], [0, 1], 'k--')
            axes[1, 0].set_xlabel('Predicted Probability')
            axes[1, 0].set_ylabel('Actual Frequency')
            axes[1, 0].set_title('Calibration Plot')
        else:
            axes[1, 0].text(0.5, 0.5, 'Нет данных для калибровки', 
                          ha='center', va='center', transform=axes[1, 0].transAxes)
        
        # 4. Distribution of predictions
        no_mask = y == 0
        yes_mask = y == 1
        
        if no_mask.sum() > 0:
            axes[1, 1].hist(y_pred_proba[no_mask], bins=20, alpha=0.5, label='NO (actual)')
        if yes_mask.sum() > 0:
            axes[1, 1].hist(y_pred_proba[yes_mask], bins=20, alpha=0.5, label='YES (actual)')
        
        axes[1, 1].set_xlabel('Predicted Probability')
        axes[1, 1].set_ylabel('Count')
        axes[1, 1].set_title('Distribution of Predictions')
        if no_mask.sum() > 0 or yes_mask.sum() > 0:
            axes[1, 1].legend()
        
        plt.tight_layout()
        plt.savefig('model_evaluation.png', dpi=150)
        logging.info("📊 Графики сохранены в model_evaluation.png")
        plt.close()
    
    def run_full_evaluation(self):
        """Запускает полную оценку модели"""
        logging.info("=" * 60)
        logging.info("НАЧАЛО ОЦЕНКИ МОДЕЛИ")
        logging.info("=" * 60)
        
        # Загружаем модель
        if not self.load_model():
            return False
        
        # Загружаем данные
        test_metadata, price_df = self.load_test_data()
        if test_metadata is None or price_df is None:
            logging.error("❌ Не удалось загрузить тестовые данные")
            return False
        
        if test_metadata.empty:
            logging.error("❌ Тестовая выборка пуста")
            return False
        
        # Извлекаем фичи
        logging.info("Извлечение фич...")
        try:
            features_df = self.extract_features(test_metadata, price_df)
        except Exception as e:
            logging.error(f"❌ Ошибка извлечения фич: {e}")
            return False
        
        if features_df.empty:
            logging.error("❌ Не удалось извлечь фичи")
            return False
        
        logging.info(f"✅ Извлечено {len(features_df)} примеров с {len(features_df.columns)} признаками")
        
        # Оцениваем
        logging.info("Оценка модели...")
        results = self.evaluate(features_df)
        if results is None:
            logging.error("❌ Не удалось оценить модель")
            return False
        
        metrics, y, y_pred, y_pred_proba = results
        
        # Выводим метрики
        logging.info("\n" + "=" * 60)
        logging.info("МЕТРИКИ КАЧЕСТВА МОДЕЛИ")
        logging.info("=" * 60)
        logging.info(f"Accuracy:      {metrics['accuracy']:.3f}  {'✅' if metrics['accuracy'] >= 0.65 else '❌'}")
        logging.info(f"Precision:     {metrics['precision']:.3f}")
        logging.info(f"Recall:        {metrics['recall']:.3f}")
        logging.info(f"F1 Score:      {metrics['f1']:.3f}")
        logging.info(f"AUC-ROC:       {metrics['auc_roc']:.3f}  {'✅' if metrics['auc_roc'] >= 0.65 else '❌'}")
        logging.info(f"Brier Score:   {metrics['brier_score']:.3f}  {'✅' if metrics['brier_score'] <= 0.25 else '❌'}")
        logging.info("=" * 60)
        
        # Classification report
        logging.info("\nClassification Report:")
        try:
            logging.info(classification_report(y, y_pred, target_names=['NO', 'YES']))
        except ValueError as e:
            logging.warning(f"⚠️  Не удалось создать classification report: {e}")
            logging.info(f"   Распределение предсказаний: NO={sum(y_pred==0)}, YES={sum(y_pred==1)}")
        
        # Строим графики (если matplotlib доступен)
        if HAS_MATPLOTLIB:
            try:
                self.plot_results(y, y_pred_proba)
            except Exception as e:
                logging.warning(f"⚠️  Ошибка при построении графиков: {e}")
        else:
            logging.info("ℹ️  Пропускаем построение графиков (matplotlib не установлен)")
        
        # Рекомендации
        logging.info("\n" + "=" * 60)
        logging.info("РЕКОМЕНДАЦИИ")
        logging.info("=" * 60)
        
        if metrics['auc_roc'] < 0.60:
            logging.warning("⚠️  AUC-ROC слишком низкий. Модель хуже случайного угадывания.")
            logging.warning("   → Собери больше данных или добавь новые фичи.")
        elif metrics['auc_roc'] < 0.65:
            logging.warning("⚠️  AUC-ROC на грани. Модель работает, но слабо.")
            logging.warning("   → Попробуй другие алгоритмы (LightGBM, CatBoost).")
        else:
            logging.info("✅ AUC-ROC хороший. Модель работает адекватно.")
        
        if metrics['brier_score'] > 0.30:
            logging.warning("⚠️  Brier Score высокий. Вероятности не калиброваны.")
            logging.warning("   → Запусти калибровку (calibrate_model.py).")
        else:
            logging.info("✅ Brier Score хороший. Вероятности калиброваны.")
        
        return True

if __name__ == "__main__":
    evaluator = ModelEvaluator()
    evaluator.run_full_evaluation()
