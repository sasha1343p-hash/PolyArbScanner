# Примеры CLI команд для ML Oracle

## Установка

```bash
# Создание виртуального окружения
python -m venv venv

# Активация (Windows)
venv\Scripts\activate

# Активация (Linux/Mac)
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

## Обучение модели

```bash
# Базовое обучение
python ml_oracle.py train

# С кастомным конфигом
python ml_oracle.py train --config configs/my_config.yaml

# Проверка логов
tail -f logs/ml_oracle.log
```

## Оценка модели

```bash
# Оценка на отложенной выборке
python ml_oracle.py evaluate

# Вывод метрик
python ml_oracle.py evaluate 2>&1 | grep "AUC-ROC"
```

## Предсказание

```bash
# Предсказание для конкретного рынка
python ml_oracle.py predict market-123-abc

# Предсказание с выводом в JSON
python ml_oracle.py predict market-123-abc --output json

# Пакетное предсказание (из файла)
python ml_oracle.py predict --batch markets.txt --output predictions.csv
```

## Мониторинг дрейфа

```bash
# Проверка дрейфа
python ml_oracle.py drift-check

# Проверка с сохранением отчёта
python ml_oracle.py drift-check --output drift_report.json

# Автоматическая проверка (cron)
# Добавить в crontab:
# 0 */24 * * * cd /path/to/polymarket_ml && python ml_oracle.py drift-check >> logs/drift.log 2>&1
```

## Важность признаков

```bash
# Топ-10 признаков
python ml_oracle.py feature-importance

# Топ-20 признаков
python ml_oracle.py feature-importance --top 20

# С визуализацией (если установлен matplotlib)
python ml_oracle.py feature-importance --plot
```

## Тестирование

```bash
# Все тесты
pytest tests/

# С coverage
pytest tests/ --cov=ml_oracle --cov-report=html

# Конкретный тест
pytest tests/test_feature_extractor.py::test_extract_price_statistics -v

# Только быстрые тесты
pytest tests/ -m "not slow"
```

## Docker

```bash
# Сборка образа
docker build -t polymarket-ml .

# Запуск обучения
docker run -v $(pwd)/artifacts:/app/artifacts \
           -v $(pwd)/polymarket_history.db:/app/polymarket_history.db \
           polymarket-ml python ml_oracle.py train

# Запуск предсказания
docker run -v $(pwd)/artifacts:/app/artifacts \
           -v $(pwd)/polymarket_history.db:/app/polymarket_history.db \
           polymarket-ml python ml_oracle.py predict market-123-abc

# Интерактивный режим
docker run -it --rm \
           -v $(pwd)/artifacts:/app/artifacts \
           -v $(pwd)/polymarket_history.db:/app/polymarket_history.db \
           polymarket-ml bash
```

## Интеграция со сканером

```bash
# Запуск сканера с ML
python market_analyzer.py --use-ml --threshold 0.15

# Только ML (без эвристики)
python market_analyzer.py --use-ml --ml-only

# Только эвристика (без ML)
python market_analyzer.py --heuristic-only

# С сохранением истории
python market_analyzer.py --use-ml --save-history

# Вывод в JSON
python market_analyzer.py --use-ml --output json > results.json
```

## Автоматизация (Windows)

```batch
REM Обучение каждый день в 3:00
schtasks /create /tn "ML Oracle Train" /tr "C:\path\to\train.bat" /sc daily /st 03:00

REM Проверка дрейфа каждый час
schtasks /create /tn "ML Oracle Drift Check" /tr "C:\path\to\drift_check.bat" /sc hourly
```

## Автоматизация (Linux/Mac)

```bash
# Обучение каждый день в 3:00
crontab -e
# Добавить строку:
0 3 * * * cd /path/to/polymarket_ml && ./train.sh >> logs/cron.log 2>&1

# Проверка дрейфа каждый час
0 * * * * cd /path/to/polymarket_ml && python ml_oracle.py drift-check >> logs/drift.log 2>&1
```

## Полезные one-liners

```bash
# Быстрая проверка качества модели
python ml_oracle.py evaluate | grep -E "AUC-ROC|Brier"

# Список всех обученных моделей
ls -lh artifacts/*.pkl

# Размер модели
du -h artifacts/ml_oracle_bundle.pkl

# Последние 50 строк лога
tail -n 50 logs/ml_oracle.log

# Поиск ошибок в логе
grep "ERROR" logs/ml_oracle.log | tail -20

# Статистика по рынкам в БД
sqlite3 polymarket_history.db "SELECT COUNT(*) FROM market_metadata WHERE resolution IS NOT NULL;"

# Экспорт предсказаний в CSV
python ml_oracle.py predict --batch markets.txt --output predictions.csv && head predictions.csv
```

## Troubleshooting

```bash
# Проверка версии Python
python --version

# Проверка установленных пакетов
pip list | grep -E "xgboost|lightgbm|sklearn"

# Переустановка зависимостей
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# Очистка кэша
rm -rf __pycache__ .pytest_cache .mypy_cache
rm -rf artifacts/*.pkl logs/*.log

# Полное переобучение
rm artifacts/ml_oracle_bundle.pkl
python ml_oracle.py train
```
