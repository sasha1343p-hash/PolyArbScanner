@echo off
echo.
echo ============================================================
echo   PolyArb ML Oracle - Quick Setup
echo ============================================================
echo.

echo Step 1: Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create venv
    pause
    exit /b 1
)
echo OK

echo.
echo Step 2: Activating environment...
call venv\Scripts\activate.bat
echo OK

echo.
echo Step 3: Installing dependencies (this takes 2-5 minutes)...
python -m pip install --upgrade pip --quiet
pip install pandas numpy scikit-learn xgboost lightgbm scipy joblib pyyaml pytest --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo. > .deps_installed
echo OK

echo.
echo Step 4: Creating test database...
python create_test_db.py
if errorlevel 1 (
    echo ERROR: Failed to create database
    pause
    exit /b 1
)
echo OK

echo.
echo Step 5: Training model (this takes 3-5 minutes)...
python ml_oracle.py train
if errorlevel 1 (
    echo ERROR: Failed to train model
    pause
    exit /b 1
)
echo OK

echo.
echo ============================================================
echo   SETUP COMPLETE!
echo ============================================================
echo.
echo You can now run:
echo   python ml_oracle.py predict market-001
echo.
echo Or start everything:
echo   start_all.bat
echo.
pause
