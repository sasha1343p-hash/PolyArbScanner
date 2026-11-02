# 📁 Структура проекта

```
polymarket_ml/
│
├── ml_oracle/                          # Основной пакет
│   ├── __init__.py                     # Инициализация пакета
│   ├── feature_extractor.py            # Извлечение признаков (50+ фич)
│   ├── model.py                        # ML-модель (XGBoost/LightGBM)
│   ├── monitor.py                      # Мониторинг дрейфа (PSI/KS-test)
│   └── ensemble.py                     # Ансамбль ML + эвристика
│
├── configs/                            # Конфигурация
│   └── oracle_config.yaml              # Параметры обучения и инференса
│
├── artifacts/                          # Артефакты (создаётся автоматически)
│   ├── ml_oracle_bundle.pkl            # Обученная модель
│   ├── ml_oracle_bundle_scaler.pkl     # Scaler для нормализации
│   └── train_stats.json                # Статистика для мониторинга дрейфа
│
├── logs/                               # Логи (создаётся автоматически)
│   └── ml_oracle.log                   # Основной лог
│
├── tests/                              # Тесты
│   ├── __init__.py
│   ├── test_feature_extractor.py       # Тесты извлечения признаков (15 тестов)
│   └── test_model.py                   # Тесты модели (12 тестов)
│
├── ml_oracle.py                        # CLI интерфейс (главный скрипт)
│
├── requirements.txt                    # Зависимости Python
├── Dockerfile                          # Docker для изоляции
├── .gitignore                          # Игнорируемые файлы
│
├── train.bat                           # Windows: обучение модели
├── predict.bat                         # Windows: предсказание
│
├── README.md                           # Полная документация
├── QUICKSTART.md                       # Быстрый старт (5 минут)
├── CLI_EXAMPLES.md                     # Примеры CLI команд
└── PROJECT_STRUCTURE.md                # Этот файл
```

## 📊 Описание модулей

### `ml_oracle/feature_extractor.py`
**Назначение**: Извлечение признаков из временных рядов цен

**Классы**:
- `FeatureExtractor` — основной класс для извлечения признаков
- `FeatureConfig` — конфигурация извлечения
- `MarketMetadata` — метаданные рынка

**Ключевые методы**:
- `extract_features()` — извлечение для одного рынка
- `extract_features_batch()` — извлечение для батча
- `_extract_price_statistics()` — статистики цен
- `_extract_volatility_features()` — волатильность
- `_extract_trend_features()` — тренд
- `_extract_momentum_features()` — моментум
- `_extract_volume_features()` — объёмные метрики
- `_extract_temporal_features()` — временные фичи
- `_extract_price_patterns()` — ценовые паттерны
- `_extract_context_features()` — контекстные фичи

**Извлекаемые признаки** (50+):
- Статистики цен (mean, std, min, max, median, skewness, kurtosis)
- Волатильность (std returns, ATR proxy, GARCH proxy)
- Тренд (slope линейной регрессии за 24h, 7d, 30d)
- Моментум (изменение цены за 1h, 6h, 24h, 7d, 14d)
- Объём (mean, std, trend, volume/liquidity ratio)
- Время (days_to_expiry, day_of_week, hour_of_day)
- Паттерны (distance from high/low, RSI)
- Контекст (category: crypto/politics/sports/culture)

---

### `ml_oracle/model.py`
**Назначение**: Обучение и инференс ML-моделей

**Классы**:
- `MLOracle` — основной класс модели
- `TrainingConfig` — конфигурация обучения
- `ModelMetrics` — метрики качества

**Ключевые методы**:
- `train()` — обучение модели (XGBoost + LightGBM)
- `predict()` — предсказание вероятности
- `predict_with_confidence()` — предсказание с уверенностью
- `get_feature_importance()` — важность признаков
- `save()` / `load()` — сохранение/загрузка модели
- `_train_xgboost()` — обучение XGBoost
- `_train_lightgbm()` — обучение LightGBM
- `_calibrate_model()` — калибровка вероятностей
- `_evaluate_model()` — оценка качества

**Особенности**:
- TimeSeriesSplit для временных рядов (НЕ random split)
- Автоматический выбор лучшей модели по AUC-ROC
- Калибровка вероятностей (isotonic/sigmoid)
- Обработка дисбаланса классов (scale_pos_weight)
- Оценка уверенности на основе расстояния до train distribution

---

### `ml_oracle/monitor.py`
**Назначение**: Мониторинг дрейфа модели и данных

**Классы**:
- `ModelMonitor` — основной класс мониторинга
- `MonitorConfig` — конфигурация мониторинга
- `DriftReport` — отчёт о дрейфе

**Ключевые методы**:
- `initialize_from_train_data()` — инициализация статистики
- `check_drift()` — проверка дрейфа
- `save_train_stats()` / `load_train_stats()` — сохранение/загрузка статистики
- `_calculate_psi()` — вычисление PSI
- `_compute_histogram()` — вычисление гистограммы

**Методы обнаружения дрейфа**:
- **PSI (Population Stability Index)**:
  - PSI < 0.1: нет значимых изменений
  - 0.1 ≤ PSI < 0.2: умеренные изменения
  - PSI ≥ 0.2: значительные изменения
- **KS-test (Kolmogorov-Smirnov)**:
  - Тестирует различие распределений
  - Порог: 0.1

