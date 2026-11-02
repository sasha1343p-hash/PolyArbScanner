@echo off
chcp 65001 >nul
echo ============================================
echo   ML Oracle — Обучение модели
echo ============================================
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден! Установите Python 3.10+
    pause
    exit /b 1
)

REM Активируем виртуальное окружение если есть
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Активация виртуального окружения...
    call venv\Scripts\activate.bat
)

REM Устанавливаем зависимости если нужно
if not exist ".deps_installed" (
    echo [INFO] Установка зависимостей...
    pip install -r requirements.txt
    echo. > .deps_installed
)

REM Создаём директории
if not exist "artifacts" mkdir artifacts
if not exist "logs" mkdir logs

REM Запуск обучения
echo.
echo [INFO] Запуск обучения модели...
python ml_oracle.py train

echo.
echo ============================================
echo   Готово! Нажмите любую клавишу для выхода.
echo ============================================
pause >nul
