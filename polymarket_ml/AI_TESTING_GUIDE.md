# 🧪 PolyArb ML Oracle - Тестирование для ИИ

Этот документ содержит инструкции для другой ИИ по тестированию приложения PolyArb ML Oracle.

**⚠️ ВАЖНО:** Все тесты находятся в отдельной папке `tests/` на верхнем уровне проекта (рядом с `polymarket_ml/`, `src/`, `public/`).

## 🎯 Быстрая проверка (30 секунд)

```bash
python quick_check.py
```

Этот скрипт проверит:
- ✅ Установку зависимостей
- ✅ Наличие базы данных
- ✅ Обученную модель
- ✅ Работоспособность предсказания
- ✅ Запуск тестов

**Ожидаемый результат:**
```
============================================================
  Summary
============================================================

  [✓ PASS] Dependencies
  [✓ PASS] Database
  [✓ PASS] Model
  [✓ PASS] Prediction
  [✓ PASS] Tests

============================================================
  ✓ ALL CHECKS PASSED!
============================================================
```

## 📊 Полное тестирование (2 минуты)

### Вариант 1: Через скрипт
```bash
run_tests.bat  # Windows
# или
pytest ../tests/ -v  # Linux/Mac (из папки polymarket_ml/)
```

### Вариант 2: С генерацией отчёта
```bash
python generate_test_report.py
```

Это создаст файл `test_report.json` с полным отчётом.

## 📋 Что проверять

### 1. Prerequisites (Обязательно)
Все должны быть `true`:
```json
{
  "python": {"status": true},
  "venv": {"status": true},
  "dependencies": {"status": true},
  "database": {"status": true},
  "model": {"status": true}
}
```

### 2. Tests (Обязательно)
Все тесты должны пройти:
```json
{
  "unit_tests": {"status": true, "passed": 27, "total": 27},
  "integration_tests": {"status": true, "passed": 10, "total": 10}
}
```

### 3. Coverage (Обязательно)
Покрытие кода должно быть > 80%:
```json
{
  "coverage": {"status": true, "percentage": 95.0}
}
```

### 4. Summary (Обязательно)
```json
{
  "all_checks_passed": true,
  "total_tests": 37,
  "passed_tests": 37,
  "failed_tests": 0,
  "coverage": 95.0
}
```

## 🔍 Структура тестов

**⚠️ ВАЖНО:** Тесты находятся в отдельной папке `tests/` на верхнем уровне проекта (рядом с `polymarket_ml/`, `src/`, `public/`).

```
project_root/
├── tests/                       ← ОТДЕЛЬНАЯ ПАПКА ДЛЯ ТЕСТОВ
│   ├── test_feature_extractor.py    # 15 unit-тестов
│   ├── test_model.py                # 12 unit-тестов
│   ├── test_integration.py          # 10 интеграционных тестов
│   ├── TESTING_GUIDE.md             # Подробное руководство
│   ├── conftest.py                  # Конфигурация pytest
│   └── README.md                    # Документация тестов
├── polymarket_ml/               ← Python проект
│   ├── ml_oracle/
│   ├── ml_oracle.py
│   └── ...
└── ...
```

## 📚 Документация

- **[TESTING.md](TESTING.md)** - главный документ по тестированию
- **[../tests/TESTING_GUIDE.md](../tests/TESTING_GUIDE.md)** - подробное руководство
- **[../tests/README.md](../tests/README.md)** - документация тестов
- **[README.md](README.md)** - основная документация проекта

## 🏃 Команды для тестирования

**⚠️ ВАЖНО:** Все команды должны выполняться из папки `polymarket_ml/`, но тесты находятся в `../tests/`.

```bash
# Быстрая проверка
python quick_check.py

# Все тесты (из папки polymarket_ml/)
pytest ../tests/ -v

# С coverage
pytest ../tests/ --cov=ml_oracle --cov-report=html

# Генерация отчёта
python generate_test_report.py

# Отладка
pytest ../tests/ -vv -s -l
```

## 🐛 Если тесты упали

### Шаг 1: Проверьте вывод
```bash
pytest ../tests/ -v --tb=short
```

### Шаг 2: Проверьте логи
```bash
cat logs/ml_oracle.log
```

### Шаг 3: Запустите с подробным выводом
```bash
pytest ../tests/ -vv -s
```

### Шаг 4: Проверьте конкретный тест
```bash
pytest ../tests/test_integration.py::TestFullPipeline::test_feature_extraction_to_prediction -v
```

## 📈 Критерии приёмки

Все тесты должны проходить:
- ✅ **37 тестов проходят**
- ✅ **Coverage > 80%**
- ✅ **Время выполнения < 2 минуты**
- ✅ **Нет критических ошибок**

## 💡 Примеры использования

### Пример 1: Быстрая проверка
```bash
python quick_check.py
```

**Вывод:**
```
============================================================
  PolyArb ML Oracle - Quick Check
============================================================

[1/5] Checking dependencies...
  ✓ All dependencies installed

[2/5] Checking database...
  ✓ Database exists (2.5 MB)

[3/5] Checking model...
  ✓ Model trained (15.3 MB)

[4/5] Checking prediction...
  ✓ Prediction works (probability: 67.30%)

[5/5] Running tests...
  ✓ All tests passed

============================================================
  Summary
============================================================

  [✓ PASS] Dependencies
  [✓ PASS] Database
  [✓ PASS] Model
  [✓ PASS] Prediction
  [✓ PASS] Tests

============================================================
  ✓ ALL CHECKS PASSED!
============================================================
```

### Пример 2: Генерация отчёта
```bash
python generate_test_report.py
```

**Вывод:**
```json
{
  "timestamp": "2026-01-15T10:30:00",
  "prerequisites": {
    "python": {"status": true, "details": "Python 3.11.5"},
    "venv": {"status": true, "details": "venv directory exists"},
    "dependencies": {"status": true, "details": "All dependencies installed"},
    "database": {"status": true, "details": "Database size: 2.5 MB"},
    "model": {"status": true, "details": "Model size: 15.3 MB"}
  },
  "tests": {
    "unit_tests": {"status": true, "passed": 27, "failed": 0, "total": 27},
    "integration_tests": {"status": true, "passed": 10, "failed": 0, "total": 10},
    "coverage": {"status": true, "percentage": 95.0}
  },
  "summary": {
    "all_checks_passed": true,
    "total_tests": 37,
    "passed_tests": 37,
    "failed_tests": 0,
    "coverage": 95.0
  }
}
```

## 🎓 Для другой ИИ

Если вы ИИ и тестируете это приложение:

1. **Запустите быструю проверку:**
   ```bash
   python quick_check.py
   ```

2. **Если всё прошло:**
   - Приложение готово к использованию
   - Можно делать предсказания
   - Можно запускать дашборд

3. **Если что-то упало:**
   - Прочитайте вывод ошибки
   - Проверьте `logs/ml_oracle.log`
   - Запустите `pytest ../tests/ -vv -s` для подробностей
   - Обратитесь к `../tests/TESTING_GUIDE.md`

4. **Для отладки:**
   - Проверьте виртуальное окружение
   - Проверьте зависимости
   - Проверьте базу данных
   - Переобучите модель: `run.bat train`

## 📞 Поддержка

Если тесты не проходят:
1. Проверьте [TESTING.md](TESTING.md)
2. Проверьте [../tests/TESTING_GUIDE.md](../tests/TESTING_GUIDE.md)
3. Проверьте логи в `logs/ml_oracle.log`
4. Запустите с флагом `-vv -s` для подробного вывода

---

**Удачи в тестировании! 🚀**
