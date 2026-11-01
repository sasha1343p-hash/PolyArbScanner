"""
Скрипт для генерации отчёта о тестировании.

Запускает все тесты и создаёт структурированный отчёт.
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime


def run_command(cmd: list) -> tuple:
    """Запускает команду и возвращает (success, output)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 минут таймаут
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT: Test execution exceeded 5 minutes"
    except Exception as e:
        return False, f"ERROR: {str(e)}"


def check_prerequisites() -> dict:
    """Проверяет необходимые компоненты."""
    checks = {}
    
    # Проверка Python
    checks['python'] = {
        'name': 'Python version',
        'status': False,
        'details': ''
    }
    success, output = run_command([sys.executable, '--version'])
    if success:
        checks['python']['status'] = True
        checks['python']['details'] = output.strip()
    
    # Проверка виртуального окружения
    checks['venv'] = {
        'name': 'Virtual environment',
        'status': False,
        'details': ''
    }
    venv_path = Path('venv')
    if venv_path.exists():
        checks['venv']['status'] = True
        checks['venv']['details'] = 'venv directory exists'
    
    # Проверка зависимостей
    checks['dependencies'] = {
        'name': 'Dependencies installed',
        'status': False,
        'details': ''
    }
    success, output = run_command([
        sys.executable, '-c',
        'import pandas, numpy, sklearn, xgboost, lightgbm; print("OK")'
    ])
    if success and 'OK' in output:
        checks['dependencies']['status'] = True
        checks['dependencies']['details'] = 'All dependencies installed'
    
    # Проверка базы данных
    checks['database'] = {
        'name': 'Database exists',
        'status': False,
        'details': ''
    }
    db_path = Path('../polymarket_history.db')
    if db_path.exists():
        checks['database']['status'] = True
        checks['database']['details'] = f'Database size: {db_path.stat().st_size / 1024:.1f} KB'
    
    # Проверка обученной модели
    checks['model'] = {
        'name': 'Model trained',
        'status': False,
        'details': ''
    }
    model_path = Path('artifacts/ml_oracle_bundle.pkl')
    if model_path.exists():
        checks['model']['status'] = True
        checks['model']['details'] = f'Model size: {model_path.stat().st_size / 1024 / 1024:.1f} MB'
    
    return checks


def run_tests() -> dict:
    """Запускает тесты и возвращает результаты."""
    results = {
        'unit_tests': {
            'name': 'Unit tests',
            'status': False,
            'output': '',
            'passed': 0,
            'failed': 0,
            'total': 0
        },
        'integration_tests': {
            'name': 'Integration tests',
            'status': False,
            'output': '',
            'passed': 0,
            'failed': 0,
            'total': 0
        },
        'coverage': {
            'name': 'Code coverage',
            'status': False,
            'output': '',
            'percentage': 0.0
        }
    }
    
    # Unit tests
    print("Running unit tests...")
    success, output = run_command([
        sys.executable, '-m', 'pytest',
        'tests/test_feature_extractor.py',
        'tests/test_model.py',
        '-v', '--tb=short'
    ])
    results['unit_tests']['status'] = success
    results['unit_tests']['output'] = output
    
    # Парсим результаты
    for line in output.split('\n'):
        if 'passed' in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if part == 'passed':
                    results['unit_tests']['passed'] = int(parts[i-1])
                elif part == 'failed':
                    results['unit_tests']['failed'] = int(parts[i-1])
    
    results['unit_tests']['total'] = results['unit_tests']['passed'] + results['unit_tests']['failed']
    
    # Integration tests
    print("Running integration tests...")
    success, output = run_command([
        sys.executable, '-m', 'pytest',
        'tests/test_integration.py',
        '-v', '--tb=short'
    ])
    results['integration_tests']['status'] = success
    results['integration_tests']['output'] = output
    
    # Парсим результаты
    for line in output.split('\n'):
        if 'passed' in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if part == 'passed':
                    results['integration_tests']['passed'] = int(parts[i-1])
                elif part == 'failed':
                    results['integration_tests']['failed'] = int(parts[i-1])
    
    results['integration_tests']['total'] = results['integration_tests']['passed'] + results['integration_tests']['failed']
    
    # Coverage
    print("Generating coverage report...")
    success, output = run_command([
        sys.executable, '-m', 'pytest',
        'tests/',
        '--cov=ml_oracle',
        '--cov-report=term-missing'
    ])
    results['coverage']['status'] = success
    results['coverage']['output'] = output
    
    # Парсим coverage
    for line in output.split('\n'):
        if 'TOTAL' in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if '%' in part:
                    try:
                        results['coverage']['percentage'] = float(part.rstrip('%'))
                    except:
                        pass
    
    return results


