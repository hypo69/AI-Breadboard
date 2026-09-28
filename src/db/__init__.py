# -*- coding: utf-8 -*-
"""Пакет управления миграциями баз данных SQLite."""
from .migrations import MigrationManager, get_migration_manager

__all__ = ['MigrationManager', 'get_migration_manager']
