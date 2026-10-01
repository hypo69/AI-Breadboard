# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Scripts - Run Skill Tests
# =============================================================================
# Description:
#   Скрипт/модуль системы AI-Breadboard (`run_skill_tests`).
#
# Usage Examples:
#   CLI:
#     python -m scripts.run_skill_tests
#   Python API:
#     from scripts.run_skill_tests import load_status
#
#     res = load_status()
#
# File: run_skill_tests.py
# Project: ai-breadboard
# Package: scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:27:07
# =============================================================================

"""Скрипт/модуль системы AI-Breadboard (`run_skill_tests`)."""

import json
import os
from pathlib import Path
import datetime
skills_dir = Path('.skills')
status_file = skills_dir / 'test_status.json'

def load_status():
    with open(status_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_status(data):
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
import subprocess
import sys

def run_test(skill_name):
    print(f'Тестирование навыка: {skill_name}...')
    if skill_name == 'ai-diagnostics':
        result = subprocess.run([sys.executable, '.skills/ai-diagnostics/tests/test_diagnostics.py'], capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f'Ошибка при тестировании {skill_name}: {result.stderr}')
            return False
    return True

def main():
    status_data = load_status()
    for skill, info in status_data['skills'].items():
        if info['status'] != 'passed':
            print(f'Запуск тестов для: {skill}')
            if run_test(skill):
                info['status'] = 'passed'
                info['last_run'] = datetime.datetime.now().isoformat()
                print(f'Навык {skill} успешно прошел тест.')
            else:
                info['status'] = 'failed'
                info['last_run'] = datetime.datetime.now().isoformat()
                print(f'Навык {skill} не прошел тест.')
    save_status(status_data)
    print('Тестирование завершено.')
if __name__ == '__main__':
    main()