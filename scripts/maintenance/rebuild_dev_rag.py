# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Developer context RAG reindexing and rebuilding
# =============================================================================
# Description:
#   Script rebuilds RAG index for development technical documentation and codebase.
#
# File: rebuild_dev_rag.py
# Project: ai-breadboard
# Package: scripts.maintenance
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
from core.ai.dev_rag import build_dev_rag
from core.logger import logger

def main():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ Error: GEMINI_API_KEY environment variable not set.")
        return

    print("🔄 Starting codebase and documentation reindexing...")
    try:
        build_dev_rag(api_key)
        print("✅ Developer index successfully rebuilt.")
    except Exception as e:
        print(f"❌ Error during reindexing: {e}")
        logger.error(f"Error rebuild_dev_rag: {e}", exc_info=True)

if __name__ == "__main__":
    main()
