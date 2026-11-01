@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                                                           ║
echo ║   🚀 PolyArb — Быстрый запуск всего                      ║
echo ║                                                           ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM ============================================
REM Проверка установки
REM ============================================
echo [1/4] Проверка установки...

if not exist "venv" (
    echo ❌ Виртуальное окружение не найдено!
    echo Сначала запустите: setup.bat
    pause
    exit /b 1
)

if not exist ".deps_installed" (
    echo ❌ Зависимости не установлены!
    echo Сначала запустите: setup.bat
    pause
    exit /b 1
)

if not exist "..\polymarket_history.db" (
    echo ❌ База данных не найдена!
    echo Сначала запустите: setup.bat
    pause
    exit /b 1
)

if not exist "artifacts\ml_oracle_bundle.pkl" (
    echo ❌ Модель не обучена!
    echo Сначала запустите: setup.bat
    pause
    exit /b 1
)

echo ✅ Все компоненты найдены

REM ============================================
REM Активация окружения
REM ============================================
echo.
echo [2/4] Активация окружения...
call venv\Scripts\activate.bat
echo ✅ Окружение активировано

REM ============================================
REM Запуск ML API сервера
REM ============================================
echo.
echo [3/4] Запуск ML API сервера...

REM Проверяем наличие api_server.py
if not exist "api_server.py" (
    echo ⚠️  api_server.py не найден, создаю...
    
    REM Создаём простой API сервер
    (
        echo from fastapi import FastAPI
        echo from fastapi.middleware.cors import CORSMiddleware
        echo import pandas as pd
        echo import sqlite3
        echo import sys
        echo import os
        echo.
        echo # Добавляем текущую директорию в PATH
        echo sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        echo.
        echo from ml_oracle import MLOracle, FeatureExtractor
        echo from ml_oracle.feature_extractor import MarketMetadata
        echo.
        echo app = FastAPI()
        echo app.add_middleware(
        echo     CORSMiddleware,
        echo     allow_origins=["*"],
        echo     allow_methods=["*"],
        echo     allow_headers=["*"],
        echo )
        echo.
        echo # Загружаем модель
        echo model = MLOracle()
        echo model.load('artifacts/ml_oracle_bundle.pkl')
        echo extractor = FeatureExtractor()
        echo.
        echo @app.get("/api/predict/{market_id}")
        echo def predict(market_id: str):
        echo     conn = sqlite3.connect('../polymarket_history.db')
        echo     metadata_df = pd.read_sql_query(f"SELECT * FROM market_metadata WHERE id = '{market_id}'", conn)
        echo     price_df = pd.read_sql_query(f"SELECT * FROM price_history WHERE market_id = '{market_id}'", conn)
        echo     conn.close()
        echo.
        echo     if metadata_df.empty:
        echo         return {"error": "Market not found"}
        echo.
        echo     row = metadata_df.iloc[0]
        echo     metadata = MarketMetadata(
        echo         id=market_id,
        echo         question=row['question'],
        echo         end_date=pd.to_datetime(row['end_date']) if pd.notna(row.get('end_date')) else None,
        echo     )
        echo.
        echo     features = extractor.extract_features(market_id, price_df, metadata)
        echo     proba, confidence = model.predict_with_confidence(features)
        echo.
        echo     return {
        echo         "market_id": market_id,
        echo         "probability": proba,
        echo         "confidence": confidence,
        echo         "recommendation": "BUY YES" if proba > 0.5 else "BUY NO",
        echo     }
        echo.
        echo if __name__ == "__main__":
        echo     import uvicorn
        echo     uvicorn.run(app, host="0.0.0.0", port=8000)
    ) > api_server.py
    
    echo ✅ api_server.py создан
)

REM Устанавливаем FastAPI если нужно
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo Установка FastAPI...
    pip install fastapi uvicorn
)

REM Запускаем API сервер в фоне
echo Запуск ML API на http://localhost:8000
start "ML API Server" /min cmd /c "python api_server.py"
timeout /t 2 /nobreak >nul
echo ✅ ML API запущен

REM ============================================
REM Запуск веб-дашборда
REM ============================================
echo.
echo [4/4] Запуск веб-дашборда...

cd ..

REM Проверяем наличие serve
npm list -g serve >nul 2>&1
if errorlevel 1 (
    echo Установка serve...
    npm install -g serve
)

echo Запуск дашборда на http://localhost:3000
echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                                                           ║
echo ║   ✅ ВСЁ ЗАПУЩЕНО!                                        ║
echo ║                                                           ║
echo ║   📊 Веб-дашборд: http://localhost:3000                  ║
echo ║   🔮 ML API:        http://localhost:8000                ║
echo ║                                                           ║
echo ║   Нажмите Ctrl+C в этом окне для остановки               ║
echo ║                                                           ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

serve dist

pause
