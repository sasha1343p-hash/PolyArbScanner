"""
Ансамбль оракулов: ML + эвристика.

Объединяет предсказания ML-модели и эвристического оракула
с настраиваемыми весами и graceful degradation.
"""

import logging
from typing import Optional, Tuple
from dataclasses import dataclass

import pandas as pd

from .model import MLOracle
from .feature_extractor import FeatureExtractor, MarketMetadata

logger = logging.getLogger(__name__)


@dataclass
class EnsembleConfig:
    """Конфигурация ансамбля."""
    use_ml: bool = True
    use_heuristic: bool = True
    ml_weight: float = 0.7
    heuristic_weight: float = 0.3
    min_confidence: float = 0.6
    
    def __post_init__(self):
        # Нормализуем веса
        total = self.ml_weight + self.heuristic_weight
        if total > 0:
            self.ml_weight /= total
            self.heuristic_weight /= total


class OracleEnsemble:
    """
    Ансамбль оракулов: ML + эвристика.
    
    Объединяет предсказания ML-модели и эвристического оракула.
    Поддерживает graceful degradation: если одна модель недоступна,
    использует другую.
    
    Attributes:
        config: Конфигурация ансамбля
        ml_oracle: ML-модель
        feature_extractor: Извлекатель признаков
        heuristic_fn: Функция эвристического оракула
    """
    
    def __init__(
        self,
        config: Optional[EnsembleConfig] = None,
        ml_oracle: Optional[MLOracle] = None,
        feature_extractor: Optional[FeatureExtractor] = None,
        heuristic_fn: Optional[callable] = None
    ):
        """
        Инициализация ансамбля.
        
        Args:
            config: Конфигурация ансамбля
            ml_oracle: Обученная ML-модель
            feature_extractor: Извлекатель признаков
            heuristic_fn: Функция эвристического оракула
        """
        self.config = config or EnsembleConfig()
        self.ml_oracle = ml_oracle
        self.feature_extractor = feature_extractor
        self.heuristic_fn = heuristic_fn
        
        logger.info(
            f"OracleEnsemble инициализирован: "
            f"ML={self.config.use_ml}, Heuristic={self.config.use_heuristic}, "
            f"ML_weight={self.config.ml_weight:.2f}"
        )
    
    def predict(
        self,
        market_id: str,
        price_df: pd.DataFrame,
        metadata: MarketMetadata
    ) -> Tuple[Optional[float], str]:
        """
        Предсказывает вероятность с использованием ансамбля.
        
        Args:
            market_id: ID рынка
            price_df: DataFrame с ценами
            metadata: Метаданные рынка
            
        Returns:
            Tuple (probability, source), где source: 'ml', 'heuristic', 'ensemble', 'none'
        """
        ml_proba = None
        heuristic_proba = None
        ml_confidence = 0.0
        
        # ML предсказание
        if self.config.use_ml and self.ml_oracle and self.feature_extractor:
            try:
                features = self.feature_extractor.extract_features(
                    market_id, price_df, metadata
                )
                
                ml_proba, ml_confidence = self.ml_oracle.predict_with_confidence(features)
                
                # Проверяем уверенность
                if ml_confidence < self.config.min_confidence:
                    logger.warning(
                        f"ML уверенность слишком низкая ({ml_confidence:.2f}), "
                        f"используем только эвристику"
                    )
                    ml_proba = None
                
            except Exception as e:
                logger.error(f"Ошибка ML предсказания: {e}")
                ml_proba = None
        
        # Эвристическое предсказание
        if self.config.use_heuristic and self.heuristic_fn:
            try:
                heuristic_proba = self.heuristic_fn(market_id, price_df, metadata)
            except Exception as e:
                logger.error(f"Ошибка эвристического предсказания: {e}")
                heuristic_proba = None
        
        # Объединяем предсказания
        if ml_proba is not None and heuristic_proba is not None:
            # Обе модели доступны
            ensemble_proba = (
                self.config.ml_weight * ml_proba +
                self.config.heuristic_weight * heuristic_proba
            )
            source = 'ensemble'
            logger.debug(
                f"Рынок {market_id}: ensemble={ensemble_proba:.3f} "
                f"(ML={ml_proba:.3f}, heuristic={heuristic_proba:.3f})"
            )
            return ensemble_proba, source
        
        elif ml_proba is not None:
            # Только ML
            source = 'ml'
            logger.debug(f"Рынок {market_id}: ml={ml_proba:.3f}")
            return ml_proba, source
        
        elif heuristic_proba is not None:
            # Только эвристика
            source = 'heuristic'
            logger.debug(f"Рынок {market_id}: heuristic={heuristic_proba:.3f}")
            return heuristic_proba, source
        
        else:
            # Ничего не доступно
            source = 'none'
            logger.warning(f"Рынок {market_id}: ни одна модель не доступна")
            return None, source
    
    def predict_batch(
        self,
        metadata_df: pd.DataFrame,
        price_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Предсказывает вероятности для батча рынков.
        
        Args:
            metadata_df: DataFrame с метаданными
            price_df: DataFrame с ценами
            
        Returns:
            DataFrame с колонками [market_id, probability, source]
        """
        results = []
        
        for _, row in metadata_df.iterrows():
            market_id = row['id']
            
            # Создаём MarketMetadata
            metadata = MarketMetadata(
                id=market_id,
                question=row['question'],
                end_date=pd.to_datetime(row['end_date']) if pd.notna(row.get('end_date')) else None,
                resolution=row.get('resolution'),
                created_at=pd.to_datetime(row['created_at']) if pd.notna(row.get('created_at')) else None,
            )
            
            # Фильтруем цены
            market_prices = price_df[price_df['market_id'] == market_id].copy()
            
            # Предсказание
            proba, source = self.predict(market_id, market_prices, metadata)
            
            results.append({
                'market_id': market_id,
                'probability': proba,
                'source': source,
            })
        
        return pd.DataFrame(results)


def default_heuristic(
    market_id: str,
    price_df: pd.DataFrame,
    metadata: MarketMetadata
) -> float:
    """
    Эвристический оракул (baseline).
    
    Простая эвристика на основе текущей цены и времени до экспирации.
    
    Args:
        market_id: ID рынка
        price_df: DataFrame с ценами
        metadata: Метаданные рынка
        
    Returns:
        Вероятность YES от 0 до 1
    """
    if price_df.empty:
        return 0.5
    
    current_price = price_df['yes_price'].iloc[-1]
    
    # Простая эвристика: используем текущую цену как вероятность
    # (это наивный baseline, в реальности нужна более сложная логика)
    return float(current_price)
