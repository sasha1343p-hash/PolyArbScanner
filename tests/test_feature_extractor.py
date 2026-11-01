"""
Тесты для FeatureExtractor.
"""

import numpy as np
import pandas as pd
import pytest

from ml_oracle.feature_extractor import FeatureExtractor, FeatureConfig, MarketMetadata


@pytest.fixture
def sample_price_df():
    """Создаёт тестовый DataFrame с ценами."""
    np.random.seed(42)
    n = 200
    
    return pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=n, freq='h'),
        'yes_price': np.random.uniform(0.3, 0.7, n),
        'volume': np.random.uniform(1000, 10000, n),
        'liquidity': np.random.uniform(5000, 50000, n),
    })


@pytest.fixture
def sample_metadata():
    """Создаёт тестовые метаданные."""
    return MarketMetadata(
        id='test-market-123',
        question='Will Bitcoin be above $100,000 by March 2026?',
        end_date=pd.Timestamp('2026-03-01'),
        resolution='YES',
        created_at=pd.Timestamp('2024-01-01'),
    )


def test_feature_extractor_initialization():
    """Тест инициализации FeatureExtractor."""
    extractor = FeatureExtractor()
    assert extractor.config is not None
    assert extractor.scaler is None
    assert extractor.is_fitted is False


def test_extract_price_statistics(sample_price_df, sample_metadata):
    """Тест извлечения статистик цен."""
    extractor = FeatureExtractor()
    features = extractor.extract_features('test', sample_price_df, sample_metadata)
    
    # Проверяем наличие основных статистик
    assert 'price_current' in features
    assert 'price_mean' in features
    assert 'price_std' in features
    assert 'price_min' in features
    assert 'price_max' in features
    
    # Проверяем диапазоны
    assert 0 <= features['price_current'] <= 1
    assert 0 <= features['price_mean'] <= 1
    assert features['price_std'] >= 0
    assert features['price_min'] <= features['price_max']


def test_extract_volatility_features(sample_price_df, sample_metadata):
    """Тест извлечения волатильностных фич."""
    extractor = FeatureExtractor()
    features = extractor.extract_features('test', sample_price_df, sample_metadata)
    
    # Проверяем наличие волатильностных фич
    assert 'volatility_24h' in features
    assert 'volatility_168h' in features
    assert 'atr_proxy' in features
    
    # Волатильность должна быть >= 0
    assert features['volatility_24h'] >= 0
    assert features['volatility_168h'] >= 0


def test_extract_momentum_features(sample_price_df, sample_metadata):
    """Тест извлечения моментум фич."""
    extractor = FeatureExtractor()
    features = extractor.extract_features('test', sample_price_df, sample_metadata)
    
    # Проверяем наличие моментум фич
    assert 'momentum_1h' in features
    assert 'momentum_24h' in features
    assert 'momentum_168h' in features


def test_extract_temporal_features(sample_price_df, sample_metadata):
    """Тест извлечения временных фич."""
    extractor = FeatureExtractor()
    features = extractor.extract_features('test', sample_price_df, sample_metadata)
    
    # Проверяем наличие временных фич
    assert 'days_to_expiry' in features
    assert 'day_of_week' in features
    assert 'hour_of_day' in features
    
    # Days to expiry должен быть >= 0
    assert features['days_to_expiry'] >= 0
    
    # Day of week: 0-6
    assert 0 <= features['day_of_week'] <= 6
    
    # Hour of day: 0-23
    assert 0 <= features['hour_of_day'] <= 23


def test_extract_category_features(sample_price_df, sample_metadata):
    """Тест извлечения категориальных фич."""
    extractor = FeatureExtractor()
    features = extractor.extract_features('test', sample_price_df, sample_metadata)
    
    # Проверяем наличие категориальных фич
    assert 'category_crypto' in features
    assert 'category_politics' in features
    assert 'category_sports' in features
    assert 'category_culture' in features
    
    # Вопрос про Bitcoin -> crypto
    assert features['category_crypto'] == 1.0
    assert features['category_politics'] == 0.0


def test_extract_rsi(sample_price_df, sample_metadata):
    """Тест вычисления RSI."""
    extractor = FeatureExtractor()
    features = extractor.extract_features('test', sample_price_df, sample_metadata)
    
    # RSI должен быть в диапазоне 0-100
    assert 'rsi' in features
    assert 0 <= features['rsi'] <= 100


