# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Поиск по кодовой базе (CLI утилита)
# =============================================================================
# Description:
#   Консольная утилита для поиска по техническому RAG-индексу кода и документации.
#
# File: search_code.py
# Project: ai-breadboard
# Package: .ai.tools.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import sys
import json
from src.ai.dev_rag import rag_search_tool

def main():
    if len(sys.argv) < 2:
        print("Использование: python scripts/search_code.py 'ваш запрос'")
        return

    query = sys.argv[1]
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ Error: GEMINI_API_KEY не установлен.")
        return

    print(f"🔍 Поиск по коду: '{query}'...")
    result_json = rag_search_tool(query, api_key=api_key)
    
    try:
        results = json.loads(result_json)
        if "error" in results:
            print(f"❌ {results['error']}")
        else:
            for i, res in enumerate(results, 1):
                path = res.get('meta', {}).get('path', 'Unknown')
                print(f"{i}. Файл: {path} (Score: {res.get('score', 0):.2f})")
    except Exception as e:
        print(f"❌ Error разбора результатов: {e}")

if __name__ == "__main__":
    main()
