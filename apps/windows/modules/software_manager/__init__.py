# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Software_Manager -   Init  
# =============================================================================
# Description:
#   # Description:
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: apps.windows.modules.software_manager
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""# Description:"""

from apps.windows.modules.software_manager.core.manager import SoftwarePackagesManager
from apps.windows.modules.software_manager.core.models import (
    InstalledPackage,
    PackageActionRequest,
    SoftwareReport,
)
from apps.windows.modules.software_manager.router import init_router
from apps.windows.modules.software_manager.tui import SoftwareManagerTUI

__all__ = [
    'SoftwarePackagesManager',
    'SoftwareManagerTUI',
    'init_router',
    'InstalledPackage',
    'PackageActionRequest',
    'SoftwareReport',
]
