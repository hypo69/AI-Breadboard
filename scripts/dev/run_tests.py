# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test runner with coverage analysis
# =============================================================================
# Description:
#   Runs project tests with optional coverage analysis and HTML report generation.
#   Supports verbose output, test markers filtering, and coverage report viewing.
#
# File: run_tests.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Test runner script for ai-breadboard project.

Provides command-line interface for running project tests with coverage
analysis, verbose output, and filtering by test markers."""

import subprocess
import sys
import argparse
from pathlib import Path

def run_tests(coverage=False, verbose=False, markers=None):
    """Run project tests.
    
    Args:
        coverage: Include coverage analysis and report generation.
        verbose: Enable verbose test output.
        markers: pytest markers to filter tests (e.g., unit, integration, slow).
        
    Returns:
        pytest return code (0 for success).
    """
    cmd = ["pytest"]
    
    # Coverage
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
    
    # Verbose
    if verbose:
        cmd.append("-v")
    
    # Markers
    if markers:
        cmd.extend(["-m", markers])
    
    # Run
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode

def show_coverage():
    """Display coverage report in browser."""
    html_path = Path("htmlcov") / "index.html"
    if html_path.exists():
        import webbrowser
        webbrowser.open(f"file://{html_path.absolute()}")
    else:
        print("HTML report not found. Run tests with --coverage flag")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run ai-breadboard project tests")
    parser.add_argument("--coverage", "-c", action="store_true", help="Run with coverage analysis")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose test output")
    parser.add_argument("--markers", "-m", type=str, help="pytest markers (unit, integration, slow)")
    parser.add_argument("--open-coverage", "-o", action="store_true", help="Open HTML coverage report")
    
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
        print("\n✓ All tests passed successfully!")
    else:
        print(f"\n✗ Tests failed (exit code: {exit_code})")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
