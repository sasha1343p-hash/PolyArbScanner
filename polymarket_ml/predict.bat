@echo off
chcp 65001 >nul

if "%~1"=="" (
    echo Использование: predict.bat ^<market_id^>
    echo Пример: predict.bat market-123-abc
    pause
    exit /b 1
)

echo ============================================
echo   ML Oracle — Предсказание для %1
echo ============================================
echo.

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python ml_oracle.py predict %1

echo.
pause
