@echo off
call venv\Scripts\activate.bat

REM Если передан Python-файл, запускаем его напрямую
if "%~1"=="" goto :show_help
if "%~x1"==".py" (
    python %*
    goto :eof
)

REM Иначе передаём в ml_oracle.py
python ml_oracle.py %*
goto :eof

:show_help
echo.
echo PolyArb ML Oracle
echo.
echo Использование:
echo   run.bat train                    - Обучение модели
echo   run.bat evaluate                 - Оценка модели
echo   run.bat predict ^<market_id^>      - Предсказание для рынка
echo   run.bat drift-check              - Проверка дрейфа
echo   run.bat feature-importance       - Важность признаков
echo.
echo   run.bat ^<script.py^>              - Запуск произвольного скрипта
echo.
echo Примеры:
echo   run.bat evaluate_model.py        - Оценка качества модели
echo   run.bat predict market-001       - Предсказание для рынка
echo.
