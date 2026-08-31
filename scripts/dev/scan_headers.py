# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Python files header validation scanner
# =============================================================================
# Description:
#   Scans all Python files in project to validate header format compliance
#   with CODE_RULES.md § 6.1 specification for file headers and docstrings.
#
# File: scan_headers.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Header validation scanner for Python files.

Scans all Python files to validate header format and documentation compliance
with project standards."""

import os
import re
from pathlib import Path

def count_words(text):
    """Count words in text.
    
    Args:
        text: Text string to count.
        
    Returns:
        Number of words in text.
    """
    words = re.findall(r'\b\w+\b', text)
    return len(words)

def extract_description(header_text):
    """Extract description from header text.
    
    Args:
        header_text: Header section text.
        
    Returns:
        Description string or empty if not found.
    """
    desc_match = re.search(r'# Description:(.*?)(?=\s*# (?:File|Project|Author|Copyright|\$))', header_text, re.DOTALL)
    if desc_match:
        desc_lines = desc_match.group(1).strip()
        lines = [line.strip().lstrip('#').strip() for line in desc_lines.split('\n')]
        return ' '.join(lines)
    return ''

def check_header(filepath):
    """Check if file has valid header.
    
    Args:
        filepath: Path to file to check.
        
    Returns:
        Dictionary with header validation results.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.split('\n')
    has_coding = False
    header_start = 0
    for i, line in enumerate(lines[:3]):
        if '# -*- coding: utf-8 -*-' in line:
            has_coding = True
            header_start = i
            break
            
    if not has_coding:
        return {'has_header': 'no', 'word_count': 0, 'description': ''}
        
    header_lines = []
    for i in range(header_start, min(len(lines), 50)):
        line = lines[i].strip()
        if not line.startswith('#') and not line.startswith('!') and 'import' not in line.lower():
            break
        header_lines.append(line)
        
    header_text = '\n'.join(header_lines)
    has_process_name = bool(re.search(r'#\s*Process Name:', header_text))
    has_description = bool(re.search(r'#\s*Description:', header_text))
    has_file = bool(re.search(r'#\s*File:', header_text))
    has_project = bool(re.search(r'#\s*Project:', header_text))
    has_author = bool(re.search(r'#\s*Author:', header_text))
    has_copyright = bool(re.search(r'#\s*Copyright:', header_text))
    
    all_fields_present = all([has_process_name, has_description, has_file, has_project, has_author, has_copyright])
    if not all_fields_present:
        if len(header_lines) <= 3 and all('coding' in l.lower() or l.strip() == '' for l in header_lines):
            return {'has_header': 'no', 'word_count': 0, 'description': ''}
        return {'has_header': 'no', 'word_count': 0, 'description': ''}
        
    description = extract_description(header_text)
    word_count = count_words(description)
    return {'has_header': 'yes', 'word_count': word_count, 'description': description[:200]}

if __name__ == '__main__':
    # Header scanning script
    import sys
    root_dir = Path(__root__ if '__root__' in globals() else '.')
    python_files = list(root_dir.glob('**/*.py'))
    
    print(f"Found {len(python_files)} Python files. Starting scan...")
    for pf in python_files:
        if 'venv' in pf.parts or '.git' in pf.parts:
            continue
        try:
            status = check_header(pf)
            if status['has_header'] == 'no':
                print(f"❌ {pf.relative_to(root_dir)} — header missing or invalid")
        except Exception as e:
            print(f"⚠️ Error processing {pf}: {e}")
