# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Backward Compatibility Shim for Legacy Core Imports
# =============================================================================
# Description:
#   Compatibility layer that routes legacy 'core.*' imports to the renamed 'src.*' package.
#
# File: __init__.py
# Project: ai-breadboard
# Package: core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Backward compatibility bridge for legacy imports.

Redirects any import referencing 'core.*' to 'src.*' with submodule path mapping.
"""

from __future__ import annotations

import sys
from pathlib import Path
import src

# Point core's search path to src directory so submodule imports resolve to src
__path__ = [str(Path(src.__file__).resolve().parent)]
