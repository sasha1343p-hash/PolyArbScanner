# 🧪 PolyArb ML Oracle - Тестирование

Полный набор тестов для проверки работоспособности ML Oracle.

## 📁 Структура

```
polymarket_ml/
├── tests/
│   ├── test_feature_extractor.py    # Unit-тесты признаков (15 тестов)
│   ├── test_model.py                # Unit-тесты модели (12 тестов)
│   ├── test_integration.py          # Интеграционные тесты (10 тестов)
│   ├── TESTING_GUIDE.md             # Подробное руководство
│   └── README.md                    # Документация тестов
├── run_tests.bat                    # Скрипт запуска тестов (Windows)
├── generate_test_report.py          # Генератор отчёта
└── README.md                        # Этот файл
```

## 🚀 Быстрый старт для другой ИИ

### 1. Запустить все тесты

**Windows:**
```cmd
run_tests.bat
```

**Linux/Mac:**
```bash
pytest tests/ -v
```

### 2. Сгенерировать отчёт

```bash
python generate_test_report.py
```

Это создаст файл `test_report.json` с полным отчётом.

### 3. Проверить результаты

Откройте `test_report.json` и проверьте:
```json
{
  "summary": {
    "all_checks_passed": true,
    "total_tests": 37,
    "passed_tests": 37,
    "failed_tests": 0,
    "coverage": 95.0
  }
}
```

## 📊 Что проверяют тесты

### Unit-тесты (27 тестов)

#### `test_feature_extractor.py` (15 тестов)
- ✅ Извлечение статистик цен
- ✅ Волатильность и тренд
- ✅ Моментум и объём
- ✅ RSI и ценовые паттерны
- ✅ Временные фичи
- ✅ Категории рынков
- ✅ Обработка пустых данных
- ✅ Нормализация признаков

#### `test_model.py` (12 тестов)
- ✅ Обучение XGBoost
- ✅ Обучение LightGBM
- ✅ Метрики качества
- ✅ Предсказания
- ✅ Уверенность предсказаний
- ✅ Сохранение/загрузка модели
- ✅ Feature importance
- ✅ Обработка NaN
- ✅ Несбалансированные классы

### Интеграционные тесты (10 тестов)

#### `TestFullPipeline`
1. ✅ Полный цикл: данные → признаки → модель → предсказание
2. ✅ Мониторинг дрейфа
3. ✅ Согласованность признаков
4. ✅ Воспроизводимость результатов
5. ✅ Граничные случаи

#### `TestDataQuality`
1. ✅ Отсутствие NaN
2. ✅ Отсутствие inf
3. ✅ Корректные диапазоны

#### `TestPerformance`
1. ✅ Скорость инференса < 50ms
2. ✅ Скорость пакетного инференса

## 🎯 Критерии приёмки

Все тесты должны проходить:
- ✅ **37 тестов проходят**
- ✅ **Coverage > 80%**
- ✅ **Время выполнения < 2 минуты**
- ✅ **Нет критических ошибок**

## 📖 Документация

- **[TESTING_GUIDE.md](tests/TESTING_GUIDE.md)** - подробное руководство по тестированию
- **[tests/README.md](tests/README.md)** - документация тестов
- **[README.md](README.md)** - основная документация проекта

## 🔍 Для другой ИИ

Если вы ИИ и тестируете это приложение:

### Шаг 1: Проверка окружения
```bash
python --version  # Должно быть 3.10+
pip list | grep -E "pandas|xgboost|lightgbm"
```

### Шаг 2: Запуск тестов
```bash
pytest tests/ -v --tb=short
```

### Шаг 3: Анализ результатов
```bash
python generate_test_report.py
cat test_report.json
```

### Шаг 4: Проверка отчёта
```json
{
  "prerequisites": {
    "python": {"status": true},
    "venv": {"status": true},
    "dependencies": {"status": true},
    "database": {"status": true},
    "model": {"status": true}
  },
  "tests": {
    "unit_tests": {"status": true, "passed": 27, "total": 27},
    "integration_tests": {"status": true, "passed": 10, "total": 10},
    "coverage": {"status": true, "percentage": 95.0}
  },
  "summary": {
    "all_checks_passed": true
  }
}
```

### Шаг 5: Если тесты упали
1. Прочитайте вывод pytest
2. Проверьте `logs/ml_oracle.log`
3. Запустите с `-vv -s` для подробностей
4. Проверьте [TESTING_GUIDE.md](tests/TESTING_GUIDE.md)

## 🏃 Команды для тестирования

```bash
# Все тесты
pytest tests/ -v

# Только unit-тесты
pytest tests/test_feature_extractor.py tests/test_model.py -v

# Только интеграционные тесты
pytest tests/test_integration.py -v

# С coverage
pytest tests/ --cov=ml_oracle --cov-report=html

# Конкретный тест
pytest tests/test_integration.py::TestFullPipeline::test_feature_extraction_to_prediction -v

# Отладка
pytest tests/ -vv -s -l

# Только упавшие тесты
pytest tests/ --lf
```

## 📈 Пример успешного отчёта

```
============================= test session starts ==============================
collected 37 items

tests/test_feature_extractor.py ...............                          [ 40%]
tests/test_model.py ............                                         [ 72%]
tests/test_integration.py .........                                      [ 97%]

---------- coverage: platform win32, python 3.11.5 ----------
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
ml_oracle/__init__.py                       6      0   100%
ml_oracle/feature_extractor.py            312     12    96%
ml_oracle/model.py                        287     18    94%
ml_oracle/monitor.py                      145      8    94%
ml_oracle/ensemble.py                      98      5    95%
---------------------------------------------------------------------
TOTAL                                     848     43    95%

============================== 37 passed in 45.23s ==============================
```

## 🐛 Troubleshooting

### Ошибка: "ModuleNotFoundError: No module named 'pytest'"
```bash
pip install pytest pytest-cov
```

### Ошибка: "venv not found"
```bash
# Windows
setup.bat

# Linux/Mac
python3 setup_crossplatform.py
```

### Тесты падают с ошибкой памяти
```bash
# Запускайте тесты по одному
pytest tests/test_integration.py::TestFullPipeline::test_feature_extraction_to_prediction
```

### Coverage ниже 80%
- Проверьте, что все модули импортируются
- Убедитесь, что тесты покрывают основные сценарии
- Добавьте новые тесты для непокрытого кода

## 📞 Поддержка

Если тесты не проходят:
1. Проверьте [TESTING_GUIDE.md](tests/TESTING_GUIDE.md)
2. Проверьте логи в `logs/ml_oracle.log`
3. Запустите с флагом `-vv -s` для подробного вывода
4. Создайте issue с полным выводом тестов

---

**Удачи в тестировании! 🚀**
