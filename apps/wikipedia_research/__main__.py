# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Wikipedia Research CLI Entry Point
# =============================================================================
# Description:
#   Command-line interface to launch Wikipedia Research experiments,
#   run interactive TUI, search articles, or start the standalone API server.
#
# Examples:
#   >>> python -m apps.wikipedia_research --topic "Artificial intelligence"
#   >>> python -m apps.wikipedia_research --mode server --port 8110
#
# File: __main__.py
# Project: ai-breadboard
# Package: apps.wikipedia_research
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CLI entry point for Wikipedia Research & Model Benchmark Application."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from src.logger import logger
from .engine import WikipediaResearchEngine
from .src.models import LanguageExperimentRequest, ModelExperimentRequest
from .tui import run_demo_tui


def main() -> None:
    """Парсинг CLI аргументов и диспетчеризация команд."""
    parser = argparse.ArgumentParser(
        prog="apps.wikipedia_research",
        description="Wikipedia Research & Multi-Model Comparative Laboratory for AI Breadboard",
    )
    parser.add_argument(
        "--mode",
        choices=["tui", "server", "experiment_a", "experiment_b"],
        default="tui",
        help="Режим работы: интерактивный tui, API server, или запуск конкретного эксперимента (default: tui)",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="Israel–Gaza war",
        help="Тема исследования (default: 'Israel–Gaza war')",
    )
    parser.add_argument(
        "--languages",
        nargs="+",
        default=["en", "ru", "he", "de", "fr"],
        help="Список языков (default: en ru he de fr)",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=["gemini", "foundry", "ollama"],
        help="Список моделей для эксперимента B (default: gemini foundry ollama)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8110,
        help="Порт сервера при запуске в режиме --mode server (default: 8110)",
    )
    parser.add_argument("--json", action="store_true", help="Вывод результатов в формате JSON")

    args = parser.parse_args()

    if args.mode == "server":
        import uvicorn
        from fastapi import FastAPI
        from apps.wikipedia_research.router import init_router

        app = FastAPI(title="Wikipedia Research & Model Benchmark API", version="1.0.0")
        app.include_router(init_router())
        print(f"Starting Wikipedia Research server on port {args.port}...")
        uvicorn.run(app, host="0.0.0.0", port=args.port)
        return

    if args.mode == "experiment_a":
        engine = WikipediaResearchEngine()
        req = LanguageExperimentRequest(
            topic=args.topic,
            languages=args.languages,
            model=args.models[0] if args.models else "gemini",
        )
        report = asyncio.run(engine.run_language_experiment(req))
        if args.json:
            print(json.dumps(report.model_dump(), indent=2, ensure_ascii=False))
        else:
            from .tui import Console, render_language_report_tui
            render_language_report_tui(report, Console())
        return

    if args.mode == "experiment_b":
        engine = WikipediaResearchEngine()
        req = ModelExperimentRequest(
            topic=args.topic,
            languages=args.languages,
            models=args.models,
        )
        report = asyncio.run(engine.run_model_experiment(req))
        if args.json:
            print(json.dumps(report.model_dump(), indent=2, ensure_ascii=False))
        else:
            from .tui import Console, render_model_report_tui
            render_model_report_tui(report, Console())
        return

    # По умолчанию запускаем интерактивную демонстрацию в TUI
    asyncio.run(run_demo_tui(topic=args.topic))


if __name__ == "__main__":
    main()
