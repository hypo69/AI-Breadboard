# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Project root directory resolver
# =============================================================================
# Description:
#   Module for finding and setting the project root path. All imports built
#   relative to this root directory. Uses marker files (.git, __root__) to identify project root.
#
# File: header.py
# Project: ai-breadboard
# Package: src.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from header import __root__, set_project_root

__all__ = ['__root__', 'set_project_root']

