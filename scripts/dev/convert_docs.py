# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Root - Convert Docs
# =============================================================================
# Description:
#   Скрипт/модуль системы AI-Breadboard (`convert_docs`).
#
# Usage Examples:
#   Python API:
#     from convert_docs import convert_readme
#
#     res = convert_readme()
#
# File: convert_docs.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:20:26
# =============================================================================

"""Скрипт/модуль системы AI-Breadboard (`convert_docs`)."""

import os
import re

def convert_readme(readme_path, target_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.split('\n')
    title = lines[0].replace('#', '').strip()
    formatted_content = f'# {title}\n\n'
    sections = {'Назначение': '', 'Структура': '', 'Запуск': '', 'API': ''}
    current_section = None
    for line in lines[1:]:
        if line.startswith('## '):
            section_name = line.replace('##', '').strip()
            if 'Назначение' in section_name:
                current_section = 'Назначение'
            elif 'Структура' in section_name:
                current_section = 'Структура'
            elif 'Запуск' in section_name:
                current_section = 'Запуск'
            elif 'API' in section_name:
                current_section = 'API'
            else:
                current_section = None
        elif current_section:
            sections[current_section] += line + '\n'
    for section, text in sections.items():
        if text:
            formatted_content += f'## {section}\n{text}\n'
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(formatted_content)
apps_dir = 'apps'
docs_apps_dir = 'docs/ru/guides/apps'
for app in os.listdir(apps_dir):
    app_path = os.path.join(apps_dir, app)
    if os.path.isdir(app_path):
        readme = os.path.join(app_path, 'README.md')
        if os.path.exists(readme):
            convert_readme(readme, os.path.join(docs_apps_dir, f'{app}.md'))