---

### `ml_oracle/ensemble.py`
**Назначение**: Ансамбль ML + эвристика

**Классы**:
- `OracleEnsemble` — ансамбль оракулов
- `EnsembleConfig` — конфигурация ансамбля

**Ключевые методы**:
- `predict()` — предсказание с использованием ансамбля
- `predict_batch()` — пакетное предсказание
- `default_heuristic()` — эвристический оракул (baseline)

**Логика работы**:
1. Если обе модели доступны → взвешенное среднее (ML: 70%, эвристика: 30%)
2. Если только ML → используем ML
3. Если только эвристика → используем эвристику
4. Если ничего не доступно → возвращаем None

**Graceful degradation**:
- Если ML уверенность < порога → используем только эвристику
- Если ML упал с ошибкой → fallback на эвристику
- Если эвристика упала → используем только ML

---

### `ml_oracle.py` (CLI)
**Назначение**: Командный интерфейс

**Команды**:
- `train` — обучение модели
- `evaluate` — оценка на отложенной выборке
- `predict <market_id>` — предсказание для рынка
- `drift-check` — проверка дрейфа
- `feature-importance` — важность признаков

**Примеры**:
```bash
python ml_oracle.py train
python ml_oracle.py predict market-123-abc
python ml_oracle.py drift-check
python ml_oracle.py feature-importance
```

---

## 🔧 Конфигурация

### `configs/oracle_config.yaml`

**Секции**:
- `paths` — пути к данным и артефактам
- `features` — параметры извлечения признаков
- `training` — параметры обучения модели
- `monitoring` — параметры мониторинга дрейфа
- `ensemble` — параметры ансамбля
- `logging` — параметры логирования
- `reproducibility` — параметры воспроизводимости

**Ключевые параметры**:
- `training.n_splits` — количество фолдов для TimeSeriesSplit (5)
- `training.models.xgboost.params` — гиперпараметры XGBoost
- `training.models.lightgbm.params` — гиперпараметры LightGBM
- `training.calibration.method` — метод калибровки (isotonic/sigmoid)
- `monitoring.psi_threshold` — порог PSI для дрейфа (0.2)
- `monitoring.ks_threshold` — порог KS-test для дрейфа (0.1)
- `ensemble.ml_weight` — вес ML в ансамбле (0.7)

---

## 📦 Артефакты

### `artifacts/ml_oracle_bundle.pkl`
**Содержимое**:
- `model` — обученная модель (XGBoost или LightGBM)
- `model_type` — тип модели ('xgboost' или 'lightgbm')
- `feature_names` — список признаков
- `metrics` — метрики качества
- `train_mean` — среднее train distribution
- `train_std` — std train distribution
- `config` — конфигурация обучения

**Размер**: ~10-50 MB (зависит от количества деревьев)

### `artifacts/train_stats.json`
**Содержимое**:
- Статистика каждого признака (mean, std, median, min, max, percentiles, histogram)
- Используется для мониторинга дрейфа

**Размер**: ~1-5 MB

---

## 🧪 Тесты

### `tests/test_feature_extractor.py` (15 тестов)
- `test_feature_extractor_initialization` — инициализация
- `test_extract_price_statistics` — статистики цен
- `test_extract_volatility_features` — волатильность
- `test_extract_momentum_features` — моментум
- `test_extract_temporal_features` — временные фичи
- `test_extract_category_features` — категории
- `test_extract_rsi` — RSI
- `test_handle_empty_dataframe` — пустой DataFrame
- `test_extract_features_batch` — батчевое извлечение
- `test_normalization` — нормализация
- `test_detect_category` — определение категории
- `test_calculate_rsi` — вычисление RSI

### `tests/test_model.py` (12 тестов)
- `test_model_initialization` — инициализация
- `test_model_training` — обучение
- `test_model_predict` — предсказание
- `test_model_predict_with_confidence` — предсказание с уверенностью
- `test_model_predict_untrained` — предсказание необученной модели
- `test_model_metrics` — метрики
- `test_model_feature_importance` — важность признаков
- `test_model_save_load` — сохранение/загрузка
- `test_model_load_nonexistent` — загрузка несуществующей модели
- `test_model_insufficient_data` — недостаточные данные
- `test_model_with_nan_values` — NaN значения
- `test_model_imbalanced_classes` — несбалансированные классы

**Запуск**:
```bash
pytest tests/
pytest tests/ --cov=ml_oracle --cov-report=html
```

---

## 📚 Документация

- `README.md` — полная документация (архитектура, использование, troubleshooting)
- `QUICKSTART.md` — быстрый старт (5 минут)
- `CLI_EXAMPLES.md` — примеры CLI команд
- `PROJECT_STRUCTURE.md` — этот файл

---

## 🚀 Быстрые команды

```bash
# Обучение
python ml_oracle.py train

# Предсказание
python ml_oracle.py predict <market-id>

# Проверка дрейфа
python ml_oracle.py drift-check

# Важность признаков
python ml_oracle.py feature-importance

# Тесты
pytest tests/

# Docker
docker build -t polymarket-ml .
docker run -v $(pwd)/artifacts:/app/artifacts polymarket-ml python ml_oracle.py train
```

---

**Создано**: PolyArb Team, 2026  
**Версия**: 1.0.0  
**Лицензия**: MIT
