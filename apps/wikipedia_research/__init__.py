# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Wikipedia_Research -   Init  
# =============================================================================
# Description:
#   Wikipedia Research & Model Comparison Application.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.wikipedia_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Wikipedia Research & Model Comparison Application."""

from .engine import WikipediaResearchEngine
from .router import init_router
__all__ = ['WikipediaResearchEngine', 'init_router']