# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Module
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: scan_headers.py
# Project: ai-breadboard
# Package: .ai.tools.setup
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import re
from pathlib import Path
from typing import Dict, Any, List

def count_words(text: str) -> int:
    """Count words in a string."""
    return len(re.findall(r'\b\w+\b', text))

def extract_description(header_text: str) -> str:
    """Extract Description block text from Python file header."""
    desc_match = re.search(
        r'#\s*Description:\s*\n((?:#\s*.*\n)+?)(?=#\s*(?:File|Project|Author|Copyright|\$|=))',
        header_text,
        re.DOTALL
    )
    if desc_match:
        desc_lines = desc_match.group(1).strip()
        lines = [line.strip().lstrip('#').strip() for line in desc_lines.split('\n')]
        return ' '.join(lines)
    return ''

def check_header(filepath: Path) -> Dict[str, Any]:
    """Verify presence and validity of required file header metadata."""
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception:
        return {'has_header': 'no', 'word_count': 0, 'description': '', 'path': str(filepath)}

    lines = content.split('\n')
    has_coding = False
    header_start = 0
    for i, line in enumerate(lines[:3]):
        if '# -*- coding: utf-8 -*-' in line:
            has_coding = True
            header_start = i
            break

    if not has_coding:
        return {'has_header': 'no', 'word_count': 0, 'description': '', 'path': str(filepath)}

    header_lines = []
    for i in range(header_start, min(len(lines), 50)):
        line = lines[i].strip()
        if not line.startswith('#') and not line.startswith('!') and 'import' not in line.lower():
            break
        header_lines.append(line)

    header_text = '\n'.join(header_lines)
    has_process = bool(re.search(r'#\s*(?:Process Name|Название\s*(?:процесса|модуля)):', header_text, re.IGNORECASE))
    has_desc = bool(re.search(r'#\s*Description:', header_text, re.IGNORECASE))
    has_file = bool(re.search(r'#\s*File:', header_text, re.IGNORECASE))
    has_project = bool(re.search(r'#\s*Project:', header_text, re.IGNORECASE))
    has_author = bool(re.search(r'#\s*Author:', header_text, re.IGNORECASE))
    has_copyright = bool(re.search(r'#\s*Copyright:', header_text, re.IGNORECASE))

    all_present = all([has_process, has_desc, has_file, has_project, has_author, has_copyright])
    if not all_present:
        return {'has_header': 'incomplete', 'word_count': 0, 'description': '', 'path': str(filepath)}

    description = extract_description(header_text)
    word_count = count_words(description)
    return {
        'has_header': 'yes',
        'word_count': word_count,
        'description': description[:200],
        'path': str(filepath)
    }

def main():
    root = Path(__file__).resolve().parents[3]
    py_files = [p for p in root.rglob('*.py') if not any(part.startswith('.') or part in {'venv', '__pycache__', 'dist'} for part in p.parts)]
    print(f"Scanning {len(py_files)} Python files for standard headers...")
    
    valid_count = 0
    incomplete_count = 0
    missing_count = 0

    for f in py_files:
        res = check_header(f)
        if res['has_header'] == 'yes':
            valid_count += 1
        elif res['has_header'] == 'incomplete':
            incomplete_count += 1
        else:
            missing_count += 1

    print(f"Results: Valid={valid_count}, Incomplete={incomplete_count}, Missing={missing_count}")

if __name__ == '__main__':
    main() 