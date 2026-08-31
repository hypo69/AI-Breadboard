# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Generate code coverage analysis reports
# =============================================================================
# Description:
#   Generates coverage analysis reports for project tests. Produces terminal
#   summary, HTML report, and XML report. Can check against coverage threshold.
#
# File: generate_coverage_report.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Code coverage report generation utility.

Generates comprehensive coverage analysis reports including terminal output,
HTML report, and XML format. Supports threshold checking."""

import os
import sys
from pathlib import Path
import json

def generate_coverage_report():
    """Generate code coverage report.
    
    Generates terminal report, HTML report, and XML report using coverage.py.
    
    Returns:
        0 if successful, 1 if error.
    """
    try:
        import coverage
        
        cov = coverage.Coverage(config_file='.coveragerc')
        cov.load()
        
        # Results summary
        cov.report(show_missing=True)
        
        # HTML report
        html_dir = Path('htmlcov')
        html_dir.mkdir(exist_ok=True)
        cov.html_report(directory=str(html_dir))
        
        # XML report
        cov.xml_report(outfile='coverage.xml')
        
        print(f"\nOK: Coverage report generated")
        print(f"  HTML: {html_dir / 'index.html'}")
        print(f"  XML: coverage.xml")
        
        return 0
        
    except ImportError:
        print("ERROR: coverage not installed. Install: pip install coverage")
        return 1
    except Exception as e:
        print(f"ERROR: Error generating report: {e}")
        return 1

def check_coverage_threshold(threshold=80):
    """Check if coverage meets minimum threshold.
    
    Args:
        threshold: Minimum coverage percentage required (default 80).
        
    Returns:
        0 if threshold met, 1 if not met or error.
    """
    try:
        import coverage
        
        cov = coverage.Coverage(config_file='.coveragerc')
        cov.load()
        
        _, missing, total, percentage = cov.report()
        
        print(f"\nCode coverage: {percentage:.1f}%")
        print(f"Minimum required: {threshold}%")
        
        if percentage >= threshold:
            print("OK: Coverage threshold met")
            return 0
        else:
            print(f"ERROR: Coverage threshold NOT met (need {threshold - percentage:.1f}% more)")
            return 1
            
    except ImportError:
        print("ERROR: coverage not installed")
        return 1

def main():
    """Main function."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate code coverage reports")
    parser.add_argument("--threshold", "-t", type=float, default=80, help="Coverage threshold percentage")
    parser.add_argument("--check", "-c", action="store_true", help="Only check threshold")
    parser.add_argument("--report", "-r", action="store_true", help="Generate report")
    
    args = parser.parse_args()
    
    if args.check:
        return check_coverage_threshold(args.threshold)
    
    if args.report:
        return generate_coverage_report()
    
    # Default - check first, then generate report
    check_result = check_coverage_threshold(args.threshold)
    report_result = generate_coverage_report()
    
    return max(check_result, report_result)

if __name__ == "__main__":
    sys.exit(main())
