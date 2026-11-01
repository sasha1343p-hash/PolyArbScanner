"""
ML-модель для предсказания вероятностей на предиктивных рынках.

Использует ансамбль XGBoost и LightGBM с калибровкой вероятностей
и оценкой уверенности предсказаний.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    brier_score_loss,
)
from sklearn.model_selection import TimeSeriesSplit

logger = logging.getLogger(__name__)

# Импорты моделей (опциональные)
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    logger.warning("XGBoost не установлен. pip install xgboost")

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False
    logger.warning("LightGBM не установлен. pip install lightgbm")


@dataclass
class ModelMetrics:
    """Метрики качества модели."""
    accuracy: float
    precision: float
    recall: float
    f1: float
    auc_roc: float
    brier_score: float
    n_samples: int
    n_positive: int
    n_negative: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует в словарь."""
        return {
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1': self.f1,
            'auc_roc': self.auc_roc,
            'brier_score': self.brier_score,
            'n_samples': self.n_samples,
            'n_positive': self.n_positive,
            'n_negative': self.n_negative,
        }


@dataclass
class TrainingConfig:
    """Конфигурация обучения модели."""
    test_size: float = 0.2
    n_splits: int = 5
    calibration_enabled: bool = True
    calibration_method: str = "isotonic"
    calibration_cv: int = 5
    random_state: int = 42
    
    # XGBoost параметры
    xgb_params: Dict[str, Any] = None
    xgb_enabled: bool = True
    
    # LightGBM параметры
    lgb_params: Dict[str, Any] = None
    lgb_enabled: bool = True
    
    def __init__(self, **kwargs):
        """Инициализация с поддержкой вложенных конфигов."""
        self.test_size = kwargs.get('test_size', 0.2)
        self.n_splits = kwargs.get('n_splits', 5)
        self.random_state = kwargs.get('random_state', 42)
        
        # Обработка calibration
        calibration = kwargs.get('calibration', {})
        if isinstance(calibration, dict):
            self.calibration_enabled = calibration.get('enabled', True)
            self.calibration_method = calibration.get('method', 'isotonic')
            self.calibration_cv = calibration.get('cv', 5)
        else:
            self.calibration_enabled = kwargs.get('calibration_enabled', True)
            self.calibration_method = kwargs.get('calibration_method', 'isotonic')
            self.calibration_cv = kwargs.get('calibration_cv', 5)
        
        # Обработка models
        models = kwargs.get('models', {})
        if isinstance(models, dict):
            # XGBoost
            xgb_config = models.get('xgboost', {})
            if isinstance(xgb_config, dict):
                self.xgb_enabled = xgb_config.get('enabled', True)
                self.xgb_params = xgb_config.get('params', {})
            else:
                self.xgb_enabled = True
                self.xgb_params = {}
            
            # LightGBM
            lgb_config = models.get('lightgbm', {})
            if isinstance(lgb_config, dict):
                self.lgb_enabled = lgb_config.get('enabled', True)
                self.lgb_params = lgb_config.get('params', {})
            else:
                self.lgb_enabled = True
                self.lgb_params = {}
        else:
            self.xgb_enabled = kwargs.get('xgb_enabled', True)
            self.xgb_params = kwargs.get('xgb_params', {})
            self.lgb_enabled = kwargs.get('lgb_enabled', True)
            self.lgb_params = kwargs.get('lgb_params', {})
        
        # Устанавливаем дефолтные параметры если они пустые
        if not self.xgb_params:
            self.xgb_params = {
                'n_estimators': 500,
                'max_depth': 6,
                'learning_rate': 0.05,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'reg_alpha': 0.1,
                'reg_lambda': 1.0,
                'min_child_weight': 3,
                'random_state': self.random_state,
                'eval_metric': 'auc',
                'tree_method': 'hist',
            }
        
        if not self.lgb_params:
            self.lgb_params = {
                'n_estimators': 500,
                'max_depth': 6,
                'learning_rate': 0.05,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'reg_alpha': 0.1,
                'reg_lambda': 1.0,
                'min_child_weight': 3,
                'random_state': self.random_state,
                'early_stopping_round': 50,
                'verbose': -1,
            }


