# 🧪 PolyArb ML Oracle - Отчёт о тестировании

## 📋 Резюме

Этот документ содержит полную информацию о системе тестирования PolyArb ML Oracle.

**⚠️ ВАЖНО:** Тесты находятся в отдельной папке `tests/` на верхнем уровне проекта (рядом с `polymarket_ml/`, `src/`, `public/`).

---

## 📁 Структура проекта

```
project_root/
├── tests/                           ← ОТДЕЛЬНАЯ ПАПКА ДЛЯ ТЕСТОВ
│   ├── test_feature_extractor.py    # 12 unit-тестов
│   ├── test_model.py                # 13 unit-тестов
│   ├── test_ensemble.py             # 6 unit-тестов
│   ├── test_integration.py          # 10 интеграционных тестов
│   ├── TESTING_GUIDE.md             # Подробное руководство
│   ├── conftest.py                  # Конфигурация pytest
│   └── README.md                    # Документация тестов
├── polymarket_ml/                   ← Python проект
│   ├── ml_oracle/                   # ML модули
│   ├── ml_oracle.py                 # CLI интерфейс
│   ├── run_tests.bat                # Скрипт запуска тестов
│   ├── generate_test_report.py      # Генератор отчёта
│   ├── quick_check.py               # Быстрая проверка
│   ├── full_setup.bat               # Полная установка
│   └── ...
└── ...
```

---

## 🎯 Критерии приёмки

Все тесты должны проходить:
- ✅ **41 тест проходит** (31 unit + 10 интеграционных)
- ✅ **Coverage > 80%**
- ✅ **Время выполнения < 2 минуты**
- ✅ **Нет критических ошибок**

---

## 🏃 Команды для тестирования

**⚠️ ВАЖНО:** Все команды должны выполняться из папки `polymarket_ml/`, но тесты находятся в `../tests/`.

### Быстрая проверка (30 секунд)
```bash
python quick_check.py
```

### Все тесты
```bash
pytest ../tests/ -v
```

### Только unit-тесты
```bash
pytest ../tests/test_feature_extractor.py ../tests/test_model.py ../tests/test_ensemble.py -v
```

### Только интеграционные тесты
```bash
pytest ../tests/test_integration.py -v
```

### С coverage
```bash
pytest ../tests/ --cov=ml_oracle --cov-report=html
```

### Генерация отчёта
```bash
python generate_test_report.py
```

### Windows (через скрипт)
```cmd
run_tests.bat
```

---

## 📊 Что проверяют тесты

### Unit-тесты (31 тест)

#### `test_feature_extractor.py` (12 тестов)
- ✅ Извлечение статистик цен
- ✅ Волатильность и тренд
- ✅ Моментум и объём
- ✅ RSI и ценовые паттерны
- ✅ Временные фичи
- ✅ Категории рынков
- ✅ Обработка пустых данных
- ✅ Нормализация признаков

#### `test_model.py` (13 тестов)
- ✅ Обучение XGBoost
- ✅ Обучение LightGBM
- ✅ Метрики качества
- ✅ Предсказания
- ✅ Уверенность предсказаний
- ✅ Сохранение/загрузка модели
- ✅ Feature importance
- ✅ Обработка NaN
- ✅ Несбалансированные классы

#### `test_ensemble.py` (6 тестов)
- ✅ Конфигурация ансамбля
- ✅ Эвристический оракул
- ✅ Ансамбль только с эвристикой
- ✅ Ансамбль без моделей

### Интеграционные тесты (10 тестов)

#### `TestFullPipeline` (5 тестов)
1. ✅ Полный цикл: данные → признаки → модель → предсказание
2. ✅ Мониторинг дрейфа
3. ✅ Согласованность признаков
4. ✅ Воспроизводимость результатов
5. ✅ Граничные случаи

#### `TestDataQuality` (3 теста)
1. ✅ Отсутствие NaN
2. ✅ Отсутствие inf
3. ✅ Корректные диапазоны

#### `TestPerformance` (2 теста)
1. ✅ Скорость инференса < 50ms
2. ✅ Скорость пакетного инференса

---

## 📈 Ожидаемый результат

### Успешный запуск
```
============================= test session starts ==============================
collected 41 items

../tests/test_feature_extractor.py ............                            [ 29%]
../tests/test_model.py .............                                       [ 60%]
../tests/test_ensemble.py ......                                           [ 75%]
../tests/test_integration.py .........                                     [ 97%]

---------- coverage: platform win32, python 3.11.5 ----------
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
ml_oracle/__init__.py                       7      0   100%
ml_oracle/feature_extractor.py            266     46    83%
ml_oracle/model.py                        315     49    84%
ml_oracle/monitor.py                      124     15    88%
ml_oracle/ensemble.py                      81     10    88%
---------------------------------------------------------------------
TOTAL                                     793     120    85%

============================== 41 passed in 90.23s ==============================
```

