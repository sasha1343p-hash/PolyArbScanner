@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   PolyArb Scanner - Запуск
echo ========================================
echo.

REM Проверка наличия папки dist
if not exist "dist\index.html" (
    echo [!] Папка dist не найдена. Сборка проекта...
    call npm run build
    if errorlevel 1 (
        echo [!] Ошибка сборки. Проверьте, что Node.js установлен.
        pause
        exit /b 1
    )
)

echo [1/2] Запуск веб-дашборда...
start "PolyArb Web" cmd /c "npx serve dist -l 3000"
timeout /t 3 /nobreak >nul

echo [2/2] Запуск ML API сервера...
cd polymarket_ml
if exist "venv\Scripts\activate.bat" (
    start "PolyArb ML API" cmd /c "venv\Scripts\activate && python api_server.py"
) else (
    echo [!] Виртуальное окружение не найдено. Пропуск ML API.
    echo [!] Для запуска ML API выполните:
    echo      cd polymarket_ml
    echo      python -m venv venv
    echo      venv\Scripts\activate
    echo      pip install -r requirements.txt
    echo      pip install fastapi uvicorn
    echo      python api_server.py
)
cd ..

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   Приложение запущено!
echo ========================================
echo.
echo   Веб-дашборд: http://localhost:3000
if exist "polymarket_ml\venv\Scripts\activate.bat" (
    echo   ML API:      http://localhost:8000
    echo   API Docs:    http://localhost:8000/docs
)
echo.
echo   Нажмите любую клавишу для остановки...
pause >nul

REM Остановка всех серверов
taskkill /FI "WINDOWTITLE eq PolyArb Web*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq PolyArb ML API*" /T /F >nul 2>&1

echo.
echo Приложения остановлены.
pause