def test_handle_empty_dataframe(sample_metadata):
    """Тест обработки пустого DataFrame."""
    extractor = FeatureExtractor()
    empty_df = pd.DataFrame(columns=['timestamp', 'yes_price', 'volume'])
    
    features = extractor.extract_features('test', empty_df, sample_metadata)
    
    # Должны вернуться дефолтные значения
    assert 'price_current' in features
    assert features['price_current'] == 0.5


def test_extract_features_batch():
    """Тест батчевого извлечения признаков."""
    extractor = FeatureExtractor()
    
    # Создаём тестовые данные
    metadata_df = pd.DataFrame({
        'id': ['market1', 'market2'],
        'question': [
            'Will BTC be above $100k?',
            'Will ETH be above $5k?',
        ],
        'end_date': ['2026-03-01', '2026-06-01'],
        'resolution': ['YES', 'NO'],
        'created_at': ['2024-01-01', '2024-01-01'],
    })
    
    price_df = pd.DataFrame({
        'market_id': ['market1'] * 100 + ['market2'] * 100,
        'timestamp': list(pd.date_range('2024-01-01', periods=100, freq='h')) * 2,
        'yes_price': np.random.uniform(0.3, 0.7, 200),
        'volume': np.random.uniform(1000, 10000, 200),
        'liquidity': np.random.uniform(5000, 50000, 200),
    })
    
    features_df = extractor.extract_features_batch(metadata_df, price_df)
    
    # Проверяем размер
    assert len(features_df) == 2
    assert 'price_mean' in features_df.columns
    assert 'volatility_24h' in features_df.columns


def test_normalization():
    """Тест нормализации признаков."""
    config = FeatureConfig(normalize=True)
    extractor = FeatureExtractor(config)
    
    # Создаём тестовые данные
    metadata_df = pd.DataFrame({
        'id': ['market1', 'market2', 'market3'],
        'question': ['Q1', 'Q2', 'Q3'],
        'end_date': ['2026-03-01', '2026-06-01', '2026-12-01'],
        'resolution': ['YES', 'NO', 'YES'],
        'created_at': ['2024-01-01', '2024-01-01', '2024-01-01'],
    })
    
    price_df = pd.DataFrame({
        'market_id': ['market1'] * 50 + ['market2'] * 50 + ['market3'] * 50,
        'timestamp': list(pd.date_range('2024-01-01', periods=50, freq='h')) * 3,
        'yes_price': np.random.uniform(0.3, 0.7, 150),
        'volume': np.random.uniform(1000, 10000, 150),
    })
    
    features_df = extractor.extract_features_batch(metadata_df, price_df)
    
    # После нормализации среднее должно быть близко к 0
    assert extractor.is_fitted is True
    assert extractor.scaler is not None


def test_detect_category():
    """Тест определения категории рынка."""
    extractor = FeatureExtractor()
    
    # Крипто
    assert extractor._detect_category('Will Bitcoin be above $100k?') == 'crypto'
    assert extractor._detect_category('Will ETH reach $5000?') == 'crypto'
    
    # Политика
    assert extractor._detect_category('Will Trump win the election?') == 'politics'
    assert extractor._detect_category('Will Democrats win Congress?') == 'politics'
    
    # Спорт
    assert extractor._detect_category('Will Lakers win NBA Finals?') == 'sports'
    assert extractor._detect_category('Will Brazil win World Cup?') == 'sports'
    
    # Культура (дефолт)
    assert extractor._detect_category('Will a Marvel movie win Oscar?') == 'culture'


def test_calculate_rsi():
    """Тест вычисления RSI."""
    extractor = FeatureExtractor()
    
    # Тренд вверх -> RSI высокий
    prices_up = np.linspace(0.3, 0.7, 50)
    rsi_up = extractor._calculate_rsi(prices_up, period=14)
    assert rsi_up > 50
    
    # Тренд вниз -> RSI низкий
    prices_down = np.linspace(0.7, 0.3, 50)
    rsi_down = extractor._calculate_rsi(prices_down, period=14)
    assert rsi_down < 50
    
    # Недостаточно данных -> дефолт
    prices_short = np.array([0.5, 0.6])
    rsi_short = extractor._calculate_rsi(prices_short, period=14)
    assert rsi_short == 50.0
