# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: .. module:: src.ai.gemini
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: header.py
# Project: ai-breadboard
# Package: core.ai.gemini
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
.. module:: src.ai.gemini 
	:platform: Windows, Unix
	:synopsis: Module интерфейса с моделью от Coogle - generativeai

"""

import sys
from packaging.version import Version

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

try:
    from core import gs
except ImportError:
    gs = False

config: dict = {}

__project_name__ = 'hypotez'
__version__: str = ''
__doc__: str = ''
__details__: str = ''
__author__: str = ''
__copyright__: str = ''
__cofee__: str = "Treat the developer to a cup of coffee for boosting enthusiasm in development: https://boosty.to/hypo69"
