@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   PolyArb Scanner - Установка и запуск
echo ========================================
echo.

REM Проверка Node.js
echo [1/4] Проверка Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Node.js не установлен!
    echo.
    echo Скачайте и установите Node.js с сайта:
    echo https://nodejs.org/
    echo.
    echo После установки перезапустите этот скрипт.
    pause
    exit /b 1
)
echo OK - Node.js установлен
echo.

REM Установка зависимостей
echo [2/4] Установка зависимостей...
if not exist "node_modules" (
    echo Установка может занять 1-2 минуты...
    call npm install
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось установить зависимости
        pause
        exit /b 1
    )
    echo OK - Зависимости установлены
) else (
    echo OK - Зависимости уже установлены
)
echo.

REM Сборка проекта
echo [3/4] Сборка проекта...
call npm run build
if errorlevel 1 (
    echo [ОШИБКА] Не удалось собрать проект
    pause
    exit /b 1
)
echo OK - Проект собран
echo.

REM Запуск веб-сервера
echo [4/4] Запуск веб-сервера...
echo.
echo ========================================
echo   Сервер запущен!
echo ========================================
echo.
echo   Откройте в браузере:
echo   http://localhost:3000
echo.
echo   Для остановки нажмите Ctrl+C
echo.
echo ========================================
echo.

npx serve dist

pause
