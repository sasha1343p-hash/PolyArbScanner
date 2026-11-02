# 🚀 Быстрый старт Price Prediction System

## 📋 Что создано

✅ **Полная структура проекта:**
```
price_prediction/
├── src/
│   ├── __init__.py
│   └── target_generator.py       # Генерация целевой переменной
├── configs/
│   └── prediction_config.yaml    # Конфигурация
├── data/                         # Для targets.csv
├── models/                       # Для обученных моделей
├── results/                      # Для результатов бэктестинга
├── logs/                         # Для логов
├── run_target_generation.py      # Скрипт запуска
└── README.md                     # Документация
```

## ⚡ Быстрый запуск

### 1. Перейти в директорию проекта

```bash
cd price_prediction
```

### 2. Запустить генерацию targets

**Простой запуск (с параметрами по умолчанию):**
```bash
python run_target_generation.py
```

**С кастомными параметрами:**
```bash
python run_target_generation.py \
  --threshold 0.05 \
  --horizon 24 \
  --min-points 48 \
  --output data/targets.csv
```

**Параметры:**
- `--threshold` - порог роста цены (0.05 = 5%)
- `--horizon` - горизонт предсказания в часах (24 = 24 часа)
- `--min-points` - минимум часов данных для рынка (48)
- `--output` - путь для сохранения результатов

### 3. Проверить результаты

После запуска будет создан файл `data/targets.csv` со столбцами:
- `market_id` - ID рынка
- `timestamp` - момент предсказания
- `current_price` - цена в момент t
- `future_price` - цена в момент t + horizon
- `price_change` - процентное изменение
- `target` - 1 если рост >= threshold, иначе 0
- `volume` - объем торгов
- `liquidity` - ликвидность

## 📊 Примеры использования

### Пример 1: Консервативная стратегия
```bash
python run_target_generation.py \
  --threshold 0.10 \
  --horizon 48 \
  --min-points 96 \
  --output data/targets_conservative.csv
```
*Ищет рынки с ростом ≥10% за 48 часов*

### Пример 2: Агрессивная стратегия
```bash
python run_target_generation.py \
  --threshold 0.03 \
  --horizon 12 \
  --min-points 24 \
  --output data/targets_aggressive.csv
```
*Ищет рынки с ростом ≥3% за 12 часов*

### Пример 3: Использование из Python
```python
from src.target_generator import TargetGenerator

generator = TargetGenerator(db_path='../polymarket_history.db')

# Генерация targets
targets_df = generator.generate_targets(
    price_increase_threshold=0.05,
    horizon_hours=24,
    min_data_points=48
)

# Анализ результатов
print(f"Всего примеров: {len(targets_df)}")
print(f"Положительных: {targets_df['target'].sum()}")
print(f"Отрицательных: {(targets_df['target'] == 0).sum()}")

# Сохранение
generator.save_targets(targets_df, 'data/targets.csv')
```

## 🎯 Что дальше?

Следующие файлы для создания:

1. **`src/feature_extractor.py`** - извлечение фич из временных рядов
   - Momentum (изменение цены за N часов)
   - Volatility (стандартное отклонение)
   - Trend (наклон линейной регрессии)
   - Volume features
   - Time features

2. **`src/model.py`** - обучение модели предсказания
   - XGBoost / LightGBM
   - Кросс-валидация по времени
   - Оценка качества

3. **`src/backtester.py`** - бэктестинг стратегии
   - Симуляция торговли
   - Расчет прибыли/убытков
   - Оценка риска

4. **`src/predictor.py`** - предсказание для текущих рынков
   - Загрузка модели
   - Предсказание для активных рынков
   - Генерация сигналов

## 📈 Ожидаемые результаты

После генерации targets вы получите:
- **Тысячи примеров** для обучения (вместо 200 рынков)
- **Четкую целевую переменную**: "цена вырастет на X% за Y часов"
- **Возможность бэктестинга** на исторических данных
- **Интерпретируемые результаты** для торговли

## 🔧 Требования

- Python 3.10+
- pandas
- numpy
- SQLite3 (встроен в Python)

Установить зависимости:
```bash
pip install pandas numpy
```

## 📝 Лицензия

MIT License

---

**Статус:** ✅ Готово к использованию (target_generator)

**Следующий шаг:** Создать `src/feature_extractor.py`
