# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Скрипт быстрого запуска переиндексации RAG
# =============================================================================
# Описание:
#   Импортирует и выполняет функцию перестроения RAG-индекса.
#
# File: rebuild_rag.py
# Project: ai-assistant
# Author: Antigravity
# =============================================================================

import argparse
from core.rag import build_rules_index


def main() -> None:
    """Запуск переиндексации Core RAG индекса."""
    parser = argparse.ArgumentParser(description="Переиндексация Core RAG индекса.")
    parser.add_argument('--fresh', action='store_true', help="Создать новый индекс с нуля.")
    args = parser.parse_args()

    print(f"Запуск переиндексации Core RAG правил (fresh={args.fresh})...")
    index_path, docs_path = build_rules_index()
    print(f"Успешно сгенерирован RAG индекс: {index_path}, {docs_path}")


if __name__ == '__main__':
    main()
