# -*- coding: utf-8 -*-
# =============================================================================
# AI Breadboard Installer Services
# =============================================================================
# Package: installer/services
# Description: Core installation logic and management classes
# =============================================================================

from .python_detector import PythonDetector
from .python_installer import PythonInstaller
from .environment_manager import EnvironmentManager

__all__ = ['PythonDetector', 'PythonInstaller', 'EnvironmentManager']