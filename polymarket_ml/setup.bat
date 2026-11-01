@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   PolyArb ML Oracle - Installation
echo ============================================================
echo.

REM Step 1: Check Python
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python not found!
    echo Download from: https://www.python.org/downloads/
    echo IMPORTANT: Check "Add Python to PATH" during install
    echo.
    pause
    exit /b 1
)
echo OK - Python found

REM Step 2: Create virtual environment
echo.
echo [2/6] Creating virtual environment...
if exist "venv" (
    echo OK - venv already exists
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create venv
        pause
        exit /b 1
    )
    echo OK - venv created
)

REM Step 3: Activate environment
echo.
echo [3/6] Activating environment...
call venv\Scripts\activate.bat
echo OK - activated

REM Step 4: Install dependencies
echo.
echo [4/6] Installing dependencies (2-5 min)...
python -m pip install --upgrade pip >nul 2>&1
pip install xgboost lightgbm scikit-learn pandas numpy scipy joblib pyyaml pytest
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo. > .deps_installed
echo OK - dependencies installed

REM Step 5: Verify installation
echo.
echo [5/6] Verifying installation...
python -c "import xgboost; import lightgbm; import sklearn; import pandas; import numpy; print('OK - all libraries installed')"
if errorlevel 1 (
    echo ERROR: Some libraries missing
    pause
    exit /b 1
)

REM Step 6: Create test database
echo.
echo [6/6] Creating test database...
if exist "..\polymarket_history.db" (
    echo OK - database already exists
) else (
    python create_test_db.py
    if errorlevel 1 (
        echo ERROR: Failed to create database
        pause
        exit /b 1
    )
    echo OK - database created
)

echo.
echo ============================================================
echo   INSTALLATION COMPLETE!
echo ============================================================
echo.
echo Next steps:
echo.
echo   1. Train model:
echo      python ml_oracle.py train
echo.
echo   2. Make prediction:
echo      python ml_oracle.py predict market-001
echo.
echo   3. Start everything:
echo      start_all.bat
echo.
echo ============================================================
echo.

set /p TRAIN="Train model now? (y/n): "
if /i "%TRAIN%"=="y" (
    echo.
    python ml_oracle.py train
)

echo.
pause
