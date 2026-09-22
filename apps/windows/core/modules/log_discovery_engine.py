# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Comprehensive Windows & Application Log Discovery Engine
# =============================================================================
# Description:
#   Discovers and indexes all log sources across the entire system:
#   - 1,000+ Native Windows Event Log Channels (with exact record counts & descriptions)
#   - Windows OS File Logs (CBS, DISM, Panther, Minidump, Setup, LogFiles)
#   - Third-party Application Logs in %ProgramData%, %LOCALAPPDATA%, %APPDATA%
#   - AI-Breadboard internal project logs
#
# Examples:
#   >>> from apps.windows.core.modules.log_discovery_engine import LogDiscoveryEngine
#   >>> engine = LogDiscoveryEngine()
#   >>> all_sources = engine.discover_all_sources()
#
# File: log_discovery_engine.py
# Project: AI-Breadboard
# Package: apps.windows.core.modules
# Class: LogDiscoveryEngine
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Движок обнаружения и классификации всех источников журналов и логов в системе."""

from __future__ import annotations

import datetime
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from logger import logger
from apps.windows.api.wevtapi import WevtAPI, ChannelMetadata


@dataclass
class LogSource:
    """Унифицированное описание обнаруженного источника логов."""
    source_id: str
    display_name: str
    description: str = ""
    source_type: str = "channel"       # "channel", "os_file", "app_file", "project_file"
    category: str = "Windows Event Log"# "Windows Event Log", "Windows OS Logs", "Application Logs", "AI-Breadboard Logs"
    location: str = ""                # Channel name or file path
    size_bytes: int = 0
    record_count: int = 0
    is_enabled: bool = True
    last_modified: str = ""
    extension: str = ""


class LogDiscoveryEngine:
    """Центральный сканер всех журналов Windows и логов приложений."""

    def __init__(self) -> None:
        """Инициализация сканера."""
        self.wevtapi = WevtAPI()

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Форматировать размер файла в понятный вид."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    @staticmethod
    def _estimate_file_records(file_path: Path, size_bytes: int) -> int:
        """Оценить или быстро подсчитать примерное количество строк/записей в файле."""
        if size_bytes == 0:
            return 0
        if size_bytes < 100 * 1024:
            try:
                with open(file_path, "rb") as f:
                    return sum(1 for line in f if line.strip())
            except Exception:
                pass
        # Оценка для больших файлов: ~150 байт на строку лога
        return max(1, int(size_bytes / 160))

    @staticmethod
    def _get_file_description(file_path: Path, category: str) -> str:
        """Сформировать понятное описание для файла лога."""
        name_lower = file_path.name.lower()
        parent_lower = file_path.parent.name.lower()

        if "cbs" in name_lower:
            return "Журнал компонентной модели Windows (CBS): логирование установки обновлений, компонентов ОС и проверок SFC."
        if "dism" in name_lower:
            return "Журнал системы обслуживания образов развертывания (DISM): восстановление системного хранилища WinSxS."
        if "setupact" in name_lower or "setuperr" in name_lower:
            return "Журнал установки и обновления Windows Setup / Panther: действия и ошибки установщика."
        if "httperr" in name_lower or "w3c" in name_lower:
            return "Журнал веб-сервера HTTP.sys / IIS: ошибки сетевых HTTP-запросов и ответов сервера."
        if "firewall" in name_lower or "pfirewall" in name_lower:
            return "Журнал сетевого брандмауэра Windows: заблокированные и разрешенные сетевые пакеты."
        if "netsetup" in name_lower:
            return "Журнал сетевых подключений: настройка сетевых адаптеров и присоединение к домену."
        if "fastapi" in name_lower:
            return "Внутренний журнал FastAPI веб-сервера AI-Breadboard: HTTP маршрутизация, запросы и ответы API."
        if "gemini" in name_lower:
            return "Журнал AI провайдера Google Gemini: генерации, обращения к моделям и стриминг токенов."
        if "errors" in name_lower:
            return "Сводный журнал критических ошибок и трейсбеков приложения AI-Breadboard."
        if "debug" in name_lower:
            return "Детальный отладочный журнал низкоуровневых операций ядра AI-Breadboard."
        if "vscode" in parent_lower or "code" in parent_lower:
            return f"Журнал среды разработки Visual Studio Code ({file_path.name}): логи расширений и ядра редактора."
        if "docker" in parent_lower or "docker" in name_lower:
            return "Журнал контейнеризации Docker Desktop и фоновых демонов WSL2."

        return f"Файл журнала {category} ({file_path.name}) в директории {file_path.parent}."

    def discover_all_sources(self, max_file_sources: int = 500) -> List[LogSource]:
        """Обнаружить абсолютно все источники логов в операционной системе.

        Returns:
            List[LogSource]: Список обнаруженных каналов и файлов.
        """
        all_sources: List[LogSource] = []

        # 1. Сбор всех Windows Event Log каналов
        event_channels = self.wevtapi.enumerate_channels()
        for ch in event_channels:
            all_sources.append(
                LogSource(
                    source_id=f"evt:{ch.channel_name}",
                    display_name=ch.display_name,
                    description=ch.description,
                    source_type="channel",
                    category="Windows Event Log",
                    location=ch.channel_name,
                    is_enabled=ch.is_enabled,
                    record_count=ch.record_count,
                )
            )

        # 2. Сканирование системных директорий Windows
        os_log_dirs = [
            Path(os.environ.get("SystemRoot", r"C:\Windows")) / "Logs",
            Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "LogFiles",
            Path(os.environ.get("SystemRoot", r"C:\Windows")) / "Panther",
            Path(os.environ.get("SystemRoot", r"C:\Windows")) / "Minidump",
            Path(os.environ.get("SystemRoot", r"C:\Windows")) / "inf",
        ]
        for d in os_log_dirs:
            if d.exists() and d.is_dir():
                all_sources.extend(self._scan_directory(d, category="Windows OS Logs", source_type="os_file", max_depth=3, limit=150))

        # 3. Сканирование директорий приложений (%ProgramData%, %LOCALAPPDATA%, %APPDATA%)
        app_dirs = []
        prog_data = os.environ.get("ProgramData")
        if prog_data:
            app_dirs.append(Path(prog_data))

        loc_app_data = os.environ.get("LOCALAPPDATA")
        if loc_app_data:
            app_dirs.append(Path(loc_app_data))

        roam_app_data = os.environ.get("APPDATA")
        if roam_app_data:
            app_dirs.append(Path(roam_app_data))

        for d in app_dirs:
            if d.exists() and d.is_dir():
                all_sources.extend(self._scan_directory(d, category="Application Logs", source_type="app_file", max_depth=3, limit=200))

        # 4. Сканирование проектных логов AI-Breadboard
        try:
            proj_logs = Path(".").resolve() / "ai-breadboard" / "logs"
            if proj_logs.exists():
                all_sources.extend(self._scan_directory(proj_logs, category="AI-Breadboard Logs", source_type="project_file", max_depth=2, limit=50))
            
            root_logs = Path(".").resolve() / "logs"
            if root_logs.exists():
                all_sources.extend(self._scan_directory(root_logs, category="AI-Breadboard Logs", source_type="project_file", max_depth=2, limit=50))
        except Exception:
            pass

        return all_sources

    def _scan_directory(
        self,
        base_dir: Path,
        category: str,
        source_type: str,
        max_depth: int = 3,
        limit: int = 100,
    ) -> List[LogSource]:
        """Рекурсивный безопасный поиск файлов логов в директории."""
        results: List[LogSource] = []
        log_extensions = {".log", ".txt", ".json", ".dmp", ".evtx", ".etl", ".csv"}

        def _walk(cur_dir: Path, current_depth: int) -> None:
            if current_depth > max_depth or len(results) >= limit:
                return
            try:
                for entry in cur_dir.iterdir():
                    if len(results) >= limit:
                        return
                    try:
                        if entry.is_dir():
                            if entry.name.lower() in ("node_modules", ".git", "__pycache__", "cache", "temp", "tmp"):
                                continue
                            _walk(entry, current_depth + 1)
                        elif entry.is_file():
                            ext = entry.suffix.lower()
                            if ext in log_extensions or "log" in entry.name.lower():
                                stat = entry.stat()
                                mtime_str = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                                est_records = self._estimate_file_records(entry, stat.st_size)
                                desc = self._get_file_description(entry, category)
                                results.append(
                                    LogSource(
                                        source_id=f"file:{entry.resolve()}",
                                        display_name=f"{entry.parent.name}/{entry.name}",
                                        description=desc,
                                        source_type=source_type,
                                        category=category,
                                        location=str(entry.resolve()),
                                        size_bytes=stat.st_size,
                                        record_count=est_records,
                                        is_enabled=True,
                                        last_modified=mtime_str,
                                        extension=ext,
                                    )
                                )
                    except (PermissionError, OSError):
                        continue
            except (PermissionError, OSError):
                pass

        _walk(base_dir, 1)
        return results

    def read_source_events(
        self,
        source_id_or_loc: str,
        limit: int = 100,
        level: str = "",
        search: str = "",
        event_id: int = 0,
        hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """Универсальное чтение событий из любого источника (канала или файла) без PowerShell."""
        if source_id_or_loc.startswith("file:") or "\\" in source_id_or_loc or "/" in source_id_or_loc or Path(source_id_or_loc).exists():
            clean_path = source_id_or_loc.replace("file:", "")
            return self._read_file_events(clean_path, limit=limit, level=level, search=search)

        chan_name = source_id_or_loc.replace("evt:", "")
        return self.wevtapi.read_events(
            channel=chan_name,
            limit=limit,
            level=level,
            search=search,
            event_id=event_id,
            hours=hours,
        )

    def _read_file_events(
        self,
        file_path_str: str,
        limit: int = 100,
        level: str = "",
        search: str = "",
    ) -> List[Dict[str, Any]]:
        """Чтение и разбор текстового/JSON файла лога."""
        path = Path(file_path_str)
        if not path.exists() or not path.is_file():
            return []

        entries: List[Dict[str, Any]] = []
        lvl_filter = level.lower() if level else ""
        s_filter = search.lower() if search else ""

        try:
            file_size = path.stat().st_size
            read_size = min(file_size, 2 * 1024 * 1024)
            with open(path, "rb") as f:
                if file_size > read_size:
                    f.seek(file_size - read_size)
                raw_bytes = f.read()

            text = raw_bytes.decode("utf-8", errors="replace")
            lines = text.splitlines()

            for line in reversed(lines):
                if len(entries) >= limit:
                    break
                line_str = line.strip()
                if not line_str:
                    continue

                if s_filter and s_filter not in line_str.lower():
                    continue

                detected_level = "Information"
                line_lower = line_str.lower()
                if "crit" in line_lower or "fatal" in line_lower:
                    detected_level = "Critical"
                elif "err" in line_lower or "exception" in line_lower:
                    detected_level = "Error"
                elif "warn" in line_lower:
                    detected_level = "Warning"
                elif "verb" in line_lower or "trace" in line_lower:
                    detected_level = "Verbose"

                if lvl_filter:
                    if lvl_filter == "critical" and detected_level != "Critical":
                        continue
                    if lvl_filter == "error" and detected_level not in ("Error", "Critical"):
                        continue
                    if lvl_filter == "warning" and detected_level not in ("Warning", "Error", "Critical"):
                        continue

                ts_match = re.search(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}", line_str)
                ts = ts_match.group(0).replace("T", " ") if ts_match else datetime.datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")

                entries.append({
                    "timestamp": ts,
                    "level": detected_level,
                    "event_id": 0,
                    "provider": path.name,
                    "computer": os.environ.get("COMPUTERNAME", "LOCALHOST"),
                    "process_id": 0,
                    "thread_id": 0,
                    "channel": f"File: {path.name}",
                    "message": line_str[:500],
                    "raw_data": line_str,
                })
        except Exception as ex:
            logger.debug(f"[LogDiscoveryEngine] Ошибка чтения файла {path}: {ex}")

        return entries


__all__ = ["LogDiscoveryEngine", "LogSource"]
