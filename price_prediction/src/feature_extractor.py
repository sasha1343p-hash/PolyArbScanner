import pandas as pd
import numpy as np
from datetime import datetime
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TimeSeriesFeatureExtractor:
    def __init__(self, lookback_windows=[1, 6, 12, 24, 48, 168]):
        """
        lookback_windows: список окон в часах для расчета фич
        [1, 6, 12, 24, 48, 168] = 1h, 6h, 12h, 1d, 2d, 1w
        """
        self.lookback_windows = lookback_windows
    
    def extract_features(self, price_df):
        """
        Извлекает фичи для каждой точки времени.
        
        Вход: DataFrame с колонками [market_id, timestamp, yes_price, volume, liquidity]
        Выход: DataFrame с фичами для каждой точки
        """
        price_df = price_df.copy()
        price_df['timestamp'] = pd.to_datetime(price_df['timestamp'])
        
        features_list = []
        
        for market_id, market_data in price_df.groupby('market_id'):
            market_data = market_data.sort_values('timestamp').reset_index(drop=True)
            
            if len(market_data) < max(self.lookback_windows):
                continue
            
            # Для каждой точки извлекаем фичи
            for i in range(max(self.lookback_windows), len(market_data)):
                current_row = market_data.iloc[i]
                history = market_data.iloc[:i+1]
                
                features = self._extract_single_point_features(
                    market_id, 
                    current_row['timestamp'],
                    history
                )
                
                features_list.append(features)
        
        features_df = pd.DataFrame(features_list)
        
        logging.info(f"Извлечено {len(features_df)} примеров с {len(features_df.columns) - 2} фичами")
        
        return features_df
    
    def _extract_single_point_features(self, market_id, timestamp, history):
        """Извлекает фичи для одной точки времени"""
        prices = history['yes_price'].values
        volumes = history['volume'].values
        
        features = {
            'market_id': market_id,
            'timestamp': timestamp,
        }
        
        # 1. Текущая цена
        features['current_price'] = prices[-1]
        
        # 2. Momentum (изменение цены за разные окна)
        for window in self.lookback_windows:
            if len(prices) >= window:
                price_change = (prices[-1] - prices[-window]) / prices[-window] if prices[-window] > 0 else 0
                features[f'momentum_{window}h'] = price_change
        
        # 3. Волатильность (стандартное отклонение returns за разные окна)
        for window in self.lookback_windows:
            if len(prices) >= window:
                returns = np.diff(prices[-window:]) / prices[-window:-1]
                volatility = np.std(returns) if len(returns) > 0 else 0
                features[f'volatility_{window}h'] = volatility
        
        # 4. Тренд (наклон линейной регрессии за разные окна)
        for window in self.lookback_windows:
            if len(prices) >= window:
                x = np.arange(window)
                y = prices[-window:]
                trend = np.polyfit(x, y, 1)[0] if len(y) > 1 else 0
                features[f'trend_{window}h'] = trend
        
        # 5. Скользящие средние
        for window in [6, 12, 24, 48]:
            if len(prices) >= window:
                sma = np.mean(prices[-window:])
                features[f'sma_{window}h'] = sma
                # Цена относительно SMA
                features[f'price_vs_sma_{window}h'] = (prices[-1] - sma) / sma if sma > 0 else 0
        
        # 6. RSI-подобный индикатор
        for window in [14, 24]:
            if len(prices) >= window:
                deltas = np.diff(prices[-window:])
                gains = np.sum(deltas[deltas > 0])
                losses = np.abs(np.sum(deltas[deltas < 0]))
                rs = gains / losses if losses > 0 else 100
                rsi = 100 - (100 / (1 + rs))
                features[f'rsi_{window}h'] = rsi
        
        # 7. Объемные фичи
        for window in [6, 24]:
            if len(volumes) >= window:
                avg_volume = np.mean(volumes[-window:])
                features[f'avg_volume_{window}h'] = avg_volume
                # Текущий объем относительно среднего
                features[f'volume_ratio_{window}h'] = volumes[-1] / avg_volume if avg_volume > 0 else 1
        
        # 8. Расстояние от экстремумов
        for window in [24, 168]:  # 1 день, 1 неделя
            if len(prices) >= window:
                max_price = np.max(prices[-window:])
                min_price = np.min(prices[-window:])
                price_range = max_price - min_price
                
                if price_range > 0:
                    features[f'distance_from_max_{window}h'] = (max_price - prices[-1]) / price_range
                    features[f'distance_from_min_{window}h'] = (prices[-1] - min_price) / price_range
                else:
                    features[f'distance_from_max_{window}h'] = 0
                    features[f'distance_from_min_{window}h'] = 0
        
        # 9. Временные фичи
        features['hour_of_day'] = timestamp.hour
        features['day_of_week'] = timestamp.dayofweek
        
        return features
    
    def save_features(self, features_df, output_path='data/features.csv'):
        """Сохраняет фичи в CSV"""
        # Создаем директорию если нужно
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        features_df.to_csv(output_path, index=False)
        logging.info(f"✅ Фичи сохранены в {output_path}")

if __name__ == "__main__":
    import sqlite3
    
    # Загружаем данные
    db_path = '../polymarket_history.db'
    if not os.path.exists(db_path):
        logging.error(f"❌ База данных не найдена: {db_path}")
        exit(1)
    
    conn = sqlite3.connect(db_path)
    price_df = pd.read_sql_query('''
        SELECT market_id, timestamp, yes_price, volume, liquidity
        FROM price_history
        WHERE yes_price IS NOT NULL
        ORDER BY market_id, timestamp
    ''', conn)
    conn.close()
    
    logging.info(f"Загружено {len(price_df)} записей")
    
    # Извлекаем фичи
    extractor = TimeSeriesFeatureExtractor(lookback_windows=[1, 6, 12, 24, 48, 168])
    features_df = extractor.extract_features(price_df)
    
    if not features_df.empty:
        extractor.save_features(features_df, output_path='data/features.csv')
    else:
        logging.error("❌ Не удалось извлечь фичи")
