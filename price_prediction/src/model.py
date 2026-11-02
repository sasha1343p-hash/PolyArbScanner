import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import xgboost as xgb
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PriceMovementModel:
    def __init__(self, model_path='models/price_movement_model.pkl'):
        self.model_path = model_path
        self.model = None
        self.feature_columns = None
    
    def load_dataset(self, dataset_path='data/dataset.csv'):
        """Загружает датасет"""
        if not os.path.exists(dataset_path):
            logging.error(f"❌ Файл {dataset_path} не найден. Сначала запустите prepare_dataset.py")
            return None
        
        df = pd.read_csv(dataset_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Сортируем по времени
        df = df.sort_values('timestamp')
        
        logging.info(f"Загружен датасет: {len(df)} примеров")
        
        return df
    
    def train(self, df):
        """Обучает модель"""
        # Разделяем фичи и target
        exclude_cols = ['market_id', 'timestamp', 'target', 'current_price', 'future_price', 'price_change']
        feature_cols = [c for c in df.columns if c not in exclude_cols]
        
        X = df[feature_cols]
        y = df['target']
        
        self.feature_columns = feature_cols
        
        logging.info(f"Фичи: {len(feature_cols)}")
        logging.info(f"Примеры: {len(X)}")
        logging.info(f"Положительных: {y.sum()} ({y.mean():.1%})")
        
        # TimeSeriesSplit для временных рядов
        tscv = TimeSeriesSplit(n_splits=5)
        
        # Обучаем XGBoost
        self.model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=(y == 0).sum() / max((y == 1).sum(), 1),  # Балансировка классов
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            eval_metric='logloss'
        )
        
        # Кросс-валидация
        cv_scores = []
        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            self.model.fit(X_train, y_train, verbose=False)
            
            y_pred = self.model.predict(X_val)
            score = accuracy_score(y_val, y_pred)
            cv_scores.append(score)
        
        logging.info(f"\nCV Accuracy: {np.mean(cv_scores):.3f} ± {np.std(cv_scores):.3f}")
        
        # Финальное обучение на всех данных
        self.model.fit(X, y, verbose=False)
        
        # Создаем директорию если нужно
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # Сохраняем модель
        bundle = {
            'model': self.model,
            'feature_columns': self.feature_columns
        }
        joblib.dump(bundle, self.model_path)
        
        logging.info(f"✅ Модель сохранена в {self.model_path}")
        
        # Feature importance
        importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logging.info("\nТоп-10 важных фич:")
        logging.info(importance.head(10).to_string(index=False))
        
        return cv_scores
    
    def predict(self, features_df):
        """Предсказывает вероятность роста"""
        if self.model is None:
            if not os.path.exists(self.model_path):
                logging.error(f"❌ Модель не найдена: {self.model_path}")
                return None
            
            bundle = joblib.load(self.model_path)
            self.model = bundle['model']
            self.feature_columns = bundle['feature_columns']
        
        X = features_df[self.feature_columns]
        proba = self.model.predict_proba(X)[:, 1]
        
        return proba

if __name__ == "__main__":
    model = PriceMovementModel()
    
    # Загружаем данные
    df = model.load_dataset()
    
    if df is not None:
        # Обучаем модель
        model.train(df)
    else:
        logging.error("❌ Не удалось загрузить датасет")
