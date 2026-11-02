# 🧪 PolyArb ML Oracle - Тестирование

Полный набор тестов для проверки работоспособности ML Oracle.

## 🚀 Быстрый старт для другой ИИ

### 1. Быстрая проверка (30 секунд)
```bash
python quick_check.py
```

### 2. Полное тестирование (2 минуты)
```bash
run_tests.bat  # Windows
# или
pytest ../tests/ -v  # Linux/Mac (из папки polymarket_ml/)
```

### 3. Генерация отчёта
```bash
python generate_test_report.py
```

## 📋 Что проверяют тесты

### Unit-тесты (31 тест)
- ✅ Извлечение 50+ признаков из временных рядов (12 тестов)
- ✅ Обучение XGBoost и LightGBM (13 тестов)
- ✅ Ансамбль ML + эвристика (6 тестов)
- ✅ Метрики качества (AUC-ROC, Brier Score)
- ✅ Предсказания и оценка уверенности
- ✅ Сохранение/загрузка модели

### Интеграционные тесты (10 тестов)
- ✅ Полный пайплайн: данные → признаки → модель → предсказание
- ✅ Мониторинг дрейфа модели
- ✅ Согласованность и воспроизводимость
- ✅ Граничные случаи и качество данных
- ✅ Производительность (< 50ms на предсказание)

## 🎯 Критерии приёмки

Все тесты должны проходить:
- ✅ **41 тест проходит** (31 unit + 10 интеграционных)
- ✅ **Coverage > 80%**
- ✅ **Время выполнения < 2 минуты**
- ✅ **Нет критических ошибок**

## 📚 Документация

| Файл | Описание |
|------|----------|
| **[AI_TESTING_GUIDE.md](AI_TESTING_GUIDE.md)** | **🎯 ГЛАВНЫЙ ФАЙЛ для другой ИИ** |
| [TESTING.md](TESTING.md) | Главный документ по тестированию |
| [../tests/TESTING_GUIDE.md](../tests/TESTING_GUIDE.md) | Подробное руководство по тестированию |
| [../tests/README.md](../tests/README.md) | Документация тестов |
| [README.md](README.md) | Основная документация проекта |

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

## 📊 Пример успешного результата

```bash
$ python quick_check.py

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

## 🔍 Структура тестов

**⚠️ ВАЖНО:** Тесты находятся в отдельной папке `tests/` на верхнем уровне проекта.

```
project_root/
├── tests/                           ← ОТДЕЛЬНАЯ ПАПКА ДЛЯ ТЕСТОВ
│   ├── test_feature_extractor.py    # 15 unit-тестов
│   ├── test_model.py                # 12 unit-тестов
│   ├── test_integration.py          # 10 интеграционных тестов
│   ├── TESTING_GUIDE.md             # Подробное руководство
│   ├── conftest.py                  # Конфигурация pytest
│   └── README.md                    # Документация тестов
├── polymarket_ml/                   ← Python проект
│   ├── run_tests.bat                # Скрипт запуска тестов
│   ├── generate_test_report.py      # Генератор отчёта
│   ├── quick_check.py               # Быстрая проверка
│   ├── TESTING.md                   # Главный документ
│   └── AI_TESTING_GUIDE.md          # 🎯 Для другой ИИ
└── ...
```

## 💡 Для другой ИИ

Если вы ИИ и тестируете это приложение, начните с:

1. **[AI_TESTING_GUIDE.md](AI_TESTING_GUIDE.md)** - главный файл для вас
2. **Запустите:** `python quick_check.py`
3. **Проверьте:** все 5 проверок должны пройти
4. **Результат:** `test_report.json` с полным отчётом

## 🐛 Troubleshooting

### Тесты упали?
1. Прочитайте вывод ошибки
2. Проверьте `logs/ml_oracle.log`
3. Запустите `pytest ../tests/ -vv -s` для подробностей
4. Обратитесь к `../tests/TESTING_GUIDE.md`

### Coverage ниже 80%?
- Проверьте, что все модули импортируются
- Убедитесь, что тесты покрывают основные сценарии
- Добавьте новые тесты для непокрытого кода

### Ошибки зависимостей?
```bash
pip install -r requirements.txt
```

---

**Удачи в тестировании! 🚀**
