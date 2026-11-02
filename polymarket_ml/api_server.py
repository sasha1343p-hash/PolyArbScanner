"""
ML API Server для PolyArb Scanner

Запуск:
    python api_server.py

API endpoints:
    GET /api/health - проверка работоспособности
    GET /api/predict/{market_id} - предсказание для рынка
    GET /api/markets - список всех рынков
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import sys
import os
import sqlite3
import pandas as pd

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_oracle import MLOracle, FeatureExtractor
from ml_oracle.feature_extractor import MarketMetadata

# Инициализация FastAPI
app = FastAPI(
    title="PolyArb ML API",
    description="API для предсказания вероятностей на предиктивных рынках",
    version="1.0.0"
)

# CORS для веб-дашборда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальные переменные
model: Optional[MLOracle] = None
extractor: Optional[FeatureExtractor] = None
db_path: str = "../polymarket_history.db"


class PredictionResponse(BaseModel):
    market_id: str
    probability: float
    confidence: float
    recommendation: str
    market_price: Optional[float] = None


class MarketInfo(BaseModel):
    id: str
    question: str
    category: str
    volume: float
    end_date: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Загрузка модели при старте"""
    global model, extractor
    
    print("Загрузка ML модели...")
    model = MLOracle()
    model_path = "artifacts/ml_oracle_bundle.pkl"
    
    if not model.load(model_path):
        print(f"⚠️  Модель не найдена: {model_path}")
        print("Запустите обучение: python ml_oracle.py train")
    else:
        print("✅ Модель загружена")
    
    extractor = FeatureExtractor()
    print("✅ API сервер готов к работе")


@app.get("/api/health")
async def health_check():
    """Проверка работоспособности"""
    return {
        "status": "ok",
        "model_loaded": model is not None and model.is_trained,
        "database_exists": os.path.exists(db_path)
    }


@app.get("/api/predict/{market_id}", response_model=PredictionResponse)
async def predict(market_id: str):
    """
    Предсказание вероятности для рынка
    
    Args:
        market_id: ID рынка из базы данных
    
    Returns:
        PredictionResponse с вероятностью и рекомендацией
    """
    if model is None or not model.is_trained:
        raise HTTPException(status_code=503, detail="Модель не загружена")
    
    # Загрузка данных из БД
    try:
        conn = sqlite3.connect(db_path)
        
        # Метаданные рынка
        metadata_query = f"""
            SELECT id, question, end_date, resolution, created_at
            FROM market_metadata
            WHERE id = '{market_id}'
        """
        metadata_df = pd.read_sql_query(metadata_query, conn)
        
        if metadata_df.empty:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Рынок {market_id} не найден")
        
        # История цен
        prices_query = f"""
            SELECT market_id, timestamp, yes_price, no_price, volume, liquidity
            FROM price_history
            WHERE market_id = '{market_id}'
            ORDER BY timestamp
        """
        prices_df = pd.read_sql_query(prices_query, conn)
        conn.close()
        
        if prices_df.empty:
            raise HTTPException(status_code=404, detail=f"История цен для {market_id} не найдена")
        
        # Извлечение признаков
        metadata_row = metadata_df.iloc[0]
        metadata = MarketMetadata(
            id=metadata_row['id'],
            question=metadata_row['question'],
            end_date=pd.to_datetime(metadata_row['end_date']) if pd.notna(metadata_row['end_date']) else None,
            resolution=metadata_row['resolution'] if pd.notna(metadata_row['resolution']) else None,
            created_at=pd.to_datetime(metadata_row['created_at']) if pd.notna(metadata_row['created_at']) else None
        )
        
        features = extractor.extract_features(market_id, prices_df, metadata)
        
        # Предсказание
        probability, confidence = model.predict_with_confidence(features)
        
        # Рекомендация
        market_price = prices_df['yes_price'].iloc[-1]
        edge = probability - market_price
        
        if edge > 0.05:
            recommendation = "BUY YES"
        elif edge < -0.05:
            recommendation = "BUY NO"
        else:
            recommendation = "HOLD"
        
        return PredictionResponse(
            market_id=market_id,
            probability=probability,
            confidence=confidence,
            recommendation=recommendation,
            market_price=market_price
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка предсказания: {str(e)}")


@app.get("/api/markets", response_model=List[MarketInfo])
async def get_markets(limit: int = 100):
    """
    Список всех рынков
    
    Args:
        limit: максимальное количество рынков (по умолчанию 100)
    
    Returns:
        Список MarketInfo
    """
    try:
        conn = sqlite3.connect(db_path)
        query = """
            SELECT id, question, end_date, volume
            FROM market_metadata
            ORDER BY volume DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        
        markets = []
        for _, row in df.iterrows():
            # Определяем категорию по вопросу
            question = row['question'].lower()
            if any(word in question for word in ['bitcoin', 'btc', 'ethereum', 'eth', 'crypto']):
                category = 'crypto'
            elif any(word in question for word in ['election', 'president', 'congress', 'trump', 'biden']):
                category = 'politics'
            elif any(word in question for word in ['nba', 'nfl', 'mlb', 'nhl', 'ufc', 'tennis']):
                category = 'sports'
            else:
                category = 'culture'
            
            markets.append(MarketInfo(
                id=row['id'],
                question=row['question'],
                category=category,
                volume=row['volume'],
                end_date=row['end_date'] if pd.notna(row['end_date']) else None
            ))
        
        return markets
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки рынков: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("PolyArb ML API Server")
    print("=" * 50)
    print("Запуск на http://localhost:8000")
    print("Документация: http://localhost:8000/docs")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
