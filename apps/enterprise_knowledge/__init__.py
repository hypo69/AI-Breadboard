# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Enterprise_Knowledge -   Init  
# =============================================================================
# Description:
#   Накопительная платформа корпоративных знаний.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.enterprise_knowledge
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Накопительная платформа корпоративных знаний."""

from apps.enterprise_knowledge.engine import EnterpriseKnowledgeEngine
from apps.enterprise_knowledge.storage import KnowledgeStore
__all__ = ['EnterpriseKnowledgeEngine', 'KnowledgeStore']