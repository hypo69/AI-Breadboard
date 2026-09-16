# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Wikipedia Research App Package Initializer
# =============================================================================
# Description:
#   Package initializer for Wikipedia Research and Model Comparison Laboratory.
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.wikipedia_research
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Wikipedia Research & Model Comparison Application."""

from .engine import WikipediaResearchEngine
from .router import init_router

__all__ = [
    "WikipediaResearchEngine",
    "init_router",
]
