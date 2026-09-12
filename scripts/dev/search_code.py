# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Search codebase via CLI utility
# =============================================================================
# Description:
#   Console utility for searching technical RAG index of code and documentation.
#
# File: search_code.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Command-line utility for searching codebase via RAG index.

Provides console interface for searching technical documentation and code
using the RAG (Retrieval-Augmented Generation) search system."""

import os
import sys
import json
from src.ai.dev_rag import rag_search_tool

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/search_code.py 'your query'")
        return

    query = sys.argv[1]
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not set.")
        return

    print(f"🔍 Searching code: '{query}'...")
    result_json = rag_search_tool(query, api_key=api_key)
    
    try:
        results = json.loads(result_json)
        if "error" in results:
            print(f"❌ {results['error']}")
        else:
            for i, res in enumerate(results, 1):
                path = res.get('meta', {}).get('path', 'Unknown')
                print(f"{i}. File: {path} (Score: {res.get('score', 0):.2f})")
    except Exception as e:
        print(f"❌ Error parsing results: {e}")

if __name__ == "__main__":
    main()
