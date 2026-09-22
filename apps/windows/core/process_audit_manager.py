# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Process Audit & Sysmon Telemetry Manager
# =============================================================================
# Description:
#   Управление и агрегация телеметрии аудита создания процессов (Event 4688)
#   и Microsoft Sysmon (Event 1, 3, 11, 23). Предоставляет проверку статуса
#   политик аудита, извлечение аргументов командной строки, построение дерева
#   процессов и корреляцию с файловыми операциями.
#
# Examples:
#   >>> from apps.windows.core.process_audit_manager import ProcessAuditManager
#   >>> manager = ProcessAuditManager()
#   >>> status = manager.get_telemetry_status()
#   >>> history = manager.get_process_execution_history(limit=50)
#
# File: process_audit_manager.py
# Project: AI-Breadboard
# Package: apps.windows.core
# Class: ProcessAuditManager
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Менеджер аудита процессов и телеметрии Sysmon / Security Audit для Windows."""

from __future__ import annotations

import sys
import winreg
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from apps.windows.api.wevtapi import WevtAPI
from logger import logger


@dataclass
class TelemetrySensorStatus:
    """Статус источников системной телеметрии Windows."""
    sysmon_installed: bool
    sysmon_running: bool
    sysmon_channel_active: bool
    process_creation_audit_enabled: bool
    command_line_audit_enabled: bool
    recommended_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return asdict(self)


@dataclass
class ProcessTreeNode:
    """Узел дерева выполнения процессов."""
    process_id: int
    process_name: str
    executable_path: str
    command_line: str
    user: str
    timestamp: str
    process_guid: str = ""
    hashes: str = ""
    children: List[ProcessTreeNode] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {
            "process_id": self.process_id,
            "process_name": self.process_name,
            "executable_path": self.executable_path,
            "command_line": self.command_line,
            "user": self.user,
            "timestamp": self.timestamp,
            "process_guid": self.process_guid,
            "hashes": self.hashes,
            "children": [c.to_dict() for c in self.children],
        }


class ProcessAuditManager:
    """Менеджер для анализа телеметрии аудита создания процессов и Sysmon."""

    REG_AUDIT_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Audit"
    REG_CMDLINE_VAL = "ProcessCreationIncludeCmdLine_Enabled"

    def __init__(self, wevtapi: Optional[WevtAPI] = None) -> None:
        """Инициализация менеджера аудита."""
        self.wevtapi = wevtapi or WevtAPI()

    def get_telemetry_status(self) -> TelemetrySensorStatus:
        """
        Проверить готовность и активность системных сенсоров Windows.

        Returns:
            TelemetrySensorStatus с флагами готовности и рекомендациями.
        """
        sysmon_installed = False
        sysmon_channel_active = False
        sysmon_running = False
        cmdline_audit_enabled = False
        proc_creation_audit_enabled = False
        recommendations: List[str] = []

        if sys.platform == "win32":
            # 1. Проверка Sysmon канала
            try:
                cnt = self.wevtapi.get_channel_record_count("Microsoft-Windows-Sysmon/Operational")
                if cnt >= 0:
                    sysmon_channel_active = True
                    sysmon_installed = True
                    sysmon_running = True
            except Exception as ex:
                logger.debug(f"[ProcessAuditManager] Ошибка проверки канала Sysmon: {ex}")

            # 2. Проверка реестра на включение аргументов командной строки
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, self.REG_AUDIT_KEY, 0, winreg.KEY_READ) as key:
                    val, _ = winreg.QueryValueEx(key, self.REG_CMDLINE_VAL)
                    cmdline_audit_enabled = bool(val == 1)
            except OSError:
                cmdline_audit_enabled = False

            # 3. Проверка записей Security 4688
            try:
                sec_cnt = self.wevtapi.get_channel_record_count("Security")
                proc_creation_audit_enabled = bool(sec_cnt > 0)
            except Exception:
                proc_creation_audit_enabled = False

        if not sysmon_installed:
            recommendations.append(
                "Microsoft Sysmon не обнаружен. Рекомендуется установить Sysmon для сбора хэшей, дерева вызовов и сетевых связей."
            )
        if not cmdline_audit_enabled:
            recommendations.append(
                "Запись аргументов командной строки отключена. Включите через реестр: HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System\\Audit\\ProcessCreationIncludeCmdLine_Enabled = 1"
            )
        if not proc_creation_audit_enabled and not sysmon_installed:
            recommendations.append(
                "Аудит создания процессов не активен. Включите: auditpol /set /subcategory:'Process Creation' /success:enable"
            )

        return TelemetrySensorStatus(
            sysmon_installed=sysmon_installed,
            sysmon_running=sysmon_running,
            sysmon_channel_active=sysmon_channel_active,
            process_creation_audit_enabled=proc_creation_audit_enabled,
            command_line_audit_enabled=cmdline_audit_enabled,
            recommended_actions=recommendations,
        )

    def get_process_execution_history(
        self,
        limit: int = 100,
        filter_process: Optional[str] = None,
        filter_user: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Получить структурированную историю запусков программ с аргументами командной строки.

        Args:
            limit: Лимит записей.
            filter_process: Фильтр по названию/пути процесса.
            filter_user: Фильтр по пользователю.

        Returns:
            Список событий создания процессов.
        """
        return self.wevtapi.query_process_events(
            limit=limit,
            filter_process=filter_process,
            filter_user=filter_user,
        )

    def build_process_tree(self, limit: int = 100) -> List[ProcessTreeNode]:
        """
        Восстановить дерево родительских и дочерних процессов из журнала событий.

        Args:
            limit: Максимальное количество событий для анализа.

        Returns:
            Список корневых узлов дерева процессов.
        """
        events = self.get_process_execution_history(limit=limit)
        nodes: Dict[int, ProcessTreeNode] = {}
        child_pids: Set[int] = set()

        for ev in reversed(events):
            pid = ev.get("process_id", 0)
            if not pid:
                continue

            node = ProcessTreeNode(
                process_id=pid,
                process_name=ev.get("process_name", ""),
                executable_path=ev.get("executable_path", ""),
                command_line=ev.get("command_line", ""),
                user=ev.get("user", ""),
                timestamp=ev.get("timestamp", ""),
                process_guid=ev.get("process_guid", ""),
                hashes=ev.get("hashes", ""),
            )
            nodes[pid] = node

        # Связываем родительские и дочерние связи
        for ev in reversed(events):
            pid = ev.get("process_id", 0)
            ppid = ev.get("parent_process_id", 0)

            if ppid and ppid in nodes and pid in nodes and ppid != pid:
                parent_node = nodes[ppid]
                child_node = nodes[pid]
                if child_node not in parent_node.children:
                    parent_node.children.append(child_node)
                    child_pids.add(pid)

        # Корневыми являются те, чей родитель не попал в выборку или ppid == 0
        root_nodes = [node for pid, node in nodes.items() if pid not in child_pids]
        return root_nodes

    def get_file_activity_with_processes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Получить события изменения/удаления файлов и связать их с вызвавшими процессами (Sysmon 11, 23, 26).

        Args:
            limit: Лимит записей.

        Returns:
            Список событий файловой активности с привязанными процессами.
        """
        results: List[Dict[str, Any]] = []

        # Запрашиваем события Sysmon Event 11 (FileCreate), 23 (FileDelete), 26 (FileDeleteDetected)
        sysmon_events = self.wevtapi.read_events(
            channel="Microsoft-Windows-Sysmon/Operational",
            limit=limit,
        )

        for ev in sysmon_events:
            eid = ev.get("event_id", 0)
            if eid in (11, 23, 26):
                ed = ev.get("event_data", {})
                action = "create" if eid == 11 else "delete"
                target_filename = ed.get("TargetFilename", "")
                exe_path = ed.get("Image", "")
                user = ed.get("User", "")
                pid = int(ed.get("ProcessId", 0) or 0)

                results.append({
                    "action": action,
                    "event_id": eid,
                    "target_file": target_filename,
                    "executable_path": exe_path,
                    "process_name": exe_path.replace("\\", "/").split("/")[-1] if exe_path else "",
                    "process_id": pid,
                    "user": user,
                    "timestamp": ev.get("timestamp"),
                })

        return results


__all__ = ["ProcessAuditManager", "TelemetrySensorStatus", "ProcessTreeNode"]
