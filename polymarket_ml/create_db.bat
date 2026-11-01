@echo off
chcp 65001 >nul
echo.
echo ============================================================
echo   Создание тестовой базы данных
echo ============================================================
echo.

REM Проверка venv
if not exist "venv" (
    echo ОШИБКА: Виртуальное окружение не найдено!
    echo Сначала запустите: install_deps.bat
    pause
    exit /b 1
)

REM Активация
call venv\Scripts\activate.bat

REM Создание БД
echo Создание тестовой базы данных...
python create_test_db.py

if errorlevel 1 (
    echo.
    echo ОШИБКА: Не удалось создать базу данных
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   База данных создана! polymarket_history.db
echo ============================================================
echo.
echo Теперь запустите обучение:
echo   run.bat train
echo.
pause
