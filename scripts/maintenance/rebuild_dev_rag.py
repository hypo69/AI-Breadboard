# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Scripts Maintenance - Rebuild Dev Rag
# =============================================================================
# Description:
#   Скрипт/модуль системы AI-Breadboard (`rebuild_dev_rag`).
#
# Usage Examples:
#   CLI:
#     python -m scripts.maintenance.rebuild_dev_rag
#   Python API:
#     from scripts.maintenance.rebuild_dev_rag import main
#
#     res = main()
#
# File: rebuild_dev_rag.py
# Project: ai-breadboard
# Package: scripts.maintenance
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:27:07
# =============================================================================

"""Скрипт/модуль системы AI-Breadboard (`rebuild_dev_rag`)."""

import os
from src.ai.dev_rag import build_dev_rag
from logger import logger

def main():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print('❌ Error: GEMINI_API_KEY environment variable not set.')
        return
    print('🔄 Starting codebase and documentation reindexing...')
    try:
        build_dev_rag(api_key)
        print('✅ Developer index successfully rebuilt.')
    except Exception as e:
        print(f'❌ Error during reindexing: {e}')
        logger.error(f'Error rebuild_dev_rag: {e}', exc_info=True)
if __name__ == '__main__':
    main()