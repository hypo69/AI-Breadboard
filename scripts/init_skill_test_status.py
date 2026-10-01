# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Scripts - Init Skill Test Status
# =============================================================================
# Description:
#   Скрипт/модуль системы AI-Breadboard (`init_skill_test_status`).
#
# Usage Examples:
#   Python API:
#     import scripts.init_skill_test_status as init_skill_test_status
#
# File: init_skill_test_status.py
# Project: ai-breadboard
# Package: scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:27:07
# =============================================================================

"""Скрипт/модуль системы AI-Breadboard (`init_skill_test_status`)."""

import json
import os
from pathlib import Path
skills_dir = Path('.skills')
status_file = skills_dir / 'test_status.json'
if not status_file.exists():
    status_data = {'skills': {}}
    for skill in [d.name for d in skills_dir.iterdir() if d.is_dir()]:
        status_data['skills'][skill] = {'status': 'pending', 'last_run': None}
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, indent=4, ensure_ascii=False)
    print(f'Файл статуса тестов создан: {status_file}')
else:
    print('Файл статуса тестов уже существует.')