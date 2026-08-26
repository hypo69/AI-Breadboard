#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для запуска тестов ai-assistant
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_tests(coverage=False, verbose=False, markers=None):
    """Запуск тестов."""
    cmd = ["pytest"]
    
    # Покрытие
    if coverage:
        cmd.extend([
            "--cov=src",
            "--cov=plugins",
            "--cov=scripts",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml",
            "--cov-config=.coveragerc"
        ])
    
    # Верbose
    if verbose:
        cmd.append("-v")
    
    # Маркеры
    if markers:
        cmd.extend(["-m", markers])
    
    # Запуск
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def show_coverage():
    """Показ отчета о покрытии."""
    html_path = Path("htmlcov") / "index.html"
    if html_path.exists():
        import webbrowser
        webbrowser.open(f"file://{html_path.absolute()}")
    else:
        print("HTML отчет не найден. Запустите тесты с --coverage")


def main():
    parser = argparse.ArgumentParser(description="Запуск тестов ai-ai-assistant")
    parser.add_argument("--coverage", "-c", action="store_true", help="С покрытием")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose вывод")
    parser.add_argument("--markers", "-m", type=str, help="Маркеры pytest (unit, integration, slow)")
    parser.add_argument("--open-coverage", "-o", action="store_true", help="Открыть HTML отчет")
    
    args = parser.parse_args()
    
    if args.open_coverage:
        show_coverage()
        return
    
    exit_code = run_tests(
        coverage=args.coverage,
        verbose=args.verbose,
        markers=args.markers
    )
    
    if exit_code == 0:
        print("\n✓ Все тесты пройдены успешно!")
    else:
        print(f"\n✗ Тесты провалились (exit code: {exit_code})")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
