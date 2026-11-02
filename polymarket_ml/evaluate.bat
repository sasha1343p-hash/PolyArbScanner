@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   Оценка качества ML модели
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

REM Проверка наличия matplotlib и seaborn
python -c "import matplotlib; import seaborn" 2>nul
if errorlevel 1 (
    echo [INFO] Установка библиотек для визуализации...
    pip install matplotlib seaborn
)

REM Проверка наличия базы данных
if not exist "..\polymarket_history.db" (
    echo [ОШИБКА] База данных не найдена!
    echo.
    echo Ожидался файл: ..\polymarket_history.db
    pause
    exit /b 1
)

echo Запуск оценки модели...
echo.

REM Запуск скрипта оценки
python evaluate_model.py

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Оценка модели завершилась с ошибкой
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Оценка завершена!
echo ========================================
echo.
echo Результаты:
echo   - Графики: model_evaluation.png
echo   - Метрики: в консоли выше
echo.
pause
