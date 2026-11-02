@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   A/B Тест: Эвристика vs ML
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

REM Проверка наличия модели
if not exist "artifacts\ml_oracle_bundle.pkl" (
    echo [ОШИБКА] Модель не найдена!
    echo.
    echo Сначала обучите модель:
    echo   python ml_oracle.py train
    pause
    exit /b 1
)

REM Проверка наличия базы данных
if not exist "polymarket_history.db" (
    echo [ОШИБКА] База данных не найдена!
    echo.
    echo Создайте тестовую БД:
    echo   python create_test_db.py
    pause
    exit /b 1
)

echo Запуск A/B теста...
echo.

REM Запуск скрипта A/B теста
python ab_test.py

if errorlevel 1 (
    echo.
    echo [ОШИБКА] A/B тест завершился с ошибкой
    pause
    exit /b 1
)

echo.
echo ========================================
echo   A/B тест завершён!
echo ========================================
echo.
echo Результаты сохранены в:
echo   - ab_test_heuristic.csv
echo   - ab_test_ml.csv
echo.

pause
