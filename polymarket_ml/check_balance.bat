@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   Проверка баланса классов
echo ========================================
echo.

REM Проверка виртуального окружения
if not exist "venv\Scripts\activate.bat" (
    echo [ОШИБКА] Виртуальное окружение не найдено!
    echo.
    echo Сначала запустите: setup.bat
    pause
    exit /b 1
)

REM Активация окружения
call venv\Scripts\activate.bat

REM Проверка наличия базы данных
if not exist "polymarket_history.db" (
    echo [ОШИБКА] База данных не найдена!
    echo.
    echo Создайте тестовую БД:
    echo   python create_test_db.py
    pause
    exit /b 1
)

echo Запуск проверки баланса классов...
echo.

REM Запуск скрипта
python check_class_balance.py

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Проверка завершилась с ошибкой
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Проверка завершена!
echo ========================================
echo.

pause
