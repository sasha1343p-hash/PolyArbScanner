"""
Тесты для MLOracle.
"""

import numpy as np
import pandas as pd
import pytest

from ml_oracle.model import MLOracle, TrainingConfig, ModelMetrics


@pytest.fixture
def sample_training_data():
    """Создаёт тестовые данные для обучения."""
    np.random.seed(42)
    n_samples = 500
    n_features = 20
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    
    # Создаём целевую переменную с некоторой структурой
    y = (X['feature_0'] + X['feature_1'] > 0).astype(int)
    
    return X, y


@pytest.fixture
def trained_model(sample_training_data):
    """Создаёт обученную модель."""
    X, y = sample_training_data
    
    config = TrainingConfig(
        test_size=0.2,
        n_splits=3,
        calibration_enabled=False,  # Отключаем для скорости тестов
        xgb_enabled=True,
        lgb_enabled=False,  # Используем только XGBoost для тестов
    )
    
    model = MLOracle(config)
    model.train(X, y)
    
    return model


def test_model_initialization():
    """Тест инициализации модели."""
    model = MLOracle()
    assert model.model is None
    assert model.is_trained is False
    assert model.metrics is None


def test_model_training(sample_training_data):
    """Тест обучения модели."""
    X, y = sample_training_data
    
    config = TrainingConfig(
        test_size=0.2,
        n_splits=3,
        calibration_enabled=False,
        xgb_enabled=True,
        lgb_enabled=False,
    )
    
    model = MLOracle(config)
    metrics = model.train(X, y)
    
    # Проверяем, что модель обучена
    assert model.is_trained is True
    assert model.model is not None
    assert metrics is not None
    
    # Проверяем метрики
    assert isinstance(metrics, ModelMetrics)
    assert 0 <= metrics.accuracy <= 1
    assert 0 <= metrics.auc_roc <= 1
    assert metrics.brier_score >= 0
    assert metrics.n_samples > 0


def test_model_predict(trained_model, sample_training_data):
    """Тест предсказания."""
    X, y = sample_training_data
    
    # Берём первый пример
    features = X.iloc[0]
    
    proba = trained_model.predict(features)
    
    # Проверяем, что предсказание валидно
    assert proba is not None
    assert 0 <= proba <= 1


def test_model_predict_with_confidence(trained_model, sample_training_data):
    """Тест предсказания с уверенностью."""
    X, y = sample_training_data
    
    features = X.iloc[0]
    
    proba, confidence = trained_model.predict_with_confidence(features)
    
    # Проверяем валидность
    assert proba is not None
    assert 0 <= proba <= 1
    assert 0 <= confidence <= 1


def test_model_predict_untrained():
    """Тест предсказания необученной модели."""
    model = MLOracle()
    
    features = pd.Series(np.random.randn(20))
    
    proba = model.predict(features)
    
    # Должно вернуть None
    assert proba is None


def test_model_metrics(sample_training_data):
    """Тест метрик качества."""
    X, y = sample_training_data
    
    config = TrainingConfig(
        test_size=0.2,
        n_splits=3,
        calibration_enabled=False,
        xgb_enabled=True,
        lgb_enabled=False,
    )
    
    model = MLOracle(config)
    metrics = model.train(X, y)
    
    # Проверяем, что метрики разумные
    assert metrics.accuracy > 0.5  # Лучше случайного
    assert metrics.n_samples == int(len(X) * 0.2)  # 20% test set
    assert metrics.n_positive + metrics.n_negative == metrics.n_samples


def test_model_feature_importance(trained_model):
    """Тест получения важности признаков."""
    importance = trained_model.get_feature_importance(top_n=5)
    
    # Должны получить список
    assert isinstance(importance, list)
    assert len(importance) <= 5
    
    # Каждый элемент - кортеж (feature_name, importance)
    for feature, score in importance:
        assert isinstance(feature, str)
        assert isinstance(score, (int, float))
        assert score >= 0


def test_model_save_load(trained_model, tmp_path):
    """Тест сохранения и загрузки модели."""
    model_path = tmp_path / 'test_model.pkl'
    
    # Сохраняем
    trained_model.save(str(model_path))
    
    # Загружаем в новую модель
    new_model = MLOracle()
    success = new_model.load(str(model_path))
    
    assert success is True
    assert new_model.is_trained is True
    assert new_model.model is not None


def test_model_load_nonexistent():
    """Тест загрузки несуществующей модели."""
    model = MLOracle()
    success = model.load('nonexistent_model.pkl')
    
    assert success is False


def test_model_insufficient_data():
    """Тест обучения на недостаточных данных."""
    X = pd.DataFrame(np.random.randn(50, 10))  # < 100 примеров
    y = pd.Series(np.random.randint(0, 2, 50))
    
    model = MLOracle()
    
    with pytest.raises(ValueError, match="Недостаточно данных"):
        model.train(X, y)


def test_model_with_nan_values():
    """Тест обучения с NaN значениями."""
    np.random.seed(42)
    X = pd.DataFrame(np.random.randn(200, 10))
    
    # Добавляем NaN
    X.iloc[0, 0] = np.nan
    X.iloc[10, 5] = np.nan
    
    y = pd.Series(np.random.randint(0, 2, 200))
    
    config = TrainingConfig(
        test_size=0.2,
        n_splits=3,
        calibration_enabled=False,
        xgb_enabled=True,
        lgb_enabled=False,
    )
    
    model = MLOracle(config)
    
    # Не должно упасть
    metrics = model.train(X, y)
    
    assert metrics is not None
    assert model.is_trained is True


def test_model_imbalanced_classes():
    """Тест обучения на несбалансированных данных."""
    np.random.seed(42)
    X = pd.DataFrame(np.random.randn(300, 10))
    
    # 90% класс 0, 10% класс 1
    y = pd.Series([0] * 270 + [1] * 30)
    
    config = TrainingConfig(
        test_size=0.2,
        n_splits=3,
        calibration_enabled=False,
        xgb_enabled=True,
        lgb_enabled=False,
    )
    
    model = MLOracle(config)
    metrics = model.train(X, y)
    
    # Модель должна обучиться
    assert model.is_trained is True
    assert metrics.n_positive == 6  # 20% от 30
    assert metrics.n_negative == 54  # 20% от 270


def test_model_metrics_to_dict(sample_training_data):
    """Тест конвертации метрик в словарь."""
    X, y = sample_training_data
    
    config = TrainingConfig(
        test_size=0.2,
        n_splits=3,
        calibration_enabled=False,
        xgb_enabled=True,
        lgb_enabled=False,
    )
    
    model = MLOracle(config)
    metrics = model.train(X, y)
    
    metrics_dict = metrics.to_dict()
    
    assert isinstance(metrics_dict, dict)
    assert 'accuracy' in metrics_dict
    assert 'auc_roc' in metrics_dict
    assert 'brier_score' in metrics_dict
