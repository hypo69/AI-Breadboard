#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Keys Loading
# =============================================================================
# Description:
#   Тест загрузки ключей через router_keys
#
# File: test_keys3.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 15:02:00
# =============================================================================

from src.api.routers.core.router_keys import _load_keys_from_file

print("Testing _load_keys_from_file()...")
keys = _load_keys_from_file()
print(f"Result type: {type(keys)}")
print(f"Result length: {len(keys)}")
if keys:
    print(f"First key: {keys[0]}")
else:
    print("WARNING: No keys loaded!")
