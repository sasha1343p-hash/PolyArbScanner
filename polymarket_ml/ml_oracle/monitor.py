"""
Мониторинг дрейфа модели и данных.

Отслеживает изменения в распределении признаков и предупреждает
о необходимости переобучения модели.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class DriftReport:
    """Отчёт о дрейфе."""
    has_drift: bool
    psi_values: Dict[str, float]
    ks_values: Dict[str, float]
    drifted_features: List[str]
    timestamp: str
    recommendation: str
    
    def to_dict(self) -> Dict:
        """Конвертирует в словарь."""
        return asdict(self)


@dataclass
class MonitorConfig:
    """Конфигурация мониторинга."""
    psi_threshold: float = 0.2
    ks_threshold: float = 0.1
    key_features: List[str] = None
    check_interval_hours: int = 24
    
    def __init__(self, **kwargs):
        """Инициализация с поддержкой конфигов из YAML."""
        self.psi_threshold = kwargs.get('psi_threshold', 0.2)
        self.ks_threshold = kwargs.get('ks_threshold', 0.1)
        self.check_interval_hours = kwargs.get('check_interval_hours', 24)
        self.key_features = kwargs.get('key_features', [
            'price_mean_24h',
            'price_std_24h',
            'volume_mean_24h',
            'momentum_24h',
            'days_to_expiry',
        ])


class ModelMonitor:
    """
    Мониторинг дрейфа модели и данных.
    
    Отслеживает изменения в распределении признаков с помощью
    PSI (Population Stability Index) и KS-test.
    
    Attributes:
        config: Конфигурация мониторинга
        train_stats: Статистика обучающей выборки
        is_initialized: Флаг инициализации
    """
    
    def __init__(self, config: Optional[MonitorConfig] = None):
        """
        Инициализация ModelMonitor.
        
        Args:
            config: Конфигурация мониторинга
        """
        self.config = config or MonitorConfig()
        self.train_stats: Optional[Dict] = None
        self.is_initialized: bool = False
        
        logger.info("ModelMonitor инициализирован")
    
    def initialize_from_train_data(self, X_train: pd.DataFrame) -> None:
        """
        Инициализирует мониторинг на основе обучающей выборки.
        
        Args:
            X_train: DataFrame с признаками обучающей выборки
        """
        logger.info("Инициализация статистики из обучающей выборки")
        
        self.train_stats = {}
        
        for feature in X_train.columns:
            values = X_train[feature].values
            
            self.train_stats[feature] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'median': float(np.median(values)),
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'percentiles': {
                    '25': float(np.percentile(values, 25)),
                    '50': float(np.percentile(values, 50)),
                    '75': float(np.percentile(values, 75)),
                },
                'histogram': self._compute_histogram(values),
            }
        
        self.is_initialized = True
        logger.info(f"Статистика инициализирована для {len(self.train_stats)} признаков")
    
    def check_drift(self, X_new: pd.DataFrame) -> DriftReport:
        """
        Проверяет дрейф в новых данных.
        
        Args:
            X_new: DataFrame с новыми признаками
            
        Returns:
            DriftReport с результатами проверки
        """
        if not self.is_initialized:
            logger.warning("Мониторинг не инициализирован, возвращаем False")
            return DriftReport(
                has_drift=False,
                psi_values={},
                ks_values={},
                drifted_features=[],
                timestamp=datetime.now().isoformat(),
                recommendation="Мониторинг не инициализирован"
            )
        
        logger.info(f"Проверка дрейфа для {len(X_new)} примеров")
        
        psi_values = {}
        ks_values = {}
        drifted_features = []
        
        # Проверяем ключевые фичи
        features_to_check = self.config.key_features
        if not features_to_check:
            features_to_check = list(X_new.columns)
        
        for feature in features_to_check:
            if feature not in X_new.columns or feature not in self.train_stats:
                continue
            
            train_values = self._reconstruct_distribution(feature)
            new_values = X_new[feature].values
            
            # PSI
            psi = self._calculate_psi(train_values, new_values)
            psi_values[feature] = psi
            
            # KS-test
            ks_stat, ks_pvalue = stats.ks_2samp(train_values, new_values)
            ks_values[feature] = ks_stat
            
            # Проверяем пороги
            if psi > self.config.psi_threshold or ks_stat > self.config.ks_threshold:
                drifted_features.append(feature)
                logger.warning(
                    f"Дрейф обнаружен в {feature}: PSI={psi:.4f}, KS={ks_stat:.4f}"
                )
        
        has_drift = len(drifted_features) > 0
        
        # Рекомендация
        if has_drift:
            if len(drifted_features) > len(features_to_check) * 0.5:
                recommendation = "КРИТИЧЕСКИЙ дрейф. Немедленное переобучение рекомендуется."
            else:
                recommendation = "Обнаружен дрейф. Планируется переобучение модели."
        else:
            recommendation = "Дрейф не обнаружен. Модель стабильна."
        
        report = DriftReport(
            has_drift=has_drift,
            psi_values=psi_values,
            ks_values=ks_values,
            drifted_features=drifted_features,
            timestamp=datetime.now().isoformat(),
            recommendation=recommendation
        )
        
        logger.info(f"Результат проверки дрейфа: {report.recommendation}")
        
        return report
    
    def _compute_histogram(self, values: np.ndarray, bins: int = 10) -> List[float]:
        """Вычисляет гистограмму для PSI."""
        hist, _ = np.histogram(values, bins=bins, range=(np.min(values), np.max(values)))
        # Нормализуем
        hist = hist / (hist.sum() + 1e-8)
        return hist.tolist()
    
    def _reconstruct_distribution(self, feature: str) -> np.ndarray:
        """Реконструирует распределение из статистики."""
        if feature not in self.train_stats:
            return np.array([])
        
        stats_data = self.train_stats[feature]
        
        # Генерируем данные из нормального распределения с известными параметрами
        mean = stats_data['mean']
        std = stats_data['std']
        
        # Генерируем 1000 точек
        return np.random.normal(mean, std, 1000)
    
    def _calculate_psi(self, train_dist: np.ndarray, new_dist: np.ndarray) -> float:
        """
        Вычисляет Population Stability Index (PSI).
        
        PSI < 0.1: нет значимых изменений
        0.1 <= PSI < 0.2: умеренные изменения
        PSI >= 0.2: значительные изменения
        """
        if len(train_dist) == 0 or len(new_dist) == 0:
            return 0.0
        
        # Создаём бины
        bins = 10
        min_val = min(np.min(train_dist), np.min(new_dist))
        max_val = max(np.max(train_dist), np.max(new_dist))
        
        # Гистограммы
        train_hist, _ = np.histogram(train_dist, bins=bins, range=(min_val, max_val))
        new_hist, _ = np.histogram(new_dist, bins=bins, range=(min_val, max_val))
        
        # Нормализуем
        train_hist = train_hist / (train_hist.sum() + 1e-8)
        new_hist = new_hist / (new_hist.sum() + 1e-8)
        
        # Добавляем epsilon для избежания log(0)
        epsilon = 1e-4
        train_hist = np.clip(train_hist, epsilon, None)
        new_hist = np.clip(new_hist, epsilon, None)
        
        # PSI
        psi = np.sum((new_hist - train_hist) * np.log(new_hist / train_hist))
        
        return float(psi)
    
    def save_train_stats(self, path: str) -> None:
        """
        Сохраняет статистику обучающей выборки.
        
        Args:
            path: Путь к файлу
        """
        if not self.is_initialized:
            logger.warning("Статистика не инициализирована")
            return
        
        # Создаём директорию
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.train_stats, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Статистика сохранена в {path}")
    
    def load_train_stats(self, path: str) -> bool:
        """
        Загружает статистику обучающей выборки.
        
        Args:
            path: Путь к файлу
            
        Returns:
            True если загрузка успешна
        """
        if not os.path.exists(path):
            logger.warning(f"Файл статистики не найден: {path}")
            return False
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.train_stats = json.load(f)
            
            self.is_initialized = True
            logger.info(f"Статистика загружена из {path}")
            return True
        
        except Exception as e:
            logger.error(f"Ошибка загрузки статистики: {e}")
            return False
