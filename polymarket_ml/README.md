# 🤖 ML Oracle для Polymarket

Production-ready ML-система для предсказания вероятностей на предиктивных рынках с использованием XGBoost, LightGBM и продвинутого feature engineering.

## 📋 Возможности

- **Feature Engineering**: 50+ признаков из временных рядов цен
- **Ансамбль моделей**: XGBoost + LightGBM с автоматическим выбором лучшей
- **Калибровка вероятностей**: Isotonic/Sigmoid калибровка для точных вероятностей
- **Мониторинг дрейфа**: PSI и KS-test для отслеживания деградации модели
- **Graceful Degradation**: Fallback на эвристику при недоступности ML
- **CLI интерфейс**: Обучение, оценка, инференс из командной строки

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
# Создаём виртуальное окружение
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Устанавливаем зависимости
pip install -r requirements.txt
```

### 2. Подготовка данных

Убедитесь, что у вас есть SQLite база `polymarket_history.db` с таблицами:

```sql
-- Метаданные рынков
CREATE TABLE market_metadata (
    id TEXT PRIMARY KEY,
    question TEXT,
    end_date DATETIME,
    resolution TEXT,  -- 'YES', 'NO', или NULL
    created_at DATETIME
);

-- История цен
CREATE TABLE price_history (
    market_id TEXT,
    timestamp DATETIME,
    yes_price REAL,
    no_price REAL,
    volume REAL,
    liquidity REAL,
    FOREIGN KEY (market_id) REFERENCES market_metadata(id)
);
```

### 3. Обучение модели

```bash
python ml_oracle.py train
```

**Что происходит:**
- Загрузка данных из БД
- Извлечение 50+ признаков для каждого рынка
- Обучение XGBoost и LightGBM с TimeSeriesSplit
- Выбор лучшей модели по AUC-ROC
- Калибровка вероятностей
- Сохранение модели в `artifacts/ml_oracle_bundle.pkl`

**Ожидаемый вывод:**
```
============================================================
МЕТРИКИ КАЧЕСТВА
============================================================
Accuracy:    0.7234
Precision:   0.7156
Recall:      0.7089
F1 Score:    0.7121
AUC-ROC:     0.7845
Brier Score: 0.1823
Samples:     1250 (YES=625, NO=625)
============================================================
✅ ОБУЧЕНИЕ ЗАВЕРШЕНО УСПЕШНО
============================================================
```

### 4. Предсказание для рынка

```bash
python ml_oracle.py predict market-123-abc
```

**Вывод:**
```
============================================================
РЫНОК: Will Bitcoin be above $100,000 by March 2026?
============================================================
Вероятность YES: 67.3%
Уверенность:     82.1%
Рекомендация:    BUY YES
============================================================
```

### 5. Проверка дрейфа

```bash
python ml_oracle.py drift-check
```

**Вывод:**
```
============================================================
ОТЧЁТ О ДРЕЙФЕ
============================================================
Дрейф обнаружен: НЕТ
Дрейфующие признаки: 0

Рекомендация: Дрейф не обнаружен. Модель стабильна.
============================================================
```

### 6. Важность признаков

```bash
python ml_oracle.py feature-importance
```

**Вывод:**
```
============================================================
ТОП-20 ВАЖНЫХ ПРИЗНАКОВ
============================================================
 1. momentum_24h                    0.0845 ████████████████████████
 2. price_std_24h                   0.0723 ████████████████████
 3. days_to_expiry                  0.0689 ███████████████████
 4. volatility_24h                  0.0634 █████████████████
 5. volume_liquidity_ratio          0.0598 ████████████████
 ...
