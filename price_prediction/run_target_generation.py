#!/usr/bin/env python3
"""
Скрипт запуска генерации целевой переменной для price prediction system.
"""

import os
import sys
import argparse
import logging

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from target_generator import TargetGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    parser = argparse.ArgumentParser(
        description='Генерация целевой переменной для предсказания движения цен'
    )
    
    parser.add_argument(
        '--db-path',
        type=str,
        default='../polymarket_history.db',
        help='Путь к базе данных с историей цен (default: ../polymarket_history.db)'
    )
    
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.05,
        help='Порог роста цены в процентах (default: 0.05 = 5%%)'
    )
    
    parser.add_argument(
        '--horizon',
        type=int,
        default=24,
        help='Горизонт предсказания в часах (default: 24)'
    )
    
    parser.add_argument(
        '--min-points',
        type=int,
        default=48,
        help='Минимум часов данных для рынка (default: 48)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='data/targets.csv',
        help='Путь для сохранения результатов (default: data/targets.csv)'
    )
    
    args = parser.parse_args()
    
    logging.info("=" * 60)
    logging.info("Price Prediction - Генерация целевой переменной")
    logging.info("=" * 60)
    logging.info(f"База данных: {args.db_path}")
    logging.info(f"Порог роста: {args.threshold:.1%}")
    logging.info(f"Горизонт: {args.horizon} часов")
    logging.info(f"Минимум точек: {args.min_points}")
    logging.info(f"Выходной файл: {args.output}")
    logging.info("=" * 60)
    
    # Создаем генератор
    generator = TargetGenerator(db_path=args.db_path)
    
    # Генерируем targets
    targets_df = generator.generate_targets(
        price_increase_threshold=args.threshold,
        horizon_hours=args.horizon,
        min_data_points=args.min_points
    )
    
    # Сохраняем результаты
    if not targets_df.empty:
        generator.save_targets(targets_df, output_path=args.output)
        logging.info("\n✅ Генерация завершена успешно!")
        logging.info(f"📊 Создано {len(targets_df)} примеров для обучения")
    else:
        logging.error("\n❌ Не удалось сгенерировать targets")
        sys.exit(1)

if __name__ == '__main__':
    main()
