# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Project root directory resolver
# =============================================================================
# Description:
#   Module for finding and setting the project root path. All imports built
#   relative to this root directory. Uses marker files (.git, __root__) to identify project root.
#
# File: header.py
# Project: ai-breadboard
# Package: core.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sys

from pathlib import Path
def set_project_root(marker_files=('__root__','.git')) -> Path:
    """
    Finds the root directory of the project starting from the current file's directory,
    searching upwards and stopping at the first directory containing any of the marker files.

    Args:
        marker_files (tuple): Filenames or directory names to identify the project root.
    
    Returns:
        Path: Path to the root directory if found, otherwise the directory where the script is located.
    """
    __root__:Path
    current_path:Path = Path(__file__).resolve().parent
    __root__ = current_path
    for parent in [current_path] + list(current_path.parents):
        if any((parent / marker).exists() for marker in marker_files):
            __root__ = parent
            break
    if __root__ not in sys.path:
        sys.path.insert(0, str(__root__))
    return __root__

# Get the root directory of the project
__root__: Path = set_project_root()
"""__root__ (Path): Path to the root directory of the project"""
