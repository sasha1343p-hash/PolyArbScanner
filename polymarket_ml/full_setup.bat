@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   PolyArb ML Oracle - Полная установка и запуск
echo ============================================================
echo.

REM Проверка Python
echo [1/5] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    echo Установите Python 3.10+ с https://www.python.org/downloads/
    pause
    exit /b 1
)
echo OK

REM Создание venv если нет
echo.
echo [2/5] Виртуальное окружение...
if not exist "venv" (
    echo Создание venv...
    python -m venv venv
    if errorlevel 1 (
        echo ОШИБКА: Не удалось создать venv
        pause
        exit /b 1
    )
)
call venv\Scripts\activate.bat
echo OK

REM Установка зависимостей
echo.
echo [3/5] Зависимости...
if not exist ".deps_installed" (
    echo Установка pandas, numpy, scikit-learn, xgboost, lightgbm...
    python -m pip install --upgrade pip >nul 2>&1
    pip install pandas numpy scikit-learn xgboost lightgbm scipy joblib pyyaml pytest
    if errorlevel 1 (
        echo ОШИБКА: Не удалось установить зависимости
        pause
        exit /b 1
    )
    echo. > .deps_installed
    echo OK - зависимости установлены
) else (
    echo OK - зависимости уже установлены
)

REM Создание БД
echo.
echo [4/5] База данных...
if not exist "polymarket_history.db" (
    echo Создание тестовой базы данных...
    python create_test_db.py
    if errorlevel 1 (
        echo ОШИБКА: Не удалось создать БД
        pause
        exit /b 1
    )
    echo OK - БД создана
) else (
    echo OK - БД уже существует
)

REM Создание директорий
if not exist "artifacts" mkdir artifacts
if not exist "logs" mkdir logs

REM Обучение модели
echo.
echo [5/5] Обучение модели...
echo Обучение может занять 3-5 минут...
echo.
python ml_oracle.py train

if errorlevel 1 (
    echo.
    echo ОШИБКА: Не удалось обучить модель
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   ВСЁ ГОТОВО!
echo ============================================================
echo.
echo Модель обучена. Теперь вы можете:
echo.
echo   run.bat predict market-001    - предсказание для рынка
echo   run.bat drift-check           - проверка дрейфа
echo   run.bat feature-importance    - важность признаков
echo   start_all.bat                 - запуск веб-дашборда
echo.
echo ============================================================
echo.

set /p PREDICT="Сделать тестовое предсказание? (y/n): "
if /i "!PREDICT!"=="y" (
    echo.
    python ml_oracle.py predict market-001
)

echo.
pause
