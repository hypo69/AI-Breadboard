# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telemetry Research Application Main Entry
# =============================================================================
# Description:
#   Точка входа запуска приложения исследования телеметрии при вызове
#   python -m apps.telemetry_research.
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Точка входа модуля исследования телеметрии."""

import sys
from apps.telemetry_research.cli import main

if __name__ == "__main__":
    sys.exit(main())
