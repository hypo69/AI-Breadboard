# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Process_Manager -   Init  
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.process_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""# Description:"""

from apps.windows.sdk.modules.process_manager.core.manager import ProcessManager
from apps.windows.sdk.modules.process_manager.core.models import (
    ProcessItem,
    ProcessKillRequest,
    ProcessReport,
)
from apps.windows.sdk.modules.process_manager.router import init_router
from apps.windows.sdk.modules.process_manager.tui import ProcessManagerTUI

__all__ = [
    'ProcessManager',
    'ProcessManagerTUI',
    'init_router',
    'ProcessItem',
    'ProcessReport',
    'ProcessKillRequest',
]
