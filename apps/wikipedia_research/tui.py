# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Wikipedia Research Rich TUI Dashboard
# =============================================================================
# Description:
#   Rich terminal user interface renderer for Wikipedia Research and Multi-Model
#   Comparative Laboratory. Renders multidimensional comparison tables,
#   sentiment polarity gauges, and framing summaries directly in console.
#
# File: tui.py
# Project: ai-breadboard
# Package: apps.wikipedia_research
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Rich TUI interactive terminal dashboard for Wikipedia Research Lab."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    Console = Any  # type: ignore
    Panel = Any  # type: ignore
    Table = Any  # type: ignore
    Text = Any  # type: ignore
    RICH_AVAILABLE = False

from .engine import WikipediaResearchEngine
from .src.models import (
    LanguageComparisonReport,
    LanguageExperimentRequest,
    ModelComparisonReport,
    ModelExperimentRequest,
)


def _format_sentiment(val: float) -> str:
    """Форматирование тональности с цветовым тегом."""
    if val > 0.05:
        return f"[bold green]+{val:.2f}[/bold green]"
    elif val < -0.05:
        return f"[bold red]{val:.2f}[/bold red]"
    return f"[bold yellow]{val:.2f}[/bold yellow]"


def render_language_report_tui(report: LanguageComparisonReport, console: Console) -> None:
    """Отображение отчета Эксперимента A (сравнение языков) в терминале."""
    if not RICH_AVAILABLE:
        print(f"\n--- Experiment A: Language Comparison for '{report.topic}' ---")
        for row in report.metrics_summary_table:
            print(f"[{row['lang']}] Sentiment: {row['sentiment']:+.2f}, Framing: {row['framing']}")
        return

    table = Table(
        title=f"🌐 [bold cyan]Experiment A — Wikipedia Language Comparison: '{report.topic}'[/bold cyan] (Model: {report.model_used})",
        header_style="bold magenta",
        show_lines=True,
    )

    table.add_column("Язык", justify="center", style="cyan", no_wrap=True)
    table.add_column("Заголовок статьи", style="white")
    table.add_column("Тональность", justify="right")
    table.add_column("Субъективность", justify="right", style="yellow")
    table.add_column("Критика", justify="right", style="red")
    table.add_column("Похвала", justify="right", style="green")
    table.add_column("Неопред.", justify="right", style="blue")
    table.add_column("Спорных тезисов", justify="center")
    table.add_column("Фрейминг", style="magenta")
    table.add_column("Слов", justify="right", style="dim")

    for r in report.metrics_summary_table:
        table.add_row(
            r["lang"].upper(),
            r["title"][:30],
            _format_sentiment(r["sentiment"]),
            f"{r['subjectivity']:.2f}",
            f"{r['criticism']:.2f}",
            f"{r['praise']:.2f}",
            f"{r['uncertainty']:.2f}",
            str(r["claims_count"]),
            r["framing"],
            f"{r['word_count']:,}",
        )

    console.print("\n")
    console.print(table)

    if report.cross_language_insights:
        insights_text = "\n".join(f"• {ins}" for ins in report.cross_language_insights)
        console.print(
            Panel(
                insights_text,
                title="🔍 Ключевые аналитические выводы (Cross-Language Insights)",
                border_style="cyan",
            )
        )


def render_model_report_tui(report: ModelComparisonReport, console: Console) -> None:
    """Отображение отчета Эксперимента B (сравнение моделей) в терминале."""
    if not RICH_AVAILABLE:
        print(f"\n--- Experiment B: Model Benchmark for '{report.topic}' ---")
        print(report.sentiment_grid)
        return

    table = Table(
        title=f"🤖 [bold green]Experiment B — Multi-Model AI Benchmark: '{report.topic}'[/bold green]",
        header_style="bold cyan",
        show_lines=True,
    )

    table.add_column("Язык", justify="center", style="bold yellow", no_wrap=True)
    for model in report.models:
        table.add_column(f"Модель: {model}", justify="center")

    for lang in report.languages:
        row_cells = [lang.upper()]
        for model in report.models:
            val = report.sentiment_grid.get(lang, {}).get(model, 0.0)
            res = report.matrix.get(lang, {}).get(model)
            framing = res.metrics.framing_tone if res else "n/a"
            row_cells.append(f"{_format_sentiment(val)}\n[dim]({framing})[/dim]")
        table.add_row(*row_cells)

    console.print("\n")
    console.print(table)

    if report.model_alignment_insights:
        insights_text = "\n".join(f"• {ins}" for ins in report.model_alignment_insights)
        console.print(
            Panel(
                insights_text,
                title="🧠 Анализ согласованности моделей (Model Alignment Insights)",
                border_style="green",
            )
        )


async def run_demo_tui(topic: str = "Israel–Gaza war") -> None:
    """Запуск демонстрационных сценариев Экспериментов A и B в TUI."""
    console = Console()
    console.print(Panel(
        f"[bold white]AI Breadboard — Wikipedia Research & Model Laboratory[/bold white]\n"
        f"[dim]Исследование темы:[/dim] [bold cyan]{topic}[/bold cyan]",
        border_style="magenta",
    ))

    engine = WikipediaResearchEngine()

    with console.status("[bold green]Выполнение Эксперимента A (Кросс-языковой анализ)...[/bold green]"):
        req_a = LanguageExperimentRequest(
            topic=topic,
            languages=["en", "ru", "he", "de", "fr"],
            model="gemini",
        )
        report_a = await engine.run_language_experiment(req_a)

    render_language_report_tui(report_a, console)

    with console.status("[bold blue]Выполнение Эксперимента B (Кросс-модельный бенчмарк)...[/bold blue]"):
        req_b = ModelExperimentRequest(
            topic=topic,
            languages=["en", "ru", "he", "de"],
            models=["gemini", "foundry", "ollama"],
        )
        report_b = await engine.run_model_experiment(req_b)

    render_model_report_tui(report_b, console)
