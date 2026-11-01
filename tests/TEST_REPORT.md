# Отчёт о тестировании ML Oracle

**Дата прогона:** 1 ноября 2026, 20:07 (+08)  
**Команда:** `polymarket_ml\venv\Scripts\python.exe -m pytest ..\tests -v --tb=short`  
**Среда:** Python 3.13.15, pytest 9.2.0, venv `polymarket_ml/venv`

**Итог: 41 пройден, 0 провалов, 0 ошибок.** Время 89.4 с.

`test_feature_ranges`, который падал в прогоне 19:44, теперь зелёный.

## Ошибки

Падений нет.

## Предупреждения

2 × `UndefinedMetricWarning` в `test_model_imbalanced_classes`:

```text
sklearn/metrics/_ranking.py: Only one class is present in y_true.
ROC AUC score is not defined in that case.
```

Тест при этом проходит. На фолде `TimeSeriesSplit` в `y_true` остаётся один класс, и ROC AUC для этого фолда не считается. На результат набора это не влияет.
