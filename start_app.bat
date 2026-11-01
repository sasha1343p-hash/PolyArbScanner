@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   PolyArb Scanner - Запуск
echo ========================================
echo.

REM Запуск Python ML сервера в фоне
echo [1/2] Запуск ML сервера...
cd polymarket_ml
start "ML Server" cmd /c "venv\Scripts\activate && python -m uvicorn api_server:app --host 0.0.0.0 --port 8000"
cd ..
timeout /t 2 /nobreak >nul

REM Запуск веб-сервера
echo [2/2] Запуск веб-сервера...
start "Web Server" cmd /c "npx serve dist -l 3000"
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   Приложение запущено!
echo ========================================
echo.
echo   Веб-дашборд: http://localhost:3000
echo   ML API:      http://localhost:8000
echo.
echo   Нажмите любую клавишу для остановки...
pause >nul

REM Остановка всех серверов
taskkill /FI "WINDOWTITLE eq ML Server*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Web Server*" /T /F >nul 2>&1

echo.
echo Приложения остановлены.
pause
