#!/bin/bash

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║   🚀 PolyArb — Быстрый запуск всего                      ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# ============================================
# Проверка установки
# ============================================
echo "[1/4] Проверка установки..."

if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено!"
    echo "Сначала запустите: python3 setup_crossplatform.py"
    exit 1
fi

if [ ! -f ".deps_installed" ]; then
    echo "❌ Зависимости не установлены!"
    echo "Сначала запустите: python3 setup_crossplatform.py"
    exit 1
fi

if [ ! -f "../polymarket_history.db" ]; then
    echo "❌ База данных не найдена!"
    echo "Сначала запустите: python3 setup_crossplatform.py"
    exit 1
fi

if [ ! -f "artifacts/ml_oracle_bundle.pkl" ]; then
    echo "❌ Модель не обучена!"
    echo "Сначала запустите: python3 setup_crossplatform.py"
    exit 1
fi

echo "✅ Все компоненты найдены"

# ============================================
# Активация окружения
# ============================================
echo ""
echo "[2/4] Активация окружения..."
source venv/bin/activate
echo "✅ Окружение активировано"

# ============================================
# Запуск ML API сервера
# ============================================
echo ""
echo "[3/4] Запуск ML API сервера..."

# Проверяем наличие api_server.py
if [ ! -f "api_server.py" ]; then
    echo "⚠️  api_server.py не найден, создаю..."
    
    cat > api_server.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_oracle import MLOracle, FeatureExtractor
from ml_oracle.feature_extractor import MarketMetadata

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = MLOracle()
model.load('artifacts/ml_oracle_bundle.pkl')
extractor = FeatureExtractor()

@app.get("/api/predict/{market_id}")
def predict(market_id: str):
    conn = sqlite3.connect('../polymarket_history.db')
    metadata_df = pd.read_sql_query(f"SELECT * FROM market_metadata WHERE id = '{market_id}'", conn)
    price_df = pd.read_sql_query(f"SELECT * FROM price_history WHERE market_id = '{market_id}'", conn)
    conn.close()
    
    if metadata_df.empty:
        return {"error": "Market not found"}
    
    row = metadata_df.iloc[0]
    metadata = MarketMetadata(
        id=market_id,
        question=row['question'],
        end_date=pd.to_datetime(row['end_date']) if pd.notna(row.get('end_date')) else None,
    )
    
    features = extractor.extract_features(market_id, price_df, metadata)
    proba, confidence = model.predict_with_confidence(features)
    
    return {
        "market_id": market_id,
        "probability": proba,
        "confidence": confidence,
        "recommendation": "BUY YES" if proba > 0.5 else "BUY NO",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
    
    echo "✅ api_server.py создан"
fi

# Устанавливаем FastAPI если нужно
python -c "import fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Установка FastAPI..."
    pip install fastapi uvicorn
fi

# Запускаем API сервер в фоне
echo "Запуск ML API на http://localhost:8000"
python api_server.py &
API_PID=$!
sleep 2
echo "✅ ML API запущен (PID: $API_PID)"

# ============================================
# Запуск веб-дашборда
# ============================================
echo ""
echo "[4/4] Запуск веб-дашборда..."

cd ..

# Проверяем наличие npx
if ! command -v npx &> /dev/null; then
    echo "❌ Node.js не найден!"
    echo "Установите Node.js с https://nodejs.org"
    kill $API_PID 2>/dev/null
    exit 1
fi

echo "Запуск дашборда на http://localhost:3000"
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║   ✅ ВСЁ ЗАПУЩЕНО!                                        ║"
echo "║                                                           ║"
echo "║   📊 Веб-дашборд: http://localhost:3000                  ║"
echo "║   🔮 ML API:        http://localhost:8000                ║"
echo "║                                                           ║"
echo "║   Нажмите Ctrl+C для остановки                           ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Функция очистки при выходе
cleanup() {
    echo ""
    echo "Остановка сервисов..."
    kill $API_PID 2>/dev/null
    echo "✅ Остановлено"
    exit 0
}

trap cleanup SIGINT SIGTERM

npx serve dist
