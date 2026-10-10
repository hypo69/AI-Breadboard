# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Process_Manager Core - Manager
# =============================================================================
# Description:
#   Диспетчер процессов Windows с поддержкой классификации на Apps,
#   Background processes и Windows processes, сбором метрик и управлением (taskkill).
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.process_manager.core.manager import ProcessManager
#
#     service = ProcessManager()
#     report = service.generate_report()
#     categorized = service.generate_categorized_report()
#
# File: manager.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.process_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 02:08:00
# =============================================================================

from __future__ import annotations
"""Диспетчер процессов и категоризации ресурсов Windows."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import psutil
from logger import logger
from apps.windows.sdk.modules.process_manager.core.classifier import ProcessClassifier
from apps.windows.sdk.modules.process_manager.core.models import (
    CategorizedProcessReport,
    ProcessGroupItem,
    ProcessItem,
    ProcessKillRequest,
    ProcessReport,
)


class ProcessManager:
    """Менеджер процессов, категоризации и мониторинга потребления ресурсов."""

    def __init__(self) -> None:
        """Инициализация менеджера процессов."""
        self._classifier = ProcessClassifier()

    def list_processes(self) -> List[ProcessItem]:
        """Получение списка всех активных процессов через psutil.

        Returns:
            List[ProcessItem]: Список всех активных процессов.
        """
        processes: List[ProcessItem] = []
        for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info', 'num_threads', 'create_time', 'exe']):
            try:
                p_info = p.info
                mem_mb = round((p_info.get('memory_info').rss / (1024 ** 2)), 1) if p_info.get('memory_info') else 0.0
                c_time = datetime.fromtimestamp(p_info.get('create_time', 0)).strftime('%Y-%m-%d %H:%M:%S') if p_info.get('create_time') else ''
                processes.append(ProcessItem(
                    pid=p_info.get('pid', 0),
                    name=p_info.get('name', 'Unknown') or 'Unknown',
                    username=p_info.get('username'),
                    cpu_percent=float(p_info.get('cpu_percent') or 0.0),
                    memory_mb=mem_mb,
                    num_threads=p_info.get('num_threads') or 1,
                    create_time=c_time,
                    exe_path=p_info.get('exe')
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes

    def generate_categorized_report(self) -> CategorizedProcessReport:
        """Формирование сводного отчета, разделенного на Apps, Background и Windows.

        Returns:
            CategorizedProcessReport: Структурированный отчет по категориям.
        """
        return self._classifier.classify_processes()

    def generate_report(self) -> ProcessReport:
        """Формирование полного сводного отчета о процессах хоста с категоризацией.

        Returns:
            ProcessReport: Полный отчет с плоским списком и группами категорий.
        """
        categorized = self._classifier.classify_processes()
        all_processes: List[ProcessItem] = []
        for group in categorized.apps:
            all_processes.extend(group.subprocesses)
        for group in categorized.background_processes:
            all_processes.extend(group.subprocesses)
        for group in categorized.windows_processes:
            all_processes.extend(group.subprocesses)

        if not all_processes:
            all_processes = self.list_processes()

        total_threads = sum(p.num_threads for p in all_processes)
        total_mem = sum(p.memory_mb for p in all_processes)
        top_cpu = sorted(all_processes, key=lambda x: x.cpu_percent, reverse=True)[:5]
        top_mem = sorted(all_processes, key=lambda x: x.memory_mb, reverse=True)[:5]

        return ProcessReport(
            total_processes=len(all_processes),
            total_threads=total_threads,
            total_memory_used_mb=round(total_mem, 1),
            apps_count=len(categorized.apps),
            background_count=len(categorized.background_processes),
            windows_count=len(categorized.windows_processes),
            top_cpu_processes=top_cpu,
            top_memory_processes=top_mem,
            processes=all_processes,
            apps=categorized.apps,
            background_processes=categorized.background_processes,
            windows_processes=categorized.windows_processes,
            timestamp=datetime.now().isoformat()
        )

    async def kill_process(self, req: ProcessKillRequest) -> Dict[str, Any]:
        """Завершение процесса с поддержкой Dry-Run и валидацией.

        Args:
            req: Параметры запроса завершения процесса.

        Returns:
            Dict[str, Any]: Результат выполнения операции.
        """
        if req.dry_run:
            return {
                'status': 'DRY_RUN_SUCCESS',
                'pid': req.pid,
                'kill_tree': req.kill_tree,
                'message': f"Симуляция завершения процесса PID={req.pid} (дерево={req.kill_tree}) выполнена успешно."
            }
        if not req.confirmed_by_user:
            return {
                'status': 'CONFIRMATION_REQUIRED',
                'pid': req.pid,
                'message': f"Завершение процесса PID={req.pid} требует явного подтверждения."
            }
        try:
            p = psutil.Process(req.pid)
            if req.kill_tree:
                for child in p.children(recursive=True):
                    child.kill()
            p.kill()
            return {'status': 'SUCCESS', 'pid': req.pid, 'message': f"Процесс PID={req.pid} успешно завершен."}
        except Exception as exc:
            return {'status': 'ERROR', 'pid': req.pid, 'message': str(exc)}


__all__ = ['ProcessManager']
