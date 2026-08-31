# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Convert Excel files to dictionary format
# =============================================================================
# Description:
#   Provides utilities for converting XLS files to dictionary format.
#
# File: xls.py
# Project: ai-breadboard
# Package: core.utils.convertors
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Excel file to dictionary conversion utilities.

Provides functions for converting Excel spreadsheet files to dictionary format
for programmatic access and manipulation."""

from pathlib import Path

from core.utils.xls import read_xls_as_dict, save_xls_file

def xls2dict(xls_file: str | Path) -> dict | None:
    """Convert Excel file to dictionary format.
    
    Args:
        xls_file: Path to Excel file to convert.
        
    Returns:
        Dictionary representation of Excel file data or None if conversion fails.
    """
    return read_xls_as_dict(xls_file = xls_file)
