@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   PolyArb ML Oracle - Установка и запуск
echo ============================================================
echo.

REM Проверка Python
echo [1/4] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    echo Установите Python 3.10+ с https://www.python.org/downloads/
    pause
    exit /b 1
)
echo OK

REM Создание виртуального окружения
echo.
echo [2/4] Создание виртуального окружения...
if not exist "venv" (
    python -m venv venv
    if errorlevel 1 (
        echo ОШИБКА: Не удалось создать виртуальное окружение
        pause
        exit /b 1
    )
    echo OK - venv создан
) else (
    echo OK - venv уже существует
)

REM Активация окружения
echo.
echo [3/4] Активация окружения...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ОШИБКА: Не удалось активировать окружение
    pause
    exit /b 1
)
echo OK

REM Установка зависимостей
echo.
echo [4/4] Установка зависимостей (это займёт 2-5 минут)...
python -m pip install --upgrade pip >nul 2>&1
pip install pandas numpy scikit-learn xgboost lightgbm scipy joblib pyyaml pytest
if errorlevel 1 (
    echo ОШИБКА: Не удалось установить зависимости
    pause
    exit /b 1
)
echo OK - зависимости установлены

echo.
echo ============================================================
echo   Установка завершена!
echo ============================================================
echo.
echo Теперь вы можете запускать:
echo   run.bat train              - обучение модели
echo   run.bat predict market-001 - предсказание
echo   run.bat drift-check        - проверка дрейфа
echo.
pause
