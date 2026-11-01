"""
Модуль извлечения признаков из временных рядов цен.

Отвечает за создание feature vector для каждого рынка на основе
исторических данных о ценах, объёмах и метаданных рынка.
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MarketMetadata:
    """Метаданные рынка."""
    id: str
    question: str
    end_date: Optional[datetime] = None
    resolution: Optional[str] = None  # "YES", "NO", или None
    created_at: Optional[datetime] = None
    category: Optional[str] = None  # crypto, politics, sports, culture


@dataclass
class FeatureConfig:
    """Конфигурация извлечения признаков."""
    windows: List[int] = None
    volatility_windows: List[int] = None
    rsi_period: int = 14
    normalize: bool = True
    scaler_type: str = "standard"
    
    def __init__(self, **kwargs):
        """Инициализация с поддержкой конфигов из YAML."""
        self.windows = kwargs.get('windows', [1, 6, 24, 168, 720])
        self.volatility_windows = kwargs.get('volatility_windows', [24, 168, 720])
        self.rsi_period = kwargs.get('rsi_period', 14)
        self.normalize = kwargs.get('normalize', True)
        self.scaler_type = kwargs.get('scaler_type', 'standard')


class FeatureExtractor:
    """
    Извлекает признаки из временных рядов цен для ML-моделей.
    
    Attributes:
        config: Конфигурация извлечения признаков
        scaler: Scikit-learn scaler для нормализации (если используется)
        feature_names: Список названий признаков
        is_fitted: Флаг, указывает был ли scaler обучен
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        """
        Инициализация FeatureExtractor.
        
        Args:
            config: Конфигурация извлечения признаков. Если None, используется дефолтная.
        """
        self.config = config or FeatureConfig()
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: List[str] = []
        self.is_fitted: bool = False
        
        logger.info(f"FeatureExtractor инициализирован с окнами: {self.config.windows}")
    
    def extract_features(
        self,
        market_id: str,
        price_df: pd.DataFrame,
        metadata: MarketMetadata
    ) -> pd.Series:
        """
        Извлекает признаки для одного рынка.
        
        Args:
            market_id: ID рынка
            price_df: DataFrame с колонками [timestamp, yes_price, volume, liquidity]
            metadata: Метаданные рынка
            
        Returns:
            pd.Series с извлечёнными признаками
            
        Raises:
            ValueError: Если недостаточно данных для извлечения признаков
        """
        if price_df.empty:
            logger.warning(f"Рынок {market_id}: пустой DataFrame с ценами")
            return self._create_empty_features()
        
        # Убедимся, что данные отсортированы по времени
        if 'timestamp' in price_df.columns:
            price_df = price_df.sort_values('timestamp').reset_index(drop=True)
        
        features = {}
        
        # 1. Статистики цен
        features.update(self._extract_price_statistics(price_df))
        
        # 2. Волатильность
        features.update(self._extract_volatility_features(price_df))
        
        # 3. Тренд
        features.update(self._extract_trend_features(price_df))
        
        # 4. Моментум
        features.update(self._extract_momentum_features(price_df))
        
        # 5. Объёмные метрики
        features.update(self._extract_volume_features(price_df))
        
        # 6. Временные фичи
        features.update(self._extract_temporal_features(metadata))
        
        # 7. Ценовые паттерны
        features.update(self._extract_price_patterns(price_df))
        
        # 8. Контекстные фичи
        features.update(self._extract_context_features(metadata))
        
        # Сохраняем названия фич
        if not self.feature_names:
            self.feature_names = sorted(features.keys())
        
        # Создаём Series
        feature_series = pd.Series(features, name=market_id)
        
        # Обработка пропусков
        feature_series = self._handle_missing_values(feature_series)
        
        return feature_series
    
    def extract_features_batch(
        self,
        metadata_df: pd.DataFrame,
        price_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Извлекает признаки для батча рынков.
        
        Args:
            metadata_df: DataFrame с колонками [id, question, end_date, resolution, created_at]
            price_df: DataFrame с колонками [market_id, timestamp, yes_price, volume, liquidity]
            
        Returns:
            pd.DataFrame с признаками для всех рынков (index = market_id)
        """
        logger.info(f"Извлечение признаков для {len(metadata_df)} рынков")
        
        all_features = []
        
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
            
            # Фильтруем цены для этого рынка
            market_prices = price_df[price_df['market_id'] == market_id].copy()
            
            try:
                features = self.extract_features(market_id, market_prices, metadata)
                all_features.append(features)
            except Exception as e:
                logger.error(f"Ошибка извлечения признаков для рынка {market_id}: {e}")
                # Добавляем пустые фичи
                all_features.append(self._create_empty_features())
        
        # Создаём DataFrame
        features_df = pd.DataFrame(all_features)
        features_df.index = metadata_df['id'].values
        
        # Нормализация
        if self.config.normalize:
            features_df = self._normalize_features(features_df)
        
        logger.info(f"Извлечено {len(features_df.columns)} признаков для {len(features_df)} рынков")
        
        return features_df
    
    def _extract_price_statistics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Извлекает статистики цен."""
        prices = df['yes_price'].values
        
        features = {
            'price_current': prices[-1] if len(prices) > 0 else 0.5,
            'price_mean': np.mean(prices) if len(prices) > 0 else 0.5,
            'price_std': np.std(prices) if len(prices) > 0 else 0.0,
            'price_min': np.min(prices) if len(prices) > 0 else 0.5,
            'price_max': np.max(prices) if len(prices) > 0 else 0.5,
            'price_median': np.median(prices) if len(prices) > 0 else 0.5,
        }
        
        # Skewness и kurtosis (если достаточно данных)
        if len(prices) >= 3:
            features['price_skewness'] = float(pd.Series(prices).skew())
            features['price_kurtosis'] = float(pd.Series(prices).kurtosis())
        else:
            features['price_skewness'] = 0.0
            features['price_kurtosis'] = 0.0
        
        # Статистики по временным окнам
        for window in self.config.windows:
            window_prices = prices[-window:] if len(prices) >= window else prices
            
            if len(window_prices) > 0:
                features[f'price_mean_{window}h'] = np.mean(window_prices)
                features[f'price_std_{window}h'] = np.std(window_prices)
                features[f'price_min_{window}h'] = np.min(window_prices)
                features[f'price_max_{window}h'] = np.max(window_prices)
            else:
                features[f'price_mean_{window}h'] = 0.5
                features[f'price_std_{window}h'] = 0.0
                features[f'price_min_{window}h'] = 0.5
                features[f'price_max_{window}h'] = 0.5
        
        return features
    
    def _extract_volatility_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """Извлекает волатильностные фичи."""
        prices = df['yes_price'].values
        
        if len(prices) < 2:
            return {f'volatility_{w}h': 0.0 for w in self.config.volatility_windows}
        
        # Returns
        returns = np.diff(prices) / prices[:-1]
        returns = np.nan_to_num(returns, nan=0.0)
        
        features = {}
        
        # Стандартное отклонение returns по окнам
        for window in self.config.volatility_windows:
            window_returns = returns[-window:] if len(returns) >= window else returns
            
            if len(window_returns) > 0:
                features[f'volatility_{window}h'] = np.std(window_returns)
            else:
                features[f'volatility_{window}h'] = 0.0
        
        # ATR-подобная метрика (Average True Range)
        if len(prices) >= 2:
            high_low = df['yes_price'].max() - df['yes_price'].min()
            features['atr_proxy'] = high_low / len(prices)
        else:
            features['atr_proxy'] = 0.0
        
        # GARCH-прокси (упрощённая версия)
        if len(returns) >= 10:
            # Используем автокорреляцию квадратов returns как прокси
            returns_sq = returns ** 2
            if len(returns_sq) > 1:
                autocorr = np.corrcoef(returns_sq[:-1], returns_sq[1:])[0, 1]
                features['garch_proxy'] = autocorr if not np.isnan(autocorr) else 0.0
            else:
                features['garch_proxy'] = 0.0
        else:
            features['garch_proxy'] = 0.0
        
        return features
    
    def _extract_trend_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """Извлекает трендовые фичи (наклон линейной регрессии)."""
        prices = df['yes_price'].values
        
        features = {}
        
        # Окна для тренда: 24h, 7d (168h), 30d (720h)
        trend_windows = [24, 168, 720]
        
        for window in trend_windows:
            window_prices = prices[-window:] if len(prices) >= window else prices
            
            if len(window_prices) >= 2:
                # Линейная регрессия
                x = np.arange(len(window_prices))
                slope, _ = np.polyfit(x, window_prices, 1)
                features[f'trend_slope_{window}h'] = slope
            else:
                features[f'trend_slope_{window}h'] = 0.0
        
        return features
    
    def _extract_momentum_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """Извлекает моментум фичи (изменение цены за разные периоды)."""
        prices = df['yes_price'].values
        
        features = {}
        
        # Периоды: 1h, 6h, 24h, 7d (168h), 14d (336h)
        momentum_periods = [1, 6, 24, 168, 336]
        
        for period in momentum_periods:
            if len(prices) > period:
                momentum = (prices[-1] - prices[-period - 1]) / prices[-period - 1]
                features[f'momentum_{period}h'] = momentum
            else:
                features[f'momentum_{period}h'] = 0.0
        
        return features
    
    def _extract_volume_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """Извлекает объёмные метрики."""
        features = {}
        
        if 'volume' not in df.columns or df['volume'].isna().all():
            return {
                'volume_mean': 0.0,
                'volume_std': 0.0,
                'volume_trend': 0.0,
                'volume_liquidity_ratio': 0.0,
            }
        
        volumes = df['volume'].values
        
        features['volume_mean'] = np.mean(volumes) if len(volumes) > 0 else 0.0
        features['volume_std'] = np.std(volumes) if len(volumes) > 0 else 0.0
        
        # Тренд объёма (наклон линейной регрессии)
        if len(volumes) >= 2:
            x = np.arange(len(volumes))
            slope, _ = np.polyfit(x, volumes, 1)
            features['volume_trend'] = slope
        else:
            features['volume_trend'] = 0.0
        
        # Volume/Liquidity ratio
        if 'liquidity' in df.columns and df['liquidity'].notna().any():
            liquidity = df['liquidity'].values
            if len(volumes) > 0 and len(liquidity) > 0:
                avg_volume = np.mean(volumes)
                avg_liquidity = np.mean(liquidity)
                features['volume_liquidity_ratio'] = avg_volume / avg_liquidity if avg_liquidity > 0 else 0.0
            else:
                features['volume_liquidity_ratio'] = 0.0
        else:
            features['volume_liquidity_ratio'] = 0.0
        
        return features
    
    def _extract_temporal_features(self, metadata: MarketMetadata) -> Dict[str, float]:
        """Извлекает временные фичи."""
        features = {}
        
        # Days to expiry
        if metadata.end_date:
            now = datetime.now()
            days_to_expiry = (metadata.end_date - now).days
            features['days_to_expiry'] = max(0, days_to_expiry)
        else:
            features['days_to_expiry'] = 365  # Дефолт
        
        # Day of week (0=Monday, 6=Sunday)
        features['day_of_week'] = datetime.now().weekday()
        
        # Hour of day
        features['hour_of_day'] = datetime.now().hour
        
        return features
    
    def _extract_price_patterns(self, df: pd.DataFrame) -> Dict[str, float]:
        """Извлекает ценовые паттерны."""
        prices = df['yes_price'].values
        
        features = {}
        
        if len(prices) == 0:
            return {
                'distance_from_high': 0.0,
                'distance_from_low': 0.0,
                'rsi': 50.0,
            }
        
        # Расстояние от 52w high/low (используем всё доступное как прокси)
        high = np.max(prices)
        low = np.min(prices)
        current = prices[-1]
        
        features['distance_from_high'] = (high - current) / high if high > 0 else 0.0
        features['distance_from_low'] = (current - low) / low if low > 0 else 0.0
        
        # RSI-подобный индикатор
        features['rsi'] = self._calculate_rsi(prices, self.config.rsi_period)
        
        return features
    
    def _extract_context_features(self, metadata: MarketMetadata) -> Dict[str, float]:
        """Извлекает контекстные фичи (тип рынка)."""
        features = {}
        
        # Определяем категорию
        if metadata.category:
            category = metadata.category
        else:
            category = self._detect_category(metadata.question)
        
        # One-hot encoding для категории
        categories = ['crypto', 'politics', 'sports', 'culture']
        for cat in categories:
            features[f'category_{cat}'] = 1.0 if category == cat else 0.0
        
        return features
    
    def _detect_category(self, question: str) -> str:
        """Определяет категорию рынка по вопросу."""
        question_lower = question.lower()
        
        if re.search(r'bitcoin|btc|ethereum|eth|solana|sol|crypto|token', question_lower):
            return 'crypto'
        elif re.search(r'election|president|congress|senate|party|vote|trump|biden', question_lower):
            return 'politics'
        elif re.search(r'nba|nfl|mlb|nhl|ufc|tennis|world cup|superbowl|match|champion', question_lower):
            return 'sports'
        else:
            return 'culture'
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Вычисляет RSI (Relative Strength Index)."""
        if len(prices) < period + 1:
            return 50.0  # Нейтральное значение
        
        # Изменения цен
        deltas = np.diff(prices)
        
        # Разделяем на gains и losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Средние значения
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)
    
    def _handle_missing_values(self, features: pd.Series) -> pd.Series:
        """Обрабатывает пропущенные значения."""
        # Заполняем NaN нулями для числовых фич
        features = features.fillna(0.0)
        
        # Заменяем inf на большие числа
        features = features.replace([np.inf, -np.inf], [1e10, -1e10])
        
        return features
    
    def _normalize_features(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Нормализует признаки."""
        if self.config.scaler_type == "standard":
            self.scaler = StandardScaler()
            
            if not self.is_fitted:
                # Обучаем scaler
                features_df = pd.DataFrame(
                    self.scaler.fit_transform(features_df),
                    columns=features_df.columns,
                    index=features_df.index
                )
                self.is_fitted = True
                logger.info("Scaler обучен на данных")
            else:
                # Трансформируем
                features_df = pd.DataFrame(
                    self.scaler.transform(features_df),
                    columns=features_df.columns,
                    index=features_df.index
                )
        
        return features_df
    
    def _create_empty_features(self) -> pd.Series:
        """Создаёт пустой Series с признаками (для обработки ошибок)."""
        # Создаём минимальный набор фич
        empty_features = {
            'price_current': 0.5,
            'price_mean': 0.5,
            'price_std': 0.0,
            'days_to_expiry': 365,
            'category_crypto': 0.0,
            'category_politics': 0.0,
            'category_sports': 0.0,
            'category_culture': 1.0,
        }
        
        return pd.Series(empty_features)
    
    def get_feature_names(self) -> List[str]:
        """Возвращает список названий признаков."""
        return self.feature_names
    
    def save_scaler(self, path: str) -> None:
        """Сохраняет scaler в файл."""
        import joblib
        
        if self.scaler is not None:
            joblib.dump(self.scaler, path)
            logger.info(f"Scaler сохранён в {path}")
        else:
            logger.warning("Scaler не обучен, нечего сохранять")
    
    def load_scaler(self, path: str) -> None:
        """Загружает scaler из файла."""
        import joblib
        import os
        
        if os.path.exists(path):
            self.scaler = joblib.load(path)
            self.is_fitted = True
            logger.info(f"Scaler загружен из {path}")
        else:
            logger.warning(f"Файл scaler не найден: {path}")
