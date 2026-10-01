# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm - Cli
# =============================================================================
# Description:
#   Консольный интерфейс управления и запросов к базе знаний WikiLLM.
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.wikillm.cli
#   Python API:
#     from apps.windows.wikillm.cli import main
#
#     res = main()
#
# File: cli.py
# Project: ai-breadboard
# Package: apps.windows.wikillm
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Консольный интерфейс управления и запросов к базе знаний WikiLLM."""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from .code_indexer import CodeKnowledgeIndexer
from .engine import WikiLLMEngine
from .extractor import ArtifactExtractor
from .models import ArtifactInput


async def _async_cli_main(args: argparse.Namespace) -> None:
    """Асинхронная точка входа для командной строки."""
    engine = WikiLLMEngine()

    if args.command == "resolve":
        extracted = ArtifactExtractor.from_raw_text(args.query)
        art = extracted[0] if extracted else ArtifactInput(raw_query=args.query)
        print(f"[*] Разрешение артефакта: {args.query}...")
        res = await engine.resolve(art, sync_gemini=not args.no_llm)
        print(f"\n[+] Результат ({res.lookup_level.value}, cached={res.cached}, {res.execution_time_ms:.1f}ms):")
        if res.entity:
            print(f"  Ключ:        {res.entity.canonical_key}")
            print(f"  Имя:         {res.entity.name}")
            print(f"  Категория:   {res.entity.category} ({res.entity.severity})")
            print(f"  Сводка:      {res.entity.summary}")
            if res.entity.diagnostic_info:
                print(f"  Причины:     {', '.join(res.entity.diagnostic_info.possible_causes)}")
                if res.entity.diagnostic_info.remediation_steps:
                    print("  Шаги устранения:")
                    for s in res.entity.diagnostic_info.remediation_steps:
                        print(f"    • {s.title}: {s.description}")
        else:
            print(f"  [-] {res.message}")

    elif args.command == "search":
        results = engine.storage.search_fts(args.query, limit=args.limit)
        print(f"[+] Найдено результатов: {len(results)}")
        for ent in results:
            print(f"  • [{ent.canonical_key}] {ent.name} - {ent.summary[:80]}...")

    elif args.command == "index-code":
        indexer = CodeKnowledgeIndexer(engine.storage)
        print(f"[*] Индексация исходного кода из {args.path}...")
        count = indexer.index_directory(args.path)
        print(f"[+] Успешно проиндексировано {count} символов.")

    elif args.command == "stats":
        metrics = engine.get_metrics()
        print(json.dumps(metrics, indent=2, ensure_ascii=False))

    elif args.command == "tui":
        from .tui import run_tui
        await run_tui(engine)

    else:
        print("Неизвестная команда. Используйте --help для справки.")


def main() -> None:
    """Главная синхронная точка входа CLI."""
    parser = argparse.ArgumentParser(description="WikiLLM: Progressive Knowledge Base CLI")
    subparsers = parser.add_subparsers(dest="command", help="Команды")

    # resolve
    p_res = subparsers.add_parser("resolve", help="Разрешить ошибку, Event ID или симптом")
    p_res.add_argument("query", help="Код ошибки, Event ID или сообщение")
    p_res.add_argument("--no-llm", action="store_true", help="Не вызывать Gemini при промахе кэша")

    # search
    p_search = subparsers.add_parser("search", help="Полнотекстовый поиск в базе знаний")
    p_search.add_argument("query", help="Поисковая фраза")
    p_search.add_argument("--limit", type=int, default=10, help="Лимит результатов")

    # index-code
    p_idx = subparsers.add_parser("index-code", help="Индексация кода в слой Code Knowledge")
    p_idx.add_argument("--path", default="apps/windows", help="Путь к каталогу с кодом")

    # stats
    subparsers.add_parser("stats", help="Статистика базы знаний и эффективность кэша")

    # tui
    subparsers.add_parser("tui", help="Запуск интерактивного TUI терминала")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    asyncio.run(_async_cli_main(args))


if __name__ == "__main__":
    main()
