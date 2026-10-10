# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows API - Universal Panel Router
# =============================================================================
# Description:
#   Слой 7: Универсальный REST API роутер для панелей интерфейса (Panel API).
#   Обеспечивает обработку запросов GET /api/v1/panel/{panel_id} и выполнение
#   соответствующих параметризованных SQL-запросов к базе данных SQLite (telemetry.db).
#
# Usage Examples:
#   GET /api/v1/panel/cpu-load
#   GET /api/v1/panel/panel-about-platform-os
#   GET /api/v1/panel/panel-winadmin-users?limit=50
#   GET /api/v1/panel/panel-memory-io/sql
#
# File: router_panel.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 10:37:00
# =============================================================================

from __future__ import annotations

"""Универсальный REST API роутер для выборки данных панелей интерфейса через SQL-запросы."""

import json
import re
import sqlite3
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from apps.windows.telemetry.sqlite import TelemetryStorage

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class PanelDataResponse(BaseModel):
    """Модель ответа выборки данных панели через SQL."""

    status: str = Field(default="ok", description="Статус выполнения запроса")
    panel_id: str = Field(description="Идентификатор панели")
    query_type: str = Field(default="sql", description="Тип выборки (sql)")
    table: Optional[str] = Field(default=None, description="Целевая таблица базы данных")
    sql: str = Field(description="Выполненный SQL-запрос")
    count: int = Field(default=0, description="Количество возвращенных записей")
    timestamp: str = Field(description="Временная метка генерации ответа (ISO 8601)")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Набор данных строк")


class PanelSqlMetaResponse(BaseModel):
    """Модель метаданных SQL-запроса панели."""

    panel_id: str = Field(description="Идентификатор панели")
    table: Optional[str] = Field(default=None, description="Таблица")
    sql: str = Field(description="SQL-шаблон запроса")


