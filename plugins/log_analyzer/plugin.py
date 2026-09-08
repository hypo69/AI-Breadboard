# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Log Analyzer Admin Plugin
# =============================================================================
# Description:
#   Provides administrative controls, error clustering, and AI diagnostics
#   for system and application logs in the AI Breadboard Admin UI.
#
# File: plugin.py
# Project: ai-breadboard
# Package: plugins.log_analyzer
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Log Analyzer Admin Plugin.

Implements BasePlugin interface to provide interactive log inspection,
pattern clustering, real-time error filtering, and Gemini AI diagnostics
directly from the Admin Web Interface.
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

# Import core parsing and clustering engine from log-analyzer skill
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
    # Fallback to absolute relative import if needed
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


class LogAnalyzerPlugin(BasePlugin):
    """Admin Plugin for Log Inspection and AI-assisted Diagnostics.

    Attributes:
        name (str): 'log_analyzer'
        title (str): Display title in Admin UI.
        version (str): Semantic version.
        icon (str): Emoji icon representing log analysis.
        category (str): 'tools'
        is_system (bool): True (admin-only scope).
    """

    name: str = "log_analyzer"
    title: str = "Log Analyzer & Diagnostics"
    version: str = "1.0.0"
    description: str = (
        "Intelligent log analyzer for Admin UI. Inspects error patterns, clusters "
        "tracebacks, and generates AI diagnostic reports."
    )
    icon: str = "📊"
    category: str = "tools"
    enabled: bool = True
    is_system: bool = True
    scope: str = "system"

    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the LogAnalyzerPlugin instance.

        Args:
            ai_model (Any): Optional AI model instance.
            config (Optional[Dict[str, Any]]): Initial configuration dictionary.
        """
        super().__init__(ai_model=ai_model, config=config)
        self.parser = LogParser()
        self.analyzer = LogAnalyzer(self.parser)

    def get_config_fields(self) -> List[Dict[str, Any]]:
        """Return configuration field specifications for Admin UI.

        Returns:
            List[Dict[str, Any]]: Configuration descriptors.
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
                "description": "Default log level filter for diagnostics.",
            },
            {
                "id": "tail_lines",
                "label": "Tail Lines Limit",
                "type": "number",
                "default": 500,
                "description": "Number of recent lines to parse per log file.",
            },
            {
                "id": "enable_ai_synthesis",
                "label": "Enable AI Diagnostics",
                "type": "boolean",
                "default": True,
                "description": "Use Gemini AI to analyze root causes and propose fixes.",
            },
            {
                "id": "auto_save_report",
                "label": "Auto-Save Reports",
                "type": "boolean",
                "default": True,
                "description": "Save generated markdown reports to the reports directory.",
            },
        ]

    def get_actions(self) -> List[Dict[str, Any]]:
        """Return executable actions for Admin UI buttons.

        Returns:
            List[Dict[str, Any]]: List of action descriptors.
        """
        return [
            {
                "id": "analyze_all",
                "label": "📊 Full Analysis",
                "color": "primary",
                "description": "Perform full static analysis on all system and app logs.",
            },
            {
                "id": "analyze_errors",
                "label": "🔴 Error Filter",
                "color": "danger",
                "description": "Extract and cluster only ERROR and CRITICAL events.",
            },
            {
                "id": "ai_diagnose",
                "label": "🤖 AI Diagnostics",
                "color": "success",
                "description": "Run AI diagnosis with remediation steps via Gemini.",
            },
            {
                "id": "rotate_and_clean",
                "label": "🧹 Rotate & Clean Logs",
                "color": "warning",
                "description": "Clear empty or oversized log files to maintain disk health.",
            },
        ]

    def get_manifest(self) -> Dict[str, Any]:
        """Return extended manifest for plugin.

        Returns:
            Dict[str, Any]: Manifest dictionary.
        """
        manifest = super().get_manifest()
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
        """Read and parse log entries from disk.

        Args:
            tail_lines: Maximum lines to read per file.
            level_filter: Level filter if any.
            custom_file: Optional single file path.

        Returns:
            tuple[List[LogEntry], List[str]]: Parsed entries and raw text blocks.
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
                logger.error(f"Error reading log file {fpath.name}: {ex}")

        return all_entries, raw_snippets

    async def execute_action(
        self, action_id: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute admin action by ID.

        Args:
            action_id: Identifier of the action.
            params: Parameters passed from the UI form.

        Returns:
            Dict[str, Any]: Structured result with message and payload.
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
                "message": f"Successfully analyzed {res.total_events} events across system logs.",
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
                "message": f"Found {len(error_entries)} error/critical events ({len(res.top_errors)} unique clusters).",
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
                "message": "AI Diagnostics completed successfully.",
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
                        # Truncate files exceeding 10MB or empty files
                        if p.stat().st_size > 10 * 1024 * 1024:
                            with open(p, "w", encoding="utf-8") as f:
                                f.truncate(0)
                            cleared_count += 1
                    except Exception as ex:
                        logger.error(f"Error rotating {p.name}: {ex}")

            return {
                "success": True,
                "message": f"Log maintenance complete. Rotated {cleared_count} oversized files.",
                "result": {"rotated_files": cleared_count},
            }

        return {
            "success": False,
            "error": f"Unknown action '{action_id}' on plugin '{self.name}'.",
        }

    async def handle(
        self, message: str, **kwargs: Any
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle streaming message requests for log analysis.

        Args:
            message: User query or prompt.
            **kwargs: Extra parameters.

        Yields:
            Dict[str, Any]: Stream chunks.
        """
        yield {"status": "started", "text": f"Analyzing logs for query: {message}..."}
        entries, _ = self._load_log_entries(tail_lines=300)
        res = self.analyzer.analyze_entries(entries)
        report = format_markdown_report(res, target_name="Live Query")
        yield {"status": "complete", "text": report, "metrics": asdict(res)}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return LLM function calling tool specifications.

        Returns:
            List[Dict[str, Any]]: Tool declarations.
        """
        return [
            {
                "name": "analyze_system_logs",
                "description": "Inspects system logs, clusters error traces, and extracts frequency metrics.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "level": {
                            "type": "string",
                            "enum": ["ALL", "ERROR", "CRITICAL", "WARNING", "INFO"],
                            "description": "Severity level filter.",
                        },
                        "tail_lines": {
                            "type": "integer",
                            "description": "Number of recent lines to parse.",
                        },
                    },
                },
            }
        ]
