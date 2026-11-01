import sqlite3
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, brier_score_loss, classification_report,
    roc_curve, precision_recall_curve
)
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ModelEvaluator:
    def __init__(self, db_path='../polymarket_history.db', model_path='artifacts/ml_oracle_bundle.pkl'):
        self.db_path = db_path
        self.model_path = model_path
        self.model_bundle = None
        self.model = None
        self.scaler = None
        
    def load_model(self):
        """Загружает обученную модель"""
        try:
            self.model_bundle = joblib.load(self.model_path)
            self.model = self.model_bundle['model']
            self.scaler = self.model_bundle['scaler']
            logging.info(f"✅ Модель загружена из {self.model_path}")
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
        
        return features_df
    
    def evaluate(self, features_df):
        """Проводит полную оценку модели"""
        if features_df.empty:
            logging.error("Нет фич для оценки")
            return None
        
        # Разделяем фичи и целевую переменную
        X = features_df.drop(['market_id', 'resolution'], axis=1)
        y = features_df['resolution']
        
        # Масштабируем фичи
        X_scaled = self.scaler.transform(X)
        
        # Предсказания
        y_pred = self.model.predict(X_scaled)
        y_pred_proba = self.model.predict_proba(X_scaled)[:, 1]
        
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
        
        axes[1, 0].plot(bin_means, bin_true_means, 'o-')
        axes[1, 0].plot([0, 1], [0, 1], 'k--')
        axes[1, 0].set_xlabel('Predicted Probability')
        axes[1, 0].set_ylabel('Actual Frequency')
        axes[1, 0].set_title('Calibration Plot')
        
        # 4. Distribution of predictions
        axes[1, 1].hist(y_pred_proba[y == 0], bins=20, alpha=0.5, label='NO (actual)')
        axes[1, 1].hist(y_pred_proba[y == 1], bins=20, alpha=0.5, label='YES (actual)')
        axes[1, 1].set_xlabel('Predicted Probability')
        axes[1, 1].set_ylabel('Count')
        axes[1, 1].set_title('Distribution of Predictions')
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
        if test_metadata is None:
            return False
        
        # Извлекаем фичи
        logging.info("Извлечение фич...")
        features_df = self.extract_features(test_metadata, price_df)
        
        if features_df.empty:
            logging.error("Не удалось извлечь фичи")
            return False
        
        # Оцениваем
        logging.info("Оценка модели...")
        results = self.evaluate(features_df)
        if results is None:
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
        logging.info(classification_report(y, y_pred, target_names=['NO', 'YES']))
        
        # Строим графики
        self.plot_results(y, y_pred_proba)
        
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
