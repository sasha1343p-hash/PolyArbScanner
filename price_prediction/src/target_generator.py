import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TargetGenerator:
    def __init__(self, db_path='polymarket_history.db'):
        self.db_path = db_path
        
    def generate_targets(
        self, 
        price_increase_threshold=0.05,  # 5% рост
        horizon_hours=24,               # за 24 часа
        min_data_points=48              # минимум 48 часов данных
    ):
        """
        Создает целевую переменную для обучения.
        
        Для каждой точки времени t:
        - Берем цену в момент t
        - Смотрим цену в момент t + horizon_hours
        - Если цена выросла на price_increase_threshold → target = 1
        - Иначе → target = 0
        
        Возвращает DataFrame с колонками:
        - market_id
        - timestamp (момент предсказания)
        - current_price (цена в момент t)
        - future_price (цена в момент t + horizon)
        - price_change (процентное изменение)
        - target (1 если рост >= threshold, иначе 0)
        """
        if not os.path.exists(self.db_path):
            logging.error(f"❌ База данных не найдена: {self.db_path}")
            return pd.DataFrame()
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Загружаем все данные
            price_df = pd.read_sql_query('''
                SELECT market_id, timestamp, yes_price, volume, liquidity
                FROM price_history
                WHERE yes_price IS NOT NULL
                ORDER BY market_id, timestamp
            ''', conn)
            
            conn.close()
            
            if price_df.empty:
                logging.error("❌ Нет данных о ценах")
                return pd.DataFrame()
            
            # Преобразуем timestamp в datetime
            price_df['timestamp'] = pd.to_datetime(price_df['timestamp'])
            
            logging.info(f"✅ Загружено {len(price_df)} записей о ценах")
            
            # Генерируем targets для каждого рынка
            targets_list = []
            
            for market_id, market_data in price_df.groupby('market_id'):
                market_data = market_data.sort_values('timestamp').reset_index(drop=True)
                
                if len(market_data) < min_data_points:
                    continue
                
                # Для каждой точки (кроме последних horizon_hours)
                for i in range(len(market_data) - horizon_hours):
                    current_row = market_data.iloc[i]
                    future_row = market_data.iloc[i + horizon_hours]
                    
                    current_price = current_row['yes_price']
                    future_price = future_row['yes_price']
                    
                    if current_price <= 0:
                        continue
                    
                    price_change = (future_price - current_price) / current_price
                    target = 1 if price_change >= price_increase_threshold else 0
                    
                    targets_list.append({
                        'market_id': market_id,
                        'timestamp': current_row['timestamp'],
                        'current_price': current_price,
                        'future_price': future_price,
                        'price_change': price_change,
                        'target': target,
                        'volume': current_row['volume'],
                        'liquidity': current_row['liquidity']
                    })
            
            targets_df = pd.DataFrame(targets_list)
            
            logging.info(f"\n{'='*60}")
            logging.info("ГЕНЕРАЦИЯ ЦЕЛЕВОЙ ПЕРЕМЕННОЙ")
            logging.info("="*60)
            logging.info(f"Всего примеров: {len(targets_df)}")
            logging.info(f"Порог роста: {price_increase_threshold:.1%}")
            logging.info(f"Горизонт: {horizon_hours} часов")
            
            if not targets_df.empty:
                positive_count = targets_df['target'].sum()
                negative_count = (targets_df['target'] == 0).sum()
                positive_pct = targets_df['target'].mean()
                
                logging.info(f"Положительных примеров (рост >= {price_increase_threshold:.1%}): {positive_count} ({positive_pct:.1%})")
                logging.info(f"Отрицательных примеров: {negative_count} ({1 - positive_pct:.1%})")
                logging.info(f"Средний price_change: {targets_df['price_change'].mean():.2%}")
                logging.info(f"Медианный price_change: {targets_df['price_change'].median():.2%}")
            else:
                logging.warning("⚠️  Не удалось сгенерировать targets")
            
            logging.info("="*60)
            
            return targets_df
            
        except Exception as e:
            conn.close()
            logging.error(f"❌ Ошибка генерации targets: {e}")
            return pd.DataFrame()
    
    def save_targets(self, targets_df, output_path='data/targets.csv'):
        """Сохраняет targets в CSV"""
        # Создаем директорию если нужно
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        targets_df.to_csv(output_path, index=False)
        logging.info(f"✅ Targets сохранены в {output_path}")

if __name__ == "__main__":
    generator = TargetGenerator()
    
    # Генерируем targets с разными параметрами
    targets_df = generator.generate_targets(
        price_increase_threshold=0.05,  # 5% рост
        horizon_hours=24,               # за 24 часа
        min_data_points=48
    )
    
    if not targets_df.empty:
        generator.save_targets(targets_df, output_path='data/targets.csv')
    else:
        logging.error("❌ Не удалось сгенерировать targets")
