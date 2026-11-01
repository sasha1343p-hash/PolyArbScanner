"""
Быстрая проверка всех компонентов PolyArb ML Oracle.

Этот скрипт проверяет:
1. Установку зависимостей
2. Наличие базы данных
3. Обученную модель
4. Работоспособность предсказания
5. Запуск тестов

Использование:
    python quick_check.py
"""

import sys
import subprocess
from pathlib import Path


def print_header(text: str):
    """Выводит заголовок."""
    print()
    print("=" * 60)
    print(f"  {text}")
    print("=" * 60)
    print()


def print_step(step: int, total: int, text: str):
    """Выводит шаг проверки."""
    print(f"[{step}/{total}] {text}")


def check_dependencies() -> bool:
    """Проверяет установку зависимостей."""
    try:
        import pandas
        import numpy
        import sklearn
        import xgboost
        import lightgbm
        import scipy
        import joblib
        import yaml
        print("  ✓ All dependencies installed")
        return True
    except ImportError as e:
        print(f"  ✗ Missing dependency: {e.name}")
        return False


def check_database() -> bool:
    """Проверяет наличие базы данных."""
    db_path = Path("../polymarket_history.db")
    if db_path.exists():
        size_mb = db_path.stat().st_size / 1024 / 1024
        print(f"  ✓ Database exists ({size_mb:.1f} MB)")
        return True
    else:
        print("  ✗ Database not found")
        return False


def check_model() -> bool:
    """Проверяет наличие обученной модели."""
    model_path = Path("artifacts/ml_oracle_bundle.pkl")
    if model_path.exists():
        size_mb = model_path.stat().st_size / 1024 / 1024
        print(f"  ✓ Model trained ({size_mb:.1f} MB)")
        return True
    else:
        print("  ✗ Model not trained")
        return False


def check_prediction() -> bool:
    """Проверяет работоспособность предсказания."""
    try:
        from ml_oracle import MLOracle, FeatureExtractor
        from ml_oracle.feature_extractor import MarketMetadata
        import pandas as pd
        import sqlite3
        
        # Загружаем модель
        model = MLOracle()
        if not model.load("artifacts/ml_oracle_bundle.pkl"):
            print("  ✗ Failed to load model")
            return False
        
        # Загружаем данные для теста
        conn = sqlite3.connect("../polymarket_history.db")
        metadata_df = pd.read_sql_query(
            "SELECT * FROM market_metadata LIMIT 1",
            conn
        )
        price_df = pd.read_sql_query(
            f"SELECT * FROM price_history WHERE market_id = '{metadata_df.iloc[0]['id']}' LIMIT 10",
            conn
        )
        conn.close()
        
        if metadata_df.empty or price_df.empty:
            print("  ✗ No test data available")
            return False
        
        # Извлекаем признаки
        extractor = FeatureExtractor()
        extractor.feature_names = model.feature_names
        
        metadata = MarketMetadata(
            id=metadata_df.iloc[0]['id'],
            question=metadata_df.iloc[0]['question'],
            end_date=pd.to_datetime(metadata_df.iloc[0]['end_date']) if pd.notna(metadata_df.iloc[0].get('end_date')) else None,
        )
        
        features = extractor.extract_features(metadata_df.iloc[0]['id'], price_df, metadata)
        
        # Делаем предсказание
        proba = model.predict(features)
        
        if proba is not None and 0 <= proba <= 1:
            print(f"  ✓ Prediction works (probability: {proba:.2%})")
            return True
        else:
            print("  ✗ Prediction failed")
            return False
        
    except Exception as e:
        print(f"  ✗ Prediction error: {e}")
        return False


def check_tests() -> bool:
    """Запускает тесты."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            # Подсчитываем количество тестов
            output = result.stdout
            if "passed" in output:
                print(f"  ✓ All tests passed")
                return True
            else:
                print("  ? Tests completed (check output)")
                return True
        else:
            print("  ✗ Some tests failed")
            print(f"     Run 'pytest tests/ -v' for details")
            return False
        
    except subprocess.TimeoutExpired:
        print("  ✗ Tests timeout (> 2 minutes)")
        return False
    except Exception as e:
        print(f"  ✗ Tests error: {e}")
        return False


def main():
    """Главная функция."""
    print_header("PolyArb ML Oracle - Quick Check")
    
    total_steps = 5
    results = []
    
    # Шаг 1: Проверка зависимостей
    print_step(1, total_steps, "Checking dependencies...")
    results.append(check_dependencies())
    
    # Шаг 2: Проверка базы данных
    print_step(2, total_steps, "Checking database...")
    results.append(check_database())
    
    # Шаг 3: Проверка модели
    print_step(3, total_steps, "Checking model...")
    results.append(check_model())
    
    # Шаг 4: Проверка предсказания
    print_step(4, total_steps, "Checking prediction...")
    results.append(check_prediction())
    
    # Шаг 5: Запуск тестов
    print_step(5, total_steps, "Running tests...")
    results.append(check_tests())
    
    # Итоги
    print_header("Summary")
    
    checks = [
        "Dependencies",
        "Database",
        "Model",
        "Prediction",
        "Tests"
    ]
    
    for check, result in zip(checks, results):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  [{status}] {check}")
    
    print()
    
    if all(results):
        print("=" * 60)
        print("  ✓ ALL CHECKS PASSED!")
        print("=" * 60)
        print()
        print("Your ML Oracle is ready to use!")
        print()
        print("Next steps:")
        print("  - Make prediction: run.bat predict market-001")
        print("  - Start dashboard: start_all.bat")
        print("  - View feature importance: run.bat feature-importance")
        sys.exit(0)
    else:
        print("=" * 60)
        print("  ✗ SOME CHECKS FAILED")
        print("=" * 60)
        print()
        print("Please fix the issues above and try again.")
        print()
        print("For detailed help:")
        print("  - Read: TESTING.md")
        print("  - Read: tests/TESTING_GUIDE.md")
        sys.exit(1)


if __name__ == "__main__":
    main()
