# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Database Migration Management Package
# =============================================================================
# Description:
#   Package for SQLite database schema versioning, migrations and backups.
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.db
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Пакет управления миграциями баз данных SQLite."""

from src.db.migrations import MigrationManager

__all__ = ["MigrationManager"]
