"""
Пример интеграции ML Oracle с market_analyzer.py

Этот файл показывает, как использовать ML Oracle в сканере.
"""

import logging
import sqlite3
from typing import Optional, Tuple

import pandas as pd

from ml_oracle import MLOracle, FeatureExtractor, OracleEnsemble
from ml_oracle.feature_extractor import MarketMetadata
from ml_oracle.ensemble import default_heuristic

logger = logging.getLogger(__name__)


class MLIntegratedScanner:
    """
    Сканер с интегрированным ML Oracle.
    
    Объединяет эвристический оракул и ML-модель для более точных предсказаний.
    """
    
    def __init__(
        self,
        db_path: str = "polymarket_history.db",
        model_path: str = "artifacts/ml_oracle_bundle.pkl",
        use_ml: bool = True,
        use_heuristic: bool = True,
        ml_weight: float = 0.7,
    ):
        """
        Инициализация сканера с ML.
        
        Args:
            db_path: Путь к базе данных
            model_path: Путь к обученной модели
            use_ml: Использовать ML-модель
            use_heuristic: Использовать эвристику
            ml_weight: Вес ML в ансамбле (0-1)
        """
        self.db_path = db_path
        self.use_ml = use_ml
        self.use_heuristic = use_heuristic
        
        # Загружаем ML модель если нужно
        self.ml_oracle: Optional[MLOracle] = None
        self.feature_extractor: Optional[FeatureExtractor] = None
        
        if use_ml:
            self.ml_oracle = MLOracle()
            if not self.ml_oracle.load(model_path):
                logger.warning("Не удалось загрузить ML модель, используем только эвристику")
                self.use_ml = False
            else:
                self.feature_extractor = FeatureExtractor()
                logger.info("ML модель загружена успешно")
        
        # Создаём ансамбль
        from ml_oracle.ensemble import EnsembleConfig
        config = EnsembleConfig(
            use_ml=self.use_ml,
            use_heuristic=self.use_heuristic,
            ml_weight=ml_weight,
            heuristic_weight=1 - ml_weight,
        )
        
        self.ensemble = OracleEnsemble(
            config=config,
            ml_oracle=self.ml_oracle,
            feature_extractor=self.feature_extractor,
            heuristic_fn=default_heuristic,
        )
        
        logger.info(
            f"Сканер инициализирован: ML={self.use_ml}, "
            f"Heuristic={self.use_heuristic}, ML_weight={ml_weight:.2f}"
        )
    
    def get_market_data(self, market_id: str) -> Tuple[pd.DataFrame, MarketMetadata]:
        """
        Загружает данные рынка из БД.
        
        Args:
            market_id: ID рынка
            
        Returns:
            Tuple (price_df, metadata)
        """
        conn = sqlite3.connect(self.db_path)
        
        # Загружаем метаданные
        metadata_df = pd.read_sql_query(
            f"SELECT * FROM market_metadata WHERE id = '{market_id}'",
            conn
        )
        
        if metadata_df.empty:
            conn.close()
            raise ValueError(f"Рынок не найден: {market_id}")
        
        # Загружаем цены
        price_df = pd.read_sql_query(
            f"SELECT * FROM price_history WHERE market_id = '{market_id}'",
            conn
        )
        
        conn.close()
        
        # Создаём MarketMetadata
        row = metadata_df.iloc[0]
        metadata = MarketMetadata(
            id=market_id,
            question=row['question'],
            end_date=pd.to_datetime(row['end_date']) if pd.notna(row.get('end_date')) else None,
            resolution=row.get('resolution'),
            created_at=pd.to_datetime(row['created_at']) if pd.notna(row.get('created_at')) else None,
        )
        
        return price_df, metadata
    
    def predict_probability(self, market_id: str) -> Tuple[Optional[float], str]:
        """
        Предсказывает вероятность YES для рынка.
        
        Args:
            market_id: ID рынка
            
        Returns:
            Tuple (probability, source), где source: 'ml', 'heuristic', 'ensemble', 'none'
        """
        try:
            # Загружаем данные
            price_df, metadata = self.get_market_data(market_id)
            
            # Предсказание через ансамбль
            probability, source = self.ensemble.predict(market_id, price_df, metadata)
            
            logger.info(
                f"Рынок {market_id}: вероятность={probability}, "
                f"источник={source}"
            )
            
            return probability, source
        
        except Exception as e:
            logger.error(f"Ошибка предсказания для рынка {market_id}: {e}")
            return None, 'none'
    
    def analyze_market(self, market_id: str) -> dict:
        """
        Полный анализ рынка с рекомендацией.
        
        Args:
            market_id: ID рынка
            
        Returns:
            Словарь с результатами анализа
        """
        probability, source = self.predict_probability(market_id)
        
        if probability is None:
            return {
                'market_id': market_id,
                'error': 'Не удалось получить предсказание',
                'recommendation': None,
            }
        
        # Определяем рекомендацию
        if probability > 0.6:
            recommendation = 'BUY YES'
        elif probability < 0.4:
            recommendation = 'BUY NO'
        else:
            recommendation = 'HOLD'
        
        # Загружаем метаданные для дополнительной информации
        price_df, metadata = self.get_market_data(market_id)
        
        return {
            'market_id': market_id,
            'question': metadata.question,
            'probability': probability,
            'source': source,
            'recommendation': recommendation,
            'current_price': price_df['yes_price'].iloc[-1] if not price_df.empty else None,
        }


# ============================================
# Пример использования
# ============================================

def main():
    """Пример использования MLIntegratedScanner."""
    
    # Инициализация
    scanner = MLIntegratedScanner(
        db_path="polymarket_history.db",
        model_path="artifacts/ml_oracle_bundle.pkl",
        use_ml=True,
        use_heuristic=True,
        ml_weight=0.7,
    )
    
    # Пример: анализ конкретного рынка
    market_id = "market-123-abc"  # Замените на реальный ID
    
    result = scanner.analyze_market(market_id)
    
    print("=" * 60)
    print(f"РЫНОК: {result['question']}")
    print("=" * 60)
    print(f"Вероятность YES: {result['probability']:.2%}")
    print(f"Источник:        {result['source']}")
    print(f"Рекомендация:    {result['recommendation']}")
    if result['current_price']:
        print(f"Текущая цена:    {result['current_price']:.2%}")
    print("=" * 60)


if __name__ == '__main__':
    main()
