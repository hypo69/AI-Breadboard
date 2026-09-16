# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Application Log Analyzer Admin Plugin
# =============================================================================
# Description:
#   Предоставляет административные инструменты инспекции, кластеризации ошибок
#   и ИИ-диагностики логов нашего приложения в панели администрирования.
#
# File: plugin.py
# Project: ai-breadboard
# Package: plugins.application_log_analyzer
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Плагин анализатора логов приложения для панели администрирования.

Реализует интерфейс BasePlugin для интерактивного просмотра логов приложения,
кластеризации паттернов ошибок, фильтрации в реальном времени и
генерации диагностических отчётов с помощью Gemini AI.
"""

from __future__ import annotations

import asyncio
import datetime
import json
import os
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from header import __root__
from src.logger import logger
from plugins.base import BasePlugin

# Импорт ядра парсинга и кластеризации из навыка анализатора логов
SKILL_SCRIPTS_PATH = __root__ / ".agents" / "skills" / "developer-skills" / "log-analyzer" / "scripts"
if not SKILL_SCRIPTS_PATH.exists():
    SKILL_SCRIPTS_PATH = __root__ / ".agents" / "skills" / "log-analyzer" / "scripts"
if str(SKILL_SCRIPTS_PATH) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS_PATH))

try:
    from analyze import (
        LogParser,
        LogAnalyzer,
        LogEntry,
        AnalysisResult,
        format_markdown_report,
        run_ai_synthesis,
        get_default_log_dir,
        get_default_reports_dir,
    )
except ImportError:
    from .clean_parser import (
        LogParser,
        LogAnalyzer,
        LogEntry,
        AnalysisResult,
        format_markdown_report,
        run_ai_synthesis,
        get_default_log_dir,
        get_default_reports_dir,
    )


class ApplicationLogAnalyzerPlugin(BasePlugin):
    """Плагин администрирования для анализа логов приложения и ИИ-диагностики.

    Attributes:
        name (str): 'application_log_analyzer'
        title (str): Отображаемое название в панели управления.
        version (str): Семантическая версия плагина.
        icon (str): Иконка плагина.
        category (str): 'tools'
        is_system (bool): True (системный плагин администрирования).
    """

    name: str = "application_log_analyzer"
    title: str = "Application Log Analyzer & Diagnostics"
    version: str = "1.0.0"
    description: str = (
        "Интеллектуальный анализатор логов приложения для панели администрирования. "
        "Анализирует паттерны ошибок, кластеризует трейсбеки и генерирует диагностические отчёты."
    )
    icon: str = "📊"
    category: str = "tools"
    enabled: bool = True
    is_system: bool = True
    scope: str = "system"

    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        """Инициализирует экземпляр ApplicationLogAnalyzerPlugin.

        Args:
            ai_model (Any): Опциональный экземпляр модели ИИ.
            config (Optional[Dict[str, Any]]): Начальный словарь конфигурации.
        """
        super().__init__(ai_model=ai_model, config=config)
        self.parser = LogParser()
        self.analyzer = LogAnalyzer(self.parser)

    def get_config_fields(self) -> List[Dict[str, Any]]:
        """Возвращает спецификацию полей конфигурации для веб-интерфейса.

        Returns:
            List[Dict[str, Any]]: Дескрипторы конфигурационных полей.
        """
        return [
            {
                "id": "log_level",
                "label": "Filter Level",
                "type": "select",
                "default": "ALL",
                "options": [
                    {"value": "ALL", "label": "All Levels (ALL)"},
                    {"value": "ERROR", "label": "Errors Only (ERROR)"},
                    {"value": "CRITICAL", "label": "Critical Only (CRITICAL)"},
                    {"value": "WARNING", "label": "Warnings & Errors (WARNING+)"},
                    {"value": "INFO", "label": "Info & Above (INFO)"},
                ],
                "description": "Уровень логирования по умолчанию для фильтрации.",
            },
            {
                "id": "tail_lines",
                "label": "Tail Lines Limit",
                "type": "number",
                "default": 500,
                "description": "Количество последних строк для парсинга из каждого файла логов.",
            },
            {
                "id": "enable_ai_synthesis",
                "label": "Enable AI Diagnostics",
                "type": "boolean",
                "default": True,
                "description": "Использовать Gemini AI для поиска первопричин и рекомендаций.",
            },
            {
                "id": "auto_save_report",
                "label": "Auto-Save Reports",
                "type": "boolean",
                "default": True,
                "description": "Автоматически сохранять сгенерированные Markdown-отчёты на диск.",
            },
        ]

    def get_actions(self) -> List[Dict[str, Any]]:
        """Возвращает список доступных действий для кнопок в панели управления.

        Returns:
            List[Dict[str, Any]]: Список дескрипторов действий.
        """
        return [
            {
                "id": "analyze_all",
                "label": "📊 Full Analysis",
                "color": "primary",
                "description": "Выполнить полный статический анализ всех логов приложения.",
            },
            {
                "id": "analyze_errors",
                "label": "🔴 Error Filter",
                "color": "danger",
                "description": "Выделить и сгруппировать только события ERROR и CRITICAL.",
            },
            {
                "id": "ai_diagnose",
                "label": "🤖 AI Diagnostics",
                "color": "success",
                "description": "Запустить ИИ-диагностику с планом исправления через Gemini.",
            },
            {
                "id": "rotate_and_clean",
                "label": "🧹 Rotate & Clean Logs",
                "color": "warning",
                "description": "Очистить или урезать устаревшие и слишком большие файлы логов.",
            },
        ]

    def get_manifest(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Возвращает расширенный манифест плагина.

        Returns:
            Dict[str, Any]: Словарь манифеста.
        """
        manifest = super().get_manifest(*args, **kwargs)
        manifest.update({
            "log_directory": str(get_default_log_dir()),
            "reports_directory": str(get_default_reports_dir()),
        })
        return manifest

    def _load_log_entries(
        self,
        tail_lines: int = 500,
        level_filter: Optional[str] = None,
        custom_file: Optional[str] = None,
    ) -> tuple[List[LogEntry], List[str]]:
        """Загружает и парсит записи логов с диска.

        Args:
            tail_lines: Максимальное количество строк для чтения из файла.
            level_filter: Опциональный фильтр уровня логирования.
            custom_file: Опциональный путь к конкретному файлу.

        Returns:
            tuple[List[LogEntry], List[str]]: Распарсенные записи и сырые текстовые блоки.
        """
        log_dir = get_default_log_dir()
        files: List[Path] = []

        if custom_file:
            cf_path = Path(custom_file)
            if cf_path.exists() and cf_path.is_file():
                files.append(cf_path)
        elif log_dir.exists():
            files.extend(sorted(log_dir.glob("*.log")))
            json_log = log_dir / "log.json"
            if json_log.exists() and json_log.is_file():
                files.append(json_log)

        all_entries: List[LogEntry] = []
        raw_snippets: List[str] = []

        for fpath in files:
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                if tail_lines > 0:
                    lines = content.splitlines()[-tail_lines:]
                    content = "\n".join(lines)

                if fpath.name.endswith(".json") or fpath.name == "log.json":
                    entries = self.parser.parse_json_lines(content)
                else:
                    entries = self.parser.parse_text(content)

                if level_filter and level_filter != "ALL":
                    entries = [e for e in entries if e.level == level_filter.upper()]

                all_entries.extend(entries)
                raw_snippets.append(f"=== File: {fpath.name} ===\n{content}\n")
            except Exception as ex:
                logger.error(f"Ошибка при чтении файла логов {fpath.name}: {ex}")

        return all_entries, raw_snippets

    async def execute_action(
        self, action_id: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Выполняет административное действие по его идентификатору.

        Args:
            action_id: Идентификатор действия.
            params: Параметры формы.

        Returns:
            Dict[str, Any]: Структурированный результат действия.
        """
        params = params or {}
        tail_lines = int(params.get("tail_lines", self.config.get("tail_lines", 500)))
        level_filter = str(params.get("log_level", self.config.get("log_level", "ALL")))

        if action_id == "analyze_all":
            entries, _ = self._load_log_entries(tail_lines=tail_lines, level_filter="ALL")
            res = self.analyzer.analyze_entries(entries)
            report_md = format_markdown_report(res, target_name="System & Application Logs")

            return {
                "success": True,
                "message": f"Успешно проанализировано {res.total_events} событий в логах приложения.",
                "result": {
                    "total_events": res.total_events,
                    "level_counts": res.level_counts,
                    "top_errors": res.top_errors,
                    "report_markdown": report_md,
                },
            }

        elif action_id == "analyze_errors":
            entries, _ = self._load_log_entries(tail_lines=tail_lines, level_filter=None)
            error_entries = [e for e in entries if e.level in ("ERROR", "CRITICAL", "EXCEPTION")]
            res = self.analyzer.analyze_entries(error_entries)
            report_md = format_markdown_report(res, target_name="Critical & Error Logs")

            return {
                "success": True,
                "message": f"Найдено {len(error_entries)} критических событий ({len(res.top_errors)} уникальных кластеров).",
                "result": {
                    "error_events": len(error_entries),
                    "clusters": res.top_errors,
                    "report_markdown": report_md,
                },
            }

        elif action_id == "ai_diagnose":
            entries, raw_snippets = self._load_log_entries(tail_lines=tail_lines, level_filter=None)
            res = self.analyzer.analyze_entries(entries)
            raw_sample = "\n".join(raw_snippets)

            ai_summary = await run_ai_synthesis(raw_sample, res)
            res.ai_summary = ai_summary
            report_md = format_markdown_report(res, target_name="AI Diagnostic Report")

            saved_path: Optional[str] = None
            if self.config.get("auto_save_report", True):
                rep_dir = get_default_reports_dir()
                rep_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                save_file = rep_dir / f"admin_ai_diagnosis_{timestamp}.md"
                save_file.write_text(report_md, encoding="utf-8")
                saved_path = str(save_file)

            return {
                "success": True,
                "message": "ИИ-диагностика успешно выполнена.",
                "result": {
                    "total_events": res.total_events,
                    "level_counts": res.level_counts,
                    "ai_summary": ai_summary,
                    "saved_to": saved_path,
                    "report_markdown": report_md,
                },
            }

        elif action_id == "rotate_and_clean":
            log_dir = get_default_log_dir()
            cleared_count = 0
            if log_dir.exists():
                for p in log_dir.glob("*.log"):
                    try:
                        if p.stat().st_size > 10 * 1024 * 1024:
                            with open(p, "w", encoding="utf-8") as f:
                                f.truncate(0)
                            cleared_count += 1
                    except Exception as ex:
                        logger.error(f"Ошибка при ротации {p.name}: {ex}")

            return {
                "success": True,
                "message": f"Обслуживание логов завершено. Очищено {cleared_count} файлов.",
                "result": {"rotated_files": cleared_count},
            }

        return {
            "success": False,
            "error": f"Неизвестное действие '{action_id}' для плагина '{self.name}'.",
        }

    async def handle(
        self, message: str, **kwargs: Any
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Обрабатывает потоковый запрос к анализу логов.

        Args:
            message: Запрос пользователя.
            **kwargs: Дополнительные аргументы.

        Yields:
            Dict[str, Any]: Потоковые чанки ответа.
        """
        yield {"status": "started", "text": f"Анализ логов приложения для запроса: {message}..."}
        entries, _ = self._load_log_entries(tail_lines=300)
        res = self.analyzer.analyze_entries(entries)
        report = format_markdown_report(res, target_name="Live Query")
        yield {"status": "complete", "text": report, "metrics": asdict(res)}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Возвращает спецификацию инструментов для вызова LLM.

        Returns:
            List[Dict[str, Any]]: Декларации инструментов.
        """
        return [
            {
                "name": "analyze_application_logs",
                "description": "Инспектирует логи приложения, кластеризует трейсбеки ошибок и извлекает метрики частоты.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "level": {
                            "type": "string",
                            "enum": ["ALL", "ERROR", "CRITICAL", "WARNING", "INFO"],
                            "description": "Фильтр уровня важности логов.",
                        },
                        "tail_lines": {
                            "type": "integer",
                            "description": "Количество последних строк для парсинга.",
                        },
                    },
                },
            }
        ]


# Псевдоним для совместимости
LogAnalyzerPlugin = ApplicationLogAnalyzerPlugin
