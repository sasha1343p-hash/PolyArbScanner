@echo off
chcp 65001 >nul
echo Установка зависимостей...
echo.

REM Создание venv если нет
if not exist "venv" (
    echo Создание виртуального окружения...
    python -m venv venv
)

REM Активация
call venv\Scripts\activate.bat

REM Установка
echo Установка pandas, numpy, scikit-learn, xgboost, lightgbm...
pip install pandas numpy scikit-learn xgboost lightgbm scipy joblib pyyaml pytest

echo.
echo Готово! Теперь запустите: run.bat train
pause