============================================================
```

## 📊 Архитектура

```
polymarket_ml/
├── ml_oracle/
│   ├── __init__.py
│   ├── feature_extractor.py    # Извлечение признаков
│   ├── model.py                # ML-модель (XGBoost/LightGBM)
│   ├── monitor.py              # Мониторинг дрейфа
│   └── ensemble.py             # Ансамбль ML + эвристика
├── configs/
│   └── oracle_config.yaml      # Конфигурация
├── artifacts/
│   ├── ml_oracle_bundle.pkl    # Обученная модель
│   └── train_stats.json        # Статистика для мониторинга
├── logs/
│   └── ml_oracle.log           # Логи
├── tests/
│   ├── test_feature_extractor.py
│   └── test_model.py
├── ml_oracle.py                # CLI интерфейс
├── requirements.txt
└── README.md
```

## 🔧 Извлекаемые признаки

### Статистики цен (20+ фич)
- `price_current`, `price_mean`, `price_std`, `price_min`, `price_max`, `price_median`
- `price_skewness`, `price_kurtosis`
- Статистики по временным окнам: 1h, 6h, 24h, 7d, 30d

### Волатильность (5+ фич)
- `volatility_24h`, `volatility_168h`, `volatility_720h`
- `atr_proxy` (Average True Range)
- `garch_proxy` (автокорреляция квадратов returns)

### Тренд (3 фичи)
- `trend_slope_24h`, `trend_slope_168h`, `trend_slope_720h`
- Наклон линейной регрессии за разные окна

### Моментум (5 фич)
- `momentum_1h`, `momentum_6h`, `momentum_24h`, `momentum_168h`, `momentum_336h`
- Изменение цены за разные периоды

### Объёмные метрики (4 фичи)
- `volume_mean`, `volume_std`, `volume_trend`
- `volume_liquidity_ratio`

### Временные фичи (3 фичи)
- `days_to_expiry`
- `day_of_week`, `hour_of_day`

### Ценовые паттерны (3 фичи)
- `distance_from_high`, `distance_from_low`
- `rsi` (Relative Strength Index)

### Контекстные фичи (4 фичи)
- `category_crypto`, `category_politics`, `category_sports`, `category_culture`
- One-hot encoding типа рынка

**Итого: 50+ признаков**

## 🎯 Критерии качества

### Пороги метрик

| Метрика | Порог | Описание |
|---------|-------|----------|
| AUC-ROC | ≥ 0.65 | Качество классификации |
| Brier Score | ≤ 0.25 | Калибровка вероятностей |
| Accuracy | ≥ 0.65 | Общая точность |
| F1 Score | ≥ 0.65 | Баланс precision/recall |

### Время инференса

- **Один рынок**: < 50ms
- **Батч 100 рынков**: < 2s

### Размер модели

- **Bundle**: < 100MB
- **Время загрузки**: < 1s

## 🔍 Мониторинг дрейфа

### Методы обнаружения

1. **PSI (Population Stability Index)**
   - PSI < 0.1: нет значимых изменений
   - 0.1 ≤ PSI < 0.2: умеренные изменения
   - PSI ≥ 0.2: значительные изменения (требуется переобучение)

2. **KS-test (Kolmogorov-Smirnov)**
   - Тестирует различие распределений
   - Порог: 0.1

### Ключевые фичи для мониторинга

- `price_mean_24h`
- `price_std_24h`
- `volume_mean_24h`
- `momentum_24h`
- `days_to_expiry`

### Частота проверки

- **Рекомендуется**: каждые 24 часа
- **Минимум**: еженедельно
- **При дрейфе**: немедленное переобучение

## 🧪 Тестирование

```bash
# Запуск всех тестов
pytest tests/

# С coverage
pytest tests/ --cov=ml_oracle --cov-report=html

# Конкретный тест
pytest tests/test_feature_extractor.py::test_extract_price_statistics
```

### Примеры тестов

```python
def test_extract_price_statistics():
    """Тест извлечения статистик цен."""
    extractor = FeatureExtractor()
    df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='H'),
        'yes_price': np.random.uniform(0.3, 0.7, 100),
        'volume': np.random.uniform(1000, 10000, 100),
    })
    metadata = MarketMetadata(id='test', question='Test market')
    
    features = extractor.extract_features('test', df, metadata)
    
    assert 'price_mean' in features
    assert 'price_std' in features
    assert 0 <= features['price_current'] <= 1

