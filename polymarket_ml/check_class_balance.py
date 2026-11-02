import sqlite3
import pandas as pd
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_balance():
    db_path = 'polymarket_history.db'
    
    # Проверяем наличие базы данных
    if not os.path.exists(db_path):
        logging.error(f"❌ База данных не найдена: {db_path}")
        logging.info("💡 Создайте тестовую БД: python create_test_db.py")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Загружаем все данные
        metadata_df = pd.read_sql_query('''
            SELECT id, resolution, created_at
            FROM market_metadata 
            WHERE resolution IS NOT NULL
            ORDER BY created_at
        ''', conn)
        
        conn.close()
        
        if metadata_df.empty:
            logging.error("❌ Нет данных с resolution в базе")
            return
        
        # Разделяем на train/test (80/20)
        split_idx = int(len(metadata_df) * 0.8)
        train_df = metadata_df.iloc[:split_idx]
        test_df = metadata_df.iloc[split_idx:]
        
        # Считаем распределение классов
        logging.info("\n" + "=" * 60)
        logging.info("РАСПРЕДЕЛЕНИЕ КЛАССОВ")
        logging.info("=" * 60)
        
        logging.info(f"\n📊 ВСЕ ДАННЫЕ:")
        logging.info(f"   Всего рынков: {len(metadata_df)}")
        yes_count = (metadata_df['resolution'] == 'YES').sum()
        no_count = (metadata_df['resolution'] == 'NO').sum()
        yes_pct = (metadata_df['resolution'] == 'YES').mean()
        no_pct = (metadata_df['resolution'] == 'NO').mean()
        logging.info(f"   YES: {yes_count} ({yes_pct:.1%})")
        logging.info(f"   NO:  {no_count} ({no_pct:.1%})")
        
        logging.info(f"\n🎯 ТРЕНИРОВОЧНАЯ ВЫБОРКА (80%):")
        logging.info(f"   Всего рынков: {len(train_df)}")
        train_yes = (train_df['resolution'] == 'YES').sum()
        train_no = (train_df['resolution'] == 'NO').sum()
        train_yes_pct = (train_df['resolution'] == 'YES').mean()
        train_no_pct = (train_df['resolution'] == 'NO').mean()
        logging.info(f"   YES: {train_yes} ({train_yes_pct:.1%})")
        logging.info(f"   NO:  {train_no} ({train_no_pct:.1%})")
        
        logging.info(f"\n🧪 ТЕСТОВАЯ ВЫБОРКА (20%):")
        logging.info(f"   Всего рынков: {len(test_df)}")
        test_yes = (test_df['resolution'] == 'YES').sum()
        test_no = (test_df['resolution'] == 'NO').sum()
        test_yes_pct = (test_df['resolution'] == 'YES').mean()
        test_no_pct = (test_df['resolution'] == 'NO').mean()
        logging.info(f"   YES: {test_yes} ({test_yes_pct:.1%})")
        logging.info(f"   NO:  {test_no} ({test_no_pct:.1%})")
        
        logging.info("=" * 60)
        
        # Рекомендации
        logging.info("\n💡 РЕКОМЕНДАЦИИ:")
        
        if train_yes_pct > 0.65 or train_yes_pct < 0.35:
            logging.warning("\n⚠️  Сильный дисбаланс в тренировочных данных!")
            logging.warning(f"   Доля YES: {train_yes_pct:.1%}")
            logging.warning("   → Нужно добавить scale_pos_weight в XGBoost")
            logging.warning("   → Или использовать SMOTE для балансировки")
        else:
            logging.info("\n✅ Дисбаланс классов в норме.")
            logging.info(f"   Доля YES: {train_yes_pct:.1%} (оптимально 35-65%)")
        
        # Проверяем дисбаланс между train и test
        if abs(train_yes_pct - test_yes_pct) > 0.10:
            logging.warning("\n⚠️  Разница в распределении между train и test!")
            logging.warning(f"   Train YES: {train_yes_pct:.1%}, Test YES: {test_yes_pct:.1%}")
            logging.warning("   → Это может указывать на проблему с временным сплитом")
        else:
            logging.info("\n✅ Распределение классов согласовано между train и test.")
        
        # Дополнительные рекомендации
        if len(metadata_df) < 100:
            logging.warning("\n⚠️  Мало данных для обучения!")
            logging.warning(f"   Всего: {len(metadata_df)} рынков")
            logging.warning("   → Рекомендуется минимум 500+ рынков")
        elif len(metadata_df) < 500:
            logging.warning("\n⚠️  Недостаточно данных для стабильной модели")
            logging.warning(f"   Всего: {len(metadata_df)} рынков")
            logging.warning("   → Рекомендуется 500-1000+ рынков")
        else:
            logging.info(f"\n✅ Достаточно данных: {len(metadata_df)} рынков")
        
    except Exception as e:
        logging.error(f"❌ Ошибка проверки баланса: {e}")

if __name__ == "__main__":
    check_balance()
