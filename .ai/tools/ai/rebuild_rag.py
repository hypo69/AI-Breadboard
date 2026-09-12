# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Запуск переиндексации Core RAG индекса.
# =============================================================================
# Description:
#   Импортирует и performs функцию перестроения RAG-индекса.
#
# File: rebuild_rag.py
# Project: ai-breadboard
# Package: .ai.tools.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import argparse
from src.rag import build_rules_index

def main() -> None:
    """Запуск переиндексации Core RAG индекса."""
    parser = argparse.ArgumentParser(description="Переиндексация Core RAG индекса.")
    parser.add_argument('--fresh', action='store_true', help="Создать новый индекс с нуля.")
    args = parser.parse_args()

    print(f"Запуск переиндексации Core RAG правил (fresh={args.fresh})...")
    index_path, docs_path = build_rules_index()
    print(f"Successfully сгенерирован RAG индекс: {index_path}, {docs_path}")

if __name__ == '__main__':
    main()
