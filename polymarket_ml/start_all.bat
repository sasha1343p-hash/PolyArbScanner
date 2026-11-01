@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   PolyArb - Starting All Services
echo ============================================================
echo.

REM Check installation
echo [1/3] Checking installation...

if not exist "venv" (
    echo ERROR: venv not found! Run setup.bat first
    pause
    exit /b 1
)

if not exist ".deps_installed" (
    echo ERROR: Dependencies not installed! Run setup.bat first
    pause
    exit /b 1
)

if not exist "..\polymarket_history.db" (
    echo ERROR: Database not found! Run setup.bat first
    pause
    exit /b 1
)

if not exist "artifacts\ml_oracle_bundle.pkl" (
    echo ERROR: Model not trained! Run: python ml_oracle.py train
    pause
    exit /b 1
)

echo OK - all components found

REM Activate environment
echo.
echo [2/3] Activating environment...
call venv\Scripts\activate.bat
echo OK - activated

REM Check for serve
echo.
echo [3/3] Starting web dashboard...
cd ..

where serve >nul 2>&1
if errorlevel 1 (
    echo Installing serve...
    npm install -g serve
)

echo.
echo ============================================================
echo   EVERYTHING IS RUNNING!
echo ============================================================
echo.
echo   Web Dashboard: http://localhost:3000
echo.
echo   Press Ctrl+C to stop
echo.
echo ============================================================
echo.

serve dist

pause
