import pandas as pd
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def prepare_dataset():
    """Объединяет фичи и targets в один датасет"""
    
    # Проверяем наличие файлов
    if not os.path.exists('data/features.csv'):
        logging.error("❌ Файл data/features.csv не найден. Сначала запустите feature_extractor.py")
        return
    
    if not os.path.exists('data/targets.csv'):
        logging.error("❌ Файл data/targets.csv не найден. Сначала запустите target_generator.py")
        return
    
    # Загружаем фичи
    features_df = pd.read_csv('data/features.csv')
    features_df['timestamp'] = pd.to_datetime(features_df['timestamp'])
    
    # Загружаем targets
    targets_df = pd.read_csv('data/targets.csv')
    targets_df['timestamp'] = pd.to_datetime(targets_df['timestamp'])
    
    logging.info(f"Фичи: {len(features_df)} строк")
    logging.info(f"Targets: {len(targets_df)} строк")
    
    # Объединяем по market_id и timestamp
    dataset_df = pd.merge(
        features_df, 
        targets_df, 
        on=['market_id', 'timestamp'], 
        how='inner'
    )
    
    logging.info(f"После объединения: {len(dataset_df)} строк")
    
    # Удаляем пропуски
    dataset_df = dataset_df.dropna()
    logging.info(f"После удаления пропусков: {len(dataset_df)} строк")
    
    # Сохраняем
    os.makedirs('data', exist_ok=True)
    dataset_df.to_csv('data/dataset.csv', index=False)
    logging.info(f"✅ Датасет сохранен в data/dataset.csv")
    
    # Статистика
    logging.info(f"\n{'='*60}")
    logging.info("СТАТИСТИКА ДАТАСЕТА")
    logging.info("="*60)
    logging.info(f"Всего примеров: {len(dataset_df)}")
    logging.info(f"Положительных (рост): {dataset_df['target'].sum()} ({dataset_df['target'].mean():.1%})")
    logging.info(f"Отрицательных (нет роста): {(dataset_df['target'] == 0).sum()} ({1 - dataset_df['target'].mean():.1%})")
    logging.info(f"Количество рынков: {dataset_df['market_id'].nunique()}")
    logging.info(f"Диапазон времени: {dataset_df['timestamp'].min()} — {dataset_df['timestamp'].max()}")
    logging.info("="*60)
    
    return dataset_df

if __name__ == "__main__":
    prepare_dataset()
