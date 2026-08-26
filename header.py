## \file header.py
# -*- coding: utf-8 -*-
#! .pyenv/bin/python3

"""
.. module:: .header
	:platform: Windows, Unix
	:synopsis: Module defining the root path to the project. All imports are built relative to this path.
"""

import os
import sys
from pathlib import Path

def set_project_root(marker_files=('__root__','.git')) -> Path:
    """
    Finds the root directory of the project starting from the current file's directory,
    searching upwards and stopping at the first directory containing any of the marker files.
    Also respects the AIBREADBOARD_DIR environment variable if present.

    Args:
        marker_files (tuple): Filenames or directory names to identify the project root.
    
    Returns:
        Path: Path to the root directory if found, otherwise the directory where the script is located.
    """
    env_dir = os.environ.get("AIBREADBOARD_DIR", "")
    if env_dir:
        env_path = Path(env_dir).resolve()
        if env_path.exists() and (env_path / "config.json").exists():
            if str(env_path) not in sys.path:
                sys.path.insert(0, str(env_path))
            return env_path

    __root__: Path
    current_path: Path = Path(__file__).resolve().parent
    __root__ = current_path
    for parent in [current_path] + list(current_path.parents):
        if any((parent / marker).exists() for marker in marker_files):
            __root__ = parent
            break
    if str(__root__) not in sys.path:
        sys.path.insert(0, str(__root__))
    return __root__


# Get the root directory of the project
__root__: Path = set_project_root()
"""__root__ (Path): Path to the root directory of the project"""

