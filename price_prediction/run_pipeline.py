#!/usr/bin/env python3
"""
Главный скрипт запуска системы предсказания движения цен.

Пайплайн:
1. Генерация целевой переменной (targets)
2. Извлечение фич из временных рядов
3. Объединение фич и targets в датасет
4. Обучение модели
5. Бэктестинг стратегии

Использование:
    python run_pipeline.py                    # Запустить весь пайплайн
    python run_pipeline.py --step 1           # Только генерация targets
    python run_pipeline.py --step 2           # Только извлечение фич
    python run_pipeline.py --skip-backtest    # Пропустить бэктестинг
"""

import os
import sys
import argparse
import logging
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_command(cmd, description):
    """Запускает команду и проверяет результат"""
    logging.info(f"\n{'='*60}")
    logging.info(f"🚀 {description}")
    logging.info(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True, capture_output=False)
    
    if result.returncode != 0:
        logging.error(f"❌ Ошибка при выполнении: {description}")
        return False
    
    logging.info(f"✅ {description} завершена успешно")
    return True

def main():
    parser = argparse.ArgumentParser(description='Пайплайн предсказания движения цен')
    
    parser.add_argument(
        '--step',
        type=int,
        choices=[1, 2, 3, 4, 5],
        help='Запустить только определенный шаг (1-5)'
    )
    
    parser.add_argument(
        '--skip-backtest',
        action='store_true',
        help='Пропустить бэктестинг'
    )
    
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.05,
        help='Порог роста цены (default: 0.05 = 5%%)'
    )
    
    parser.add_argument(
        '--horizon',
        type=int,
        default=24,
        help='Горизонт предсказания в часах (default: 24)'
    )
    
    args = parser.parse_args()
    
    logging.info("="*60)
    logging.info("🎯 PRICE PREDICTION PIPELINE")
    logging.info("="*60)
    logging.info(f"Порог роста: {args.threshold:.1%}")
    logging.info(f"Горизонт: {args.horizon} часов")
    logging.info("="*60)
    
    # Определяем какие шаги выполнять
    steps_to_run = []
    
    if args.step:
        steps_to_run = [args.step]
    else:
        steps_to_run = [1, 2, 3, 4]
        if not args.skip_backtest:
            steps_to_run.append(5)
    
    # Шаг 1: Генерация targets
    if 1 in steps_to_run:
        cmd = f'python run_target_generation.py --threshold {args.threshold} --horizon {args.horizon}'
        if not run_command(cmd, "Шаг 1: Генерация целевой переменной"):
            sys.exit(1)
    
    # Шаг 2: Извлечение фич
    if 2 in steps_to_run:
        cmd = 'python src/feature_extractor.py'
        if not run_command(cmd, "Шаг 2: Извлечение фич"):
            sys.exit(1)
    
    # Шаг 3: Подготовка датасета
    if 3 in steps_to_run:
        cmd = 'python src/prepare_dataset.py'
        if not run_command(cmd, "Шаг 3: Подготовка датасета"):
            sys.exit(1)
    
    # Шаг 4: Обучение модели
    if 4 in steps_to_run:
        cmd = 'python src/model.py'
        if not run_command(cmd, "Шаг 4: Обучение модели"):
            sys.exit(1)
    
    # Шаг 5: Бэктестинг
    if 5 in steps_to_run:
        cmd = 'python src/backtester.py'
        if not run_command(cmd, "Шаг 5: Бэктестинг"):
            sys.exit(1)
    
    # Финальное сообщение
    logging.info("\n" + "="*60)
    logging.info("✅ PIPELINE ЗАВЕРШЕН УСПЕШНО!")
    logging.info("="*60)
    logging.info("\nСозданные файлы:")
    logging.info("  - data/targets.csv          (целевая переменная)")
    logging.info("  - data/features.csv         (извлеченные фичи)")
    logging.info("  - data/dataset.csv          (объединенный датасет)")
    logging.info("  - models/price_movement_model.pkl  (обученная модель)")
    
    if 5 in steps_to_run:
        logging.info("  - data/backtest_trades.csv  (результаты бэктестинга)")
    
    logging.info("\n" + "="*60)

if __name__ == '__main__':
    main()