def generate_report() -> dict:
    """Генерирует полный отчёт."""
    print("=" * 60)
    print("  PolyArb ML Oracle - Test Report Generator")
    print("=" * 60)
    print()
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'prerequisites': {},
        'tests': {},
        'summary': {
            'all_checks_passed': False,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'coverage': 0.0
        }
    }
    
    # Проверка prerequisites
    print("[1/2] Checking prerequisites...")
    report['prerequisites'] = check_prerequisites()
    
    # Запуск тестов
    print("\n[2/2] Running tests...")
    report['tests'] = run_tests()
    
    # Подсчёт итогов
    total = 0
    passed = 0
    failed = 0
    
    for test_type in ['unit_tests', 'integration_tests']:
        total += report['tests'][test_type]['total']
        passed += report['tests'][test_type]['passed']
        failed += report['tests'][test_type]['failed']
    
    report['summary']['total_tests'] = total
    report['summary']['passed_tests'] = passed
    report['summary']['failed_tests'] = failed
    report['summary']['coverage'] = report['tests']['coverage']['percentage']
    
    # Проверка, все ли проверки пройдены
    all_prereq_passed = all(check['status'] for check in report['prerequisites'].values())
    all_tests_passed = failed == 0
    coverage_ok = report['summary']['coverage'] >= 80.0
    
    report['summary']['all_checks_passed'] = all_prereq_passed and all_tests_passed and coverage_ok
    
    return report


def print_report(report: dict):
    """Выводит отчёт в консоль."""
    print()
    print("=" * 60)
    print("  TEST REPORT")
    print("=" * 60)
    print()
    
    # Prerequisites
    print("PREREQUISITES:")
    for key, check in report['prerequisites'].items():
        status = "✓ PASS" if check['status'] else "✗ FAIL"
        print(f"  [{status}] {check['name']}: {check['details']}")
    print()
    
    # Tests
    print("TESTS:")
    for test_type in ['unit_tests', 'integration_tests']:
        test = report['tests'][test_type]
        status = "✓ PASS" if test['status'] else "✗ FAIL"
        print(f"  [{status}] {test['name']}: {test['passed']}/{test['total']} passed")
    
    # Coverage
    coverage = report['tests']['coverage']
    status = "✓ PASS" if coverage['percentage'] >= 80 else "✗ FAIL"
    print(f"  [{status}] Code coverage: {coverage['percentage']:.1f}%")
    print()
    
    # Summary
    print("SUMMARY:")
    print(f"  Total tests:    {report['summary']['total_tests']}")
    print(f"  Passed:         {report['summary']['passed_tests']}")
    print(f"  Failed:         {report['summary']['failed_tests']}")
    print(f"  Coverage:       {report['summary']['coverage']:.1f}%")
    print()
    
    if report['summary']['all_checks_passed']:
        print("=" * 60)
        print("  ✓ ALL CHECKS PASSED!")
        print("=" * 60)
    else:
        print("=" * 60)
        print("  ✗ SOME CHECKS FAILED - See details above")
        print("=" * 60)
    print()


def save_report(report: dict, filename: str = 'test_report.json'):
    """Сохраняет отчёт в JSON файл."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Report saved to: {filename}")


def main():
    """Главная функция."""
    report = generate_report()
    print_report(report)
    save_report(report)
    
    # Возвращаем код выхода
    sys.exit(0 if report['summary']['all_checks_passed'] else 1)


if __name__ == '__main__':
    main()