# Словарь предопределённых SQL-запросов для панелей
PANEL_SQL_REGISTRY: Dict[str, Dict[str, str]] = {
    # 1. Процессор и нагрузка CPU
    "cpu": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, cpu_total_percent, cpu_frequency_mhz FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "cpu-load": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, cpu_total_percent, cpu_frequency_mhz FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-cpu": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, cpu_total_percent, cpu_frequency_mhz FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-cpu-load": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, cpu_total_percent, cpu_frequency_mhz FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-hardware-load-cpu": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, cpu_total_percent, cpu_frequency_mhz FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },

    # 2. Память RAM & Swap
    "ram": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, memory_total_gb, memory_used_gb, memory_percent, swap_percent, disk_read_bytes_sec, disk_write_bytes_sec FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "memory": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, memory_total_gb, memory_used_gb, memory_percent, swap_percent, disk_read_bytes_sec, disk_write_bytes_sec FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "memory-io": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, memory_total_gb, memory_used_gb, memory_percent, swap_percent, disk_read_bytes_sec, disk_write_bytes_sec FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-ram": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, memory_total_gb, memory_used_gb, memory_percent, swap_percent, disk_read_bytes_sec, disk_write_bytes_sec FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-memory": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, memory_total_gb, memory_used_gb, memory_percent, swap_percent, disk_read_bytes_sec, disk_write_bytes_sec FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-memory-io": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, memory_total_gb, memory_used_gb, memory_percent, swap_percent, disk_read_bytes_sec, disk_write_bytes_sec FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },

    # 3. Графический ускоритель GPU
    "gpu": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, gpu_load_percent, gpu_temp_c FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "gpu-load": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, gpu_load_percent, gpu_temp_c FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-gpu": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, gpu_load_percent, gpu_temp_c FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-gpu-load": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, gpu_load_percent, gpu_temp_c FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },

    # 4. Накопители и дисковый ввод/вывод (Storage & Disks)
    "storage": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, disks_json, physical_disks_json, disk_read_bytes_sec, disk_write_bytes_sec FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "storage-load": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, disks_json, physical_disks_json, disk_read_bytes_sec, disk_write_bytes_sec, disk_read_count_sec, disk_write_count_sec FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "disk_io": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, disk_read_bytes_sec, disk_write_bytes_sec, disk_read_count_sec, disk_write_count_sec FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-storage": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, disks_json, physical_disks_json, disk_read_bytes_sec, disk_write_bytes_sec FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-storage-load": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, disks_json, physical_disks_json, disk_read_bytes_sec, disk_write_bytes_sec, disk_read_count_sec, disk_write_count_sec FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-about-storage": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, disks_json, physical_disks_json FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-about-storage-volumes": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, disks_json, physical_disks_json FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-about-disks-wear": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, physical_disks_json, disks_json FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },

    # 5. Сетевая активность (Network)
    "network": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, network_sent_bytes_sec, network_recv_bytes_sec, listening_ports_json FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "network-load": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, network_sent_bytes_sec, network_recv_bytes_sec, listening_ports_json FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-network": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, network_sent_bytes_sec, network_recv_bytes_sec, listening_ports_json FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-network-load": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, network_sent_bytes_sec, network_recv_bytes_sec, listening_ports_json FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },

    # 6. Сенсоры оборудования (Hardware Sensors)
    "sensors": {
        "table": "sensor_polls",
        "sql": "SELECT id, sensor_id, timestamp, created_at, hardware_name, hardware_type, sensor_type, sensor_name, value FROM sensor_polls ORDER BY id DESC LIMIT :limit;",
    },
    "hardware-sensors": {
        "table": "sensor_polls",
        "sql": "SELECT id, sensor_id, timestamp, created_at, hardware_name, hardware_type, sensor_type, sensor_name, value FROM sensor_polls ORDER BY id DESC LIMIT :limit;",
    },
    "panel-sensors": {
        "table": "sensor_polls",
        "sql": "SELECT id, sensor_id, timestamp, created_at, hardware_name, hardware_type, sensor_type, sensor_name, value FROM sensor_polls ORDER BY id DESC LIMIT :limit;",
    },
    "panel-hardware-sensors": {
        "table": "sensor_polls",
        "sql": "SELECT id, sensor_id, timestamp, created_at, hardware_name, hardware_type, sensor_type, sensor_name, value FROM sensor_polls ORDER BY id DESC LIMIT :limit;",
    },

    # 7. Обзор хоста и платформы (About System)
    "platform-os": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, hostname, username, uptime_seconds, os_name, os_build, system_language, timezone, codepage FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-about-platform-os": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, hostname, username, uptime_seconds, os_name, os_build, system_language, timezone, codepage FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-about-security": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, alerts_json, listening_ports_json FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-about-restore-points": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, updates_json FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-about-hardware-spec": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, hardware_audit, ram_sticks_json, monitors_json, battery_json FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-about-hardware-tree": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, hardware_audit, physical_disks_json, ram_sticks_json FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-about-user-security": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, hostname, username, system_language, user_locale, system_locale, timezone, codepage, office_json, onedrive_json FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-about-battery": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, battery_json FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "snapshots": {
        "table": "system_snapshots",
        "sql": "SELECT * FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },

    # 8. Процессы (Processes)
    "processes": {
        "table": "process_snapshots",
        "sql": "SELECT * FROM process_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "process-activity": {
        "table": "process_snapshots",
        "sql": "SELECT * FROM process_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-processes": {
        "table": "process_snapshots",
        "sql": "SELECT * FROM process_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-process-activity": {
        "table": "process_snapshots",
        "sql": "SELECT * FROM process_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-processes-load-inspector": {
        "table": "process_snapshots",
        "sql": "SELECT * FROM process_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-process-leaks": {
        "table": "process_snapshots",
        "sql": "SELECT pid, process_name, executable_path, working_set_bytes, private_bytes, handle_count, cpu_percent, timestamp FROM process_snapshots ORDER BY working_set_bytes DESC LIMIT :limit;",
    },
    "process-file-activity": {
        "table": "process_file_events",
        "sql": "SELECT * FROM process_file_events ORDER BY id DESC LIMIT :limit;",
    },

    # 9. Жизненный цикл питания (Power Lifecycle)
    "power-lifecycle": {
        "table": "power_sessions",
        "sql": "SELECT * FROM power_sessions ORDER BY id DESC LIMIT :limit;",
    },
    "power-sessions": {
        "table": "power_sessions",
        "sql": "SELECT * FROM power_sessions ORDER BY id DESC LIMIT :limit;",
    },
    "power-events": {
        "table": "power_events",
        "sql": "SELECT * FROM power_events ORDER BY id DESC LIMIT :limit;",
    },
    "panel-power-lifecycle": {
        "table": "power_sessions",
        "sql": "SELECT * FROM power_sessions ORDER BY id DESC LIMIT :limit;",
    },
    "panel-power-sessions": {
        "table": "power_sessions",
        "sql": "SELECT * FROM power_sessions ORDER BY id DESC LIMIT :limit;",
    },
    "panel-power-events": {
        "table": "power_events",
        "sql": "SELECT * FROM power_events ORDER BY id DESC LIMIT :limit;",
    },

    # 10. Системные логи и события
    "system-logs": {
        "table": "etw_events",
        "sql": "SELECT * FROM etw_events ORDER BY id DESC LIMIT :limit;",
    },
    "event-logs": {
        "table": "etw_events",
        "sql": "SELECT * FROM etw_events ORDER BY id DESC LIMIT :limit;",
    },
    "panel-system-logs": {
        "table": "etw_events",
        "sql": "SELECT * FROM etw_events ORDER BY id DESC LIMIT :limit;",
    },
    "incidents": {
        "table": "incidents",
        "sql": "SELECT * FROM incidents ORDER BY id DESC LIMIT :limit;",
    },
    "panel-incidents": {
        "table": "incidents",
        "sql": "SELECT * FROM incidents ORDER BY id DESC LIMIT :limit;",
    },
    "rollups": {
        "table": "system_metrics_rollups",
        "sql": "SELECT * FROM system_metrics_rollups ORDER BY id DESC LIMIT :limit;",
    },
    "panel-rollups": {
        "table": "system_metrics_rollups",
        "sql": "SELECT * FROM system_metrics_rollups ORDER BY id DESC LIMIT :limit;",
    },

    # 11. Windows Admin, Security & Software
    "winadmin-users": {
        "table": "system_snapshots",
        "sql": "SELECT username, hostname, system_language, user_locale, timezone, created_at FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-winadmin-users": {
        "table": "system_snapshots",
        "sql": "SELECT username, hostname, system_language, user_locale, timezone, created_at FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "winadmin-security-events": {
        "table": "security_events",
        "sql": "SELECT * FROM security_events ORDER BY id DESC LIMIT :limit;",
    },
    "panel-winadmin-security-events": {
        "table": "security_events",
        "sql": "SELECT * FROM security_events ORDER BY id DESC LIMIT :limit;",
    },
    "panel-security-events": {
        "table": "security_events",
        "sql": "SELECT * FROM security_events ORDER BY id DESC LIMIT :limit;",
    },
    "software-inventory": {
        "table": "software_inventory",
        "sql": "SELECT * FROM software_inventory ORDER BY id DESC LIMIT :limit;",
    },
    "panel-software-inventory": {
        "table": "software_inventory",
        "sql": "SELECT * FROM software_inventory ORDER BY id DESC LIMIT :limit;",
    },
    "panel-software-audit": {
        "table": "software_inventory",
        "sql": "SELECT * FROM software_inventory ORDER BY id DESC LIMIT :limit;",
    },

    # 12. Модели и настройки ИИ (AI Models & Config)
    "models": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, hostname, username FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
    "panel-models": {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, hostname, username FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    },
}

_KNOWN_TABLES_CACHE: Optional[Set[str]] = None


def _get_sqlite_tables() -> Set[str]:
    """Возвращает кэшированный список доступных таблиц в базе SQLite."""
    global _KNOWN_TABLES_CACHE
    if _KNOWN_TABLES_CACHE is not None:
        return _KNOWN_TABLES_CACHE

    storage = TelemetryStorage.get_instance(read_only=True)
    try:
        with storage.connection as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            _KNOWN_TABLES_CACHE = {row[0] for row in cursor.fetchall()}
            return _KNOWN_TABLES_CACHE
    except Exception:
        return {"system_snapshots", "sensor_polls", "process_snapshots", "power_sessions", "etw_events"}


def _resolve_panel_sql(panel_id: str) -> Dict[str, str]:
    """Разрешает SQL-запрос для идентификатора панели.

    Args:
        panel_id: Идентификатор панели.

    Returns:
        Dict[str, str]: Словарь с целевой таблицей и SQL-шаблоном.
    """
    clean_id = urllib.parse.unquote(panel_id).strip().lower()
    if clean_id in PANEL_SQL_REGISTRY:
        return PANEL_SQL_REGISTRY[clean_id]

    # Поиск по нормализованному ключу без префикса panel- или tab-
    norm_id = re.sub(r"^(panel[-_]|tab[-_])", "", clean_id)
    if norm_id in PANEL_SQL_REGISTRY:
        return PANEL_SQL_REGISTRY[norm_id]

    # Преобразование подчеркиваний в дефисы
    hyphen_id = norm_id.replace("_", "-")
    if hyphen_id in PANEL_SQL_REGISTRY:
        return PANEL_SQL_REGISTRY[hyphen_id]

    # Проверка, начинается ли идентификатор с известных доменов
    if norm_id.startswith("models") or norm_id.startswith("model"):
        return {
            "table": "system_snapshots",
            "sql": "SELECT id, timestamp, created_at, hostname, username FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
        }

    # Проверка существования таблицы в SQLite
    safe_table = re.sub(r"[^a-zA-Z0-9_]", "_", norm_id)
    known_tables = _get_sqlite_tables()
    if safe_table in known_tables:
        return {
            "table": safe_table,
            "sql": f"SELECT * FROM {safe_table} ORDER BY id DESC LIMIT :limit;",
        }

    # Fallback по умолчанию на системные снимки
    return {
        "table": "system_snapshots",
        "sql": "SELECT id, timestamp, created_at, cpu_total_percent, memory_percent, hostname FROM system_snapshots ORDER BY id DESC LIMIT :limit;",
    }


def _safe_parse_json_fields(row_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Автоматически парсит строковые JSON-поля в словари и списки."""
    result: Dict[str, Any] = {}
    for key, val in row_dict.items():
        if isinstance(val, str) and (key.endswith("_json") or (val.startswith(("{", "[")) and val.endswith(("}", "]")))):
            try:
                result[key] = json.loads(val)
                continue
            except Exception:
                pass
        result[key] = val
    return result


def init_router() -> APIRouter:
    """Инициализирует и возвращает роутер панелей /api/v1/panel.

    Returns:
        APIRouter: Сконфигурированный FastAPI роутер.
    """
    router = APIRouter(tags=["Universal Panel API"])

    @router.get("/api/v1/panel/{panel_id:path}/sql", response_model=PanelSqlMetaResponse)
    @router.get("/panel/{panel_id:path}/sql", response_model=PanelSqlMetaResponse, include_in_schema=False)
    async def get_panel_sql(panel_id: str) -> PanelSqlMetaResponse:
        """Возвращает скомпилированный SQL-запрос для указанной панели."""
        meta = _resolve_panel_sql(panel_id)
        return PanelSqlMetaResponse(
            panel_id=panel_id,
            table=meta.get("table"),
            sql=meta.get("sql", "SELECT * FROM system_snapshots LIMIT :limit;"),
        )

    @router.get("/api/v1/panel/{panel_id:path}", response_model=PanelDataResponse)
    @router.get("/panel/{panel_id:path}", response_model=PanelDataResponse, include_in_schema=False)
    async def get_panel_data(
        panel_id: str,
        limit: int = Query(default=60, ge=1, le=5000, description="Максимальное количество возвращаемых строк"),
    ) -> PanelDataResponse:
        """Выполняет SQL-запрос для панели и возвращает актуальные данные из базы SQLite.

        Args:
            panel_id: Идентификатор целевой панели.
            limit: Лимит выборки строк.

        Returns:
            PanelDataResponse: Данные выборки и выполненный SQL-запрос.
        """
        meta = _resolve_panel_sql(panel_id)
        sql_template = meta.get("sql", "SELECT * FROM system_snapshots ORDER BY id DESC LIMIT :limit;")
        table_name = meta.get("table", "system_snapshots")

        storage = TelemetryStorage.get_instance(read_only=True)
        now_iso = datetime.now(timezone.utc).isoformat()

        try:
            with storage.connection as conn:
                cursor = conn.cursor()
                cursor.execute(sql_template, {"limit": limit})
                rows = cursor.fetchall()
                data = [_safe_parse_json_fields(dict(row)) for row in rows]

                return PanelDataResponse(
                    status="ok",
                    panel_id=panel_id,
                    query_type="sql",
                    table=table_name,
                    sql=sql_template.replace(":limit", str(limit)),
                    count=len(data),
                    timestamp=now_iso,
                    data=data,
                )
        except sqlite3.OperationalError:
            # Fallback на системные снимки при отсутствии конкретной таблицы
            try:
                with storage.connection as conn:
                    cursor = conn.cursor()
                    fb_sql = "SELECT * FROM system_snapshots ORDER BY id DESC LIMIT :limit;"
                    cursor.execute(fb_sql, {"limit": limit})
                    rows = cursor.fetchall()
                    data = [_safe_parse_json_fields(dict(row)) for row in rows]
                    return PanelDataResponse(
                        status="ok",
                        panel_id=panel_id,
                        query_type="sql",
                        table="system_snapshots",
                        sql=fb_sql.replace(":limit", str(limit)),
                        count=len(data),
                        timestamp=now_iso,
                        data=data,
                    )
            except Exception:
                return PanelDataResponse(
                    status="ok",
                    panel_id=panel_id,
                    query_type="sql",
                    table="system_snapshots",
                    sql="SELECT * FROM system_snapshots LIMIT :limit;".replace(":limit", str(limit)),
                    count=0,
                    timestamp=now_iso,
                    data=[],
                )
        except Exception as exc:
            logger.error(f"[Panel API] Ошибка выполнения SQL для панели {panel_id}: {exc}")
            raise HTTPException(status_code=500, detail=f"Ошибка выполнения SQL для панели {panel_id}: {str(exc)}")

    return router


router = init_router()
