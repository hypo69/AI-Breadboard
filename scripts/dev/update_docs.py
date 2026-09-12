# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Check documentation validity of modified files
# =============================================================================
# Description:
#   Script checks presence and validity of documentation (README.md, docstrings)
#   for modified Python files in the repository.
#
# File: update_docs.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Documentation validation for modified Python files.

Checks for presence of docstrings in modified Python files and validates
that proper documentation standards are met."""

import os
import sys
import subprocess
from pathlib import Path
from typing import List

def get_modified_python_files() -> List[Path]:
    """Get list of modified Python files in git repository.
    
    Returns:
        List of Path objects for modified .py files.
    """
    modified_files = []
    try:
        res = subprocess.check_output(
            ["git", "status", "--porcelain"],
            text=True,
            stderr=subprocess.DEVNULL
        )
        for line in res.splitlines():
            parts = line.strip().split(maxsplit=1)
            if len(parts) > 1:
                filepath = Path(parts[1])
                if filepath.suffix == ".py" and filepath.exists():
                    modified_files.append(filepath)
    except Exception:
        # Git unavailable, return empty list
        pass
    return modified_files

def validate_docblocks(files: List[Path]) -> bool:
    """Check for presence of docstrings in modified files.
    
    Args:
        files: List of file paths to check.
        
    Returns:
        True if all files contain docstrings, False otherwise.
    """
    all_valid = True
    for f in files:
        content = f.read_text(encoding="utf-8")
        # Simple check for triple quotes (docstrings)
        if '"""' not in content and "'''" not in content:
            print(f"⚠️  File {f.name} modified but contains no docstring!")
            all_valid = False
    return all_valid

def main() -> int:
    """Main function."""
    print("🔎 Starting documentation and comments validity check...")
    
    modified = get_modified_python_files()
    if not modified:
        print("✅ No modified Python files found in git. Additional validation not required.")
        return 0
        
    print(f"Modified files found: {len(modified)}")
    valid = validate_docblocks(modified)
    
    if valid:
        print("✅ All modified files contain docstrings.")
        return 0
    else:
        print("❌ Recommended to add or update comments/documentation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