def test_model_training():
    """Тест обучения модели."""
    X = pd.DataFrame(np.random.randn(200, 10))
    y = pd.Series(np.random.randint(0, 2, 200))
    
    model = MLOracle()
    metrics = model.train(X, y)
    
    assert 0 <= metrics.auc_roc <= 1
    assert metrics.n_samples == 40  # 20% test split
```

## 📈 Интеграция со сканером

### Использование в market_analyzer.py

```python
from ml_oracle import OracleEnsemble, MLOracle, FeatureExtractor
from ml_oracle.ensemble import default_heuristic

# Загружаем ML модель
ml_oracle = MLOracle()
ml_oracle.load('artifacts/ml_oracle_bundle.pkl')

# Создаём ансамбль
ensemble = OracleEnsemble(
    ml_oracle=ml_oracle,
    feature_extractor=FeatureExtractor(),
    heuristic_fn=default_heuristic
)

# Предсказание
probability, source = ensemble.predict(market_id, price_df, metadata)
print(f"Вероятность: {probability:.2%} (источник: {source})")
```

### CLI интеграция

```bash
# Запуск сканера с ML
python market_analyzer.py --use-ml --threshold 0.15

# Только ML (без эвристики)
python market_analyzer.py --use-ml --ml-only

# Только эвристика (без ML)
python market_analyzer.py --heuristic-only
```

## ⚙️ Конфигурация

Все параметры в `configs/oracle_config.yaml`:

```yaml
training:
  test_size: 0.2
  n_splits: 5  # TimeSeriesSplit
  
  models:
    xgboost:
      n_estimators: 500
      max_depth: 6
      learning_rate: 0.05
    
    lightgbm:
      n_estimators: 500
      max_depth: 6
      learning_rate: 0.05

monitoring:
  psi_threshold: 0.2
  ks_threshold: 0.1
  check_interval_hours: 24

ensemble:
  use_ml: true
  use_heuristic: true
  ml_weight: 0.7
  heuristic_weight: 0.3
```

## 🐛 Troubleshooting

### Проблема: "Недостаточно данных для обучения"

**Решение**: Убедитесь, что в БД至少 100 рынков с `resolution IS NOT NULL`.

```sql
SELECT COUNT(*) FROM market_metadata WHERE resolution IS NOT NULL;
```

### Проблема: "AUC-ROC ниже порога 0.65"

**Решение**:
1. Проверьте качество данных (нет ли пропусков, выбросов)
2. Увеличьте количество примеров
3. Попробуйте другие гиперпараметры в `oracle_config.yaml`
4. Добавьте больше признаков в `FeatureExtractor`

### Проблема: "Дрейф обнаружен"

**Решение**:
1. Переобучите модель: `python ml_oracle.py train`
2. Проверьте, не изменилась ли структура данных
3. Обновите `train_stats.json`

### Проблема: "Модель не загружена"

**Решение**: Убедитесь, что файл `artifacts/ml_oracle_bundle.pkl` существует. Если нет — выполните обучение.

## 📚 Дополнительная литература

- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [LightGBM Documentation](https://lightgbm.readthedocs.io/)
- [Time Series Cross-Validation](https://scikit-learn.org/stable/modules/cross_validation.html#time-series-split)
- [Probability Calibration](https://scikit-learn.org/stable/modules/calibration.html)
- [Population Stability Index](https://www.lexjansen.com/nesug/nesug07/ad/ad16.pdf)

## 📄 Лицензия

MIT License

## 👥 Авторы

PolyArb Team, 2026

---

**⚠️ Disclaimer**: Это экспериментальная система. Не используйте для реальных финансовых решений без дополнительной валидации.
