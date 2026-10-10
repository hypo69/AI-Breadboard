# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Native - IP Helper API
# =============================================================================
# Description:
#   Win32 C-FFI вызовы к iphlpapi.dll (сетевые соединения, сокеты, интерфейсы).
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.native.iphlpapi import get_extended_tcp_table, get_extended_udp_table
#
# File: iphlpapi.py
# Project: ai-breadboard
# Package: apps.windows.sdk.native
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 09:36:00
# =============================================================================

from __future__ import annotations
"""Экспорт Win32 IP Helper API (iphlpapi.dll) для сетевой аналитики и сокетов процессов."""

from apps.windows.sdk.native.nethelper import *
