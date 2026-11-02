"""
Скрипт для создания тестовой базы данных.

Создаёт polymarket_history.db с тестовыми данными для демонстрации.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys


def create_test_database(db_path: str = "polymarket_history.db"):
    """
    Создаёт тестовую базу данных с синтетическими данными.
    
    Args:
        db_path: Путь к файлу базы данных
    """
    print(f"Создание тестовой базы данных: {db_path}")
    
    # Устанавливаем seed для воспроизводимости
    np.random.seed(42)
    
    # Параметры
    n_markets = 200
    n_price_points = 100
    
    # Подключение к БД
    conn = sqlite3.connect(db_path)
    
    try:
        # ========================================
        # Создание таблицы market_metadata
        # ========================================
        print("  → Создание таблицы market_metadata...")
        
        metadata = []
        for i in range(n_markets):
            # Генерируем вопросы разных типов
            if i % 4 == 0:
                question = f"Will BTC be above ${60000 + i * 500} by {datetime.now() + timedelta(days=i)}?"
            elif i % 4 == 1:
                question = f"Will ETH reach ${3000 + i * 50}?"
            elif i % 4 == 2:
                question = f"Will Trump win the election?"
            else:
                question = f"Will Lakers win NBA Finals?"
            
            metadata.append({
                'id': f'market-{i:03d}',
                'question': question,
                'end_date': (datetime.now() + timedelta(days=i)).isoformat(),
                'resolution': np.random.choice(['YES', 'NO'], p=[0.55, 0.45]),
                'created_at': (datetime.now() - timedelta(days=365)).isoformat(),
            })
        
        metadata_df = pd.DataFrame(metadata)
        metadata_df.to_sql('market_metadata', conn, if_exists='replace', index=False)
        print(f"    ✅ Создано {len(metadata_df)} рынков")
        
        # ========================================
        # Создание таблицы price_history
        # ========================================
        print("  → Создание таблицы price_history...")
        
        prices = []
        for market in metadata:
            market_id = market['id']
            
            # Базовая цена с трендом
            base_price = np.random.uniform(0.3, 0.7)
            trend = np.random.uniform(-0.001, 0.001)
            
            for h in range(n_price_points):
                # Добавляем шум и тренд
                noise = np.random.normal(0, 0.05)
                price = base_price + trend * h + noise
                
                # Ограничиваем диапазон [0.01, 0.99]
                price = max(0.01, min(0.99, price))
                
                prices.append({
                    'market_id': market_id,
                    'timestamp': (datetime.now() - timedelta(hours=n_price_points - h)).isoformat(),
                    'yes_price': price,
                    'no_price': 1 - price,
                    'volume': np.random.uniform(1000, 10000),
                    'liquidity': np.random.uniform(5000, 50000),
                })
        
        prices_df = pd.DataFrame(prices)
        prices_df.to_sql('price_history', conn, if_exists='replace', index=False)
        print(f"    ✅ Создано {len(prices_df)} записей цен")
        
        # ========================================
        # Закрытие соединения
        # ========================================
        conn.close()
        
        print(f"\n✅ База данных успешно создана: {db_path}")
        print(f"   - Рынков: {n_markets}")
        print(f"   - Записей цен: {n_markets * n_price_points}")
        
        return True
        
    except Exception as e:
        conn.close()
        print(f"\n❌ Ошибка создания базы данных: {e}", file=sys.stderr)
        return False


if __name__ == '__main__':
    success = create_test_database()
    sys.exit(0 if success else 1)
