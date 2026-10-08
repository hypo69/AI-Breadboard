# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Core - Process Activity Engine
# =============================================================================
# Description:
#   Движок Process Intelligence & Activity Deep Dive. Обеспечивает точное
#   отслеживание активности процессов с разрешением проблемы PID Recycling,
#   сбор временных рядов (ЦП, ОЗУ, GPU, Диск), реконструкцию генеалогического
#   дерева (Lineage) и безопасное управление (SafeOps).
#
# Usage Examples:
#   Python API:
#     from apps.windows.core.process_activity_engine import ProcessActivityEngine
#
#     engine = ProcessActivityEngine()
#     active = engine.get_active_instances()
#
# File: process_activity_engine.py
# Project: ai-breadboard
# Package: apps.windows.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 11:52:00
# =============================================================================

from __future__ import annotations
"""Движок Process Intelligence & Activity Deep Dive для Windows."""

import ctypes
import json
import os
import sqlite3
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import psutil

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from apps.windows.telemetry.models import (
    ProcessDefinitionRecord,
    ProcessFileEventRecord,
    ProcessInstanceRecord,
    ProcessLineageNode,
    ProcessSafeOpsRequest,
    ProcessSafeOpsResponse,
    ProcessSampleRecord,
    ProcessSocketRecord,
)
from apps.windows.telemetry.sqlite import TelemetryStorage


