#!/usr/bin/env python3
"""
Cross-platform установщик PolyArb ML Oracle.

Работает на Windows, Linux и macOS.
Автоматически устанавливает все зависимости и настраивает окружение.

Использование:
    python setup_crossplatform.py
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_header():
    """Выводит заголовок."""
    print()
    print("=" * 60)
    print("  🚀 PolyArb ML Oracle — Кроссплатформенная установка")
    print("=" * 60)
    print()


def print_step(step: int, total: int, message: str):
    """Выводит шаг установки."""
    print(f"\n[{step}/{total}] {message}")


def run_command(cmd: list, check: bool = True) -> bool:
    """
    Запускает команду и возвращает True если успешно.
    
    Args:
        cmd: Команда и аргументы
        check: Проверять ли успешность выполнения
        
    Returns:
        True если команда выполнена успешно
    """
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ Команда не найдена: {cmd[0]}")
        return False


def check_python_version() -> bool:
    """Проверяет версию Python."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"❌ Требуется Python 3.10+, у вас {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies() -> bool:
    """Проверяет наличие необходимых библиотек."""
    try:
        import xgboost
        import lightgbm
        import sklearn
        import pandas
        import numpy
        print("✅ Все библиотеки установлены")
        return True
    except ImportError as e:
        print(f"❌ Не найдена библиотека: {e.name}")
        return False


def install_dependencies() -> bool:
    """Устанавливает зависимости из requirements.txt."""
    print("Установка может занять 2-5 минут...")
    print()
    
    # Обновляем pip
    print("  → Обновление pip...")
    if not run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=False):
        print("⚠️  Не удалось обновить pip, продолжаем...")
    
    # Устанавливаем зависимости
    print("  → Установка зависимостей...")
    if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]):
        return False
    
    print("✅ Зависимости установлены")
    return True


def create_test_database() -> bool:
    """Создаёт тестовую базу данных."""
    db_path = Path("polymarket_history.db")
    
    if db_path.exists():
        print("✅ База данных уже существует")
        return True
    
    print("⚠️  База данных не найдена, создаю тестовую...")
    
    # Импортируем скрипт создания БД
    try:
        from create_test_db import create_test_database
        return create_test_database(str(db_path))
    except ImportError:
        print("❌ Скрипт create_test_db.py не найден")
        return False


def train_model() -> bool:
    """Обучает модель."""
    model_path = Path("artifacts/ml_oracle_bundle.pkl")
    
    if model_path.exists():
        print("✅ Модель уже обучена")
        response = input("Хотите переобучить? (y/n): ").strip().lower()
        if response != 'y':
            return True
    
    print("Обучение может занять 3-5 минут...")
    print()
    
    if not run_command([sys.executable, "ml_oracle.py", "train"]):
        return False
    
    print("✅ Модель обучена")
    return True


def create_marker_files():
    """Создаёт маркерные файлы для отслеживания установки."""
    Path(".deps_installed").touch()
    print("✅ Маркерные файлы созданы")


def print_success():
    """Выводит сообщение об успешной установке."""
    print()
    print("=" * 60)
    print("  ✅ УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 60)
    print()
    print("📊 Доступные команды:")
    print()
    print("  1. Предсказание для рынка:")
    print("     python ml_oracle.py predict market-001")
    print()
    print("  2. Проверка дрейфа:")
    print("     python ml_oracle.py drift-check")
    print()
    print("  3. Важность признаков:")
    print("     python ml_oracle.py feature-importance")
    print()
    print("  4. Запуск веб-дашборда:")
    print("     cd .. && npx serve dist")
    print()
    print("  5. Быстрый запуск всего:")
    if platform.system() == "Windows":
        print("     start_all.bat")
    else:
        print("     ./start_all.sh")
    print()
    print("=" * 60)
    print()


def main():
    """Главная функция."""
    print_header()
    
    total_steps = 6
    current_step = 0
    
    # ШАГ 1: Проверка Python
    current_step += 1
    print_step(current_step, total_steps, "Проверка Python...")
    if not check_python_version():
        sys.exit(1)
    
    # ШАГ 2: Проверка/установка зависимостей
    current_step += 1
    print_step(current_step, total_steps, "Проверка зависимостей...")
    
    if not check_dependencies():
        print()
        response = input("Установить зависимости? (y/n): ").strip().lower()
        if response != 'y':
            print("❌ Установка отменена")
            sys.exit(1)
        
        if not install_dependencies():
            sys.exit(1)
    
    # ШАГ 3: Создание маркерных файлов
    current_step += 1
    print_step(current_step, total_steps, "Создание маркерных файлов...")
    create_marker_files()
    
    # ШАГ 4: Создание тестовой БД
    current_step += 1
    print_step(current_step, total_steps, "Проверка базы данных...")
    if not create_test_database():
        sys.exit(1)
    
    # ШАГ 5: Обучение модели
    current_step += 1
    print_step(current_step, total_steps, "Обучение модели...")
    if not train_model():
        sys.exit(1)
    
    # ШАГ 6: Финальная проверка
    current_step += 1
    print_step(current_step, total_steps, "Финальная проверка...")
    
    if not check_dependencies():
        print("❌ Проверка не пройдена")
        sys.exit(1)
    
    # Успех!
    print_success()
    
    # Предложение сделать тестовое предсказание
    response = input("Сделать тестовое предсказание? (y/n): ").strip().lower()
    if response == 'y':
        print()
        print("Запускаю предсказание для market-001...")
        print()
        run_command([sys.executable, "ml_oracle.py", "predict", "market-001"], check=False)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Установка отменена пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Непредвиденная ошибка: {e}")
        sys.exit(1)
