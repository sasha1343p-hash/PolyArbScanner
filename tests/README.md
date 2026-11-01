# 🧪 PolyArb ML Oracle - Тесты

Полный набор тестов для проверки работоспособности ML Oracle.

## 📁 Структура

```
tests/
├── test_feature_extractor.py    # Unit-тесты извлечения признаков (15 тестов)
├── test_model.py                # Unit-тесты ML-модели (12 тестов)
├── test_integration.py          # Интеграционные тесты (10 тестов)
├── TESTING_GUIDE.md             # Подробное руководство по тестированию
└── README.md                    # Этот файл
```

## 🚀 Быстрый старт

### Запуск всех тестов
```bash
cd polymarket_ml
pytest ../tests/ -v
```

### Запуск с coverage
```bash
cd polymarket_ml
pytest ../tests/ --cov=ml_oracle --cov-report=html
```

### Быстрая проверка
```bash
cd polymarket_ml
python quick_check.py
```

## 📊 Что проверяют тесты

### Unit-тесты (27 тестов)
- ✅ Извлечение 50+ признаков из временных рядов
- ✅ Статистики цен, волатильность, тренд, моментум
- ✅ Обучение XGBoost и LightGBM
- ✅ Метрики качества (AUC-ROC, Brier Score)
- ✅ Предсказания и оценка уверенности
- ✅ Сохранение/загрузка модели

### Интеграционные тесты (10 тестов)
- ✅ Полный пайплайн: данные → признаки → модель → предсказание
- ✅ Мониторинг дрейфа модели
- ✅ Согласованность извлечения признаков
- ✅ Воспроизводимость результатов
- ✅ Граничные случаи (пустые данные, мало данных)
- ✅ Качество данных (нет NaN, inf, корректные диапазоны)
- ✅ Производительность (инференс < 50ms)

## 🎯 Критерии приёмки

Все тесты должны проходить:
- ✅ **37 тестов проходят**
- ✅ **Coverage > 80%**
- ✅ **Время выполнения < 2 минуты**
- ✅ **Нет критических ошибок**

## 📖 Документация

- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - подробное руководство по тестированию
- **[../polymarket_ml/AI_TESTING_GUIDE.md](../polymarket_ml/AI_TESTING_GUIDE.md)** - главный файл для другой ИИ
- **[../polymarket_ml/TEST_REPORT.md](../polymarket_ml/TEST_REPORT.md)** - полный отчёт о тестировании
- **[../polymarket_ml/README.md](../polymarket_ml/README.md)** - основная документация проекта

## 🏃 Команды для тестирования

```bash
# Все тесты
cd polymarket_ml
pytest ../tests/ -v

# Только unit-тесты
pytest ../tests/test_feature_extractor.py ../tests/test_model.py -v

# Только интеграционные тесты
pytest ../tests/test_integration.py -v

# С coverage
pytest ../tests/ --cov=ml_oracle --cov-report=html

# Конкретный тест
pytest ../tests/test_integration.py::TestFullPipeline::test_feature_extraction_to_prediction -v
```

## 📝 Запуск из папки polymarket_ml

Все команды должны выполняться из папки `polymarket_ml/`, так как тесты импортируют модули из `ml_oracle/`.

```bash
# Перейти в папку проекта
cd polymarket_ml

# Активировать виртуальное окружение
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Запустить тесты
pytest ../tests/ -v
```

## 🐛 Troubleshooting

### Ошибка: "ModuleNotFoundError: No module named 'ml_oracle'"
Убедитесь, что вы находитесь в папке `polymarket_ml/` и виртуальное окружение активировано.

### Ошибка: "No such file or directory: 'polymarket_history.db'"
База данных должна находиться в `../polymarket_history.db` (на уровне выше `polymarket_ml/`).

### Тесты падают с ошибкой памяти
Запускайте тесты по одному:
```bash
pytest ../tests/test_integration.py::TestFullPipeline::test_feature_extraction_to_prediction
```

## 💡 Советы

1. **Запускайте тесты из папки `polymarket_ml/`** - это важно для импортов
2. **Используйте виртуальное окружение** - для изоляции зависимостей
3. **Проверяйте coverage** - стремитесь к > 80%
4. **Читайте ошибки** - они говорят, что не так

---

**Удачи в тестировании! 🚀**
