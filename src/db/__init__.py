# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard DB -   Init   Module
# =============================================================================
# Description:
#   Пакет управления миграциями баз данных SQLite.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.db
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Пакет управления миграциями баз данных SQLite."""

from .migrations import MigrationManager, get_migration_manager

__all__ = ['MigrationManager', 'get_migration_manager']