class MLOracle:
    """
    ML-модель для предсказания вероятностей на предиктивных рынках.
    
    Использует ансамбль XGBoost и LightGBM с калибровкой вероятностей.
    Поддерживает обучение, инференс и оценку уверенности предсказаний.
    
    Attributes:
        config: Конфигурация обучения
        model: Обученная модель (или калиброванная обёртка)
        model_type: Тип модели ('xgboost', 'lightgbm', 'ensemble')
        feature_names: Список признаков
        metrics: Метрики качества после обучения
        is_trained: Флаг обученности модели
    """
    
    def __init__(self, config: Optional[TrainingConfig] = None):
        """
        Инициализация MLOracle.
        
        Args:
            config: Конфигурация обучения. Если None, используется дефолтная.
        """
        self.config = config or TrainingConfig()
        self.model: Optional[Any] = None
        self.model_type: Optional[str] = None
        self.feature_names: List[str] = []
        self.metrics: Optional[ModelMetrics] = None
        self.is_trained: bool = False
        
        # Для оценки уверенности
        self.train_mean: Optional[np.ndarray] = None
        self.train_std: Optional[np.ndarray] = None
        
        logger.info("MLOracle инициализирован")
    
    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        feature_names: Optional[List[str]] = None
    ) -> ModelMetrics:
        """
        Обучает модель на данных.
        
        Использует TimeSeriesSplit для временных рядов (НЕ random split).
        Обучает XGBoost и LightGBM, выбирает лучшую модель по AUC-ROC.
        
        Args:
            X: DataFrame с признаками
            y: Series с целевой переменной (0 или 1)
            feature_names: Список названий признаков
            
        Returns:
            ModelMetrics с метриками качества на тестовой выборке
            
        Raises:
            ValueError: Если недостаточно данных для обучения
        """
        logger.info(f"Начало обучения модели на {len(X)} примерах")
        
        # Проверки
        if len(X) < 100:
            raise ValueError(f"Недостаточно данных для обучения: {len(X)} < 100")
        
        if X.isna().any().any():
            logger.warning("Обнаружены NaN в данных, заполняем нулями")
            X = X.fillna(0)
        
        self.feature_names = feature_names or list(X.columns)
        
        # Проверка баланса классов
        n_positive = y.sum()
        n_negative = len(y) - n_positive
        logger.info(f"Баланс классов: YES={n_positive}, NO={n_negative}")
        
        # TimeSeriesSplit для временных рядов
        tscv = TimeSeriesSplit(n_splits=self.config.n_splits)
        
        # Обучаем модели
        models_scores = {}
        
        # XGBoost
        if self.config.xgb_enabled and HAS_XGBOOST:
            logger.info("Обучение XGBoost...")
            xgb_model, xgb_score = self._train_xgboost(X, y, tscv)
            if xgb_model is not None:
                models_scores['xgboost'] = (xgb_model, xgb_score)
                logger.info(f"XGBoost AUC-ROC: {xgb_score:.4f}")
        
        # LightGBM
        if self.config.lgb_enabled and HAS_LIGHTGBM:
            logger.info("Обучение LightGBM...")
            lgb_model, lgb_score = self._train_lightgbm(X, y, tscv)
            if lgb_model is not None:
                models_scores['lightgbm'] = (lgb_model, lgb_score)
                logger.info(f"LightGBM AUC-ROC: {lgb_score:.4f}")
        
        if not models_scores:
            raise RuntimeError("Не удалось обучить ни одну модель")
        
        # Выбираем лучшую модель
        best_model_name = max(models_scores, key=lambda k: models_scores[k][1])
        best_model, best_score = models_scores[best_model_name]
        
        logger.info(f"Лучшая модель: {best_model_name} (AUC-ROC: {best_score:.4f})")
        
        # Калибровка вероятностей
        if self.config.calibration_enabled:
            logger.info("Калибровка вероятностей...")
            best_model = self._calibrate_model(best_model, X, y)
        
        self.model = best_model
        self.model_type = best_model_name
        self.is_trained = True
        
        # Сохраняем статистику для оценки уверенности
        self.train_mean = X.mean().values
        self.train_std = X.std().values
        
        # Оценка на тестовой выборке (последние 20%)
        test_size = int(len(X) * self.config.test_size)
        X_test = X.iloc[-test_size:]
        y_test = y.iloc[-test_size:]
        
        self.metrics = self._evaluate_model(X_test, y_test)
        
        logger.info(f"Обучение завершено. Метрики: {self.metrics.to_dict()}")
        
        return self.metrics
    
    def _train_xgboost(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        tscv: TimeSeriesSplit
    ) -> Tuple[Optional[Any], float]:
        """Обучает XGBoost с кросс-валидацией."""
        if not HAS_XGBOOST:
            return None, 0.0
        
        scores = []
        best_model = None
        
        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            # Обработка дисбаланса классов
            scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
            params = self.config.xgb_params.copy()
            params['scale_pos_weight'] = scale_pos_weight
            
            model = xgb.XGBClassifier(**params)
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    verbose=False
                )
            
            y_pred_proba = model.predict_proba(X_val)[:, 1]
            score = roc_auc_score(y_val, y_pred_proba)
            scores.append(score)
            
            if best_model is None or score > max(scores[:-1], default=0):
                best_model = model
        
        avg_score = np.mean(scores) if scores else 0.0
        
        # Переобучаем лучшую модель на всех данных (без early stopping)
        if best_model is not None:
            final_params = self.config.xgb_params.copy()
            final_params['scale_pos_weight'] = (y == 0).sum() / max((y == 1).sum(), 1)
            final_model = xgb.XGBClassifier(**final_params)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                final_model.fit(X, y, verbose=False)
            return final_model, avg_score
        
        return best_model, avg_score
    
    def _train_lightgbm(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        tscv: TimeSeriesSplit
    ) -> Tuple[Optional[Any], float]:
        """Обучает LightGBM с кросс-валидацией."""
        if not HAS_LIGHTGBM:
            return None, 0.0
        
        scores = []
        best_model = None
        
        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            # Обработка дисбаланса классов
            scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
            params = self.config.lgb_params.copy()
            params['scale_pos_weight'] = scale_pos_weight
            
            model = lgb.LGBMClassifier(**params)
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    eval_metric='auc',
                )
            
            y_pred_proba = model.predict_proba(X_val)[:, 1]
            score = roc_auc_score(y_val, y_pred_proba)
            scores.append(score)
            
            if best_model is None or score > max(scores[:-1], default=0):
                best_model = model
        
        avg_score = np.mean(scores) if scores else 0.0
        
        # Переобучаем лучшую модель на всех данных (без early stopping)
        if best_model is not None:
            final_params = self.config.lgb_params.copy()
            final_params['scale_pos_weight'] = (y == 0).sum() / max((y == 1).sum(), 1)
            # Убираем early stopping для финального обучения
            final_params.pop('early_stopping_round', None)
            final_params.pop('early_stopping_rounds', None)
            final_model = lgb.LGBMClassifier(**final_params)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                final_model.fit(X, y)
            return final_model, avg_score
        
        return best_model, avg_score
    
    def _calibrate_model(
        self,
        model: Any,
        X: pd.DataFrame,
        y: pd.Series
    ) -> CalibratedClassifierCV:
        """Калибрует вероятности модели.
        
        Использует cv='prefit' чтобы не переобучать модель,
        а только откалибровать её вероятности на данных.
        """
        # Для XGBoost убираем early_stopping_rounds перед калибровкой
        if hasattr(model, 'set_params'):
            try:
                model.set_params(early_stopping_rounds=None)
            except Exception:
                pass
        
        # Убираем eval_set если есть
        if hasattr(model, 'eval_set'):
            model.eval_set = None
        
        calibrated = CalibratedClassifierCV(
            model,
            method=self.config.calibration_method,
            cv='prefit'  # Используем уже обученную модель
        )
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            calibrated.fit(X, y)
        
        return calibrated
    
    def _evaluate_model(self, X_test: pd.DataFrame, y_test: pd.Series) -> ModelMetrics:
        """Оценивает модель на тестовой выборке."""
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        y_pred = (y_pred_proba >= 0.5).astype(int)
        
        metrics = ModelMetrics(
            accuracy=accuracy_score(y_test, y_pred),
            precision=precision_score(y_test, y_pred, zero_division=0),
            recall=recall_score(y_test, y_pred, zero_division=0),
            f1=f1_score(y_test, y_pred, zero_division=0),
            auc_roc=roc_auc_score(y_test, y_pred_proba),
            brier_score=brier_score_loss(y_test, y_pred_proba),
            n_samples=len(y_test),
            n_positive=int(y_test.sum()),
            n_negative=int(len(y_test) - y_test.sum()),
        )
        
        return metrics
    
    def predict(
        self,
        features: pd.Series
    ) -> Optional[float]:
        """
        Предсказывает вероятность YES для одного рынка.
        
        Args:
            features: Series с признаками для одного рынка
            
        Returns:
            Вероятность YES от 0 до 1, или None если модель не обучена
        """
        if not self.is_trained or self.model is None:
            logger.warning("Модель не обучена, возвращаем None")
            return None
        
        try:
            # Конвертируем в DataFrame
            X = pd.DataFrame([features.values], columns=self.feature_names)
            
            # Предсказание
            proba = self.model.predict_proba(X)[0, 1]
            
            return float(proba)
        
        except Exception as e:
            logger.error(f"Ошибка предсказания: {e}")
            return None
    
    def predict_with_confidence(
        self,
        features: pd.Series
    ) -> Tuple[Optional[float], float]:
        """
        Предсказывает вероятность с оценкой уверенности.
        
        Уверенность основана на расстоянии от распределения обучающей выборки.
        
        Args:
            features: Series с признаками
            
        Returns:
            Tuple (probability, confidence_score), где confidence от 0 до 1
        """
        proba = self.predict(features)
        
        if proba is None:
            return None, 0.0
        
        # Оценка уверенности на основе расстояния до train distribution
        confidence = self._estimate_confidence(features)
        
        return proba, confidence
    
    def _estimate_confidence(self, features: pd.Series) -> float:
        """Оценивает уверенность предсказания."""
        if self.train_mean is None or self.train_std is None:
            return 0.5
        
        try:
            # Mahalanobis-подобное расстояние (упрощённое)
            x = features.values
            z_scores = np.abs((x - self.train_mean) / (self.train_std + 1e-8))
            avg_z = np.mean(z_scores)
            
            # Конвертируем в уверенность (0-1)
            # Чем ближе к train distribution, тем выше уверенность
            confidence = 1 / (1 + avg_z)
            
            return float(np.clip(confidence, 0, 1))
        
        except Exception as e:
            logger.error(f"Ошибка оценки уверенности: {e}")
            return 0.5
    
    def get_feature_importance(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """
        Возвращает важность признаков.
        
        Args:
            top_n: Количество топ признаков
            
        Returns:
            Список кортежей (feature_name, importance)
        """
        if not self.is_trained or self.model is None:
            logger.warning("Модель не обучена")
            return []
        
        try:
            # Получаем базовую модель (если калибрована)
            base_model = self.model
            if isinstance(self.model, CalibratedClassifierCV):
                base_model = self.model.calibrated_classifiers_[0].estimator
            
            # Feature importance
            if hasattr(base_model, 'feature_importances_'):
                importances = base_model.feature_importances_
            else:
                logger.warning("Модель не поддерживает feature_importances_")
                return []
            
            # Создаём список (feature, importance)
            feature_importance = list(zip(self.feature_names, importances))
            
            # Сортируем по убыванию
            feature_importance.sort(key=lambda x: x[1], reverse=True)
            
            return feature_importance[:top_n]
        
        except Exception as e:
            logger.error(f"Ошибка получения feature importance: {e}")
            return []
    
    def save(self, path: str) -> None:
        """
        Сохраняет модель в файл.
        
        Args:
            path: Путь к файлу
        """
        if not self.is_trained:
            logger.warning("Модель не обучена, нечего сохранять")
            return
        
        bundle = {
            'model': self.model,
            'model_type': self.model_type,
            'feature_names': self.feature_names,
            'metrics': self.metrics.to_dict() if self.metrics else None,
            'train_mean': self.train_mean,
            'train_std': self.train_std,
            'config': self.config,
        }
        
        # Создаём директорию если нужно
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        joblib.dump(bundle, path)
        logger.info(f"Модель сохранена в {path}")
    
    def load(self, path: str) -> bool:
        """
        Загружает модель из файла.
        
        Args:
            path: Путь к файлу
            
        Returns:
            True если загрузка успешна, False иначе
        """
        if not os.path.exists(path):
            logger.warning(f"Файл модели не найден: {path}")
            return False
        
        try:
            bundle = joblib.load(path)
            
            self.model = bundle['model']
            self.model_type = bundle['model_type']
            self.feature_names = bundle['feature_names']
            self.train_mean = bundle.get('train_mean')
            self.train_std = bundle.get('train_std')
            self.config = bundle.get('config', TrainingConfig())
            
            if bundle.get('metrics'):
                self.metrics = ModelMetrics(**bundle['metrics'])
            
            self.is_trained = True
            
            logger.info(f"Модель загружена из {path}")
            return True
        
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
            return False