### Отчёт в JSON
```json
{
  "timestamp": "2026-01-15T10:30:00",
  "prerequisites": {
    "python": {"status": true, "details": "Python 3.13.15"},
    "venv": {"status": true, "details": "venv directory exists"},
    "dependencies": {"status": true, "details": "All dependencies installed"},
    "database": {"status": true, "details": "Database size: 2.5 MB"},
    "model": {"status": true, "details": "Model size: 15.3 MB"}
  },
  "tests": {
    "unit_tests": {"status": true, "passed": 31, "failed": 0, "total": 31},
    "integration_tests": {"status": true, "passed": 10, "failed": 0, "total": 10},
    "coverage": {"status": true, "percentage": 85.0}
  },
  "summary": {
    "all_checks_passed": true,
    "total_tests": 41,
    "passed_tests": 41,
    "failed_tests": 0,
    "coverage": 85.0
  }
}
```

---

## 🔧 Исправленные проблемы

### 1. pandas 3.1 несовместимость
**Проблема:** `freq='H'` больше не работает в pandas 3.1  
**Решение:** Заменено на `freq='h'` во всех тестах

### 2. numpy 2 несовместимость
**Проблема:** `isinstance(score, (int, float))` не работает с `np.float32`  
**Решение:** Заменено на `hasattr(score, '__float__')`

### 3. LightGBM на дисбалансе
**Проблема:** LightGBM падает, если в фолде нет одного из классов  
**Решение:** Добавлена проверка `len(set(y_train)) < 2` и пропуск таких фолдов

### 4. Монитор дрейфа
**Проблема:** Ложный PSI из-за генерации случайных данных  
**Решение:** Сохраняются реальные данные из обучающей выборки в `train_data`

### 5. price_current вне [0, 1]
**Проблема:** Синтетические цены выходят за диапазон вероятностей  
**Решение:** Добавлен `np.clip(prices, 0.0, 1.0)` в `_extract_price_statistics`

### 6. test_edge_cases для pandas 3
**Проблема:** Сравнение Series с разным индексом запрещено  
**Решение:** Извлечение значения как скаляр через `.iloc[0]`

### 7. ensemble.py не покрыт
**Проблема:** Покрытие ensemble.py было 25%  
**Решение:** Добавлен `test_ensemble.py` с 6 тестами

---

## 📚 Документация

| Файл | Описание |
|------|----------|
| **[TEST_REPORT.md](TEST_REPORT.md)** | **🎯 ЭТОТ ФАЙЛ** - полный отчёт о тестировании |
| [AI_TESTING_GUIDE.md](AI_TESTING_GUIDE.md) | Главный файл для другой ИИ |
| [TESTING.md](TESTING.md) | Документ по тестированию |
| [../tests/TESTING_GUIDE.md](../tests/TESTING_GUIDE.md) | Подробное руководство |
| [../tests/README.md](../tests/README.md) | Документация тестов |
| [README.md](README.md) | Основная документация проекта |

---

## 🐛 Troubleshooting

### Ошибка: "ModuleNotFoundError: No module named 'ml_oracle'"
**Решение:** Убедитесь, что вы находитесь в папке `polymarket_ml/` и виртуальное окружение активировано.

### Ошибка: "No such file or directory: '../tests/'"
**Решение:** Тесты находятся в папке `tests/` на верхнем уровне проекта. Убедитесь, что структура проекта правильная.

### Тесты падают с ошибкой памяти
**Решение:** Запускайте тесты по одному:
```bash
pytest ../tests/test_integration.py::TestFullPipeline::test_feature_extraction_to_prediction
```

### Coverage ниже 80%
**Решение:**
- Проверьте, что все модули импортируются
- Убедитесь, что тесты покрывают основные сценарии
- Добавьте новые тесты для непокрытого кода

---

## 💡 Для другой ИИ

Если вы ИИ и тестируете это приложение:

### Шаг 1: Быстрая проверка
```bash
python quick_check.py
```

### Шаг 2: Полное тестирование
```bash
pytest ../tests/ -v
```

### Шаг 3: Генерация отчёта
```bash
python generate_test_report.py
```

### Шаг 4: Проверка результатов
Откройте `test_report.json` и проверьте:
- Все prerequisites должны быть `true`
- Все тесты должны пройти
- Coverage должен быть > 80%

---

## 📞 Поддержка

Если тесты не проходят:
1. Проверьте этот документ
2. Проверьте [../tests/TESTING_GUIDE.md](../tests/TESTING_GUIDE.md)
3. Проверьте логи в `logs/ml_oracle.log`
4. Запустите с флагом `-vv -s` для подробного вывода

---

**Удачи в тестировании! 🚀**
