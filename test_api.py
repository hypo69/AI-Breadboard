#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test API Endpoint
# =============================================================================
# Description:
#   Тест эндпоинта /api/keys/
#
# File: test_api.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 15:06:00
# =============================================================================

import urllib.request
import json

try:
    req = urllib.request.Request('http://localhost:8001/api/keys/')
    req.add_header('Content-Type', 'application/json')
    
    with urllib.request.urlopen(req, timeout=5) as response:
        content = response.read().decode()
        print(f"Status: {response.status}")
        print(f"Content: {content}")
        
        data = json.loads(content) if content else []
        print(f"Parsed data type: {type(data)}")
        print(f"Number of keys: {len(data)}")
        if data:
            print(f"First key: {data[0]}")
except Exception as e:
    print(f"Error: {e}")
