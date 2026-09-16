# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: System Control Center Microservice Application
# =============================================================================
# Description:
#   Инициализация пакета микросервиса Центра управления системой Windows.
#
# File: __init__.py
# Project: AI-Breadboard
# Package: apps.system_control_center
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Пакет микросервиса Центра управления системой Windows."""

from .router import init_router, router

__all__ = ["init_router", "router"]
