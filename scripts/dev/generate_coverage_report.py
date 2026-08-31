# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: # ================================================
# =============================================================================
# Description:
#   Генерация отчета о покрытии."""
#
# File: generate_coverage_report.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Генерация отчета о покрытии кода
"""

import os
import sys
from pathlib import Path
import json

def generate_coverage_report():
    """Генерация отчета о покрытии."""
    try:
        import coverage
        
        cov = coverage.Coverage(config_file='.coveragerc')
        cov.load()
        
        # Результаты
        cov.report(show_missing=True)
        
        # HTML отчет
        html_dir = Path('htmlcov')
        html_dir.mkdir(exist_ok=True)
        cov.html_report(directory=str(html_dir))
        
        # XML отчет
        cov.xml_report(outfile='coverage.xml')
        
        print(f"\nOK: Otchet o pokrytii sgeneryrovan")
        print(f"  HTML: {html_dir / 'index.html'}")
        print(f"  XML: coverage.xml")
        
        return 0
        
    except ImportError:
        print("ERROR: coverage ne ustanovlen. Ustanovite: pip install coverage")
        return 1
    except Exception as e:
        print(f"ERROR: Oshibka geneneracii otcheta: {e}")
        return 1

def check_coverage_threshold(threshold=80):
    """Check порога покрытия."""
    try:
        import coverage
        
        cov = coverage.Coverage(config_file='.coveragerc')
        cov.load()
        
        _, missing, total, percentage = cov.report()
        
        print(f"\nPokritie kodа: {percentage:.1f}%")
        print(f"Minimallno trebuemoe: {threshold}%")
        
        if percentage >= threshold:
            print("OK: Porog pokrytiya dostignut")
            return 0
        else:
            print(f"ERROR: Porog pokrytiya NE dostignut (ne hvataet {threshold - percentage:.1f}%)")
            return 1
            
    except ImportError:
        print("ERROR: coverage ne ustanovlen")
        return 1

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Genneracia otcheta o pokrytii")
    parser.add_argument("--threshold", "-t", type=float, default=80, help="Porog pokrytiya")
    parser.add_argument("--check", "-c", action="store_true", help="Tolko proverka poroga")
    parser.add_argument("--report", "-r", action="store_true", help="Genneracia otcheta")
    
    args = parser.parse_args()
    
    if args.check:
        return check_coverage_threshold(args.threshold)
    
    if args.report:
        return generate_coverage_report()
    
    # Po umolchaniyu - sначala proverka, potom otchet
    check_result = check_coverage_threshold(args.threshold)
    report_result = generate_coverage_report()
    
    return max(check_result, report_result)

if __name__ == "__main__":
    sys.exit(main())
