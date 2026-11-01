@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                                                           ║
echo ║   🚀 PolyArb ML Oracle — Автоматическая установка        ║
echo ║                                                           ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM ============================================
REM ШАГ 1: Проверка Python
REM ============================================
echo [1/7] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ ОШИБКА: Python не найден!
    echo.
    echo Скачайте и установите Python 3.10+ с:
    echo https://www.python.org/downloads/
    echo.
    echo ВАЖНО: При установке отметьте "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo ✅ Python %PYTHON_VERSION% найден

REM ============================================
REM ШАГ 2: Создание виртуального окружения
REM ============================================
echo.
echo [2/7] Создание виртуального окружения...

if exist "venv" (
    echo ✅ Виртуальное окружение уже существует
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ❌ ОШИБКА: Не удалось создать виртуальное окружение
        pause
        exit /b 1
    )
    echo ✅ Виртуальное окружение создано
)

REM ============================================
REM ШАГ 3: Активация окружения
REM ============================================
echo.
echo [3/7] Активация окружения...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ ОШИБКА: Не удалось активировать окружение
    echo Попробуйте: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    pause
    exit /b 1
)
echo ✅ Окружение активировано

REM ============================================
REM ШАГ 4: Установка зависимостей
REM ============================================
echo.
echo [4/7] Установка зависимостей...

if exist ".deps_installed" (
    echo ✅ Зависимости уже установлены
) else (
    echo Установка может занять 2-5 минут...
    echo.
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ ОШИБКА: Не удалось установить зависимости
        pause
        exit /b 1
    )
    echo. > .deps_installed
    echo ✅ Зависимости установлены
)

REM ============================================
REM ШАГ 5: Проверка установки
REM ============================================
echo.
echo [5/7] Проверка установки...
python -c "import xgboost; import lightgbm; import sklearn; import pandas; import numpy" 2>nul
if errorlevel 1 (
    echo ❌ ОШИБКА: Не все библиотеки установлены корректно
    echo Попробуйте удалить папку venv и запустить установку заново
    pause
    exit /b 1
)
echo ✅ Все библиотеки установлены

REM ============================================
REM ШАГ 6: Создание тестовой БД
REM ============================================
echo.
echo [6/7] Проверка базы данных...

if exist "..\polymarket_history.db" (
    echo ✅ База данных найдена
) else (
    echo ⚠️  База данных не найдена, создаю тестовую...
    python create_test_db.py
    if errorlevel 1 (
        echo ❌ ОШИБКА: Не удалось создать тестовую БД
        pause
        exit /b 1
    )
    echo ✅ Тестовая база данных создана
)

REM ============================================
REM ШАГ 7: Обучение модели
REM ============================================
echo.
echo [7/7] Обучение модели...

if exist "artifacts\ml_oracle_bundle.pkl" (
    echo ✅ Модель уже обучена
    echo.
    set /p RETRAIN="Хотите переобучить модель? (y/n): "
    if /i not "!RETRAIN!"=="y" goto :SKIP_TRAIN
)

echo Обучение может занять 3-5 минут...
echo.
python ml_oracle.py train
if errorlevel 1 (
    echo ❌ ОШИБКА: Не удалось обучить модель
    pause
    exit /b 1
)
echo ✅ Модель обучена

:SKIP_TRAIN

REM ============================================
REM ГОТОВО!
REM ============================================
echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                                                           ║
echo ║   ✅ УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!                        ║
echo ║                                                           ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo 📊 Доступные команды:
echo.
echo   1. Предсказание для рынка:
echo      python ml_oracle.py predict market-001
echo.
echo   2. Проверка дрейфа:
echo      python ml_oracle.py drift-check
echo.
echo   3. Важность признаков:
echo      python ml_oracle.py feature-importance
echo.
echo   4. Запуск веб-дашборда:
echo      cd .. ^&^& serve dist
echo.
echo   5. Быстрый запуск всего:
echo      start_all.bat
echo.
echo ═══════════════════════════════════════════════════════════
echo.

REM Предложение сделать тестовое предсказание
set /p TEST="Хотите сделать тестовое предсказание? (y/n): "
if /i "%TEST%"=="y" (
    echo.
    echo Запускаю предсказание для market-001...
    echo.
    python ml_oracle.py predict market-001
    echo.
)

pause