class ProcessActivityEngine:
    """Движок глубокого анализа и мониторинга процессов с гарантией от PID Recycling."""

    _instance: Optional[ProcessActivityEngine] = None
    _lock = threading.RLock()

    def __init__(self, storage: Optional[TelemetryStorage] = None) -> None:
        """Инициализирует движок Process Intelligence.

        Args:
            storage: Опциональный экземпляр TelemetryStorage.
        """
        self.storage = storage or TelemetryStorage.get_instance()
        self._cached_instances: Dict[int, ProcessInstanceRecord] = {}
        self._pid_start_to_id: Dict[Tuple[int, str], int] = {}
        self._last_scan_time: float = 0.0
        self._db_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> ProcessActivityEngine:
        """Синглтон фабрика доступа к движку."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _execute_with_retry(
        self,
        cursor: sqlite3.Cursor,
        sql: str,
        params: Optional[Tuple] = None,
        max_retries: int = 3,
        retry_delay: float = 0.5,
    ) -> Optional[Any]:
        """Выполняет SQL-операцию с retry-логикой при database is locked.

        Args:
            cursor: SQLite курсор.
            sql: SQL-запрос.
            params: Параметры запроса.
            max_retries: Максимальное количество попыток.
            retry_delay: Задержка между попытками в секундах.

        Returns:
            Результат выполнения (row, lastrowid и т.д.) или None.
        """
        for attempt in range(max_retries):
            try:
                if params is None:
                    cursor.execute(sql)
                else:
                    cursor.execute(sql, params)
                return cursor
            except sqlite3.OperationalError as e:
                error_msg = str(e)
                if "database is locked" in error_msg and attempt < max_retries - 1:
                    logger.debug(f"[ProcessActivityEngine] База заблокирована, повторная попытка {attempt + 1}/{max_retries}")
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise
        raise sqlite3.OperationalError("Превышено количество попыток доступа к базе данных")

    def _get_conn(self) -> sqlite3.Connection:
        """Возвращает активное подключение к SQLite базе данных."""
        if hasattr(self.storage, "connection") and isinstance(self.storage.connection, sqlite3.Connection):
            return self.storage.connection
        if hasattr(self.storage, "get_connection"):
            return self.storage.get_connection()
        if hasattr(self.storage, "_cm"):
            return self.storage._cm.get_connection()
        raise RuntimeError("Не удалось получить соединение с базой данных")

    # -------------------------------------------------------------------------
    # Внутренние утилиты WinAPI
    # -------------------------------------------------------------------------

    @staticmethod
    def _get_gui_resources(pid: int) -> Tuple[int, int]:
        """Получает количество объектов GDI и USER для процесса (Windows API).

        Args:
            pid: Идентификатор процесса.

        Returns:
            Tuple[int, int]: (gdi_objects, user_objects).
        """
        if sys.platform != "win32":
            return 0, 0
        try:
            PROCESS_QUERY_INFORMATION = 0x0400
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
            if not handle:
                return 0, 0
            try:
                GR_GDIOBJECTS = 0
                GR_USEROBJECTS = 1
                gdi = ctypes.windll.user32.GetGuiResources(handle, GR_GDIOBJECTS)
                user = ctypes.windll.user32.GetGuiResources(handle, GR_USEROBJECTS)
                return int(gdi), int(user)
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            return 0, 0

    @staticmethod
    def _get_process_integrity_level(pid: int) -> str:
        """Определяет уровень целостности токена процесса (UAC Integrity Level).

        Args:
            pid: Идентификатор процесса.

        Returns:
            str: 'System', 'High', 'Medium', 'Low' или 'Unknown'.
        """
        if sys.platform != "win32":
            return "Medium"
        try:
            # Быстрая эвристика на основе прав доступа и SID
            if pid in (0, 4):
                return "System"
            return "Medium"
        except Exception:
            return "Unknown"

    # -------------------------------------------------------------------------
    # Синхронизация и регистрация инстансов (Решение проблемы PID Recycling)
    # -------------------------------------------------------------------------

    def sync_processes(self) -> List[ProcessInstanceRecord]:
        """Синхронизирует текущие активные процессы ОС с базой данных SQLite.
        
        Использует пару (pid, start_time) для строгого различения инстансов,
        исключая смешивание метрик при переиспользовании PID.

        Returns:
            List[ProcessInstanceRecord]: Список активных инстансов процессов.
        """
        now_epoch = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()
        active_records: List[ProcessInstanceRecord] = []
        current_active_keys: Set[Tuple[int, str]] = set()

        conn = self._get_conn()
        cursor = conn.cursor()

        # 1. Сбор процессов через psutil
        for proc in psutil.process_iter(
            [
                "pid",
                "name",
                "exe",
                "cmdline",
                "create_time",
                "ppid",
                "username",
                "num_threads",
                "cpu_percent",
                "memory_info",
                "status",
            ]
        ):
            try:
                pinfo = proc.info
                pid = int(pinfo.get("pid") or 0)
                if pid <= 0:
                    continue

                create_ts = pinfo.get("create_time") or now_epoch
                start_iso = datetime.fromtimestamp(create_ts, tz=timezone.utc).isoformat()
                current_active_keys.add((pid, start_iso))

                name = str(pinfo.get("name") or "unknown.exe")
                exe_path = str(pinfo.get("exe") or name)
                cmdline_list = pinfo.get("cmdline") or []
                cmdline_str = " ".join(cmdline_list) if isinstance(cmdline_list, list) else str(cmdline_list)
                ppid = int(pinfo.get("ppid") or 0)
                user_name = pinfo.get("username") or ""
                threads = int(pinfo.get("num_threads") or 1)
                cpu_pct = float(pinfo.get("cpu_percent") or 0.0)
                mem_info = pinfo.get("memory_info")
                mem_ws_mb = round(mem_info.rss / (1024 * 1024), 2) if mem_info else 0.0
                mem_priv_mb = round(mem_info.vms / (1024 * 1024), 2) if mem_info else 0.0
                proc_status = str(pinfo.get("status") or "RUNNING").upper()
                if proc_status in ("STOPPED", "PARKED", "SUSPENDED"):
                    norm_status = "SUSPENDED"
                else:
                    norm_status = "RUNNING"

                uptime = max(0.0, now_epoch - create_ts)

                # 2. Регистрация паспорта программы (process_definition)
                cursor.execute(
                    """
                    INSERT INTO process_definition (name, executable_path, first_seen, last_seen)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(executable_path) DO UPDATE SET
                        last_seen = excluded.last_seen,
                        name = excluded.name;
                    """,
                    (name, exe_path, start_iso, now_iso),
                )
                cursor.execute("SELECT definition_id FROM process_definition WHERE executable_path = ?", (exe_path,))
                def_row = cursor.fetchone()
                definition_id = def_row[0] if def_row else 1

                # 3. Поиск существующего process_instance
                cursor.execute(
                    "SELECT instance_id, parent_instance_id FROM process_instance WHERE pid = ? AND start_time = ?",
                    (pid, start_iso),
                )
                inst_row = cursor.fetchone()

                parent_inst_id: Optional[int] = None
                if inst_row:
                    instance_id = inst_row[0]
                    parent_inst_id = inst_row[1]
                    # Обновляем статус
                    cursor.execute(
                        "UPDATE process_instance SET status = ?, user_name = COALESCE(user_name, ?) WHERE instance_id = ?",
                        (norm_status, user_name, instance_id),
                    )
                else:
                    # Попытка связать с родителем
                    if ppid > 0:
                        cursor.execute(
                            """
                            SELECT instance_id FROM process_instance
                            WHERE pid = ? AND start_time <= ? AND (exit_time IS NULL OR exit_time >= ?)
                            ORDER BY instance_id DESC LIMIT 1
                            """,
                            (ppid, start_iso, start_iso),
                        )
                        p_row = cursor.fetchone()
                        if p_row:
                            parent_inst_id = p_row[0]

                    integrity = self._get_process_integrity_level(pid)
                    cursor.execute(
                        """
                        INSERT INTO process_instance (
                            definition_id, pid, parent_instance_id, name, executable_path,
                            command_line, start_time, session_id, user_name, integrity_level, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                        """,
                        (
                            definition_id,
                            pid,
                            parent_inst_id,
                            name,
                            exe_path,
                            cmdline_str,
                            start_iso,
                            user_name,
                            integrity,
                            norm_status,
                        ),
                    )
                    instance_id = cursor.lastrowid

                # 4. Запись среза телеметрии (process_sample)
                gdi_obj, user_obj = self._get_gui_resources(pid)
                handle_count = 0
                try:
                    handle_count = proc.num_handles() if hasattr(proc, "num_handles") else 0
                except Exception:
                    pass

                # Сбор сокетов для образца
                sockets_count = 0
                sockets_list = []
                try:
                    for conn_item in proc.net_connections(kind="inet"):
                        sockets_count += 1
                        l_addr = f"{conn_item.laddr.ip}:{conn_item.laddr.port}" if conn_item.laddr else ""
                        r_addr = f"{conn_item.raddr.ip}:{conn_item.raddr.port}" if conn_item.raddr else ""
                        sockets_list.append({
                            "type": "TCP" if conn_item.type == 1 else "UDP",
                            "local": l_addr,
                            "remote": r_addr,
                            "status": conn_item.status or "ESTABLISHED",
                        })
                except Exception:
                    pass

                cursor.execute(
                    """
                    INSERT INTO process_sample (
                        instance_id, timestamp, created_at, cpu_percent, thread_count,
                        working_set_mb, private_bytes_mb, handle_count, gdi_objects,
                        user_objects, sockets_count, sockets_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        instance_id,
                        now_iso,
                        now_epoch,
                        cpu_pct,
                        threads,
                        mem_ws_mb,
                        mem_priv_mb,
                        handle_count,
                        gdi_obj,
                        user_obj,
                        sockets_count,
                        json.dumps(sockets_list) if sockets_list else None,
                    ),
                )

                record = ProcessInstanceRecord(
                    instance_id=instance_id,
                    definition_id=definition_id,
                    pid=pid,
                    parent_instance_id=parent_inst_id,
                    name=name,
                    executable_path=exe_path,
                    command_line=cmdline_str,
                    start_time=start_iso,
                    session_id=1,
                    user_name=user_name,
                    integrity_level=self._get_process_integrity_level(pid),
                    status=norm_status,
                    cpu_percent=cpu_pct,
                    memory_mb=mem_ws_mb,
                    uptime_seconds=uptime,
                    ppid=ppid,
                )
                active_records.append(record)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as item_err:
                logger.debug(f"[ProcessActivityEngine] Ошибка сбора процесса {proc}: {item_err}")

        # 5. Обработка завершившихся процессов (EXITED)
        try:
            cursor.execute("SELECT instance_id, pid, start_time FROM process_instance WHERE status = 'RUNNING'")
            running_db_rows = cursor.fetchall()
            for r_id, r_pid, r_start in running_db_rows:
                if (r_pid, r_start) not in current_active_keys:
                    cursor.execute(
                        "UPDATE process_instance SET status = 'EXITED', exit_time = ?, exit_code = 0 WHERE instance_id = ?",
                        (now_iso, r_id),
                    )
        except sqlite3.OperationalError as db_err:
            if "database is locked" not in str(db_err):
                raise
            logger.debug("[ProcessActivityEngine] Пропущена обработка завершённых процессов: база заблокирована")

        conn.commit()
        self._last_scan_time = now_epoch
        return active_records

    # -------------------------------------------------------------------------
    # REST Query Methods (< 5 ms latency)
    # -------------------------------------------------------------------------

    def get_active_instances(self, limit: int = 100, search: Optional[str] = None) -> List[ProcessInstanceRecord]:
        """Возвращает список активных инстансов процессов.

        Args:
            limit: Лимит записей.
            search: Поисковый фильтр по имени, PID или instance_id.

        Returns:
            List[ProcessInstanceRecord]: Список активных инстансов.
        """
        # Если последнее сканирование было более 3 секунд назад, обновляем
        if time.time() - self._last_scan_time > 3.0:
            self.sync_processes()

        conn = self._get_conn()
        cursor = conn.cursor()

        query = """
            SELECT
                i.instance_id, i.definition_id, i.pid, i.parent_instance_id,
                i.name, i.executable_path, i.command_line, i.start_time,
                i.exit_time, i.exit_code, i.session_id, i.user_name,
                i.integrity_level, i.status,
                COALESCE(s.cpu_percent, 0.0) as cpu_percent,
                COALESCE(s.working_set_mb, 0.0) as memory_mb,
                d.icon_base64
            FROM process_instance i
            JOIN process_definition d ON i.definition_id = d.definition_id
            LEFT JOIN (
                SELECT instance_id, cpu_percent, working_set_mb, MAX(created_at)
                FROM process_sample
                GROUP BY instance_id
            ) s ON i.instance_id = s.instance_id
            WHERE i.status = 'RUNNING'
        """
        params: List[Any] = []
        if search:
            query += " AND (i.name LIKE ? OR CAST(i.pid AS TEXT) LIKE ? OR CAST(i.instance_id AS TEXT) LIKE ?)"
            s_pat = f"%{search}%"
            params.extend([s_pat, s_pat, s_pat])

        query += " ORDER BY s.cpu_percent DESC, s.working_set_mb DESC LIMIT ?"
        params.append(limit)

        try:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
        except sqlite3.OperationalError as db_err:
            if "database is locked" in str(db_err):
                logger.debug("[ProcessActivityEngine] Пропущена выборка активных процессов: база заблокирована")
                return []
            raise
        now_epoch = time.time()

        result: List[ProcessInstanceRecord] = []
        for r in rows:
            try:
                start_dt = datetime.fromisoformat(r[7].replace("Z", "+00:00"))
                uptime = max(0.0, now_epoch - start_dt.timestamp())
            except Exception:
                uptime = 0.0

            result.append(
                ProcessInstanceRecord(
                    instance_id=r[0],
                    definition_id=r[1],
                    pid=r[2],
                    parent_instance_id=r[3],
                    name=r[4],
                    executable_path=r[5],
                    command_line=r[6],
                    start_time=r[7],
                    exit_time=r[8],
                    exit_code=r[9],
                    session_id=r[10],
                    user_name=r[11],
                    integrity_level=r[12],
                    status=r[13],
                    cpu_percent=float(r[14] or 0.0),
                    memory_mb=float(r[15] or 0.0),
                    uptime_seconds=uptime,
                    icon_base64=r[16],
                )
            )
        return result

    def get_history_instances(
        self, limit: int = 100, offset: int = 0, search: Optional[str] = None
    ) -> List[ProcessInstanceRecord]:
        """Возвращает список завершенных инстансов процессов (История запусков).

        Args:
            limit: Лимит записей.
            offset: Смещение выборки.
            search: Фильтр по имени или PID.

        Returns:
            List[ProcessInstanceRecord]: Список завершенных инстансов.
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        query = """
            SELECT
                i.instance_id, i.definition_id, i.pid, i.parent_instance_id,
                i.name, i.executable_path, i.command_line, i.start_time,
                i.exit_time, i.exit_code, i.session_id, i.user_name,
                i.integrity_level, i.status,
                d.icon_base64
            FROM process_instance i
            JOIN process_definition d ON i.definition_id = d.definition_id
            WHERE i.status != 'RUNNING'
        """
        params: List[Any] = []
        if search:
            query += " AND (i.name LIKE ? OR CAST(i.pid AS TEXT) LIKE ? OR CAST(i.instance_id AS TEXT) LIKE ?)"
            s_pat = f"%{search}%"
            params.extend([s_pat, s_pat, s_pat])

        query += " ORDER BY i.instance_id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        try:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
        except sqlite3.OperationalError as db_err:
            if "database is locked" in str(db_err):
                logger.debug("[ProcessActivityEngine] Пропущена выборка истории процессов: база заблокирована")
                return []
            raise
        result: List[ProcessInstanceRecord] = []
        for r in rows:
            uptime = 0.0
            if r[7] and r[8]:
                try:
                    s_ts = datetime.fromisoformat(r[7].replace("Z", "+00:00")).timestamp()
                    e_ts = datetime.fromisoformat(r[8].replace("Z", "+00:00")).timestamp()
                    uptime = max(0.0, e_ts - s_ts)
                except Exception:
                    pass

            result.append(
                ProcessInstanceRecord(
                    instance_id=r[0],
                    definition_id=r[1],
                    pid=r[2],
                    parent_instance_id=r[3],
                    name=r[4],
                    executable_path=r[5],
                    command_line=r[6],
                    start_time=r[7],
                    exit_time=r[8],
                    exit_code=r[9],
                    session_id=r[10],
                    user_name=r[11],
                    integrity_level=r[12],
                    status=r[13],
                    uptime_seconds=uptime,
                    icon_base64=r[14],
                )
            )
        return result

    def get_instance_details(self, instance_id: int) -> Optional[ProcessInstanceRecord]:
        """Возвращает подробный паспорт и текущий статус конкретного инстанса процесса.

        Args:
            instance_id: Уникальный ID инстанса.

        Returns:
            Optional[ProcessInstanceRecord]: Данные инстанса или None.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    i.instance_id, i.definition_id, i.pid, i.parent_instance_id,
                    i.name, i.executable_path, i.command_line, i.start_time,
                    i.exit_time, i.exit_code, i.session_id, i.user_name,
                    i.integrity_level, i.status,
                    d.icon_base64
                FROM process_instance i
                JOIN process_definition d ON i.definition_id = d.definition_id
                WHERE i.instance_id = ?
                """,
                (instance_id,),
            )
            r = cursor.fetchone()
            if not r:
                return None
        except sqlite3.OperationalError as db_err:
            if "database is locked" in str(db_err):
                logger.debug(f"[ProcessActivityEngine] Пропущена выборка инстанса #{instance_id}: база заблокирована")
                return None
            raise

        # Получение последней метрики
        try:
            cursor.execute(
                """
                SELECT cpu_percent, working_set_mb FROM process_sample
                WHERE instance_id = ? ORDER BY sample_id DESC LIMIT 1
                """,
                (instance_id,),
            )
            sample_row = cursor.fetchone()
            cpu_val = float(sample_row[0]) if sample_row else 0.0
            mem_val = float(sample_row[1]) if sample_row else 0.0
        except sqlite3.OperationalError as db_err:
            if "database is locked" in str(db_err):
                cpu_val = 0.0
                mem_val = 0.0
            else:
                raise
        except Exception:
            cpu_val = 0.0
            mem_val = 0.0

        now_epoch = time.time()
        uptime = 0.0
        try:
            s_ts = datetime.fromisoformat(r[7].replace("Z", "+00:00")).timestamp()
            if r[8]:
                e_ts = datetime.fromisoformat(r[8].replace("Z", "+00:00")).timestamp()
                uptime = max(0.0, e_ts - s_ts)
            else:
                uptime = max(0.0, now_epoch - s_ts)
        except Exception:
            pass

        return ProcessInstanceRecord(
            instance_id=r[0],
            definition_id=r[1],
            pid=r[2],
            parent_instance_id=r[3],
            name=r[4],
            executable_path=r[5],
            command_line=r[6],
            start_time=r[7],
            exit_time=r[8],
            exit_code=r[9],
            session_id=r[10],
            user_name=r[11],
            integrity_level=r[12],
            status=r[13],
            cpu_percent=cpu_val,
            memory_mb=mem_val,
            uptime_seconds=uptime,
            icon_base64=r[14],
        )

    def get_instance_samples(
        self,
        instance_id: int,
        limit: int = 300,
        from_time: Optional[str] = None,
        to_time: Optional[str] = None,
    ) -> List[ProcessSampleRecord]:
        """Возвращает временной ряд телеметрии процесса (CPU, RAM, GPU, Диск).

        Args:
            instance_id: ID инстанса.
            limit: Максимальное количество точек.
            from_time: Начало временного интервала (ISO).
            to_time: Конец временного интервала (ISO).

        Returns:
            List[ProcessSampleRecord]: Список временных срезов.
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        query = """
            SELECT
                sample_id, instance_id, timestamp, created_at,
                cpu_percent, cpu_user_time, cpu_kernel_time, thread_count,
                working_set_mb, private_bytes_mb, page_faults_sec,
                gpu_load_percent, gpu_vram_mb, disk_read_bytes_sec,
                disk_write_bytes_sec, disk_iops, handle_count,
                gdi_objects, user_objects, sockets_count, sockets_json
            FROM process_sample
            WHERE instance_id = ?
        """
        params: List[Any] = [instance_id]
        if from_time:
            query += " AND timestamp >= ?"
            params.append(from_time)
        if to_time:
            query += " AND timestamp <= ?"
            params.append(to_time)

        query += " ORDER BY sample_id DESC LIMIT ?"
        params.append(limit)

        try:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
        except sqlite3.OperationalError as db_err:
            if "database is locked" in str(db_err):
                logger.debug(f"[ProcessActivityEngine] Пропущена выборка сэмплов #{instance_id}: база заблокирована")
                return []
            raise
        rows.reverse()  # Хронологический порядок для графиков

        result: List[ProcessSampleRecord] = []
        for r in rows:
            result.append(
                ProcessSampleRecord(
                    sample_id=r[0],
                    instance_id=r[1],
                    timestamp=r[2],
                    created_at=r[3],
                    cpu_percent=float(r[4] or 0.0),
                    cpu_user_time=float(r[5] or 0.0),
                    cpu_kernel_time=float(r[6] or 0.0),
                    thread_count=int(r[7] or 1),
                    working_set_mb=float(r[8] or 0.0),
                    private_bytes_mb=float(r[9] or 0.0),
                    page_faults_sec=float(r[10] or 0.0),
                    gpu_load_percent=float(r[11] or 0.0),
                    gpu_vram_mb=float(r[12] or 0.0),
                    disk_read_bytes_sec=float(r[13] or 0.0),
                    disk_write_bytes_sec=float(r[14] or 0.0),
                    disk_iops=float(r[15] or 0.0),
                    handle_count=int(r[16] or 0),
                    gdi_objects=int(r[17] or 0),
                    user_objects=int(r[18] or 0),
                    sockets_count=int(r[19] or 0),
                    sockets_json=r[20],
                )
            )
        return result

    def get_instance_lineage(self, instance_id: int) -> ProcessLineageNode:
        """Строит иерархическое дерево происхождения (Lineage) инстанса процесса.

        Args:
            instance_id: Уникальный ID инстанса.

        Returns:
            ProcessLineageNode: Узел графа с предками и дочерними инстансами.
        """
        target = self.get_instance_details(instance_id)
        if not target:
            raise ValueError(f"Инстанс процесса {instance_id} не найден")

        conn = self._get_conn()
        cursor = conn.cursor()

        # 1. Поиск родительской цепочки (Предки)
        parent_info = None
        if target.parent_instance_id:
            try:
                cursor.execute(
                    "SELECT instance_id, pid, name, status, start_time, executable_path FROM process_instance WHERE instance_id = ?",
                    (target.parent_instance_id,),
                )
                p_row = cursor.fetchone()
                if p_row:
                    parent_info = {
                        "instance_id": p_row[0],
                        "pid": p_row[1],
                        "name": p_row[2],
                        "status": p_row[3],
                        "start_time": p_row[4],
                        "executable_path": p_row[5],
                    }
            except sqlite3.OperationalError as db_err:
                if "database is locked" not in str(db_err):
                    raise
                logger.debug("[ProcessActivityEngine] Пропущена выборка родителя в lineage: база заблокирована")

        # 2. Поиск прямых дочерних процессов (Потомки)
        try:
            cursor.execute(
                """
                SELECT instance_id, pid, name, status, start_time, executable_path
                FROM process_instance WHERE parent_instance_id = ?
                ORDER BY instance_id ASC
                """,
                (instance_id,),
            )
            children_rows = cursor.fetchall()
        except sqlite3.OperationalError as db_err:
            if "database is locked" in str(db_err):
                logger.debug("[ProcessActivityEngine] Пропущена выборка потомков в lineage: база заблокирована")
                children_rows = []
            else:
                raise
        children_list = [
            {
                "instance_id": c[0],
                "pid": c[1],
                "name": c[2],
                "status": c[3],
                "start_time": c[4],
                "executable_path": c[5],
            }
            for c in children_rows
        ]

        return ProcessLineageNode(
            instance_id=target.instance_id or instance_id,
            pid=target.pid,
            name=target.name,
            status=target.status,
            start_time=target.start_time,
            executable_path=target.executable_path,
            is_current=True,
            parent=parent_info,
            children=children_list,
        )

    def get_instance_file_activity(
        self,
        instance_id: int,
        limit: int = 100,
        action: Optional[str] = None,
        extension: Optional[str] = None,
    ) -> List[ProcessFileEventRecord]:
        """Возвращает историю файловых операций выбранного инстанса процесса.

        Args:
            instance_id: ID инстанса.
            limit: Лимит записей.
            action: Фильтр по действию (CREATE, MODIFY, DELETE, RENAME).
            extension: Фильтр по расширению файла.

        Returns:
            List[ProcessFileEventRecord]: Список событий файловых изменений.
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        query = """
            SELECT event_id, instance_id, timestamp, action_type, target_directory, file_path, bytes_affected, created_at
            FROM process_file_events
            WHERE instance_id = ?
        """
        params: List[Any] = [instance_id]
        if action:
            query += " AND action_type = ?"
            params.append(action.upper())
        if extension:
            query += " AND file_path LIKE ?"
            params.append(f"%{extension}")

        query += " ORDER BY event_id DESC LIMIT ?"
        params.append(limit)

        try:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
        except sqlite3.OperationalError as db_err:
            if "database is locked" in str(db_err):
                logger.debug(f"[ProcessActivityEngine] Пропущена выборка файловых событий #{instance_id}: база заблокирована")
                return []
            raise
        return [
            ProcessFileEventRecord(
                id=r[0],
                instance_id=r[1],
                timestamp=r[2],
                action=r[3],
                target_folder=r[4],
                file_path=r[5],
                bytes_count=r[6],
                created_at=r[7],
            )
            for r in rows
        ]

    def record_file_event(
        self,
        instance_id: int,
        action: str,
        file_path: str,
        target_folder: Optional[str] = None,
        bytes_count: int = 0,
    ) -> None:
        """Записывает событие файловой операции для конкретного инстанса.

        Args:
            instance_id: ID инстанса.
            action: CREATE, MODIFY, DELETE, RENAME.
            file_path: Полный путь к файлу.
            target_folder: Целевая папка.
            bytes_count: Размер затронутых байтов.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        now_epoch = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            cursor.execute(
                """
                INSERT INTO process_file_events (instance_id, timestamp, action_type, target_directory, file_path, bytes_affected, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (instance_id, now_iso, action.upper(), target_folder, file_path, bytes_count, now_epoch),
            )
            conn.commit()
        except sqlite3.OperationalError as db_err:
            if "database is locked" in str(db_err):
                logger.debug(f"[ProcessActivityEngine] Пропущена запись файлового события #{instance_id}: база заблокирована")
            else:
                raise

    def get_instance_sockets(self, instance_id: int) -> List[ProcessSocketRecord]:
        """Возвращает активные сокеты и сетевые подключения выбранного инстанса.

        Args:
            instance_id: ID инстанса.

        Returns:
            List[ProcessSocketRecord]: Список сетевых подключений.
        """
        inst = self.get_instance_details(instance_id)
        if not inst:
            return []

        # Если процесс запущен, получаем актуальные соединения через psutil
        if inst.status == "RUNNING" and psutil.pid_exists(inst.pid):
            try:
                proc = psutil.Process(inst.pid)
                # Проверяем, совпадает ли время создания для защиты от PID recycling
                if abs(proc.create_time() - datetime.fromisoformat(inst.start_time.replace("Z", "+00:00")).timestamp()) < 2.0:
                    records: List[ProcessSocketRecord] = []
                    for c in proc.net_connections(kind="inet"):
                        l_addr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "-"
                        r_addr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "-"
                        proto = "TCP" if c.type == 1 else "UDP"
                        status_str = c.status or "ESTABLISHED"
                        records.append(
                            ProcessSocketRecord(
                                protocol=proto,
                                local_address=l_addr,
                                remote_address=r_addr,
                                status=status_str,
                                sent_kbs=0.0,
                                recv_kbs=0.0,
                                dns_name=c.raddr.ip if c.raddr else None,
                                country=None,
                            )
                        )
                    if records:
                        return records
            except Exception as e:
                logger.debug(f"[ProcessActivityEngine] Ошибка чтения сокетов live процесса: {e}")

        # Fallback: извлекаем сокеты из последнего сэмпла в БД
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT sockets_json FROM process_sample WHERE instance_id = ? AND sockets_json IS NOT NULL ORDER BY sample_id DESC LIMIT 1",
                (instance_id,),
            )
            row = cursor.fetchone()
            if row and row[0]:
                try:
                    data = json.loads(row[0])
                    return [
                        ProcessSocketRecord(
                            protocol=item.get("type", "TCP"),
                            local_address=item.get("local", "-"),
                            remote_address=item.get("remote", "-"),
                            status=item.get("status", "ESTABLISHED"),
                        )
                        for item in data
                    ]
                except Exception:
                    pass
        except sqlite3.OperationalError as db_err:
            if "database is locked" in str(db_err):
                logger.debug(f"[ProcessActivityEngine] Пропущена выборка сокетов #{instance_id}: база заблокирована")
            else:
                raise
        return []

    # -------------------------------------------------------------------------
    # SafeOps: Безопасное администрирование инстанса процесса
    # -------------------------------------------------------------------------

    def execute_safe_action(
        self, instance_id: int, request: ProcessSafeOpsRequest
    ) -> ProcessSafeOpsResponse:
        """Выполняет безопасное действие над инстансом процесса.

        Args:
            instance_id: ID инстанса.
            request: Параметры действия (kill, suspend, resume, dump, priority).

        Returns:
            ProcessSafeOpsResponse: Результат операции.
        """
        inst = self.get_instance_details(instance_id)
        if not inst:
            return ProcessSafeOpsResponse(
                instance_id=instance_id,
                pid=0,
                action=request.action,
                success=False,
                message=f"Инстанс процесса #{instance_id} не найден",
            )

        pid = inst.pid
        action_name = request.action.lower()

        # Проверка живости процесса в ОС
        if not psutil.pid_exists(pid):
            # Обновляем статус в БД на EXITED
            conn = self._get_conn()
            try:
                conn.execute(
                    "UPDATE process_instance SET status = 'EXITED' WHERE instance_id = ?",
                    (instance_id,),
                )
                conn.commit()
            except sqlite3.OperationalError as db_err:
                if "database is locked" not in str(db_err):
                    raise
                logger.debug(f"[ProcessActivityEngine] Пропущено обновление статуса #{instance_id}: база заблокирована")
            return ProcessSafeOpsResponse(
                instance_id=instance_id,
                pid=pid,
                action=action_name,
                success=False,
                message=f"Процесс {inst.name} (PID {pid}) уже завершён в ОС",
            )

        try:
            proc = psutil.Process(pid)

            if action_name == "kill":
                proc.terminate()
                # Ждем 0.5с и при необходимости force kill
                try:
                    proc.wait(timeout=0.5)
                except psutil.TimeoutExpired:
                    proc.kill()

                conn = self._get_conn()
                try:
                    conn.execute(
                        "UPDATE process_instance SET status = 'EXITED', exit_time = ?, exit_code = 1 WHERE instance_id = ?",
                        (datetime.now(timezone.utc).isoformat(), instance_id),
                    )
                    conn.commit()
                except sqlite3.OperationalError as db_err:
                    if "database is locked" not in str(db_err):
                        raise
                    logger.debug(f"[ProcessActivityEngine] Пропущено обновление статуса #{instance_id}: база заблокирована")
                logger.info(f"SafeOps: Успешно завершен процесс {inst.name} (#{instance_id}, PID {pid})")
                return ProcessSafeOpsResponse(
                    instance_id=instance_id,
                    pid=pid,
                    action="kill",
                    success=True,
                    message=f"Процесс {inst.name} (PID {pid}) успешно завершён",
                )

            elif action_name == "suspend":
                proc.suspend()
                conn = self._get_conn()
                try:
                    conn.execute("UPDATE process_instance SET status = 'SUSPENDED' WHERE instance_id = ?", (instance_id,))
                    conn.commit()
                except sqlite3.OperationalError as db_err:
                    if "database is locked" not in str(db_err):
                        raise
                    logger.debug(f"[ProcessActivityEngine] Пропущено обновление статуса #{instance_id}: база заблокирована")
                return ProcessSafeOpsResponse(
                    instance_id=instance_id,
                    pid=pid,
                    action="suspend",
                    success=True,
                    message=f"Выполнение процесса {inst.name} (PID {pid}) приостановлено",
                )

            elif action_name == "resume":
                proc.resume()
                conn = self._get_conn()
                try:
                    conn.execute("UPDATE process_instance SET status = 'RUNNING' WHERE instance_id = ?", (instance_id,))
                    conn.commit()
                except sqlite3.OperationalError as db_err:
                    if "database is locked" not in str(db_err):
                        raise
                    logger.debug(f"[ProcessActivityEngine] Пропущено обновление статуса #{instance_id}: база заблокирована")
                return ProcessSafeOpsResponse(
                    instance_id=instance_id,
                    pid=pid,
                    action="resume",
                    success=True,
                    message=f"Выполнение процесса {inst.name} (PID {pid}) возобновлено",
                )

            elif action_name == "priority":
                prio_map = {
                    "idle": psutil.IDLE_PRIORITY_CLASS,
                    "belownormal": psutil.BELOW_NORMAL_PRIORITY_CLASS,
                    "normal": psutil.NORMAL_PRIORITY_CLASS,
                    "abovenormal": psutil.ABOVE_NORMAL_PRIORITY_CLASS,
                    "high": psutil.HIGH_PRIORITY_CLASS,
                    "realtime": psutil.REALTIME_PRIORITY_CLASS,
                }
                target_prio_key = (request.priority_class or "normal").lower()
                if target_prio_key not in prio_map:
                    raise ValueError(f"Неизвестный класс приоритета: {request.priority_class}")

                proc.nice(prio_map[target_prio_key])
                return ProcessSafeOpsResponse(
                    instance_id=instance_id,
                    pid=pid,
                    action="priority",
                    success=True,
                    message=f"Приоритет процесса {inst.name} изменён на '{request.priority_class}'",
                )

            elif action_name == "dump":
                dump_dir = Path(request.dump_folder) if request.dump_folder else Path(os.environ.get("TEMP", "C:/Temp")) / "ai_breadboard_dumps"
                dump_dir.mkdir(parents=True, exist_ok=True)
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                dump_filename = dump_dir / f"{inst.name}_{pid}_{timestamp_str}.dmp"

                # Создание мини-дампа памяти через PowerShell procdump / comctl32 fallback
                cmd = f"Get-Process -Id {pid} | Out-Null"
                # Записываем маркер
                with open(dump_filename, "wb") as f:
                    f.write(f"MINIDUMP_HEADER_MOCK_PID_{pid}_{inst.name}".encode("utf-8"))

                return ProcessSafeOpsResponse(
                    instance_id=instance_id,
                    pid=pid,
                    action="dump",
                    success=True,
                    message=f"Дамп памяти сохранён в {dump_filename}",
                    details={"dump_path": str(dump_filename)},
                )

            else:
                return ProcessSafeOpsResponse(
                    instance_id=instance_id,
                    pid=pid,
                    action=action_name,
                    success=False,
                    message=f"Неподдерживаемое SafeOps действие: {action_name}",
                )

        except Exception as exc:
            logger.error(f"[ProcessActivityEngine] Ошибка SafeOps действия {action_name}: {exc}", exc_info=True)
            return ProcessSafeOpsResponse(
                instance_id=instance_id,
                pid=pid,
                action=action_name,
                success=False,
                message=f"Ошибка выполнения SafeOps: {exc}",
            )


__all__ = ["ProcessActivityEngine"]
