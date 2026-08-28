# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Поиск по кодовой базе (CLI утилита)
# =============================================================================
# Описание:
#   Консольная утилита для поиска по техническому RAG-индексу кода и документации.
#   Принимает запрос из командной строки, выполняет семантический поиск и выводит
#   результаты с указанием пути к файлу и показателем релевантности (Score).
#
# File: search_code.py
# Project: ai-breadboard
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import sys
import json
from core.ai.dev_rag import rag_search_tool

def main():
    if len(sys.argv) < 2:
        print("Использование: python scripts/search_code.py 'ваш запрос'")
        return

    query = sys.argv[1]
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ Ошибка: GEMINI_API_KEY не установлен.")
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
        print(f"❌ Ошибка разбора результатов: {e}")

if __name__ == "__main__":
    main()
