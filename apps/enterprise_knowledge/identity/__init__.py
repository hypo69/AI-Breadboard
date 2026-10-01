# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Enterprise_Knowledge Identity -   Init  
# =============================================================================
# Description:
#   Управление идентичностью сотрудников.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.enterprise_knowledge.identity
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Управление идентичностью сотрудников."""

from apps.enterprise_knowledge.identity.registry import IdentityRegistry
from apps.enterprise_knowledge.identity.resolution import IdentityResolver
from apps.enterprise_knowledge.identity.aliases import AliasManager
from apps.enterprise_knowledge.identity.verification import IdentityVerifier
__all__ = ['IdentityRegistry', 'IdentityResolver', 'AliasManager', 'IdentityVerifier']