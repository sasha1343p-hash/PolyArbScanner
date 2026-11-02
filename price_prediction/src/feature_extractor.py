import pandas as pd
import numpy as np
from datetime import datetime
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TimeSeriesFeatureExtractor:
    def __init__(self, max_lookback=48):  # Уменьшили с 168 до 48 часов
        """
        max_lookback: максимальное окно в часах для расчета фич
        48 часов = 2 дня (умещается в 100 точек)
        """
        self.max_lookback = max_lookback
        # Окна для расчета фич (все <= max_lookback)
        self.lookback_windows = [1, 6, 12, 24, 48]
    
    def extract_features(self, price_df):
        """
        Извлекает фичи для каждой точки времени.
        Использует адаптивный lookback: для каждого рынка берем доступную историю.
        """
        price_df = price_df.copy()
        price_df['timestamp'] = pd.to_datetime(price_df['timestamp'])
        
        features_list = []
        markets_processed = 0
        
        for market_id, market_data in price_df.groupby('market_id'):
            market_data = market_data.sort_values('timestamp').reset_index(drop=True)
            
            # Минимум 24 точки для расчета базовых фич
            if len(market_data) < 24:
                continue
            
            markets_processed += 1
            
            # Для каждой точки извлекаем фичи
            # Начинаем с max_lookback, чтобы было достаточно истории
            start_idx = min(self.max_lookback, len(market_data) - 24)
            
            for i in range(start_idx, len(market_data)):
                current_row = market_data.iloc[i]
                history = market_data.iloc[:i+1]
                
                features = self._extract_single_point_features(
                    market_id, 
                    current_row['timestamp'],
                    history
                )
                
                if features:
                    features_list.append(features)
        
        features_df = pd.DataFrame(features_list)
        
        logging.info(f"\n{'='*60}")
        logging.info("ИЗВЛЕЧЕНИЕ ФИЧ")
        logging.info("="*60)
        logging.info(f"Рынков обработано: {markets_processed}")
        logging.info(f"Примеров извлечено: {len(features_df)}")
        if not features_df.empty:
            logging.info(f"Фич на пример: {len(features_df.columns) - 2}")
        logging.info("="*60)
        
        return features_df
    
    def _extract_single_point_features(self, market_id, timestamp, history):
        """Извлекает фичи для одной точки времени"""
        prices = history['yes_price'].values
        volumes = history['volume'].values
        
        if len(prices) < 24:
            return None
        
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
                returns = returns[~np.isnan(returns)]  # Убираем NaN
                volatility = np.std(returns) if len(returns) > 0 else 0
                features[f'volatility_{window}h'] = volatility
        
        # 4. Тренд (наклон линейной регрессии за разные окна)
        for window in self.lookback_windows:
            if len(prices) >= window:
                x = np.arange(window)
                y = prices[-window:]
                try:
                    trend = np.polyfit(x, y, 1)[0] if len(y) > 1 else 0
                except:
                    trend = 0
                features[f'trend_{window}h'] = trend
        
        # 5. Скользящие средние (SMA)
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
        for window in [24, 48]:  # 1 день, 2 дня
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
        
        # 10. Дополнительные фичи
        # Стандартное отклонение цены
        if len(prices) >= 24:
            features['price_std_24h'] = np.std(prices[-24:])
        
        # Максимальное изменение цены за 24 часа
        if len(prices) >= 24:
            price_changes = np.abs(np.diff(prices[-24:]) / prices[-24:-1])
            price_changes = price_changes[~np.isnan(price_changes)]
            features['max_price_change_24h'] = np.max(price_changes) if len(price_changes) > 0 else 0
        
        # Средний объем за 24 часа
        if len(volumes) >= 24:
            features['avg_volume_24h'] = np.mean(volumes[-24:])
        
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
    extractor = TimeSeriesFeatureExtractor(max_lookback=48)
    features_df = extractor.extract_features(price_df)
    
    if not features_df.empty:
        extractor.save_features(features_df, output_path='data/features.csv')
    else:
        logging.error("❌ Не удалось извлечь фичи")
