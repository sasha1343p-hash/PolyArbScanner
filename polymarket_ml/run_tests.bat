@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   PolyArb ML Oracle - Test Runner
echo ============================================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Activate environment
call venv\Scripts\activate.bat

echo [1/3] Running unit tests...
pytest ../tests/test_feature_extractor.py ../tests/test_model.py -v --tb=short
if errorlevel 1 (
    echo.
    echo WARNING: Some unit tests failed
    set UNIT_TESTS_FAILED=1
) else (
    echo OK - Unit tests passed
)

echo.
echo [2/3] Running integration tests...
pytest ../tests/test_integration.py -v --tb=short
if errorlevel 1 (
    echo.
    echo WARNING: Some integration tests failed
    set INTEGRATION_TESTS_FAILED=1
) else (
    echo OK - Integration tests passed
)

echo.
echo [3/3] Generating coverage report...
pytest ../tests/ --cov=ml_oracle --cov-report=html --cov-report=term-missing
if errorlevel 1 (
    echo WARNING: Coverage report generation failed
) else (
    echo OK - Coverage report generated in htmlcov/
)

echo.
echo ============================================================
echo   TEST SUMMARY
echo ============================================================
echo.

if defined UNIT_TESTS_FAILED (
    echo [FAIL] Unit tests: FAILED
) else (
    echo [PASS] Unit tests: PASSED
)

if defined INTEGRATION_TESTS_FAILED (
    echo [FAIL] Integration tests: FAILED
) else (
    echo [PASS] Integration tests: PASSED
)

echo.
echo Coverage report: htmlcov/index.html
echo.

if defined UNIT_TESTS_FAILED goto :errors
if defined INTEGRATION_TESTS_FAILED goto :errors

echo ============================================================
echo   ALL TESTS PASSED!
echo ============================================================
pause
exit /b 0

:errors
echo ============================================================
echo   SOME TESTS FAILED - Check output above
echo ============================================================
pause
exit /b 1
