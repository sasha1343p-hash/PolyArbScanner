# 🧪 Тесты PolyArb ML Oracle

Автоматизированные тесты для проверки работоспособности ML Oracle.

## 📁 Структура тестов

```
tests/
├── test_feature_extractor.py    # Unit-тесты извлечения признаков (15 тестов)
├── test_model.py                # Unit-тесты ML-модели (12 тестов)
├── test_integration.py          # Интеграционные тесты (10 тестов)
├── TESTING_GUIDE.md             # Подробное руководство по тестированию
└── README.md                    # Этот файл
```

## 🚀 Быстрый старт

### Windows
```cmd
run_tests.bat
```

### Linux / macOS
```bash
pytest tests/ -v
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

## 📈 Критерии приёмки

Все тесты должны проходить:
- ✅ **37 тестов проходят**
- ✅ **Coverage > 80%**
- ✅ **Время выполнения < 2 минуты**
- ✅ **Нет критических ошибок**

## 🏃 Запуск тестов

### Все тесты
```bash
pytest tests/ -v
```

### Только unit-тесты
```bash
pytest tests/test_feature_extractor.py tests/test_model.py -v
```

### Только интеграционные тесты
```bash
pytest tests/test_integration.py -v
```

### С coverage
```bash
pytest tests/ --cov=ml_oracle --cov-report=html
```

### Конкретный тест
```bash
pytest tests/test_integration.py::TestFullPipeline::test_feature_extraction_to_prediction -v
```

## 📖 Документация

- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - подробное руководство по тестированию
- **[README.md](../README.md)** - основная документация проекта

## 🎯 Для другой ИИ

Если вы ИИ и тестируете это приложение:

1. **Запустите все тесты:**
   ```bash
   pytest tests/ -v --tb=short
   ```

2. **Проверьте результаты:**
   - Все 37 тестов должны пройти
   - Coverage должен быть > 80%
   - Не должно быть критических ошибок

3. **Если тесты упали:**
   - Прочитайте сообщение об ошибке
   - Проверьте логи в `logs/ml_oracle.log`
   - Запустите тест с `-s` для вывода print
   - Проверьте, что виртуальное окружение активировано

4. **Для отладки:**
   ```bash
   pytest tests/ -vv -s -l
   ```

## 📝 Пример отчёта

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
ml_oracle/feature_extractor.py            312     12    96%   45-48, 123-125
ml_oracle/model.py                        287     18    94%   67-70, 234-236
ml_oracle/monitor.py                      145      8    94%   89-92
ml_oracle/ensemble.py                      98      5    95%   56-58
---------------------------------------------------------------------
TOTAL                                     848     43    95%

============================== 37 passed in 45.23s ==============================
```

## 🔧 Troubleshooting

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
1. Проверьте [TESTING_GUIDE.md](TESTING_GUIDE.md)
2. Проверьте логи в `logs/ml_oracle.log`
3. Запустите с флагом `-vv -s` для подробного вывода

---

**Удачи в тестировании! 🚀**
