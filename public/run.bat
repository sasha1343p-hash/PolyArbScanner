@echo off
chcp 65001 >nul
echo ============================================
echo   PolyArb Scanner — Запуск...
echo ============================================
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден! Установите Python 3.10+
    pause
    exit /b 1
)

REM Устанавливаем зависимости если нужно
if not exist ".deps_installed" (
    echo [INFO] Установка зависимостей...
    pip install -r requirements.txt
    echo. > .deps_installed
)

REM Запуск сканера
echo.
echo [INFO] Запуск сканера в режиме MOCK...
python market_analyzer.py --mock --threshold 0.15

echo.
echo ============================================
echo   Готово! Нажмите любую клавишу для выхода.
echo ============================================
pause >nul
