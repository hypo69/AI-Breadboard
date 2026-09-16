# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Inspector Application Module Initialization
# =============================================================================
# Description:
#   Root package initialization for the System & Hardware Inspector application.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.system_inspector
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""System Inspector application package."""

from .router import init_router
from .tui import run_system_inspector

__all__ = [
    "init_router",
    "run_system_inspector",
]
