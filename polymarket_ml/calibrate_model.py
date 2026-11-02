import sqlite3
import pandas as pd
import numpy as np
import joblib
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss
import logging
import os
import warnings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ModelCalibrator:
    def __init__(self, db_path='polymarket_history.db', model_path='artifacts/ml_oracle_bundle.pkl'):
        self.db_path = db_path
        self.model_path = model_path
        self.scaler_path = model_path.replace('.pkl', '_scaler.pkl')
        
    def load_model(self):
        """Загружает модель и scaler"""
        logging.info(f"Загрузка модели из {self.model_path}...")
        model_bundle = joblib.load(self.model_path)
        model = model_bundle['model']
        
        # Загружаем scaler из отдельного файла
        if os.path.exists(self.scaler_path):
            scaler = joblib.load(self.scaler_path)
            logging.info(f"✅ Scaler загружен из {self.scaler_path}")
        else:
            logging.warning(f"⚠️  Scaler не найден: {self.scaler_path}")
            scaler = None
        
        return model, scaler, model_bundle
    
    def load_data(self):
        """Загружает данные для калибровки"""
        if not os.path.exists(self.db_path):
            logging.error(f"❌ База данных не найдена: {self.db_path}")
            return None, None
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            metadata_df = pd.read_sql_query('''
                SELECT id, question, end_date, resolution, created_at
                FROM market_metadata 
                WHERE resolution IS NOT NULL
                ORDER BY created_at
            ''', conn)
            
            price_df = pd.read_sql_query('''
                SELECT market_id, timestamp, yes_price, volume, liquidity
                FROM price_history
                ORDER BY market_id, timestamp
            ''', conn)
            
            conn.close()
            
            if metadata_df.empty or price_df.empty:
                logging.error("❌ Нет данных в базе")
                return None, None
            
            # Используем последние 30% данных для калибровки
            split_idx = int(len(metadata_df) * 0.7)
            calib_metadata = metadata_df.iloc[split_idx:].copy()
            
            logging.info(f"✅ Загружено {len(calib_metadata)} рынков для калибровки")
            
            return calib_metadata, price_df
            
        except Exception as e:
            conn.close()
            logging.error(f"❌ Ошибка загрузки данных: {e}")
            return None, None
    
    def extract_features(self, metadata_df, price_df):
        """Извлекает фичи"""
        from ml_oracle.feature_extractor import FeatureExtractor
        
        extractor = FeatureExtractor()
        features_df = extractor.extract_features_batch(metadata_df, price_df)
        
        # Добавляем market_id и resolution
        features_df['market_id'] = metadata_df['id'].values
        features_df['resolution'] = (metadata_df['resolution'] == 'YES').astype(int).values
        
        return features_df
    
    def calibrate(self, method='isotonic'):
        """Калибрует модель"""
        # Загружаем модель
        try:
            model, scaler, model_bundle = self.load_model()
        except Exception as e:
            logging.error(f"❌ Ошибка загрузки модели: {e}")
            return False
        
        # Загружаем данные
        calib_metadata, price_df = self.load_data()
        if calib_metadata is None or price_df is None:
            return False
        
        if calib_metadata.empty:
            logging.error("❌ Нет данных для калибровки")
            return False
        
        # Извлекаем фичи
        logging.info("Извлечение фич...")
        try:
            features_df = self.extract_features(calib_metadata, price_df)
        except Exception as e:
            logging.error(f"❌ Ошибка извлечения фич: {e}")
            return False
        
        if features_df.empty:
            logging.error("❌ Не удалось извлечь фичи")
            return False
        
        logging.info(f"✅ Извлечено {len(features_df)} примеров с {len(features_df.columns)} признаками")
        
        # Разделяем фичи и целевую переменную
        X = features_df.drop(['market_id', 'resolution'], axis=1).copy()
        y = features_df['resolution'].copy()
        
        # Сбрасываем индексы
        X = X.reset_index(drop=True)
        y = y.reset_index(drop=True)
        
        # Проверяем наличие обоих классов
        unique_classes = np.unique(y)
        if len(unique_classes) < 2:
            logging.error(f"❌ В данных для калибровки только один класс: {unique_classes[0]}")
            logging.error("   Калибровка невозможна")
            return False
        
        # Получаем список признаков, которые ожидает модель
        if hasattr(model, 'feature_names_in_'):
            expected_features = list(model.feature_names_in_)
        elif isinstance(model_bundle, dict) and 'feature_names' in model_bundle:
            expected_features = model_bundle['feature_names']
        else:
            expected_features = X.columns.tolist()
            logging.warning("⚠️  Не удалось определить ожидаемые признаки модели")
        
        # Фильтруем и упорядочиваем признаки
        missing_features = set(expected_features) - set(X.columns)
        extra_features = set(X.columns) - set(expected_features)
        
        if missing_features:
            logging.warning(f"⚠️  Отсутствуют {len(missing_features)} признаков: {list(missing_features)[:5]}...")
            for feat in missing_features:
                X[feat] = 0
        
        if extra_features:
            logging.info(f"ℹ️  Игнорируем {len(extra_features)} лишних признаков")
        
        X = X[expected_features]
        
        # Масштабируем фичи
        if scaler is not None:
            X_scaled = scaler.transform(X)
        else:
            logging.warning("⚠️  Scaler не загружен, используем ненормализованные данные")
            X_scaled = X
        
        # Очищаем модель от callbacks (для XGBoost)
        if hasattr(model, 'callbacks'):
            model.callbacks = []
        if hasattr(model, 'set_params'):
            try:
                model.set_params(early_stopping_rounds=None)
            except Exception:
                pass
        
        # Калибруем модель
        logging.info(f"Калибровка модели методом '{method}'...")
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            calibrated_model = CalibratedClassifierCV(
                model, 
                method=method, 
                cv=min(5, len(unique_classes) * 2)  # Уменьшаем cv если мало данных
            )
            calibrated_model.fit(X_scaled, y)
        
        # Сравниваем Brier Score до и после
        y_pred_proba_before = model.predict_proba(X_scaled)[:, 1]
        y_pred_proba_after = calibrated_model.predict_proba(X_scaled)[:, 1]
        
        brier_before = brier_score_loss(y, y_pred_proba_before)
        brier_after = brier_score_loss(y, y_pred_proba_after)
        
        logging.info("\n" + "=" * 60)
        logging.info("РЕЗУЛЬТАТЫ КАЛИБРОВКИ")
        logging.info("=" * 60)
        logging.info(f"Brier Score до калибровки: {brier_before:.4f}")
        logging.info(f"Brier Score после калибровки: {brier_after:.4f}")
        
        improvement = brier_before - brier_after
        improvement_pct = (improvement / brier_before * 100) if brier_before > 0 else 0
        logging.info(f"Улучшение: {improvement:.4f} ({improvement_pct:.1f}%)")
        logging.info("=" * 60)
        
        if brier_after < brier_before:
            logging.info("✅ Калибровка улучшила модель!")
            
            # Сохраняем калиброванную модель
            model_bundle['model'] = calibrated_model
            output_path = 'artifacts/ml_oracle_bundle_calibrated.pkl'
            
            # Создаём директорию если нужно
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            joblib.dump(model_bundle, output_path)
            logging.info(f"✅ Калиброванная модель сохранена в {output_path}")
            
            return True
        else:
            logging.warning("⚠️  Калибровка не улучшила модель. Оставляем оригинал.")
            return False

if __name__ == "__main__":
    calibrator = ModelCalibrator()
    success = calibrator.calibrate(method='isotonic')
    
    if success:
        print("\n✅ Калибровка завершена успешно!")
        print("Используйте калиброванную модель: artifacts/ml_oracle_bundle_calibrated.pkl")
    else:
        print("\n❌ Калибровка не удалась или не улучшила модель")
