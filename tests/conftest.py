"""
Конфигурация pytest для тестов.

Этот файл настраивает пути импорта и фикстуры для всех тестов.
"""

import sys
from pathlib import Path

# Добавляем папку polymarket_ml в путь для импортов
polymarket_ml_path = Path(__file__).parent.parent / 'polymarket_ml'
if str(polymarket_ml_path) not in sys.path:
    sys.path.insert(0, str(polymarket_ml_path))

# Теперь тесты могут импортировать из ml_oracle
# from ml_oracle import FeatureExtractor, MLOracle, ModelMonitor
