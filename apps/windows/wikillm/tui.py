# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm - Tui
# =============================================================================
# Description:
#   Интерактивный консольный терминал для исследования, поиска и разрешения
#
# Usage Examples:
#   Python API:
#     import apps.windows.wikillm.tui as tui
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.windows.wikillm
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Интерактивный консольный терминал для исследования, поиска и разрешения"""

import asyncio
from typing import Optional
from .engine import WikiLLMEngine
from .extractor import ArtifactExtractor
from .models import ArtifactInput


async def run_tui(engine: Optional[WikiLLMEngine] = None) -> None:
    """Запускает интерактивный TUI цикл в консоли."""
    eng = engine or WikiLLMEngine()
    await eng.start()

    print("\n" + "=" * 70)
    print(" 🧠 WikiLLM: Progressive Windows Knowledge Terminal")
    print(" Команды: ':stats', ':list', ':q' для выхода")
    print("=" * 70 + "\n")

    try:
        while True:
            try:
                user_input = input("WikiLLM> ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input:
                continue

            if user_input.lower() in (":q", ":quit", "exit"):
                break

            if user_input == ":stats":
                metrics = eng.get_metrics()
                print("\n📊 Статистика базы знаний:")
                print(f"  Сущностей в БД:      {metrics['storage_stats']['total_entities']}")
                print(f"  Наблюдений артефактов: {metrics['storage_stats']['total_observation_events']}")
                print(f"  Всего запросов:      {metrics['lookup_stats']['total_requests']}")
                print(f"  L1 Exact Hits:       {metrics['lookup_stats']['l1_exact_hits']}")
                print(f"  L2 Fingerprint Hits: {metrics['lookup_stats']['l2_fingerprint_hits']}")
                print(f"  L3 Semantic Hits:    {metrics['lookup_stats']['l3_semantic_hits']}")
                print(f"  L4 Gemini Синтез:    {metrics['lookup_stats']['l4_gemini_resolutions']}")
                print(f"  Cache Hit Rate:      {metrics['cache_hit_rate_pct']}%\n")
                continue

            if user_input == ":list":
                entities = eng.storage.list_entities(limit=20)
                print(f"\n📑 Последние {len(entities)} записей базы знаний:")
                for e in entities:
                    print(f"  • [{e.canonical_key}] {e.name} ({e.category})")
                print()
                continue

            # Разрешение пользовательского запроса
            extracted = ArtifactExtractor.from_raw_text(user_input)
            art = extracted[0] if extracted else ArtifactInput(raw_query=user_input)

            print(f"[*] Поиск артефакта '{art.raw_query or user_input}'...")
            res = await eng.resolve(art, sync_gemini=True)

            print(f"\n[+] Уровень: {res.lookup_level.value.upper()} | Время: {res.execution_time_ms:.1f} мс | Кэш: {res.cached}")
            if res.entity:
                print(f"  Ключ:        {res.entity.canonical_key}")
                print(f"  Имя:         {res.entity.name}")
                print(f"  Категория:   {res.entity.category} ({res.entity.severity})")
                print(f"  Сводка:      {res.entity.summary}")
                if res.entity.diagnostic_info and res.entity.diagnostic_info.possible_causes:
                    print(f"  Причины:     {', '.join(res.entity.diagnostic_info.possible_causes)}")
                if res.entity.diagnostic_info and res.entity.diagnostic_info.remediation_steps:
                    print("  Шаги устранения:")
                    for s in res.entity.diagnostic_info.remediation_steps:
                        print(f"    -> {s.title}: {s.description}")
            else:
                print(f"  [-] {res.message}")
            print()

    finally:
        await eng.stop()
        print("\nЗавершение работы WikiLLM.")
