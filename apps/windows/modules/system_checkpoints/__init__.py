# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules System_Checkpoints -   Init  
# =============================================================================
# Description:
#   Пакет управления контрольными точками системы и образами восстановления Windows.
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.modules.system_checkpoints
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Пакет управления контрольными точками системы и образами восстановления Windows."""

from apps.windows.system_checkpoints.models import (
    CheckpointType,
    RecoveryMechanism,
    FreshnessLevel,
    SystemDriftMetrics,
    FreshnessReport,
    WinREStatus,
    SystemImageMetadata,
    SystemCheckpointRecord,
    CheckpointCreateRequest,
    WimImageCreateRequest,
    WinREActionRequest,
)
from apps.windows.system_checkpoints.core.winre_manager import WinREManager
from apps.windows.system_checkpoints.core.image_manager import SystemImageManager
from apps.windows.system_checkpoints.core.freshness_auditor import FreshnessAuditor
from apps.windows.system_checkpoints.core.checkpoint_coordinator import CheckpointCoordinator
from apps.windows.system_checkpoints.router import router, init_router

__all__ = [
    "CheckpointType",
    "RecoveryMechanism",
    "FreshnessLevel",
    "SystemDriftMetrics",
    "FreshnessReport",
    "WinREStatus",
    "SystemImageMetadata",
    "SystemCheckpointRecord",
    "CheckpointCreateRequest",
    "WimImageCreateRequest",
    "WinREActionRequest",
    "WinREManager",
    "SystemImageManager",
    "FreshnessAuditor",
    "CheckpointCoordinator",
    "router",
    "init_router",
]
