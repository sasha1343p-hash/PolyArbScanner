# PolyArb ML Oracle - Инструкция по запуску

## Быстрый старт (3 минуты)

### Шаг 1: Запустите установщик

Откройте командную строку в папке `polymarket_ml` и выполните:

```cmd
quick_setup.bat
```

Или просто дважды кликните на файл `quick_setup.bat`.

### Шаг 2: Дождитесь завершения

Установщик автоматически:
- ✅ Создаст виртуальное окружение
- ✅ Установит все зависимости (pandas, xgboost, lightgbm и др.)
- ✅ Создаст тестовую базу данных
- ✅ Обучит ML модель

### Шаг 3: Используйте

После установки доступны команды:

```cmd
# Предсказание для рынка
python ml_oracle.py predict market-001

# Проверка дрейфа модели
python ml_oracle.py drift-check

# Важность признаков
python ml_oracle.py feature-importance

# Запуск веб-дашборда
start_all.bat
```

## Если возникли ошибки

### Ошибка: "ModuleNotFoundError: No module named 'pandas'"

Решение: запустите `quick_setup.bat` заново.

### Ошибка: "Python not found"

Решение: установите Python 3.10+ с [python.org](https://python.org)
**ВАЖНО:** отметьте "Add Python to PATH" при установке.

### Ошибка: "venv cannot be loaded"

Решение: откройте PowerShell от имени администратора и выполните:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Структура проекта

```
polymarket_ml/
├── quick_setup.bat          ← Запустите это первым!
├── start_all.bat            ← Запуск веб-дашборда
├── ml_oracle.py             ← CLI интерфейс
├── ml_oracle/               ← ML модули
├── configs/                 ← Конфигурация
├── tests/                   ← Тесты
└── artifacts/               ← Обученная модель (создаётся автоматически)
```

## Веб-дашборд

После обучения модели запустите:

```cmd
start_all.bat
```

Откроется дашборд на http://localhost:3000

## Поддержка

Если возникли проблемы:
1. Удалите папку `venv`
2. Запустите `quick_setup.bat` заново
3. Проверьте, что Python 3.10+ установлен

---

**Готово! Теперь у вас работает ML Oracle для предиктивных рынков.**
