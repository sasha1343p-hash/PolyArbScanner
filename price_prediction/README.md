# 🎯 Price Prediction System

Система предсказания движения цен на предиктивных рынках Polymarket.

## 🔄 Новая постановка задачи

**Было:** Предсказать, закончится ли рынок YES или NO (бинарная классификация)
- ❌ Мало данных (200 рынков)
- ❌ Фичи из временных рядов не работают эффективно
- ❌ Сложно интерпретировать результаты

**Стало:** Предсказать, вырастет ли цена YES на X% в ближайшие Y часов
- ✅ Больше данных (каждый час = новый пример, тысячи примеров)
- ✅ Фичи из временных рядов работают: momentum, volatility, trend
- ✅ Можно тестировать на исторических данных (backtesting)
- ✅ Проще интерпретировать: "цена вырастет на 5% за 24 часа"

## 📁 Структура проекта

```
price_prediction/
├── src/
│   ├── __init__.py
│   ├── target_generator.py       ✅ Генерация целевой переменной
│   ├── feature_extractor.py      ✅ Извлечение фич из временных рядов
│   ├── prepare_dataset.py        ✅ Объединение фич и targets
│   ├── model.py                  ✅ Модель XGBoost для предсказания
│   └── backtester.py             ✅ Бэктестинг стратегии
├── configs/
│   └── prediction_config.yaml    ✅ Конфигурация системы
├── data/
│   ├── targets.csv               ⏳ Генерируется target_generator.py
│   ├── features.csv              ⏳ Генерируется feature_extractor.py
│   ├── dataset.csv               ⏳ Генерируется prepare_dataset.py
│   └── backtest_trades.csv       ⏳ Генерируется backtester.py
├── models/
│   └── price_movement_model.pkl  ⏳ Генерируется model.py
├── run_pipeline.py               ✅ Главный скрипт запуска
├── run_target_generation.py      ✅ Скрипт генерации targets
├── run_all.bat                   ✅ BAT-файл для Windows
├── requirements.txt              ✅ Зависимости Python
└── README.md                     ✅ Документация
```

## 🚀 Быстрый старт

### 1. Генерация целевой переменной

```bash
cd price_prediction
python src/target_generator.py
```

**Что делает:**
- Загружает часовые цены из `polymarket_history.db`
- Для каждой точки времени t:
  - Берет цену в момент t
  - Смотрит цену в момент t + 24 часа
  - Если цена выросла на ≥5% → target = 1
  - Иначе → target = 0
- Сохраняет результаты в `data/targets.csv`

**Ожидаемый вывод:**
```
✅ Загружено 20000 записей о ценах

============================================================
ГЕНЕРАЦИЯ ЦЕЛЕВОЙ ПЕРЕМЕННОЙ
============================================================
Всего примеров: 15234
Порог роста: 5.0%
Горизонт: 24 часов
Положительных примеров (рост >= 5.0%): 4567 (30.0%)
Отрицательных примеров: 10667 (70.0%)
Средний price_change: 2.34%
Медианный price_change: 1.87%
============================================================
✅ Targets сохранены в data/targets.csv
```

### 2. Настройка параметров

Отредактируйте `configs/prediction_config.yaml`:

```yaml
target_generation:
  price_increase_threshold: 0.05  # 5% рост
  horizon_hours: 24               # горизонт 24 часа
  min_data_points: 48             # минимум 48 часов данных
```

**Параметры:**
- `price_increase_threshold` - порог роста (0.05 = 5%, 0.10 = 10%)
- `horizon_hours` - горизонт предсказания (24 часа, 48 часов, 7 дней)
- `min_data_points` - минимум часов данных для рынка

## 📊 Примеры использования

### Генерация targets с разными параметрами

```python
from src.target_generator import TargetGenerator

generator = TargetGenerator(db_path='../polymarket_history.db')

# Консервативная стратегия: 10% рост за 48 часов
targets_conservative = generator.generate_targets(
    price_increase_threshold=0.10,
    horizon_hours=48,
    min_data_points=96
)

# Агрессивная стратегия: 3% рост за 12 часов
targets_aggressive = generator.generate_targets(
    price_increase_threshold=0.03,
    horizon_hours=12,
    min_data_points=24
)
```

