@echo off
chcp 65001 >nul
echo.
echo ============================================================
echo   Price Prediction Pipeline - Запуск
echo ============================================================
echo.

REM Проверка виртуального окружения
if not exist "..\venv\Scripts\activate.bat" (
    echo [ОШИБКА] Виртуальное окружение не найдено!
    echo.
    echo Сначала создайте venv в папке polymarket_ml:
    echo   cd ..\polymarket_ml
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

REM Активация окружения
call ..\venv\Scripts\activate.bat

REM Проверка наличия БД
if not exist "..\polymarket_history.db" (
    echo [ОШИБКА] База данных не найдена!
    echo.
    echo Создайте тестовую БД:
    echo   cd ..\polymarket_ml
    echo   python create_test_db.py
    pause
    exit /b 1
)

echo Запуск пайплайна...
echo.

REM Запуск пайплайна
python run_pipeline.py

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Пайплайн завершился с ошибкой
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Пайплайн завершен успешно!
echo ============================================================
echo.
pause
