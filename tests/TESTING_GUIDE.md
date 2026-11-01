# 🧪 Руководство по тестированию PolyArb ML Oracle

Полное руководство по запуску и интерпретации тестов.

## 📋 Содержание

- [Быстрый старт](#быстрый-старт)
- [Типы тестов](#типы-тестов)
- [Запуск тестов](#запуск-тестов)
- [Интерпретация результатов](#интерпретация-результатов)
- [Добавление новых тестов](#добавление-новых-тестов)

## 🚀 Быстрый старт

### 1. Перейдите в папку проекта
```bash
cd polymarket_ml
```

### 2. Активируйте виртуальное окружение
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Запустите все тесты
```bash
pytest ../tests/ -v
```

### 4. Запустите с coverage
```bash
pytest ../tests/ --cov=ml_oracle --cov-report=html
```

### 5. Откройте отчёт coverage
```bash
# Windows
start htmlcov/index.html

# Mac
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html
```

## 📊 Типы тестов

### 1. Unit-тесты (`test_feature_extractor.py`)
Тестируют отдельные компоненты:
- Извлечение признаков из временных рядов
- Статистики цен (mean, std, min, max)
- Волатильность и тренд
- Моментум и объёмные метрики
- RSI и другие индикаторы

**Количество:** 15 тестов

### 2. Unit-тесты модели (`test_model.py`)
Тестируют ML-модель:
- Обучение XGBoost и LightGBM
- Метрики качества (AUC-ROC, Brier Score)
- Предсказания и уверенность
- Сохранение/загрузка модели
- Feature importance

**Количество:** 12 тестов

### 3. Интеграционные тесты (`test_integration.py`)
Тестируют полный пайплайн:
- От загрузки данных до предсказания
- Мониторинг дрейфа
- Согласованность признаков
- Воспроизводимость результатов
- Граничные случаи
- Качество данных
- Производительность

**Количество:** 10 тестов

## 🏃 Запуск тестов

### Все тесты
```bash
cd polymarket_ml
pytest ../tests/ -v
```

### Конкретный файл
```bash
pytest ../tests/test_integration.py -v
```

### Конкретный тест
```bash
pytest ../tests/test_integration.py::TestFullPipeline::test_feature_extraction_to_prediction -v
```

### С coverage
```bash
pytest ../tests/ --cov=ml_oracle --cov-report=html
```

### Только быстрые тесты
```bash
pytest ../tests/ -m "not slow"
```

### С выводом print
```bash
pytest ../tests/ -s
```

## 📈 Интерпретация результатов

### ✅ Успешный запуск
```
============================= test session starts ==============================
collected 37 items

../tests/test_feature_extractor.py ...............                          [ 40%]
../tests/test_model.py ............                                         [ 72%]
../tests/test_integration.py .........                                      [ 97%]

============================== 37 passed in 45.23s ==============================
```

### ❌ Ошибки
```
FAILED ../tests/test_integration.py::TestFullPipeline::test_feature_extraction_to_prediction
AssertionError: Должно быть 150 примеров
```

**Что делать:**
1. Прочитать сообщение об ошибке
2. Проверить, какие данные передаются в тест
3. Проверить логи в `logs/ml_oracle.log`
4. Запустить тест с `-s` для вывода print

### ⚠️ Предупреждения
```
WARNING: AUC-ROC ниже порога 0.65
```

**Что делать:**
- Это нормально для тестовых данных
- Для реальных данных нужно больше примеров (1000+)

## 🔍 Что проверяют тесты

### Интеграционные тесты

#### `TestFullPipeline`
1. **test_feature_extraction_to_prediction** - полный цикл от данных до предсказания
2. **test_model_monitoring_pipeline** - мониторинг дрейфа
3. **test_feature_extractor_consistency** - согласованность извлечения признаков
4. **test_model_reproducibility** - воспроизводимость результатов
5. **test_edge_cases** - граничные случаи (пустые данные, мало данных)

#### `TestDataQuality`
1. **test_no_nan_in_features** - отсутствие NaN
2. **test_no_inf_in_features** - отсутствие inf
3. **test_feature_ranges** - корректные диапазоны значений

#### `TestPerformance`
1. **test_inference_speed** - скорость инференса < 50ms
2. **test_batch_inference_speed** - скорость пакетного инференса

## 🎯 Критерии приёмки

Все тесты должны проходить:
- ✅ 37 тестов проходят
- ✅ Coverage > 80%
- ✅ Время выполнения < 2 минуты
- ✅ Нет ошибок и предупреждений

## 🐛 Отладка тестов

### Включить подробный вывод
```bash
pytest ../tests/ -vv -s
```

### Остановиться на первой ошибке
```bash
pytest ../tests/ -x
```

### Запустить только упавшие тесты
```bash
pytest ../tests/ --lf
```

### Показать локальные переменные
```bash
pytest ../tests/ -l
```

## 📝 Добавление новых тестов

### Структура теста
```python
def test_something(self, sample_data, temp_dir):
    """Описание того, что проверяет тест."""
    # Arrange - подготовка данных
    metadata_df, price_df = sample_data
    
    # Act - выполнение действия
    extractor = FeatureExtractor()
    X = extractor.extract_features_batch(metadata_df, price_df)
    
    # Assert - проверки
    assert len(X) == 150, "Должно быть 150 примеров"
    assert not X.isna().any().any(), "Не должно быть NaN"
```

### Фикстуры
```python
@pytest.fixture
def sample_data():
    """Создаёт тестовые данные."""
    # ... код создания данных ...
    return metadata_df, price_df
```

### Классы тестов
```python
class TestMyFeature:
    """Группа тестов для одной фичи."""
    
    def test_case_1(self, sample_data):
        # ... тест ...
        pass
    
    def test_case_2(self, sample_data):
        # ... тест ...
        pass
```

## 💡 Советы

1. **Запускайте тесты часто** - после каждого изменения кода
2. **Пишите тесты сначала** - TDD (Test-Driven Development)
3. **Используйте фикстуры** - для переиспользования данных
4. **Проверяйте coverage** - стремитесь к > 80%
5. **Читайте ошибки** - они говорят, что не так

## 📖 Документация проекта

- **[../polymarket_ml/TEST_REPORT.md](../polymarket_ml/TEST_REPORT.md)** - полный отчёт о тестировании
- **[../polymarket_ml/AI_TESTING_GUIDE.md](../polymarket_ml/AI_TESTING_GUIDE.md)** - главный файл для другой ИИ
- **[../polymarket_ml/TESTING.md](../polymarket_ml/TESTING.md)** - документ по тестированию
- **[../polymarket_ml/README.md](../polymarket_ml/README.md)** - основная документация проекта

## 📚 Дополнительные ресурсы

- [Pytest documentation](https://docs.pytest.org/)
- [Pytest fixtures](https://docs.pytest.org/en/stable/explanation/fixtures.html)
- [Coverage.py](https://coverage.readthedocs.io/)

---

**Удачи в тестировании! 🚀**