### Анализ распределения targets

```python
import pandas as pd

targets_df = pd.read_csv('data/targets.csv')

# Статистика по рынкам
market_stats = targets_df.groupby('market_id').agg({
    'target': ['mean', 'sum', 'count'],
    'price_change': ['mean', 'std', 'min', 'max']
})

print(market_stats)
```

## 🎯 Использование

### Быстрый старт (все шаги сразу)

```bash
cd price_prediction
python run_pipeline.py
```

Это запустит полный пайплайн:
1. ✅ Генерация целевой переменной (targets)
2. ✅ Извлечение фич из временных рядов
3. ✅ Объединение фич и targets в датасет
4. ✅ Обучение модели XGBoost
5. ✅ Бэктестинг стратегии

### Пошаговый запуск

**Шаг 1: Генерация целевой переменной**
```bash
python run_target_generation.py --threshold 0.05 --horizon 24
```

**Шаг 2: Извлечение фич**
```bash
python src/feature_extractor.py
```

**Шаг 3: Подготовка датасета**
```bash
python src/prepare_dataset.py
```

**Шаг 4: Обучение модели**
```bash
python src/model.py
```

**Шаг 5: Бэктестинг**
```bash
python src/backtester.py
```

### Запуск только определенных шагов

```bash
# Только генерация targets
python run_pipeline.py --step 1

# Только извлечение фич
python run_pipeline.py --step 2

# Пропустить бэктестинг
python run_pipeline.py --skip-backtest
```

### Windows (BAT-файл)

```cmd
run_all.bat
```

## 📈 Преимущества новой системы

| Характеристика | Старая система | Новая система |
|----------------|----------------|---------------|
| Количество примеров | 200 рынков | 15000+ часов |
| Тип задачи | Бинарная классификация | Предсказание движения |
| Интерпретируемость | "YES с вероятностью 65%" | "Цена вырастет на 5% за 24ч" |
| Backtesting | Невозможен | Полноценный бэктест |
| Использование фич | Ограниченное | Полное использование временных рядов |

## 🔧 Требования

- Python 3.10+
- pandas, numpy, scikit-learn
- xgboost или lightgbm
- SQLite3 (для работы с БД)

## 📝 Лицензия

MIT License

---

**Статус:** ✅ **Готово к использованию!**

**Созданные файлы:**
- ✅ `src/target_generator.py` - генерация целевой переменной
- ✅ `src/feature_extractor.py` - извлечение фич из временных рядов
- ✅ `src/prepare_dataset.py` - объединение фич и targets
- ✅ `src/model.py` - модель XGBoost для предсказания
- ✅ `src/backtester.py` - бэктестинг стратегии
- ✅ `run_pipeline.py` - главный скрипт запуска
- ✅ `run_target_generation.py` - скрипт генерации targets
- ✅ `run_all.bat` - BAT-файл для Windows
- ✅ `configs/prediction_config.yaml` - конфигурация
- ✅ `requirements.txt` - зависимости Python

## 📊 Ожидаемые результаты

После запуска пайплайна вы получите:

1. **`data/targets.csv`** - целевая переменная (тысячи примеров)
2. **`data/features.csv`** - извлеченные фичи (50+ признаков)
3. **`data/dataset.csv`** - объединенный датасет для обучения
4. **`models/price_movement_model.pkl`** - обученная модель XGBoost
5. **`data/backtest_trades.csv`** - результаты бэктестинга

### Метрики качества

Модель должна показать:
- **Accuracy**: 60-70% (лучше случайного угадывания)
- **Precision**: 55-65% (точность положительных предсказаний)
- **Recall**: 50-60% (полнота положительных предсказаний)
- **AUC-ROC**: 0.60-0.70 (качество классификации)

### Результаты бэктестинга

Бэктестинг покажет:
- **Total P&L**: прибыль/убыток стратегии
- **Win rate**: процент прибыльных сделок
- **Max drawdown**: максимальная просадка капитала
- **Sharpe ratio**: отношение доходности к риску

## 🚀 Быстрый старт

```bash
cd price_prediction
python run_pipeline.py
```

Или на Windows:
```cmd
run_all.bat
```
