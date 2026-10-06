# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Sqlite - Writer
# =============================================================================
# Description:
#   Класс TelemetryWriter для сериализации и записи телеметрии в SQLite.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.sqlite.writer import TelemetryWriter
#
#     writer = TelemetryWriter(connection_manager)
#     saved = writer.batch_insert_records(records)
#
# File: writer.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.sqlite
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 13:57:00
# =============================================================================

from __future__ import annotations

"""Класс TelemetryWriter для сериализации, подготовки строк и транзакционной записи в SQLite."""

import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .connection import TelemetryConnectionManager
from ..models import (
    HardwareArchiveEntry,
    ProcessLifecycleEvent,
    ProcessProvenanceInfo,
    StartupArchiveEntry,
    SystemMetricRollup,
    SystemSnapshot,
    TelemetryIncident,
)

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class TelemetryWriter:
    """Выполняет пакетную и прямую вставку записей телеметрии в базу данных SQLite."""

    def __init__(self, connection_manager: TelemetryConnectionManager) -> None:
        """Инициализирует писатель телеметрии.

        Args:
            connection_manager: Менеджер соединений SQLite.
        """
        self._cm = connection_manager

    def batch_insert_records(self, records: List[Dict[str, Any]]) -> int:
        """Выполняет пакетную вставку разнородных записей в SQLite в единой транзакции.

        Args:
            records: Список словарей записей.

        Returns:
            int: Общее число сохраненных записей.
        """
        if not records or self._cm.read_only:
            return 0

        saved_total = 0
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            sensor_poll_rows: List[tuple] = []
            sensor_agg_rows: List[tuple] = []

            for item in records:
                rec_type = item.get('type')

                if rec_type == 'snapshot':
                    self.insert_snapshot_row(cursor, item)
                    saved_total += 1

                elif rec_type == 'sensor_poll':
                    sensor_poll_rows.append(self.prepare_sensor_poll_row(item.get('data', {}), item.get('timestamp')))

                elif rec_type == 'sensor_polls_batch':
                    ts = item.get('timestamp')
                    for s in item.get('data', []):
                        sensor_poll_rows.append(self.prepare_sensor_poll_row(s, ts))

                elif rec_type == 'sensor_aggregates_batch':
                    for a in item.get('data', []):
                        sensor_agg_rows.append((
                            a.get('sensor_id', ''),
                            a.get('period_start', ''),
                            a.get('period_end', ''),
                            a.get('avg', None),
                            a.get('min', None),
                            a.get('max', None),
                            a.get('count', 0),
                            json.dumps(a, ensure_ascii=False, default=str),
                        ))

                elif rec_type == 'hardware_archive':
                    self.insert_hardware_archive_row(cursor, item.get('data', {}))
                    saved_total += 1

                elif rec_type == 'startup_archive':
                    self.insert_startup_archive_row(cursor, item.get('data', {}))
                    saved_total += 1

                elif rec_type == 'event':
                    ts_str = item.get('timestamp') or datetime.now(timezone.utc).isoformat()
                    try:
                        now_epoch = datetime.fromisoformat(ts_str).timestamp()
                    except Exception:
                        now_epoch = datetime.now(timezone.utc).timestamp()
                    details_str = json.dumps(item.get('details', {}), ensure_ascii=False, default=str)
                    cursor.execute('''
                        INSERT INTO telemetry_events (
                            timestamp, created_at, event_type, severity, event_details, raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (ts_str, now_epoch, item.get('event_type', ''), item.get('severity', 'info'), details_str, details_str))
                    saved_total += 1

                elif rec_type == 'disk_inventory':
                    self.upsert_disk_inventory(cursor, item.get('data') or item)
                    saved_total += 1

                elif rec_type == 'volume_inventory':
                    self.upsert_volume_inventory(cursor, item.get('data') or item)
                    saved_total += 1

                elif rec_type == 'disk_health':
                    self.insert_disk_health_snapshot(cursor, item.get('data') or item)
                    saved_total += 1

                elif rec_type == 'disk_performance':
                    self.insert_disk_performance_sample(cursor, item.get('data') or item)
                    saved_total += 1

                elif rec_type == 'disk_io_event':
                    self.insert_disk_io_event(cursor, item.get('data') or item)
                    saved_total += 1

                elif rec_type in ('cpu_inventory', 'cpu_inv'):
                    self.upsert_cpu_inventory(cursor, item.get('data') or item)
                    saved_total += 1

                elif rec_type in ('ram_module_inventory', 'ram_inventory', 'ram_module'):
                    self.upsert_ram_module_inventory(cursor, item.get('data') or item)
                    saved_total += 1

                elif rec_type in ('gpu_inventory', 'gpu_inv'):
                    self.upsert_gpu_inventory(cursor, item.get('data') or item)
                    saved_total += 1

                elif rec_type in ('network_adapter_inventory', 'net_inventory', 'net_adapter_inv'):
                    self.upsert_network_adapter_inventory(cursor, item.get('data') or item)
                    saved_total += 1

                elif rec_type in ('cpu_telemetry', 'cpu_sample'):
                    self.insert_cpu_telemetry_sample(cursor, item.get('data') or item)
                    saved_total += 1

                elif rec_type in ('ram_telemetry', 'ram_sample'):
                    self.insert_ram_telemetry_sample(cursor, item.get('data') or item)
                    saved_total += 1

                elif rec_type in ('gpu_telemetry', 'gpu_sample'):
                    self.insert_gpu_telemetry_sample(cursor, item.get('data') or item)
                    saved_total += 1

                elif rec_type in ('network_adapter_sample', 'network_sample', 'net_sample'):
                    self.insert_network_adapter_sample(cursor, item.get('data') or item)
                    saved_total += 1

                elif rec_type == 'app_poll':
                    cursor.execute('''
                        INSERT INTO app_polls (
                            timestamp, created_at, app, poll_type, metric_name, value, unit, status, details, raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', self.prepare_app_poll_row(item.get('data') or item))
                    saved_total += 1

                elif rec_type == 'app_polls_batch':
                    rows = [self.prepare_app_poll_row(p) for p in item.get('data', [])]
                    if rows:
                        cursor.executemany('''
                            INSERT INTO app_polls (
                                timestamp, created_at, app, poll_type, metric_name, value, unit, status, details, raw_json
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', rows)
                        saved_total += len(rows)

                elif rec_type == 'app_event':
                    cursor.execute('''
                        INSERT INTO app_events (
                            timestamp, created_at, app, event_type, status, details, raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', self.prepare_app_event_row(item.get('data') or item))
                    saved_total += 1

                elif rec_type == 'app_events_batch':
                    rows = [self.prepare_app_event_row(ev) for ev in item.get('data', [])]
                    if rows:
                        cursor.executemany('''
                            INSERT INTO app_events (
                                timestamp, created_at, app, event_type, status, details, raw_json
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', rows)
                        saved_total += len(rows)

                elif rec_type == 'app_param_change':
                    cursor.execute('''
                        INSERT INTO app_param_changes (
                            timestamp, created_at, app, param_name, old_value, new_value, status, user, details, raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', self.prepare_app_param_row(item.get('data') or item))
                    saved_total += 1

                elif rec_type == 'app_param_changes_batch':
                    rows = [self.prepare_app_param_row(pc) for pc in item.get('data', [])]
                    if rows:
                        cursor.executemany('''
                            INSERT INTO app_param_changes (
                                timestamp, created_at, app, param_name, old_value, new_value, status, user, details, raw_json
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', rows)
                        saved_total += len(rows)

                elif rec_type == 'custom_record':
                    ts_str = item.get('timestamp') or datetime.now(timezone.utc).isoformat()
                    try:
                        now_epoch = datetime.fromisoformat(ts_str).timestamp()
                    except Exception:
                        now_epoch = datetime.now(timezone.utc).timestamp()
                    payload_str = json.dumps(item.get('payload', {}), ensure_ascii=False, default=str)
                    cursor.execute('''
                        INSERT INTO custom_records (timestamp, created_at, source_file, payload_json)
                        VALUES (?, ?, ?, ?)
                    ''', (ts_str, now_epoch, item.get('source_file', ''), payload_str))
                    saved_total += 1

                elif rec_type == 'device_event':
                    cursor.execute('''
                        INSERT INTO device_events (
                            timestamp, created_at, event_type, device_instance_id,
                            friendly_name, device_class, category, has_problem,
                            problem_code, status_code, manufacturer,
                            flapping_count, uptime_seconds, raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', self.prepare_device_event_row(item.get('data', {}), item.get('timestamp')))
                    saved_total += 1

                elif rec_type == 'w64_event':
                    cursor.execute('''
                        INSERT INTO w64_events (
                            event_id, timestamp, created_at, event_type, path, pid, name, provider, raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', self.prepare_w64_event_row(item.get('data', {}), item.get('provider', 'w64_collector')))
                    saved_total += 1

                elif rec_type == 'process_provenance_event':
                    cursor.execute('''
                        INSERT INTO process_provenance_events (
                            event_id, timestamp, created_at, event_type, process_guid, parent_guid,
                            pid, ppid, name, executable_path, command_line, user, sid, session_id,
                            integrity_level, elevation, parent_name, parent_cmdline,
                            ancestor_chain, launch_reason, source, details_json, raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', self.prepare_process_provenance_row(item.get('data', {})))
                    saved_total += 1

                elif rec_type == 'process_provenance_events_batch':
                    rows = [self.prepare_process_provenance_row(ev) for ev in item.get('data', [])]
                    if rows:
                        cursor.executemany('''
                            INSERT INTO process_provenance_events (
                                event_id, timestamp, created_at, event_type, process_guid, parent_guid,
                                pid, ppid, name, executable_path, command_line, user, sid, session_id,
                                integrity_level, elevation, parent_name, parent_cmdline,
                                ancestor_chain, launch_reason, source, details_json, raw_json
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', rows)
                        saved_total += len(rows)

                elif rec_type == 'incident':
                    inc_data = item.get('data', {})
                    now_dt = datetime.now(timezone.utc)
                    ts_str = inc_data.get('timestamp') or item.get('timestamp') or now_dt.isoformat()
                    try:
                        now_epoch = datetime.fromisoformat(ts_str).timestamp()
                    except Exception:
                        now_epoch = now_dt.timestamp()
                    inc_id = inc_data.get('incident_id') or f"INC-{int(now_epoch)}"
                    cursor.execute('''
                        INSERT OR REPLACE INTO incidents (
                            incident_id, timestamp, created_at, trigger_type, severity, title,
                            description, trigger_metrics_json, suspect_processes_json,
                            related_events_json, metrics_summary_json, raw_window_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        inc_id, ts_str, now_epoch,
                        inc_data.get('trigger_type', ''),
                        inc_data.get('severity', 'warning'),
                        inc_data.get('title', ''),
                        inc_data.get('description', ''),
                        json.dumps(inc_data.get('trigger_metrics', {}), ensure_ascii=False, default=str),
                        json.dumps(inc_data.get('suspect_processes', []), ensure_ascii=False, default=str),
                        json.dumps(inc_data.get('related_events', []), ensure_ascii=False, default=str),
                        json.dumps(inc_data.get('metrics_summary', {}), ensure_ascii=False, default=str),
                        json.dumps(inc_data.get('raw_window', []), ensure_ascii=False, default=str),
                    ))
                    saved_total += 1

                elif rec_type == 'system_rollup':
                    r_data = item.get('data', {})
                    p_start = r_data.get('period_start', '')
                    p_end = r_data.get('period_end', '')
                    try:
                        p_start_epoch = datetime.fromisoformat(p_start).timestamp()
                    except Exception:
                        p_start_epoch = 0.0
                    try:
                        p_end_epoch = datetime.fromisoformat(p_end).timestamp()
                    except Exception:
                        p_end_epoch = 0.0
                    cursor.execute('''
                        INSERT INTO telemetry_rollups (
                            period_start, period_end, period_start_epoch, period_end_epoch,
                            duration_seconds, sample_count, tier,
                            cpu_avg, cpu_min, cpu_max, cpu_p95,
                            ram_avg_gb, ram_min_gb, ram_max_gb, ram_percent_avg, ram_percent_max,
                            disk_read_avg_mbs, disk_read_max_mbs, disk_read_total_mb,
                            disk_write_avg_mbs, disk_write_max_mbs, disk_write_total_mb,
                            network_rx_avg_mbs, network_rx_max_mbs, network_rx_total_mb,
                            network_tx_avg_mbs, network_tx_max_mbs, network_tx_total_mb,
                            raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        p_start, p_end, p_start_epoch, p_end_epoch,
                        float(r_data.get('duration_seconds', 0.0) or 0.0),
                        int(r_data.get('sample_count', 0) or 0),
                        str(r_data.get('tier', '1m')),
                        r_data.get('cpu_avg'), r_data.get('cpu_min'), r_data.get('cpu_max'), r_data.get('cpu_p95'),
                        r_data.get('ram_avg_gb'), r_data.get('ram_min_gb'), r_data.get('ram_max_gb'),
                        r_data.get('ram_percent_avg'), r_data.get('ram_percent_max'),
                        r_data.get('disk_read_avg_mbs'), r_data.get('disk_read_max_mbs'), r_data.get('disk_read_total_mb'),
                        r_data.get('disk_write_avg_mbs'), r_data.get('disk_write_max_mbs'), r_data.get('disk_write_total_mb'),
                        r_data.get('network_rx_avg_mbs'), r_data.get('network_rx_max_mbs'), r_data.get('network_rx_total_mb'),
                        r_data.get('network_tx_avg_mbs'), r_data.get('network_tx_max_mbs'), r_data.get('network_tx_total_mb'),
                        json.dumps(r_data, ensure_ascii=False, default=str),
                    ))
                    saved_total += 1

                elif rec_type == 'reboot_session':
                    s_data = item.get('data', {})
                    now_dt = datetime.now(timezone.utc)
                    boot_time = s_data.get('boot_time') or now_dt.isoformat()
                    try:
                        now_epoch = datetime.fromisoformat(boot_time).timestamp()
                    except Exception:
                        now_epoch = now_dt.timestamp()
                    cursor.execute('''
                        INSERT OR REPLACE INTO reboot_history (
                            boot_id, boot_time, previous_boot_time, uptime_seconds, uptime_human,
                            shutdown_type, likely_class, conclusion, initiating_process, initiating_user,
                            shutdown_action, reason_text, reason_code, bugcheck_code, bugcheck_params_json,
                            power_button_timestamp, windows_update_kb, service_installed, evidence_json,
                            events_chain_json, raw_json, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        s_data.get('boot_id') or f"boot_{int(now_epoch)}",
                        boot_time,
                        s_data.get('previous_boot_time'),
                        float(s_data.get('uptime_seconds', 0.0) or 0.0),
                        s_data.get('uptime_human'),
                        s_data.get('shutdown_type', 'unknown'),
                        s_data.get('likely_class'),
                        s_data.get('conclusion'),
                        s_data.get('initiating_process'),
                        s_data.get('initiating_user'),
                        s_data.get('shutdown_action'),
                        s_data.get('reason_text'),
                        s_data.get('reason_code'),
                        s_data.get('bugcheck_code'),
                        json.dumps(s_data.get('bugcheck_params', {}), ensure_ascii=False, default=str),
                        s_data.get('power_button_timestamp'),
                        s_data.get('windows_update_kb'),
                        s_data.get('service_installed'),
                        json.dumps(s_data.get('evidence', {}), ensure_ascii=False, default=str),
                        json.dumps(s_data.get('events_chain', []), ensure_ascii=False, default=str),
                        json.dumps(s_data, ensure_ascii=False, default=str),
                        now_epoch,
                    ))
                    saved_total += 1

                elif rec_type == 'extended_audit':
                    audit_data = item.get('data', {})
                    now_dt = datetime.now(timezone.utc)
                    ts_str = item.get('timestamp') or audit_data.get('timestamp') or now_dt.isoformat()
                    try:
                        now_epoch = datetime.fromisoformat(ts_str).timestamp()
                    except Exception:
                        now_epoch = now_dt.timestamp()

                    def _get_f(obj: Any, key: str, default: Any = None) -> Any:
                        if isinstance(obj, dict):
                            return obj.get(key, default)
                        return getattr(obj, key, default)

                    def_obj = _get_f(audit_data, 'defender', {})
                    startup_obj = _get_f(audit_data, 'startup', {})
                    vss_obj = _get_f(audit_data, 'vss', {})
                    users_obj = _get_f(audit_data, 'users', {})

                    cursor.execute('''
                        INSERT INTO system_extended_audits (
                            timestamp, created_at, hostname,
                            defender_cfa_enabled, defender_asr_count, defender_exclusions_count, defender_threats_count,
                            startup_entries_count, vss_snapshots_count, users_total_count, users_admin_count,
                            raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        ts_str, now_epoch, _get_f(audit_data, 'hostname', ''),
                        int(bool(_get_f(def_obj, 'cfa_enabled', False))),
                        int(_get_f(def_obj, 'asr_rules_count', 0) or 0),
                        int(_get_f(def_obj, 'exclusions_count', len(_get_f(def_obj, 'path_exclusions', []) or [])) or 0),
                        int(_get_f(def_obj, 'active_threats_count', 0) or 0),
                        int(_get_f(startup_obj, 'total_entries', len(_get_f(startup_obj, 'entries', []) or [])) or 0),
                        int(_get_f(vss_obj, 'total_snapshots_count', len(_get_f(vss_obj, 'snapshots', []) or [])) or 0),
                        int(_get_f(users_obj, 'total_users_count', len(_get_f(users_obj, 'users', []) or [])) or 0),
                        int(len(_get_f(users_obj, 'admin_usernames', []) or []) or _get_f(users_obj, 'users_admin_count', 0) or 0),
                        json.dumps(audit_data, ensure_ascii=False, default=str),
                    ))
                    saved_total += 1

            if sensor_poll_rows:
                cursor.executemany('''
                    INSERT INTO sensor_polls (
                        sensor_id, timestamp, created_at, hardware_name, hardware_type,
                        sensor_category, sensor_name, unit, value, provider, provider_priority, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(sensor_id, timestamp) DO UPDATE SET
                        created_at = excluded.created_at,
                        hardware_name = excluded.hardware_name,
                        hardware_type = excluded.hardware_type,
                        sensor_category = excluded.sensor_category,
                        sensor_name = excluded.sensor_name,
                        unit = excluded.unit,
                        value = excluded.value,
                        provider = excluded.provider,
                        provider_priority = excluded.provider_priority,
                        raw_json = excluded.raw_json
                ''', sensor_poll_rows)
                saved_total += len(sensor_poll_rows)

            if sensor_agg_rows:
                cursor.executemany('''
                    INSERT INTO sensor_aggregates_hourly (
                        sensor_id, period_start, period_end, avg_value, min_value, max_value, count, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', sensor_agg_rows)
                saved_total += len(sensor_agg_rows)

            conn.commit()
        return saved_total

    def prepare_sensor_poll_row(self, s: Dict[str, Any], timestamp: Optional[str] = None) -> tuple:
        """Подготавливает кортеж для вставки в sensor_polls."""
        now_dt = datetime.now(timezone.utc)
        ts_str = timestamp or s.get('timestamp') or now_dt.isoformat()
        try:
            now_epoch = datetime.fromisoformat(ts_str).timestamp()
        except Exception:
            now_epoch = now_dt.timestamp()
        sid = str(s.get('id') or s.get('sensor_id') or '')
        s_name = s.get('sensor_name') or s.get('name') or (f'Sensor #{sid}' if sid else 'Sensor')
        cat = s.get('sensor_category') or s.get('category') or 'General'
        
        # Определение типа оборудования с fallback
        hw_type = s.get('hardware_type')
        if not hw_type:
            sid_l = sid.lower()
            cat_l = cat.lower()
            if 'disk' in sid_l or 'storage' in sid_l or 'storage' in cat_l:
                hw_type = 'storage'
            elif 'gpu' in sid_l or 'vram' in sid_l or 'graphics' in sid_l:
                hw_type = 'gpu'
            elif 'ram' in sid_l or 'memory' in sid_l:
                hw_type = 'memory'
            elif 'net' in sid_l or 'nic' in sid_l or 'network' in cat_l:
                hw_type = 'network'
            else:
                hw_type = 'cpu'

        hw_name = s.get('hardware_name') or ('Storage' if hw_type == 'storage' else 'System')
        unit = s.get('unit', '')
        raw_val = s.get('value', s.get('value_num', 0.0))
        try:
            val_float = round(float(raw_val), 2)
        except (ValueError, TypeError):
            val_float = 0.0

        provider_raw = s.get('_provider') or s.get('provider') or 'CIM_SYSTEM'
        if hasattr(provider_raw, 'name'):
            provider_str = provider_raw.name
            provider_priority = provider_raw.value
        elif isinstance(provider_raw, str):
            provider_str = provider_raw.upper()
            try:
                from ..sensor_registry import SensorProvider
                provider_priority = SensorProvider[provider_raw.upper()].value
            except (KeyError, ImportError):
                provider_priority = 30
        else:
            provider_str = 'CIM_SYSTEM'
            provider_priority = 30

        raw_json_str = s.get('raw_json')
        if not raw_json_str:
            try:
                raw_json_str = json.dumps(s, ensure_ascii=False, default=str)
            except Exception:
                raw_json_str = None

        return (sid, ts_str, now_epoch, hw_name, hw_type, cat, s_name, unit, val_float, provider_str, provider_priority, raw_json_str)

    def prepare_app_poll_row(self, p: Dict[str, Any]) -> tuple:
        now_dt = datetime.now(timezone.utc)
        ts_str = p.get('timestamp') or now_dt.isoformat()
        try:
            now_epoch = datetime.fromisoformat(ts_str).timestamp()
        except Exception:
            now_epoch = now_dt.timestamp()
        app = p.get('app', 'unknown')
        poll_type = p.get('poll_type', 'poll')
        metric_name = p.get('metric_name', 'metric')
        val = p.get('value')
        try:
            val_num = float(val) if val is not None and not isinstance(val, (dict, list)) else None
        except (ValueError, TypeError):
            val_num = None
        unit = p.get('unit', '')
        status = p.get('status', 'OK')
        details = p.get('details', '')
        details_str = json.dumps(details, ensure_ascii=False) if isinstance(details, (dict, list)) else str(details or '')
        raw_json = json.dumps({'app': app, 'poll_type': poll_type, 'metric_name': metric_name, 'value': val, 'unit': unit, 'status': status, 'details': details}, ensure_ascii=False)
        return (ts_str, now_epoch, app, poll_type, metric_name, val_num, unit, status, details_str, raw_json)

    def prepare_app_event_row(self, ev: Dict[str, Any]) -> tuple:
        now_dt = datetime.now(timezone.utc)
        ts_str = ev.get('timestamp') or now_dt.isoformat()
        try:
            now_epoch = datetime.fromisoformat(ts_str).timestamp()
        except Exception:
            now_epoch = now_dt.timestamp()
        app = ev.get('app', 'unknown')
        event_type = ev.get('event_type', 'event')
        status = ev.get('status', 'OK')
        details = ev.get('details', '')
        details_str = json.dumps(details, ensure_ascii=False) if isinstance(details, (dict, list)) else str(details or '')
        raw_json = json.dumps({'app': app, 'event_type': event_type, 'status': status, 'details': details}, ensure_ascii=False)
        return (ts_str, now_epoch, app, event_type, status, details_str, raw_json)

    def prepare_app_param_row(self, pc: Dict[str, Any]) -> tuple:
        now_dt = datetime.now(timezone.utc)
        ts_str = pc.get('timestamp') or now_dt.isoformat()
        try:
            now_epoch = datetime.fromisoformat(ts_str).timestamp()
        except Exception:
            now_epoch = now_dt.timestamp()
        app = pc.get('app', 'unknown')
        param_name = pc.get('param_name', 'param')
        old_val = pc.get('old_value')
        new_val = pc.get('new_value')
        old_str = json.dumps(old_val, ensure_ascii=False) if isinstance(old_val, (dict, list)) else str(old_val or '')
        new_str = json.dumps(new_val, ensure_ascii=False) if isinstance(new_val, (dict, list)) else str(new_val or '')
        status = pc.get('status', 'SUCCESS')
        user = pc.get('user', 'system')
        details = pc.get('details', '')
        details_str = json.dumps(details, ensure_ascii=False) if isinstance(details, (dict, list)) else str(details or '')
        raw_json = json.dumps({'app': app, 'param_name': param_name, 'old_value': old_val, 'new_value': new_val, 'status': status, 'user': user, 'details': details}, ensure_ascii=False)
        return (ts_str, now_epoch, app, param_name, old_str, new_str, status, user, details_str, raw_json)

    def prepare_device_event_row(self, event: Dict[str, Any], timestamp: Optional[str] = None) -> tuple:
        now_dt = datetime.now(timezone.utc)
        ts_str = timestamp or event.get('timestamp') or now_dt.isoformat()
        try:
            now_epoch = datetime.fromisoformat(ts_str).timestamp()
        except Exception:
            now_epoch = now_dt.timestamp()
        raw_json = json.dumps(event, ensure_ascii=False, default=str)
        return (
            ts_str, now_epoch, event.get('event_type', ''), event.get('device_instance_id', ''),
            event.get('friendly_name', ''), event.get('device_class', ''), event.get('category', ''),
            int(bool(event.get('has_problem', False))), event.get('problem_code', 0),
            event.get('status_code', 0), event.get('manufacturer', ''),
            event.get('flapping_count_in_window', 0), event.get('uptime_seconds', 0.0), raw_json,
        )

    def prepare_w64_event_row(self, event_data: Dict[str, Any], provider: str = 'w64_collector') -> tuple:
        now_dt = datetime.now(timezone.utc)
        ts_str = event_data.get('timestamp') or now_dt.isoformat()
        try:
            now_epoch = datetime.fromisoformat(ts_str).timestamp()
        except Exception:
            now_epoch = now_dt.timestamp()
        event_id = str(event_data.get('event_id') or f'evt_{int(now_epoch)}')
        event_type = str(event_data.get('event_type', 'unknown'))
        path_val = event_data.get('path')
        pid_val = event_data.get('pid')
        if pid_val is not None:
            try:
                pid_val = int(pid_val)
            except (ValueError, TypeError):
                pid_val = None
        name_val = event_data.get('name')
        raw_json = json.dumps(event_data, ensure_ascii=False, default=str)
        return (event_id, ts_str, now_epoch, event_type, path_val, pid_val, name_val, provider, raw_json)

    def prepare_process_provenance_row(self, p: Any) -> tuple:
        """Подготавливает кортеж для вставки в process_provenance_events."""
        p_dict = p if isinstance(p, dict) else (p.model_dump() if hasattr(p, 'model_dump') else (vars(p) if hasattr(p, '__dict__') else p))
        now_dt = datetime.now(timezone.utc)
        ts_str = p_dict.get('timestamp') or now_dt.isoformat()
        try:
            now_epoch = datetime.fromisoformat(ts_str).timestamp()
        except Exception:
            now_epoch = now_dt.timestamp()

        pid = int(p_dict.get('pid') or 0)
        event_id = p_dict.get('event_id') or f"pp_{int(now_epoch * 1000)}_{pid}"
        event_type = p_dict.get('event_type') or 'ProcessCreated'
        ppid = int(p_dict['ppid']) if p_dict.get('ppid') is not None else None
        name = p_dict.get('name') or 'unknown'
        exe_path = p_dict.get('executable_path') or p_dict.get('executable')
        cmdline = p_dict.get('command_line') or p_dict.get('cmdline')
        user = p_dict.get('user') or p_dict.get('username')
        sid = p_dict.get('sid')
        session_id = int(p_dict['session_id']) if p_dict.get('session_id') is not None else None
        integrity = p_dict.get('integrity_level')
        elevation = int(bool(p_dict.get('elevation', False)))
        parent_name = p_dict.get('parent_name')
        parent_cmdline = p_dict.get('parent_cmdline')
        ancestor_chain = p_dict.get('ancestor_chain') or p_dict.get('ancestor_chain_str')
        if isinstance(ancestor_chain, list):
            ancestor_chain = ' -> '.join(ancestor_chain)
        launch_reason = p_dict.get('launch_reason') or p_dict.get('why_was_it_created')
        source = p_dict.get('source') or 'system'
        creation_time = p_dict.get('creation_time') or ts_str
        process_guid = p_dict.get('process_guid') or f"proc_{pid}_{creation_time}"
        parent_guid = p_dict.get('parent_guid')
        details = p_dict.get('details') or p_dict.get('details_json')
        details_json = json.dumps(details, ensure_ascii=False) if isinstance(details, (dict, list)) else (str(details) if details else None)
        raw_json = json.dumps(p_dict, ensure_ascii=False, default=str)

        return (
            event_id, ts_str, now_epoch, event_type, process_guid, parent_guid,
            pid, ppid, name, exe_path, cmdline, user, sid, session_id,
            integrity, elevation, parent_name, parent_cmdline,
            ancestor_chain, launch_reason, source, details_json, raw_json
        )

    def insert_snapshot_row(self, cursor: sqlite3.Cursor, item: Dict[str, Any]) -> int:
        """Вставляет строку снимка и процессы в базу данных со всеми расширенными параметрами."""
        snap_data = item.get('data', {})
        top_n = item.get('top_n', 20)
        snapshot = snap_data if isinstance(snap_data, SystemSnapshot) else None

        if snapshot:
            hostname = snapshot.hostname
            username = snapshot.username or ''
            uptime = snapshot.uptime_seconds
            os_name = snapshot.os_name or 'Windows'
            os_build = str(snapshot.os_build or '')
            os_install_date = str(snapshot.os_install_date or '')
            system_lang = str(snapshot.system_language or '')
            os_install_lang = str(snapshot.os_install_language or '')
            user_locale = str(snapshot.user_locale or '')
            sys_locale = str(snapshot.system_locale or '')
            timezone_val = str(snapshot.timezone or '')
            codepage_val = str(snapshot.codepage or '')
            input_langs = snapshot.input_languages or []
            input_langs_json = json.dumps(input_langs, ensure_ascii=False) if input_langs else None

            cpu_pct = snapshot.cpu.total_percent if snapshot.cpu else 0.0
            cpu_freq = snapshot.cpu.frequency_mhz if snapshot.cpu else 0.0
            mem_tot = snapshot.memory.total_gb if snapshot.memory else 0.0
            mem_used = snapshot.memory.used_gb if snapshot.memory else 0.0
            mem_pct = snapshot.memory.percent if snapshot.memory else 0.0
            swap_pct = snapshot.memory.swap_percent if snapshot.memory else 0.0
            disk_rb = snapshot.disk_io.read_bytes_per_sec if snapshot.disk_io else 0.0
            disk_wb = snapshot.disk_io.write_bytes_per_sec if snapshot.disk_io else 0.0
            disk_rc = snapshot.disk_io.read_count_per_sec if snapshot.disk_io else 0.0
            disk_wc = snapshot.disk_io.write_count_per_sec if snapshot.disk_io else 0.0
            net_sent = sum(getattr(i, 'bytes_sent_sec', 0.0) or 0.0 for i in (snapshot.network or []))
            net_recv = sum(getattr(i, 'bytes_recv_sec', 0.0) or 0.0 for i in (snapshot.network or []))
            gpu_load = 0.0
            gpu_temp = 0.0
            if snapshot.gpus:
                gpu = snapshot.gpus[0]
                gpu_load = getattr(gpu, 'load_percent', None) or getattr(gpu, 'utilization_gpu_pct', 0.0) or 0.0
                gpu_temp = getattr(gpu, 'temperature_celsius', None) or getattr(gpu, 'temperature_gpu_c', 0.0) or 0.0
            raw_procs = snapshot.top_processes or []

            disks_list = [d if isinstance(d, dict) else (d.model_dump() if hasattr(d, 'model_dump') else (vars(d) if hasattr(d, '__dict__') else d)) for d in (snapshot.disks or [])]
            disks_json = json.dumps(disks_list, ensure_ascii=False, default=str) if disks_list else None
            phys_disks_list = [d if isinstance(d, dict) else (d.model_dump() if hasattr(d, 'model_dump') else (vars(d) if hasattr(d, '__dict__') else d)) for d in (snapshot.physical_disks or [])]
            physical_disks_json = json.dumps(phys_disks_list, ensure_ascii=False, default=str) if phys_disks_list else None

            monitors_list = [m if isinstance(m, dict) else (m.model_dump() if hasattr(m, 'model_dump') else (vars(m) if hasattr(m, '__dict__') else m)) for m in (snapshot.monitors or [])]
            monitors_json = json.dumps(monitors_list, ensure_ascii=False, default=str) if monitors_list else None

            updates_obj = snapshot.updates.model_dump() if hasattr(snapshot.updates, 'model_dump') else (snapshot.updates if isinstance(snapshot.updates, dict) else (vars(snapshot.updates) if hasattr(snapshot.updates, '__dict__') else None))
            updates_json = json.dumps(updates_obj, ensure_ascii=False, default=str) if updates_obj else None

            office_obj = snapshot.office.model_dump() if hasattr(snapshot.office, 'model_dump') else (snapshot.office if isinstance(snapshot.office, dict) else (vars(snapshot.office) if hasattr(snapshot.office, '__dict__') else None))
            office_json = json.dumps(office_obj, ensure_ascii=False, default=str) if office_obj else None

            onedrive_obj = snapshot.onedrive.model_dump() if hasattr(snapshot.onedrive, 'model_dump') else (snapshot.onedrive if isinstance(snapshot.onedrive, dict) else (vars(snapshot.onedrive) if hasattr(snapshot.onedrive, '__dict__') else None))
            onedrive_json = json.dumps(onedrive_obj, ensure_ascii=False, default=str) if onedrive_obj else None

            battery_obj = snapshot.battery.model_dump() if hasattr(snapshot.battery, 'model_dump') else (snapshot.battery if isinstance(snapshot.battery, dict) else (vars(snapshot.battery) if hasattr(snapshot.battery, '__dict__') else None))
            battery_json = json.dumps(battery_obj, ensure_ascii=False, default=str) if battery_obj else None

            ram_sticks_list = [r if isinstance(r, dict) else (r.model_dump() if hasattr(r, 'model_dump') else (vars(r) if hasattr(r, '__dict__') else r)) for r in (snapshot.ram_sticks or [])]
            ram_sticks_json = json.dumps(ram_sticks_list, ensure_ascii=False, default=str) if ram_sticks_list else None

            ports_list = [p if isinstance(p, dict) else (p.model_dump() if hasattr(p, 'model_dump') else (vars(p) if hasattr(p, '__dict__') else p)) for p in (snapshot.listening_ports or [])]
            listening_ports_json = json.dumps(ports_list, ensure_ascii=False, default=str) if ports_list else None

            alerts_list = [a if isinstance(a, dict) else (a.model_dump() if hasattr(a, 'model_dump') else (vars(a) if hasattr(a, '__dict__') else a)) for a in (snapshot.alerts or [])]
            alerts_json = json.dumps(alerts_list, ensure_ascii=False, default=str) if alerts_list else None

            ts_str = snapshot.timestamp
            hw_audit = getattr(snapshot, 'hardware_audit', None)
            raw_full_dict = snapshot.model_dump() if hasattr(snapshot, 'model_dump') else (vars(snapshot) if hasattr(snapshot, '__dict__') else snapshot)
            raw_json_str = json.dumps(raw_full_dict, ensure_ascii=False, default=str)
        else:
            hostname = snap_data.get('hostname')
            username = snap_data.get('username') or ''
            uptime = snap_data.get('uptime_seconds')
            os_name = snap_data.get('os_name') or 'Windows'
            os_build = str(snap_data.get('os_build') or '')
            os_install_date = str(snap_data.get('os_install_date') or '')
            system_lang = str(snap_data.get('system_language') or '')
            os_install_lang = str(snap_data.get('os_install_language') or '')
            user_locale = str(snap_data.get('user_locale') or '')
            sys_locale = str(snap_data.get('system_locale') or '')
            timezone_val = str(snap_data.get('timezone') or '')
            codepage_val = str(snap_data.get('codepage') or '')
            input_langs = snap_data.get('input_languages', [])
            input_langs_json = json.dumps(input_langs, ensure_ascii=False) if input_langs else None

            disks_val = snap_data.get('disks', [])
            disks_list = [d if isinstance(d, dict) else (d.model_dump() if hasattr(d, 'model_dump') else (vars(d) if hasattr(d, '__dict__') else d)) for d in disks_val] if isinstance(disks_val, list) else []
            disks_json = json.dumps(disks_list, ensure_ascii=False, default=str) if disks_list else None
            phys_disks_val = snap_data.get('physical_disks', [])
            phys_disks_list = [d if isinstance(d, dict) else (d.model_dump() if hasattr(d, 'model_dump') else (vars(d) if hasattr(d, '__dict__') else d)) for d in phys_disks_val] if isinstance(phys_disks_val, list) else []
            physical_disks_json = json.dumps(phys_disks_list, ensure_ascii=False, default=str) if phys_disks_list else None

            mon_val = snap_data.get('monitors', [])
            monitors_json = json.dumps(mon_val, ensure_ascii=False, default=str) if mon_val else None

            upd_val = snap_data.get('updates')
            updates_json = json.dumps(upd_val, ensure_ascii=False, default=str) if upd_val else None

            off_val = snap_data.get('office')
            office_json = json.dumps(off_val, ensure_ascii=False, default=str) if off_val else None

            od_val = snap_data.get('onedrive')
            onedrive_json = json.dumps(od_val, ensure_ascii=False, default=str) if od_val else None

            bat_val = snap_data.get('battery')
            battery_json = json.dumps(bat_val, ensure_ascii=False, default=str) if bat_val else None

            ram_val = snap_data.get('ram_sticks', [])
            ram_sticks_json = json.dumps(ram_val, ensure_ascii=False, default=str) if ram_val else None

            ports_val = snap_data.get('listening_ports', [])
            listening_ports_json = json.dumps(ports_val, ensure_ascii=False, default=str) if ports_val else None

            alerts_val = snap_data.get('alerts', [])
            alerts_json = json.dumps(alerts_val, ensure_ascii=False, default=str) if alerts_val else None

            cpu_obj = snap_data.get('cpu', {})
            cpu_pct = cpu_obj.get('total_percent', 0.0) if isinstance(cpu_obj, dict) else getattr(cpu_obj, 'total_percent', 0.0)
            cpu_freq = cpu_obj.get('frequency_mhz', 0.0) if isinstance(cpu_obj, dict) else getattr(cpu_obj, 'frequency_mhz', 0.0)
            mem_obj = snap_data.get('memory', {})
            mem_tot = mem_obj.get('total_gb', 0.0) if isinstance(mem_obj, dict) else getattr(mem_obj, 'total_gb', 0.0)
            mem_used = mem_obj.get('used_gb', 0.0) if isinstance(mem_obj, dict) else getattr(mem_obj, 'used_gb', 0.0)
            mem_pct = mem_obj.get('percent', 0.0) if isinstance(mem_obj, dict) else getattr(mem_obj, 'percent', 0.0)
            swap_pct = mem_obj.get('swap_percent', 0.0) if isinstance(mem_obj, dict) else getattr(mem_obj, 'swap_percent', 0.0)
            disk_obj = snap_data.get('disk_io', {})
            disk_rb = disk_obj.get('read_bytes_per_sec', 0.0) if isinstance(disk_obj, dict) else getattr(disk_obj, 'read_bytes_per_sec', 0.0)
            disk_wb = disk_obj.get('write_bytes_per_sec', 0.0) if isinstance(disk_obj, dict) else getattr(disk_obj, 'write_bytes_per_sec', 0.0)
            disk_rc = disk_obj.get('read_count_per_sec', 0.0) if isinstance(disk_obj, dict) else getattr(disk_obj, 'read_count_per_sec', 0.0)
            disk_wc = disk_obj.get('write_count_per_sec', 0.0) if isinstance(disk_obj, dict) else getattr(disk_obj, 'write_count_per_sec', 0.0)
            net_list = snap_data.get('network', [])
            net_sent = sum((n.get('bytes_sent_sec', 0.0) if isinstance(n, dict) else getattr(n, 'bytes_sent_sec', 0.0)) or 0.0 for n in net_list)
            net_recv = sum((n.get('bytes_recv_sec', 0.0) if isinstance(n, dict) else getattr(n, 'bytes_recv_sec', 0.0)) or 0.0 for n in net_list)
            gpus = snap_data.get('gpus', [])
            gpu_load = 0.0
            gpu_temp = 0.0
            if gpus:
                g0 = gpus[0]
                gpu_load = (g0.get('load_percent', 0.0) if isinstance(g0, dict) else getattr(g0, 'load_percent', 0.0)) or 0.0
                gpu_temp = (g0.get('temperature_celsius', 0.0) if isinstance(g0, dict) else getattr(g0, 'temperature_celsius', 0.0)) or 0.0
            raw_procs = snap_data.get('top_processes', [])
            ts_str = snap_data.get('timestamp')
            hw_audit = snap_data.get('hardware_audit')
            raw_json_str = json.dumps(snap_data, ensure_ascii=False, default=str)

        now_dt = datetime.now(timezone.utc)
        ts_str = ts_str or now_dt.isoformat()
        try:
            now_epoch = datetime.fromisoformat(ts_str).timestamp()
        except Exception:
            now_epoch = now_dt.timestamp()

        hardware_audit_json = json.dumps(hw_audit or {}, ensure_ascii=False, default=str)

        cursor.execute('''
            INSERT INTO system_snapshots (
                timestamp, created_at, hostname, username, uptime_seconds, os_name, os_build, os_install_date,
                system_language, os_install_language, user_locale, system_locale, timezone, codepage,
                input_languages_json, disks_json, physical_disks_json, monitors_json, updates_json, office_json,
                onedrive_json, battery_json, ram_sticks_json, listening_ports_json, alerts_json,
                cpu_total_percent, cpu_frequency_mhz, memory_total_gb, memory_used_gb,
                memory_percent, swap_percent, gpu_load_percent, gpu_temp_c,
                disk_read_bytes_sec, disk_write_bytes_sec, disk_read_count_sec,
                disk_write_count_sec, network_sent_bytes_sec, network_recv_bytes_sec, hardware_audit, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ts_str, now_epoch, hostname, username, uptime, os_name, os_build, os_install_date,
            system_lang, os_install_lang, user_locale, sys_locale, timezone_val, codepage_val,
            input_langs_json, disks_json, physical_disks_json, monitors_json, updates_json, office_json,
            onedrive_json, battery_json, ram_sticks_json, listening_ports_json, alerts_json,
            cpu_pct, cpu_freq, mem_tot, mem_used,
            mem_pct, swap_pct, gpu_load, gpu_temp,
            disk_rb, disk_wb, disk_rc,
            disk_wc, net_sent, net_recv, hardware_audit_json, raw_json_str
        ))
        snapshot_id = cursor.lastrowid or 0

        processes = raw_procs if top_n is None or top_n <= 0 else raw_procs[:top_n]
        proc_rows = []
        for p in processes:
            p_dict = p if isinstance(p, dict) else (p.model_dump() if hasattr(p, 'model_dump') else (vars(p) if hasattr(p, '__dict__') else p))
            proc_rows.append((
                snapshot_id, ts_str, p_dict.get('pid', 0), p_dict.get('name', 'unknown'),
                p_dict.get('status', ''), float(p_dict.get('cpu_percent', 0.0) or 0.0),
                float(p_dict.get('memory_mb', 0.0) or 0.0), float(p_dict.get('memory_percent', 0.0) or 0.0),
                int(p_dict.get('num_threads', 0) or 0), int(p_dict.get('num_handles', 0) or 0),
                str(p_dict.get('username', '') or ''), float(p_dict.get('read_bytes_sec', 0.0) or 0.0),
                float(p_dict.get('write_bytes_sec', 0.0) or 0.0), p_dict.get('integrity_level', None),
                int(bool(p_dict.get('elevation', False))), p_dict.get('ppid', None),
                p_dict.get('parent_name', None), p_dict.get('executable_path', p_dict.get('executable', None)),
                p_dict.get('cmdline', p_dict.get('command_line', None)), p_dict.get('sid', None),
                p_dict.get('session_id', None), p_dict.get('creation_time', None),
                p_dict.get('process_guid', None), p_dict.get('ancestor_chain', None),
                p_dict.get('launch_reason', None),
            ))
        if proc_rows:
            cursor.executemany('''
                INSERT INTO process_snapshots (
                    snapshot_id, timestamp, pid, name, status, cpu_percent,
                    memory_mb, memory_percent, num_threads, num_handles,
                    username, read_bytes_sec, write_bytes_sec, integrity_level, elevation,
                    ppid, parent_name, executable, cmdline, sid, session_id,
                    creation_time, process_guid, ancestor_chain, launch_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', proc_rows)

        # Синхронизация нормализованных таблиц оборудования и метрик
        try:
            # 1. CPU
            cpu_data = getattr(snapshot, 'cpu', None) or snap_data.get('cpu')
            if cpu_data:
                c_dict = cpu_data if isinstance(cpu_data, dict) else (cpu_data.model_dump() if hasattr(cpu_data, 'model_dump') else vars(cpu_data))
                if c_dict.get('model') or c_dict.get('name'):
                    self.upsert_cpu_inventory(cursor, {
                        'processor_id': 0,
                        'name': c_dict.get('model') or c_dict.get('name', 'CPU'),
                        'architecture': c_dict.get('architecture', 'x86_64'),
                        'physical_cores': c_dict.get('physical_cores', 1),
                        'logical_cores': c_dict.get('logical_cores', 1),
                        'base_frequency_mhz': c_dict.get('frequency_mhz', 0.0),
                    })
                self.insert_cpu_telemetry_sample(cursor, {
                    'timestamp': ts_str,
                    'created_at': now_epoch,
                    'processor_id': 0,
                    'total_percent': cpu_pct,
                    'frequency_mhz': cpu_freq,
                    'temperature_c': c_dict.get('temperature_celsius') or c_dict.get('temperature_c'),
                    'core_utilization': c_dict.get('per_core_percent', []),
                })

            # 2. RAM
            mem_data = getattr(snapshot, 'memory', None) or snap_data.get('memory')
            if mem_data:
                m_dict = mem_data if isinstance(mem_data, dict) else (mem_data.model_dump() if hasattr(mem_data, 'model_dump') else vars(mem_data))
                self.insert_ram_telemetry_sample(cursor, {
                    'timestamp': ts_str,
                    'created_at': now_epoch,
                    'total_gb': mem_tot,
                    'used_gb': mem_used,
                    'available_gb': m_dict.get('available_gb', max(0.0, mem_tot - mem_used)),
                    'percent_used': mem_pct,
                    'swap_total_gb': m_dict.get('swap_total_gb', 0.0),
                    'swap_used_gb': m_dict.get('swap_used_gb', 0.0),
                    'swap_percent': swap_pct,
                })

            # 3. RAM Sticks (SPD)
            sticks = getattr(snapshot, 'ram_sticks', None) or snap_data.get('ram_sticks') or []
            for s in sticks:
                self.upsert_ram_module_inventory(cursor, s)

            # 4. GPUs
            gpus_list = getattr(snapshot, 'gpus', None) or snap_data.get('gpus') or []
            for g_idx, g_item in enumerate(gpus_list):
                g_dict = g_item if isinstance(g_item, dict) else (g_item.model_dump() if hasattr(g_item, 'model_dump') else vars(g_item))
                g_name = g_dict.get('name', f'GPU {g_idx}')
                name_l = g_name.lower()
                if 'nvidia' in name_l or 'geforce' in name_l or g_dict.get('has_cuda'):
                    vendor = 'NVIDIA'
                elif 'amd' in name_l or 'radeon' in name_l:
                    vendor = 'AMD'
                elif 'intel' in name_l or 'arc' in name_l or 'uhd' in name_l or 'hd graphics' in name_l:
                    vendor = 'Intel'
                else:
                    vendor = g_dict.get('vendor') or 'Generic'

                self.upsert_gpu_inventory(cursor, {
                    'gpu_id': g_idx,
                    'name': g_name,
                    'vendor': vendor,
                    'vram_gb': g_dict.get('memory_total_gb', 0.0),
                    'directml_supported': bool(g_dict.get('has_directml', True)),
                })
                self.insert_gpu_telemetry_sample(cursor, {
                    'timestamp': ts_str,
                    'created_at': now_epoch,
                    'gpu_id': g_idx,
                    'name': g_dict.get('name', f'GPU {g_idx}'),
                    'load_percent': g_dict.get('load_percent'),
                    'memory_used_mb': (g_dict.get('memory_used_gb', 0.0) or 0.0) * 1024.0,
                    'memory_total_mb': (g_dict.get('memory_total_gb', 0.0) or 0.0) * 1024.0,
                    'temperature_gpu_c': g_dict.get('temperature_celsius') or g_dict.get('temperature_gpu_c'),
                })

            # 5. Network
            net_items = getattr(snapshot, 'network', None) or snap_data.get('network') or []
            for n_idx, n_item in enumerate(net_items):
                n_dict = n_item if isinstance(n_item, dict) else (n_item.model_dump() if hasattr(n_item, 'model_dump') else vars(n_item))
                self.upsert_network_adapter_inventory(cursor, {
                    'adapter_id': n_idx,
                    'adapter_guid': n_dict.get('name', f'Adapter_{n_idx}'),
                    'name': n_dict.get('name', f'Adapter {n_idx}'),
                    'max_speed_mbps': n_dict.get('speed_mbps', 0),
                })
                self.insert_network_adapter_sample(cursor, {
                    'timestamp': ts_str,
                    'created_at': now_epoch,
                    'adapter_name': n_dict.get('name', f'Adapter {n_idx}'),
                    'bytes_recv_sec': n_dict.get('bytes_recv_per_sec', 0.0),
                    'bytes_sent_sec': n_dict.get('bytes_sent_per_sec', 0.0),
                    'link_speed_mbps': n_dict.get('speed_mbps', 0),
                    'is_connected': bool(n_dict.get('is_up', True)),
                })
        except Exception as norm_err:
            logger.debug(f'Предупреждение синхронизации нормализованных таблиц оборудования: {norm_err}')

        return snapshot_id

    def insert_hardware_archive_row(self, cursor: sqlite3.Cursor, data: Any) -> int:
        now_dt = datetime.now(timezone.utc)
        if isinstance(data, HardwareArchiveEntry):
            raw_json = data.model_dump_json()
            report = data.report
            prob_count = report.problem_devices_count if report else 0
            outdated_count = report.outdated_drivers_count if report else 0
            archive_id = data.archive_id
            timestamp = data.timestamp
            devices_count = data.devices_count
            changes_count = data.changes_count
        else:
            raw_json = json.dumps(data, ensure_ascii=False, default=str)
            report = data.get('report', {})
            prob_count = report.get('problem_devices_count', 0) if isinstance(report, dict) else getattr(report, 'problem_devices_count', 0)
            outdated_count = report.get('outdated_drivers_count', 0) if isinstance(report, dict) else getattr(report, 'outdated_drivers_count', 0)
            archive_id = data.get('archive_id', f'arch_{int(now_dt.timestamp())}')
            timestamp = data.get('timestamp', now_dt.isoformat())
            devices_count = data.get('devices_count', 0)
            changes_count = data.get('changes_count', 0)

        try:
            now_epoch = datetime.fromisoformat(timestamp).timestamp()
        except Exception:
            now_epoch = now_dt.timestamp()

        cursor.execute('''
            INSERT OR REPLACE INTO hardware_audits (
                archive_id, timestamp, created_at, devices_count,
                problem_devices_count, outdated_drivers_count, changes_count, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (archive_id, timestamp, now_epoch, devices_count, prob_count, outdated_count, changes_count, raw_json))
        return cursor.lastrowid or 0

    def insert_startup_archive_row(self, cursor: sqlite3.Cursor, data: Any) -> int:
        """Сохранение снимка аудита автозапуска и зафиксированных изменений в БД."""
        now_dt = datetime.now(timezone.utc)
        if isinstance(data, StartupArchiveEntry):
            raw_json = data.model_dump_json()
            archive_id = data.archive_id
            timestamp = data.timestamp
            total_entries = data.total_entries
            health_score = data.health_score
            changes_count = data.changes_count
            report = data.report
            changes = data.changes
            if hasattr(report, 'summary') and report.summary:
                active_entries = report.summary.active_entries
                disabled_entries = report.summary.disabled_entries
                broken_entries = report.summary.broken_entries
            else:
                active_entries = 0
                disabled_entries = 0
                broken_entries = 0
        else:
            raw_json = json.dumps(data, ensure_ascii=False, default=str)
            archive_id = data.get('archive_id', f'startup_{int(now_dt.timestamp())}')
            timestamp = data.get('timestamp', now_dt.isoformat())
            total_entries = data.get('total_entries', 0)
            health_score = data.get('health_score', 100)
            changes_count = data.get('changes_count', 0)
            report = data.get('report', {})
            summary = report.get('summary', {}) if isinstance(report, dict) else getattr(report, 'summary', None)
            if isinstance(summary, dict):
                active_entries = summary.get('active_entries', 0)
                disabled_entries = summary.get('disabled_entries', 0)
                broken_entries = summary.get('broken_entries', 0)
            else:
                active_entries = getattr(summary, 'active_entries', 0) if summary else 0
                disabled_entries = getattr(summary, 'disabled_entries', 0) if summary else 0
                broken_entries = getattr(summary, 'broken_entries', 0) if summary else 0
            changes = data.get('changes', [])

        try:
            now_epoch = datetime.fromisoformat(timestamp).timestamp()
        except Exception:
            now_epoch = now_dt.timestamp()

        cursor.execute('''
            INSERT OR REPLACE INTO startup_audit_archives (
                archive_id, timestamp, created_at, total_entries,
                active_entries, disabled_entries, broken_entries,
                health_score, changes_count, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            archive_id, timestamp, now_epoch, total_entries,
            active_entries, disabled_entries, broken_entries,
            health_score, changes_count, raw_json
        ))

        if changes:
            for ch in changes:
                ch_dict = ch.model_dump(mode='json') if hasattr(ch, 'model_dump') else ch
                cursor.execute('''
                    INSERT INTO startup_changes (
                        archive_id, timestamp, created_at, change_type,
                        entry_id, name, description, previous_value, current_value
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    archive_id,
                    ch_dict.get('timestamp', timestamp),
                    now_epoch,
                    ch_dict.get('change_type', 'modified'),
                    ch_dict.get('entry_id', ''),
                    ch_dict.get('name', ''),
                    ch_dict.get('description', ''),
                    json.dumps(ch_dict.get('previous_value'), ensure_ascii=False) if ch_dict.get('previous_value') is not None else None,
                    json.dumps(ch_dict.get('current_value'), ensure_ascii=False) if ch_dict.get('current_value') is not None else None,
                ))

        return cursor.lastrowid or 0

    def upsert_device_inventory(
        self,
        cursor: sqlite3.Cursor,
        device_instance_id: str,
        friendly_name: Optional[str] = None,
        device_class: Optional[str] = None,
        install_date: Optional[str] = None,
    ) -> int:
        """Вставка или обновление записи в таблице device_inventory."""
        now_dt = datetime.now(timezone.utc)
        now_epoch = now_dt.timestamp()
        norm_id = str(device_instance_id).strip().upper()
        date_val = install_date or now_dt.strftime('%d.%m.%Y %H:%M')
        cursor.execute('''
            INSERT INTO device_inventory (
                device_instance_id, friendly_name, device_class, install_date, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(device_instance_id) DO UPDATE SET
                friendly_name = COALESCE(excluded.friendly_name, device_inventory.friendly_name),
                device_class = COALESCE(excluded.device_class, device_inventory.device_class),
                updated_at = excluded.updated_at
        ''', (norm_id, friendly_name or '', device_class or '', date_val, now_epoch, now_epoch))
        return cursor.lastrowid or 0

    def upsert_disk_inventory(self, cursor: sqlite3.Cursor, data: Any) -> int:
        """Вставка или обновление паспорта физического накопителя (disk_inventory)."""
        d = data if isinstance(data, dict) else (data.model_dump() if hasattr(data, 'model_dump') else vars(data))
        now_dt = datetime.now(timezone.utc)
        ts_str = d.get('timestamp') or now_dt.isoformat()
        now_epoch = now_dt.timestamp()
        serial = str(d.get('serial_number') or f"DISK_{d.get('disk_id', 0)}").strip()

        cursor.execute('''
            INSERT INTO disk_inventory (
                disk_id, device_path, serial_number, vendor, product,
                revision, bus_type, media_type, size_bytes, size_gb,
                sector_size, removable, partition_style, gpt_guid,
                partitions_json, first_seen, last_seen, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(serial_number) DO UPDATE SET
                disk_id = excluded.disk_id,
                device_path = excluded.device_path,
                vendor = excluded.vendor,
                product = excluded.product,
                revision = excluded.revision,
                bus_type = excluded.bus_type,
                media_type = excluded.media_type,
                size_bytes = excluded.size_bytes,
                size_gb = excluded.size_gb,
                sector_size = excluded.sector_size,
                removable = excluded.removable,
                partition_style = excluded.partition_style,
                gpt_guid = excluded.gpt_guid,
                partitions_json = excluded.partitions_json,
                last_seen = excluded.last_seen,
                updated_at = excluded.updated_at
        ''', (
            int(d.get('disk_id', 0)),
            d.get('device_path') or f"\\\\.\\PhysicalDrive{d.get('disk_id', 0)}",
            serial,
            d.get('vendor', ''),
            d.get('product') or d.get('name', ''),
            d.get('revision', ''),
            d.get('bus_type', 'Unknown'),
            d.get('media_type', 'SSD'),
            int(d.get('size_bytes', 0)),
            float(d.get('size_gb', 0.0)),
            int(d.get('sector_size', 512)),
            int(bool(d.get('removable', False))),
            d.get('partition_style', 'GPT'),
            d.get('gpt_guid', ''),
            json.dumps(d.get('partitions', []), ensure_ascii=False, default=str),
            ts_str,
            ts_str,
            now_epoch,
        ))
        return cursor.lastrowid or 0

    def upsert_volume_inventory(self, cursor: sqlite3.Cursor, data: Any) -> int:
        """Вставка или обновление паспорта логического тома (volume_inventory)."""
        v = data if isinstance(data, dict) else (data.model_dump() if hasattr(data, 'model_dump') else vars(data))
        now_dt = datetime.now(timezone.utc)
        ts_str = v.get('timestamp') or now_dt.isoformat()
        now_epoch = now_dt.timestamp()
        guid = str(v.get('volume_guid') or v.get('volume_id') or v.get('drive_letter', 'UNKNOWN')).strip()

        cursor.execute('''
            INSERT INTO volume_inventory (
                volume_guid, drive_letter, mount_point, label, filesystem,
                filesystem_flags, cluster_size_bytes, sector_size_bytes,
                total_bytes, total_gb, disk_id, first_seen, last_seen, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(volume_guid) DO UPDATE SET
                drive_letter = excluded.drive_letter,
                mount_point = excluded.mount_point,
                label = excluded.label,
                filesystem = excluded.filesystem,
                filesystem_flags = excluded.filesystem_flags,
                cluster_size_bytes = excluded.cluster_size_bytes,
                sector_size_bytes = excluded.sector_size_bytes,
                total_bytes = excluded.total_bytes,
                total_gb = excluded.total_gb,
                disk_id = excluded.disk_id,
                last_seen = excluded.last_seen,
                updated_at = excluded.updated_at
        ''', (
            guid,
            v.get('drive_letter', ''),
            v.get('mount_point', ''),
            v.get('label', ''),
            v.get('filesystem', 'NTFS'),
            int(v.get('filesystem_flags', 0) or 0),
            int(v.get('cluster_size_bytes', 4096) or 4096),
            int(v.get('sector_size_bytes', 512) or 512),
            int(v.get('total_bytes', 0) or 0),
            float(v.get('total_gb', 0.0) or 0.0),
            v.get('disk_id'),
            ts_str,
            ts_str,
            now_epoch,
        ))
        return cursor.lastrowid or 0

    def insert_disk_health_snapshot(self, cursor: sqlite3.Cursor, data: Any) -> int:
        """Вставка снимка здоровья / SMART / TBW накопителя (disk_health_snapshots)."""
        h = data if isinstance(data, dict) else (data.model_dump() if hasattr(data, 'model_dump') else vars(data))
        now_dt = datetime.now(timezone.utc)
        ts_str = h.get('timestamp') or now_dt.isoformat()
        try:
            created_at = float(h.get('created_at') or datetime.fromisoformat(ts_str).timestamp())
        except Exception:
            created_at = now_dt.timestamp()

        cursor.execute('''
            INSERT INTO disk_health_snapshots (
                timestamp, created_at, disk_id, serial_number, model, bus_type,
                temperature_c, wear_percent, available_spare, tbw_written_tb,
                tbw_read_tb, power_on_hours, power_cycles, unsafe_shutdowns,
                media_errors, error_log_entries, health_status, raw_smart_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ts_str,
            created_at,
            int(h.get('disk_id', 0)),
            h.get('serial_number'),
            h.get('model', ''),
            h.get('bus_type', 'Unknown'),
            h.get('temperature_c'),
            h.get('wear_percentage') or h.get('wear_percent'),
            h.get('available_spare_percent') or h.get('available_spare'),
            h.get('tbw_written_tb') or h.get('lifetime_write_tb'),
            h.get('tbw_read_tb') or h.get('lifetime_read_tb'),
            h.get('power_on_hours'),
            h.get('power_cycles'),
            h.get('unsafe_shutdowns'),
            h.get('media_errors'),
            h.get('error_log_entries'),
            h.get('health_status', 'Healthy'),
            json.dumps(h, ensure_ascii=False, default=str),
        ))
        return cursor.lastrowid or 0

    def insert_disk_performance_sample(self, cursor: sqlite3.Cursor, data: Any) -> int:
        """Вставка сэмпла производительности диска (disk_performance_samples)."""
        p = data if isinstance(data, dict) else (data.model_dump() if hasattr(data, 'model_dump') else vars(data))
        now_dt = datetime.now(timezone.utc)
        ts_str = p.get('timestamp') or now_dt.isoformat()
        try:
            created_at = float(p.get('created_at') or datetime.fromisoformat(ts_str).timestamp())
        except Exception:
            created_at = now_dt.timestamp()

        cursor.execute('''
            INSERT INTO disk_performance_samples (
                timestamp, created_at, disk_name, read_bytes_sec, write_bytes_sec,
                read_iops, write_iops, read_time_ms, write_time_ms, percent_disk_time, queue_length
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ts_str,
            created_at,
            p.get('disk_name') or f"PhysicalDrive{p.get('disk_id', 0)}",
            float(p.get('read_bytes_sec', 0.0) or 0.0),
            float(p.get('write_bytes_sec', 0.0) or 0.0),
            float(p.get('read_iops', 0.0) or 0.0),
            float(p.get('write_iops', 0.0) or 0.0),
            float(p.get('read_time_ms', 0.0) or p.get('avg_read_latency_ms', 0.0) or 0.0),
            float(p.get('write_time_ms', 0.0) or p.get('avg_write_latency_ms', 0.0) or 0.0),
            float(p.get('percent_disk_time', 0.0) or p.get('disk_time_percent', 0.0) or 0.0),
            float(p.get('queue_length', 0.0) or 0.0),
        ))
        return cursor.lastrowid or 0

    def insert_disk_io_event(self, cursor: sqlite3.Cursor, data: Any) -> int:
        """Вставка события ввода-вывода (disk_io_events)."""
        ev = data if isinstance(data, dict) else (data.model_dump() if hasattr(data, 'model_dump') else vars(data))
        now_dt = datetime.now(timezone.utc)
        ts_str = ev.get('timestamp') or now_dt.isoformat()
        try:
            created_at = float(ev.get('created_at') or datetime.fromisoformat(ts_str).timestamp())
        except Exception:
            created_at = now_dt.timestamp()

        cursor.execute('''
            INSERT INTO disk_io_events (
                timestamp, created_at, pid, process_name, disk_id,
                operation, bytes_count, duration_ms, offset, file_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ts_str,
            created_at,
            int(ev.get('pid', 0)),
            ev.get('process_name', ''),
            int(ev.get('disk_id', 0)),
            ev.get('operation', 'READ'),
            int(ev.get('bytes_count', 0)),
            ev.get('duration_ms'),
            ev.get('offset'),
            ev.get('file_path'),
        ))
        return cursor.lastrowid or 0

    def upsert_cpu_inventory(self, cursor: sqlite3.Cursor, data: Any) -> int:
        """Вставка или обновление паспорта физического процессора (cpu_inventory)."""
        c = data if isinstance(data, dict) else (data.model_dump() if hasattr(data, 'model_dump') else vars(data))
        now_dt = datetime.now(timezone.utc)
        ts_str = c.get('timestamp') or now_dt.isoformat()
        now_epoch = now_dt.timestamp()
        name = str(c.get('name') or f"CPU_{c.get('processor_id', 0)}").strip()

        cursor.execute('''
            INSERT INTO cpu_inventory (
                processor_id, name, vendor, architecture, physical_cores, logical_cores,
                base_frequency_mhz, max_frequency_mhz, l2_cache_kb, l3_cache_kb,
                socket, features_json, first_seen, last_seen, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                processor_id = excluded.processor_id,
                vendor = excluded.vendor,
                architecture = excluded.architecture,
                physical_cores = excluded.physical_cores,
                logical_cores = excluded.logical_cores,
                base_frequency_mhz = excluded.base_frequency_mhz,
                max_frequency_mhz = excluded.max_frequency_mhz,
                l2_cache_kb = excluded.l2_cache_kb,
                l3_cache_kb = excluded.l3_cache_kb,
                socket = excluded.socket,
                features_json = excluded.features_json,
                last_seen = excluded.last_seen,
                updated_at = excluded.updated_at
        ''', (
            int(c.get('processor_id', 0)),
            name,
            c.get('vendor', ''),
            c.get('architecture', 'x86_64'),
            int(c.get('physical_cores', 1) or 1),
            int(c.get('logical_cores', 1) or 1),
            float(c.get('base_frequency_mhz', 0.0) or 0.0),
            float(c.get('max_frequency_mhz', 0.0) or 0.0),
            c.get('l2_cache_kb'),
            c.get('l3_cache_kb'),
            c.get('socket', ''),
            json.dumps(c.get('features', []), ensure_ascii=False, default=str),
            ts_str,
            ts_str,
            now_epoch,
        ))
        return cursor.lastrowid or 0

    def upsert_ram_module_inventory(self, cursor: sqlite3.Cursor, data: Any) -> int:
        """Вставка или обновление паспорта планки оперативной памяти (ram_module_inventory)."""
        r = data if isinstance(data, dict) else (data.model_dump() if hasattr(data, 'model_dump') else vars(data))
        now_dt = datetime.now(timezone.utc)
        ts_str = r.get('timestamp') or now_dt.isoformat()
        now_epoch = now_dt.timestamp()
        serial = str(r.get('serial_number') or f"RAM_{r.get('bank_label', '')}_{r.get('slot_id', 0)}").strip()

        cursor.execute('''
            INSERT INTO ram_module_inventory (
                slot_id, bank_label, device_locator, serial_number, part_number,
                manufacturer, capacity_bytes, capacity_gb, speed_mhz, memory_type,
                form_factor, configured_voltage, first_seen, last_seen, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(serial_number) DO UPDATE SET
                slot_id = excluded.slot_id,
                bank_label = excluded.bank_label,
                device_locator = excluded.device_locator,
                part_number = excluded.part_number,
                manufacturer = excluded.manufacturer,
                capacity_bytes = excluded.capacity_bytes,
                capacity_gb = excluded.capacity_gb,
                speed_mhz = excluded.speed_mhz,
                memory_type = excluded.memory_type,
                form_factor = excluded.form_factor,
                configured_voltage = excluded.configured_voltage,
                last_seen = excluded.last_seen,
                updated_at = excluded.updated_at
        ''', (
            int(r.get('slot_id', 0)),
            r.get('bank_label', 'DIMM'),
            r.get('device_locator', ''),
            serial,
            r.get('part_number', ''),
            r.get('manufacturer', ''),
            int(r.get('capacity_bytes', 0) or 0),
            float(r.get('capacity_gb', 0.0) or 0.0),
            int(r.get('speed_mhz', 0) or 0),
            r.get('memory_type', 'DDR4'),
            r.get('form_factor', 'DIMM'),
            r.get('configured_voltage'),
            ts_str,
            ts_str,
            now_epoch,
        ))
        return cursor.lastrowid or 0

    def upsert_gpu_inventory(self, cursor: sqlite3.Cursor, data: Any) -> int:
        """Вставка или обновление паспорта графического ускорителя (gpu_inventory)."""
        g = data if isinstance(data, dict) else (data.model_dump() if hasattr(data, 'model_dump') else vars(data))
        now_dt = datetime.now(timezone.utc)
        ts_str = g.get('timestamp') or now_dt.isoformat()
        now_epoch = now_dt.timestamp()
        pci_id = str(g.get('pci_device_id') or g.get('pci_bus_id') or f"GPU_{g.get('gpu_id', 0)}_{g.get('name', '')}").strip()

        cursor.execute('''
            INSERT INTO gpu_inventory (
                gpu_id, pci_device_id, name, vendor, driver_version, driver_date,
                vram_bytes, vram_gb, pci_bus_id, bios_version, cuda_cores,
                directml_supported, first_seen, last_seen, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(pci_device_id) DO UPDATE SET
                gpu_id = excluded.gpu_id,
                name = excluded.name,
                vendor = excluded.vendor,
                driver_version = excluded.driver_version,
                driver_date = excluded.driver_date,
                vram_bytes = excluded.vram_bytes,
                vram_gb = excluded.vram_gb,
                pci_bus_id = excluded.pci_bus_id,
                bios_version = excluded.bios_version,
                cuda_cores = excluded.cuda_cores,
                directml_supported = excluded.directml_supported,
                last_seen = excluded.last_seen,
                updated_at = excluded.updated_at
        ''', (
            int(g.get('gpu_id', 0)),
            pci_id,
            g.get('name', 'Graphics Adapter'),
            g.get('vendor', ''),
            g.get('driver_version', ''),
            g.get('driver_date', ''),
            int(g.get('vram_bytes', 0) or 0),
            float(g.get('vram_gb', 0.0) or (g.get('memory_total_mb', 0.0) / 1024.0 if g.get('memory_total_mb') else 0.0)),
            g.get('pci_bus_id', ''),
            g.get('bios_version', ''),
            g.get('cuda_cores'),
            int(bool(g.get('directml_supported', True))),
            ts_str,
            ts_str,
            now_epoch,
        ))
        return cursor.lastrowid or 0

    def upsert_network_adapter_inventory(self, cursor: sqlite3.Cursor, data: Any) -> int:
        """Вставка или обновление паспорта сетевого адаптера (network_adapter_inventory)."""
        n = data if isinstance(data, dict) else (data.model_dump() if hasattr(data, 'model_dump') else vars(data))
        now_dt = datetime.now(timezone.utc)
        ts_str = n.get('timestamp') or now_dt.isoformat()
        now_epoch = now_dt.timestamp()
        guid = str(n.get('adapter_guid') or n.get('mac_address') or n.get('name', 'UNKNOWN')).strip()

        cursor.execute('''
            INSERT INTO network_adapter_inventory (
                adapter_id, adapter_guid, name, interface_name, mac_address,
                adapter_type, is_physical, is_wireless, max_speed_mbps,
                driver_name, driver_version, first_seen, last_seen, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(adapter_guid) DO UPDATE SET
                adapter_id = excluded.adapter_id,
                name = excluded.name,
                interface_name = excluded.interface_name,
                mac_address = excluded.mac_address,
                adapter_type = excluded.adapter_type,
                is_physical = excluded.is_physical,
                is_wireless = excluded.is_wireless,
                max_speed_mbps = excluded.max_speed_mbps,
                driver_name = excluded.driver_name,
                driver_version = excluded.driver_version,
                last_seen = excluded.last_seen,
                updated_at = excluded.updated_at
        ''', (
            int(n.get('adapter_id', 0)),
            guid,
            n.get('name', 'Network Adapter'),
            n.get('interface_name', ''),
            n.get('mac_address', ''),
            n.get('adapter_type', 'Ethernet'),
            int(bool(n.get('is_physical', True))),
            int(bool(n.get('is_wireless', False))),
            int(n.get('max_speed_mbps', 0) or 0),
            n.get('driver_name', ''),
            n.get('driver_version', ''),
            ts_str,
            ts_str,
            now_epoch,
        ))
        return cursor.lastrowid or 0

    def insert_cpu_telemetry_sample(self, cursor: sqlite3.Cursor, data: Any) -> int:
        """Вставка снимка метрик нагрузки и температур процессора (cpu_telemetry_samples)."""
        c = data if isinstance(data, dict) else (data.model_dump() if hasattr(data, 'model_dump') else vars(data))
        now_dt = datetime.now(timezone.utc)
        ts_str = c.get('timestamp') or now_dt.isoformat()
        try:
            created_at = float(c.get('created_at') or datetime.fromisoformat(ts_str).timestamp())
        except Exception:
            created_at = now_dt.timestamp()

        cursor.execute('''
            INSERT INTO cpu_telemetry_samples (
                timestamp, created_at, processor_id, total_percent, user_percent,
                kernel_percent, frequency_mhz, temperature_c, package_power_w,
                core_utilization_json, core_temperatures_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ts_str,
            created_at,
            int(c.get('processor_id', 0)),
            float(c.get('total_percent', 0.0) or 0.0),
            float(c.get('user_percent', 0.0) or 0.0),
            float(c.get('kernel_percent', 0.0) or 0.0),
            float(c.get('frequency_mhz', 0.0) or 0.0),
            c.get('temperature_c') or c.get('temperature_celsius'),
            c.get('package_power_w'),
            json.dumps(c.get('core_utilization') or c.get('per_core_percent', []), ensure_ascii=False, default=str),
            json.dumps(c.get('core_temperatures', []), ensure_ascii=False, default=str),
        ))
        return cursor.lastrowid or 0

    def insert_ram_telemetry_sample(self, cursor: sqlite3.Cursor, data: Any) -> int:
        """Вставка снимка метрик использования оперативной памяти (ram_telemetry_samples)."""
        r = data if isinstance(data, dict) else (data.model_dump() if hasattr(data, 'model_dump') else vars(data))
        now_dt = datetime.now(timezone.utc)
        ts_str = r.get('timestamp') or now_dt.isoformat()
        try:
            created_at = float(r.get('created_at') or datetime.fromisoformat(ts_str).timestamp())
        except Exception:
            created_at = now_dt.timestamp()

        cursor.execute('''
            INSERT INTO ram_telemetry_samples (
                timestamp, created_at, total_bytes, total_gb, used_bytes, used_gb,
                available_bytes, available_gb, percent_used, swap_total_gb,
                swap_used_gb, swap_percent, pool_paged_mb, pool_nonpaged_mb
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ts_str,
            created_at,
            int(r.get('total_bytes', 0) or 0),
            float(r.get('total_gb', 0.0) or 0.0),
            int(r.get('used_bytes', 0) or 0),
            float(r.get('used_gb', 0.0) or 0.0),
            int(r.get('available_bytes', 0) or 0),
            float(r.get('available_gb', 0.0) or 0.0),
            float(r.get('percent_used', 0.0) or r.get('percent', 0.0) or 0.0),
            float(r.get('swap_total_gb', 0.0) or 0.0),
            float(r.get('swap_used_gb', 0.0) or 0.0),
            float(r.get('swap_percent', 0.0) or 0.0),
            r.get('pool_paged_mb'),
            r.get('pool_nonpaged_mb'),
        ))
        return cursor.lastrowid or 0

    def insert_gpu_telemetry_sample(self, cursor: sqlite3.Cursor, data: Any) -> int:
        """Вставка снимка метрик GPU (gpu_telemetry_samples)."""
        g = data if isinstance(data, dict) else (data.model_dump() if hasattr(data, 'model_dump') else vars(data))
        now_dt = datetime.now(timezone.utc)
        ts_str = g.get('timestamp') or now_dt.isoformat()
        try:
            created_at = float(g.get('created_at') or datetime.fromisoformat(ts_str).timestamp())
        except Exception:
            created_at = now_dt.timestamp()

        cursor.execute('''
            INSERT INTO gpu_telemetry_samples (
                timestamp, created_at, gpu_id, name, load_percent, memory_used_mb,
                memory_total_mb, memory_percent, temperature_gpu_c, temperature_memory_c,
                fan_speed_pct, power_draw_w, clock_graphics_mhz, clock_memory_mhz
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ts_str,
            created_at,
            int(g.get('gpu_id', 0) or g.get('index', 0)),
            g.get('name', 'GPU'),
            g.get('load_percent') or g.get('utilization_gpu_pct'),
            float(g.get('memory_used_mb', 0.0) or (g.get('memory_used_gb', 0.0) * 1024.0 if g.get('memory_used_gb') else 0.0)),
            float(g.get('memory_total_mb', 0.0) or (g.get('memory_total_gb', 0.0) * 1024.0 if g.get('memory_total_gb') else 0.0)),
            g.get('memory_percent') or g.get('utilization_memory_pct'),
            g.get('temperature_gpu_c') or g.get('temperature_celsius'),
            g.get('temperature_memory_c'),
            g.get('fan_speed_pct'),
            g.get('power_draw_w'),
            g.get('clock_graphics_mhz'),
            g.get('clock_memory_mhz'),
        ))
        return cursor.lastrowid or 0

    def insert_network_adapter_sample(self, cursor: sqlite3.Cursor, data: Any) -> int:
        """Вставка снимка метрик сетевого адаптера (network_adapter_samples)."""
        n = data if isinstance(data, dict) else (data.model_dump() if hasattr(data, 'model_dump') else vars(data))
        now_dt = datetime.now(timezone.utc)
        ts_str = n.get('timestamp') or now_dt.isoformat()
        try:
            created_at = float(n.get('created_at') or datetime.fromisoformat(ts_str).timestamp())
        except Exception:
            created_at = now_dt.timestamp()

        cursor.execute('''
            INSERT INTO network_adapter_samples (
                timestamp, created_at, adapter_name, bytes_recv_sec, bytes_sent_sec,
                packets_recv_sec, packets_sent_sec, errors_in_sec, errors_out_sec,
                link_speed_mbps, is_connected
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ts_str,
            created_at,
            n.get('adapter_name') or n.get('name', 'Network Adapter'),
            float(n.get('bytes_recv_sec', 0.0) or n.get('bytes_recv_per_sec', 0.0) or 0.0),
            float(n.get('bytes_sent_sec', 0.0) or n.get('bytes_sent_per_sec', 0.0) or 0.0),
            float(n.get('packets_recv_sec', 0.0) or 0.0),
            float(n.get('packets_sent_sec', 0.0) or 0.0),
            float(n.get('errors_in_sec', 0.0) or 0.0),
            float(n.get('errors_out_sec', 0.0) or 0.0),
            int(n.get('link_speed_mbps', 0) or n.get('speed_mbps', 0) or 0),
            int(bool(n.get('is_connected', True) if n.get('is_connected') is not None else n.get('is_up', True))),
        ))
        return cursor.lastrowid or 0

