"""
Тесты для OracleEnsemble.
"""

import numpy as np
import pandas as pd
import pytest

from ml_oracle.ensemble import OracleEnsemble, EnsembleConfig, default_heuristic
from ml_oracle.feature_extractor import MarketMetadata


@pytest.fixture
def sample_price_df():
    """Создаёт тестовый DataFrame с ценами."""
    np.random.seed(42)
    n = 100
    
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


def test_ensemble_config_initialization():
    """Тест инициализации EnsembleConfig."""
    config = EnsembleConfig()
    assert config.use_ml is True
    assert config.use_heuristic is True
    assert config.ml_weight == 0.7
    assert config.heuristic_weight == 0.3
    assert config.min_confidence == 0.6


def test_ensemble_config_custom_weights():
    """Тест кастомных весов в EnsembleConfig."""
    config = EnsembleConfig(ml_weight=0.8, heuristic_weight=0.2)
    assert config.ml_weight == 0.8
    assert config.heuristic_weight == 0.2


def test_default_heuristic(sample_price_df, sample_metadata):
    """Тест эвристического оракула по умолчанию."""
    proba = default_heuristic('test', sample_price_df, sample_metadata)
    
    assert proba is not None
    assert 0 <= proba <= 1


def test_default_heuristic_empty_df(sample_metadata):
    """Тест эвристики с пустым DataFrame."""
    empty_df = pd.DataFrame(columns=['timestamp', 'yes_price', 'volume'])
    proba = default_heuristic('test', empty_df, sample_metadata)
    
    assert proba == 0.5  # Дефолтное значение


def test_ensemble_heuristic_only(sample_price_df, sample_metadata):
    """Тест ансамбля только с эвристикой."""
    config = EnsembleConfig(use_ml=False, use_heuristic=True)
    ensemble = OracleEnsemble(config=config, heuristic_fn=default_heuristic)
    
    proba, source = ensemble.predict('test', sample_price_df, sample_metadata)
    
    assert proba is not None
    assert 0 <= proba <= 1
    assert source == 'heuristic'


def test_ensemble_no_models(sample_price_df, sample_metadata):
    """Тест ансамбля без моделей."""
    config = EnsembleConfig(use_ml=False, use_heuristic=False)
    ensemble = OracleEnsemble(config=config)
    
    proba, source = ensemble.predict('test', sample_price_df, sample_metadata)
    
    assert proba is None
    assert source == 'none'
