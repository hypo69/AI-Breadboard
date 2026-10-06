# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Sqlite - Reader
# =============================================================================
# Description:
#   Класс TelemetryReader для чтения и выборки данных телеметрии из SQLite.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.sqlite.reader import TelemetryReader
#
#     reader = TelemetryReader(connection_manager)
#     snapshots = reader.get_snapshots(limit=10)
#
# File: reader.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.sqlite
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 13:57:00
# =============================================================================

from __future__ import annotations

"""Класс TelemetryReader для выполнения выборок, аналитики и чтения данных телеметрии."""

import csv
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .connection import TelemetryConnectionManager

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class TelemetryReader:
    """Выполняет запросы чтения данных телеметрии, процессов, сенсоров и аудита из базы SQLite."""

    def __init__(self, connection_manager: TelemetryConnectionManager) -> None:
        """Инициализирует ридер телеметрии.

        Args:
            connection_manager: Менеджер подключений SQLite.
        """
        self._cm = connection_manager

    def get_snapshots(self, limit: int = 60, since_epoch: Optional[float] = None) -> List[Dict[str, Any]]:
        """Извлекает исторические срезы системной телеметрии."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            if since_epoch is not None:
                cursor.execute(
                    'SELECT * FROM system_snapshots WHERE created_at >= ? ORDER BY id DESC LIMIT ?',
                    (since_epoch, limit)
                )
            else:
                cursor.execute('SELECT * FROM system_snapshots ORDER BY id DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_latest_cpu(self) -> Optional[Dict[str, Any]]:
        """Извлекает последние метрики процессора из таблицы system_snapshots."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, timestamp, created_at, hostname, cpu_total_percent, cpu_frequency_mhz
                FROM system_snapshots
                ORDER BY id DESC
                LIMIT 1;
            ''')
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_cpu_history(self, limit: int = 60, since_epoch: Optional[float] = None) -> List[Dict[str, Any]]:
        """Извлекает историю нагрузки процессора."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            if since_epoch is not None:
                cursor.execute('''
                    SELECT id, timestamp, created_at, cpu_total_percent, cpu_frequency_mhz
                    FROM system_snapshots
                    WHERE created_at >= ?
                    ORDER BY id DESC
                    LIMIT ?;
                ''', (since_epoch, limit))
            else:
                cursor.execute('''
                    SELECT id, timestamp, created_at, cpu_total_percent, cpu_frequency_mhz
                    FROM system_snapshots
                    ORDER BY id DESC
                    LIMIT ?;
                ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_latest_storage_data(self) -> Dict[str, Any]:
        """Извлекает последние данные о накопителях и разделах."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, timestamp, created_at, disks_json, physical_disks_json
                FROM system_snapshots
                ORDER BY id DESC
                LIMIT 1;
            ''')
            row = cursor.fetchone()
            if not row:
                return {'partitions': [], 'physical_disks': []}

            partitions: List[Dict[str, Any]] = []
            if row['disks_json']:
                try:
                    partitions = json.loads(row['disks_json'])
                except Exception:
                    partitions = []

            physical_disks: List[Dict[str, Any]] = []
            if row['physical_disks_json']:
                try:
                    physical_disks = json.loads(row['physical_disks_json'])
                except Exception:
                    physical_disks = []

            return {
                'id': row['id'],
                'timestamp': row['timestamp'],
                'created_at': row['created_at'],
                'partitions': partitions,
                'physical_disks': physical_disks,
            }

    def get_latest_snapshot_full(self) -> Optional[Dict[str, Any]]:
        """Извлекает и десериализует последний системный снимок со всеми метаданными и процессами."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM system_snapshots ORDER BY id DESC LIMIT 1;')
            row = cursor.fetchone()
            if not row:
                return None

            snap_row = dict(row)
            snap_id = snap_row.get('id')

            # 1. Попытка десериализации raw_json
            raw_json_str = snap_row.get('raw_json')
            full_dict: Dict[str, Any] = {}
            if raw_json_str and isinstance(raw_json_str, str):
                try:
                    full_dict = json.loads(raw_json_str)
                except Exception:
                    full_dict = {}

            # 2. Обогащение/fallback из именованных колонок
            for field in ('hostname', 'username', 'uptime_seconds', 'os_name', 'os_build', 'os_install_date',
                          'system_language', 'os_install_language', 'user_locale', 'system_locale', 'timezone', 'codepage',
                          'cpu_total_percent', 'cpu_frequency_mhz', 'memory_total_gb', 'memory_used_gb', 'memory_percent',
                          'swap_percent', 'gpu_load_percent', 'gpu_temp_c', 'disk_read_bytes_sec', 'disk_write_bytes_sec',
                          'disk_read_count_sec', 'disk_write_count_sec', 'network_sent_bytes_sec', 'network_recv_bytes_sec', 'timestamp'):
                if snap_row.get(field) is not None and (field not in full_dict or not full_dict[field]):
                    full_dict[field] = snap_row[field]

            # 3. Десериализация JSON-колонок
            json_column_mappings = {
                'input_languages_json': 'input_languages',
                'disks_json': 'disks',
                'physical_disks_json': 'physical_disks',
                'monitors_json': 'monitors',
                'updates_json': 'updates',
                'office_json': 'office',
                'onedrive_json': 'onedrive',
                'battery_json': 'battery',
                'ram_sticks_json': 'ram_sticks',
                'listening_ports_json': 'listening_ports',
                'alerts_json': 'alerts',
                'hardware_audit': 'hardware_audit',
            }
            for col_name, target_key in json_column_mappings.items():
                val_str = snap_row.get(col_name)
                if val_str and isinstance(val_str, str) and (target_key not in full_dict or not full_dict[target_key]):
                    try:
                        full_dict[target_key] = json.loads(val_str)
                    except Exception:
                        pass

            # 4. Процессы (если не были в raw_json)
            if 'top_processes' not in full_dict or not full_dict['top_processes']:
                if snap_id:
                    cursor.execute(
                        'SELECT pid, name, status, cpu_percent, memory_mb, memory_percent, num_threads, num_handles, '
                        'username, read_bytes_sec, write_bytes_sec, integrity_level, elevation, ppid, parent_name, '
                        'executable as executable_path, cmdline, sid, session_id, creation_time, process_guid, ancestor_chain, launch_reason '
                        'FROM process_snapshots WHERE snapshot_id = ? ORDER BY cpu_percent DESC LIMIT 50;',
                        (snap_id,)
                    )
                    full_dict['top_processes'] = [dict(p) for p in cursor.fetchall()]

            # 5. Структурирование CPU и Memory если отсутствуют объекты
            if 'cpu' not in full_dict or not isinstance(full_dict.get('cpu'), dict):
                full_dict['cpu'] = {
                    'total_percent': float(snap_row.get('cpu_total_percent') or 0.0),
                    'frequency_mhz': float(snap_row.get('cpu_frequency_mhz') or 0.0),
                    'model': full_dict.get('cpu_model', 'Intel / AMD Processor'),
                    'architecture': 'x86_64',
                }
            if 'memory' not in full_dict or not isinstance(full_dict.get('memory'), dict):
                tot_m = float(snap_row.get('memory_total_gb') or 0.0)
                used_m = float(snap_row.get('memory_used_gb') or 0.0)
                full_dict['memory'] = {
                    'total_gb': tot_m,
                    'used_gb': used_m,
                    'available_gb': max(0.0, tot_m - used_m),
                    'percent': float(snap_row.get('memory_percent') or 0.0),
                    'swap_percent': float(snap_row.get('swap_percent') or 0.0),
                }
            if 'disk_io' not in full_dict or not isinstance(full_dict.get('disk_io'), dict):
                full_dict['disk_io'] = {
                    'read_bytes_per_sec': float(snap_row.get('disk_read_bytes_sec') or 0.0),
                    'write_bytes_per_sec': float(snap_row.get('disk_write_bytes_sec') or 0.0),
                    'read_count_per_sec': float(snap_row.get('disk_read_count_sec') or 0.0),
                    'write_count_per_sec': float(snap_row.get('disk_write_count_sec') or 0.0),
                }

            return full_dict

    def get_snapshot_processes(self, snapshot_id: int) -> List[Dict[str, Any]]:
        """Извлекает список процессов, зафиксированных в снимке."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM process_snapshots WHERE snapshot_id = ? ORDER BY cpu_percent DESC, memory_mb DESC',
                (snapshot_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_process_history(
        self,
        name: Optional[str] = None,
        pid: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Извлекает историю поведения процесса по имени или PID."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            if pid is not None and name is not None:
                cursor.execute(
                    'SELECT * FROM process_snapshots WHERE pid = ? AND name LIKE ? ORDER BY id DESC LIMIT ?',
                    (pid, f'%{name}%', limit)
                )
            elif pid is not None:
                cursor.execute(
                    'SELECT * FROM process_snapshots WHERE pid = ? ORDER BY id DESC LIMIT ?',
                    (pid, limit)
                )
            elif name is not None:
                cursor.execute(
                    'SELECT * FROM process_snapshots WHERE name LIKE ? ORDER BY id DESC LIMIT ?',
                    (f'%{name}%', limit)
                )
            else:
                cursor.execute('SELECT * FROM process_snapshots ORDER BY id DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_latest_processes(self, limit: int = 50, sort_by: str = 'cpu') -> List[Dict[str, Any]]:
        """Извлекает процессы из самого последнего зафиксированного снимка."""
        sort_key = (sort_by or 'cpu').lower()
        if sort_key in ('handles', 'descriptors'):
            order_col = 'num_handles DESC, cpu_percent DESC'
        elif sort_key in ('memory', 'ram'):
            order_col = 'memory_mb DESC, cpu_percent DESC'
        else:
            order_col = 'cpu_percent DESC, memory_mb DESC'

        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(id) FROM system_snapshots;')
            row = cursor.fetchone()
            last_snap_id = row[0] if row and row[0] is not None else None
            if last_snap_id is None:
                cursor.execute('SELECT MAX(snapshot_id) FROM process_snapshots;')
                row = cursor.fetchone()
                last_snap_id = row[0] if row and row[0] is not None else None
            if last_snap_id is None:
                return []

            sql = f'''
                SELECT pid, name, status, cpu_percent, memory_mb, memory_percent,
                       num_threads, num_handles, username, read_bytes_sec, write_bytes_sec, timestamp
                FROM process_snapshots
                WHERE snapshot_id = ?
                ORDER BY {order_col}
            '''
            if limit is not None and limit > 0:
                cursor.execute(sql + ' LIMIT ?', (last_snap_id, limit))
            else:
                cursor.execute(sql, (last_snap_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_process_stats(self, name: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Возвращает агрегированную статистику процессов и выбросы."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            if name:
                cursor.execute('SELECT * FROM process_rollups_2min WHERE name LIKE ? ORDER BY id DESC LIMIT ?', (f'%{name}%', limit))
            else:
                cursor.execute('SELECT * FROM process_rollups_2min ORDER BY id DESC LIMIT ?', (limit,))
            rollups_2min = [dict(r) for r in cursor.fetchall()]

            if name:
                cursor.execute('SELECT * FROM process_rollups_daily WHERE name LIKE ? ORDER BY date DESC LIMIT ?', (f'%{name}%', limit))
            else:
                cursor.execute('SELECT * FROM process_rollups_daily ORDER BY date DESC LIMIT ?', (limit,))
            daily_stats = [dict(r) for r in cursor.fetchall()]

            if name:
                cursor.execute('SELECT * FROM process_outliers WHERE name LIKE ? ORDER BY id DESC LIMIT ?', (f'%{name}%', limit))
            else:
                cursor.execute('SELECT * FROM process_outliers ORDER BY id DESC LIMIT ?', (limit,))
            outliers = [dict(r) for r in cursor.fetchall()]

            return {
                'name_filter': name,
                'rollups_2min': rollups_2min,
                'daily_stats': daily_stats,
                'outliers': outliers,
                'total_rollups_count': len(rollups_2min),
                'total_outliers_count': len(outliers),
            }

    def get_events(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Извлекает список зафиксированных событий телеметрии."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            if event_type:
                cursor.execute('SELECT * FROM telemetry_events WHERE event_type = ? ORDER BY id DESC LIMIT ?', (event_type, limit))
            else:
                cursor.execute('SELECT * FROM telemetry_events ORDER BY id DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_sensor_history(
        self,
        sensor_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Извлекает историю показаний сенсоров."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            if sensor_id and category:
                cursor.execute(
                    'SELECT * FROM sensor_polls WHERE sensor_id = ? AND sensor_category = ? ORDER BY id DESC LIMIT ?',
                    (sensor_id, category, limit)
                )
            elif sensor_id:
                cursor.execute('SELECT * FROM sensor_polls WHERE sensor_id = ? ORDER BY id DESC LIMIT ?', (sensor_id, limit))
            elif category:
                cursor.execute('SELECT * FROM sensor_polls WHERE sensor_category = ? ORDER BY id DESC LIMIT ?', (category, limit))
            else:
                cursor.execute('SELECT * FROM sensor_polls ORDER BY id DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_latest_sensors(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Извлекает последнее актуальное значение каждого сенсора."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            query = '''
                SELECT s1.* FROM sensor_polls s1
                INNER JOIN (
                    SELECT sensor_id, MAX(id) as max_id
                    FROM sensor_polls
                    GROUP BY sensor_id
                ) s2 ON s1.id = s2.max_id
                ORDER BY s1.sensor_category, s1.sensor_name
            '''
            if limit is not None:
                cursor.execute(query + ' LIMIT ?', (limit,))
            else:
                cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def get_cpu_hierarchy_metrics(self) -> Dict[str, Any]:
        """Извлекает структурированные иерархические метрики процессора из SQLite.

        Выбирает последние замеры сенсоров CPU, системные снимки и историю нагрузки/температур.

        Returns:
            Dict[str, Any]: Словарь с сенсорами, снимками, паспортом и историей.
        """
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Последние сенсоры CPU из sensor_polls (исключая дисковые и GPU метрики)
            query_sensors = '''
                SELECT s1.* FROM sensor_polls s1
                INNER JOIN (
                    SELECT sensor_id, MAX(id) as max_id
                    FROM sensor_polls
                    WHERE hardware_type = 'cpu' OR (
                        hardware_name NOT LIKE '%GPU%'
                        AND hardware_name NOT LIKE '%Storage%'
                        AND hardware_name NOT LIKE '%Disk%'
                        AND sensor_id NOT LIKE 'disk_speed_%'
                        AND (hardware_type = 'system' OR sensor_category IN ('Voltages', 'Powers', 'Clocks', 'Temperatures', 'Load', 'voltages', 'powers', 'clocks', 'temperatures', 'load'))
                    )
                    GROUP BY sensor_id
                ) s2 ON s1.id = s2.max_id
                ORDER BY s1.sensor_category, s1.sensor_name
            '''
            cursor.execute(query_sensors)
            sensors = [dict(row) for row in cursor.fetchall()]

            # 2. Последний системный снимок
            cursor.execute('SELECT * FROM system_snapshots ORDER BY id DESC LIMIT 1')
            snap_row = cursor.fetchone()
            latest_snapshot = dict(snap_row) if snap_row else None

            # 3. Данные инвентаризации CPU
            cursor.execute('SELECT * FROM cpu_inventory ORDER BY processor_id ASC LIMIT 1')
            inv_row = cursor.fetchone()
            if inv_row:
                cpu_inv = dict(inv_row)
            else:
                cpu_inv = self._probe_and_persist_cpu_inventory(cursor)

            # 4. История снимков для графиков
            cursor.execute('''
                SELECT timestamp, created_at, cpu_total_percent, cpu_frequency_mhz
                FROM system_snapshots
                ORDER BY id DESC
                LIMIT 60
            ''')
            history_rows = [dict(r) for r in cursor.fetchall()]
            history_rows.reverse()

            return {
                'sensors': sensors,
                'snapshot': latest_snapshot,
                'inventory': cpu_inv,
                'history': history_rows,
            }

    def _probe_and_persist_cpu_inventory(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        """Опрашивает спецификации CPU и сохраняет их в cpu_inventory."""
        import os
        import platform
        import time
        from datetime import datetime, timezone
        try:
            import psutil
        except ImportError:
            psutil = None

        vendor = 'Intel'
        model = platform.processor() or 'Processor'
        arch = 'x86_64' if platform.machine() in ('AMD64', 'x86_64') else platform.machine()
        phys_cores = psutil.cpu_count(logical=False) if psutil else 1
        log_cores = psutil.cpu_count(logical=True) if psutil else 1
        freq = psutil.cpu_freq() if psutil else None
        base_mhz = float(freq.current if freq else 2900.0)
        max_mhz = float(freq.max if (freq and freq.max) else base_mhz)
        socket = ''
        l2_kb = None
        l3_kb = None
        stepping = ''
        features: List[str] = []

        if os.name == 'nt':
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as k:
                    reg_name, _ = winreg.QueryValueEx(k, 'ProcessorNameString')
                    reg_vendor, _ = winreg.QueryValueEx(k, 'VendorIdentifier')
                    reg_mhz, _ = winreg.QueryValueEx(k, '~MHz')
                    reg_ident, _ = winreg.QueryValueEx(k, 'Identifier')
                    if reg_name:
                        model = str(reg_name).strip()
                    if reg_vendor:
                        v_str = str(reg_vendor).strip()
                        vendor = 'Intel' if 'intel' in v_str.lower() else ('AMD' if 'amd' in v_str.lower() else v_str)
                    if reg_mhz:
                        base_mhz = float(reg_mhz)
                    if reg_ident:
                        stepping = str(reg_ident).strip()
            except Exception:
                pass

            try:
                import win32com.client
                wmi_obj = win32com.client.GetObject('winmgmts:')
                for p in wmi_obj.InstancesOf('Win32_Processor'):
                    if getattr(p, 'Name', None):
                        model = str(p.Name).strip()
                    if getattr(p, 'SocketDesignation', None):
                        socket = str(p.SocketDesignation).strip()
                    if getattr(p, 'L2CacheSize', None):
                        l2_kb = int(p.L2CacheSize)
                    if getattr(p, 'L3CacheSize', None):
                        l3_kb = int(p.L3CacheSize)
                    if getattr(p, 'MaxClockSpeed', None):
                        max_mhz = float(p.MaxClockSpeed)
                    if getattr(p, 'Manufacturer', None):
                        m_str = str(p.Manufacturer).strip()
                        vendor = 'Intel' if 'intel' in m_str.lower() else ('AMD' if 'amd' in m_str.lower() else m_str)
                    if getattr(p, 'NumberOfCores', None):
                        phys_cores = int(p.NumberOfCores)
                    if getattr(p, 'NumberOfLogicalProcessors', None):
                        log_cores = int(p.NumberOfLogicalProcessors)
                    break
            except Exception:
                pass

        now_iso = datetime.now(timezone.utc).isoformat()
        now_epoch = time.time()

        cpu_inv = {
            'processor_id': 0,
            'name': model,
            'vendor': vendor,
            'architecture': arch,
            'physical_cores': phys_cores or 1,
            'logical_cores': log_cores or 1,
            'base_frequency_mhz': base_mhz,
            'max_frequency_mhz': max_mhz,
            'l2_cache_kb': l2_kb,
            'l3_cache_kb': l3_kb,
            'socket': socket,
            'stepping': stepping,
            'features_json': json.dumps(features),
            'first_seen': now_iso,
            'last_seen': now_iso,
            'updated_at': now_epoch,
        }

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO cpu_inventory (
                    processor_id, name, vendor, architecture, physical_cores, logical_cores,
                    base_frequency_mhz, max_frequency_mhz, l2_cache_kb, l3_cache_kb, socket,
                    features_json, first_seen, last_seen, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                cpu_inv['processor_id'], cpu_inv['name'], cpu_inv['vendor'], cpu_inv['architecture'],
                cpu_inv['physical_cores'], cpu_inv['logical_cores'], cpu_inv['base_frequency_mhz'],
                cpu_inv['max_frequency_mhz'], cpu_inv['l2_cache_kb'], cpu_inv['l3_cache_kb'],
                cpu_inv['socket'], cpu_inv['features_json'], cpu_inv['first_seen'],
                cpu_inv['last_seen'], cpu_inv['updated_at']
            ))
        except Exception as ex:
            logger.debug(f"[reader] Не удалось сохранить cpu_inventory: {ex}")

        return cpu_inv

    def get_app_polls(self, app: Optional[str] = None, metric_name: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Извлекает историю опросов приложений."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            if app and metric_name:
                cursor.execute('SELECT * FROM app_polls WHERE app = ? AND metric_name = ? ORDER BY id DESC LIMIT ?', (app, metric_name, limit))
            elif app:
                cursor.execute('SELECT * FROM app_polls WHERE app = ? ORDER BY id DESC LIMIT ?', (app, limit))
            else:
                cursor.execute('SELECT * FROM app_polls ORDER BY id DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_app_events(self, app: Optional[str] = None, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Извлекает события приложений."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            if app and event_type:
                cursor.execute('SELECT * FROM app_events WHERE app = ? AND event_type = ? ORDER BY id DESC LIMIT ?', (app, event_type, limit))
            elif app:
                cursor.execute('SELECT * FROM app_events WHERE app = ? ORDER BY id DESC LIMIT ?', (app, limit))
            else:
                cursor.execute('SELECT * FROM app_events ORDER BY id DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_app_param_changes(self, app: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Извлекает изменения параметров приложений."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            if app:
                cursor.execute('SELECT * FROM app_param_changes WHERE app = ? ORDER BY id DESC LIMIT ?', (app, limit))
            else:
                cursor.execute('SELECT * FROM app_param_changes ORDER BY id DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def export_app_polls_to_csv(self, app: Optional[str] = None, output_path: Optional[Union[str, Path]] = None, limit: int = 50000) -> Path:
        """Экспортирует историю опросов приложений в CSV-файл."""
        polls = self.get_app_polls(app=app, limit=limit)
        target = Path(output_path) if output_path else Path('app_polls.csv')
        target.parent.mkdir(parents=True, exist_ok=True)
        headers = ['timestamp', 'app', 'poll_type', 'metric_name', 'value', 'unit', 'status', 'details']
        with open(target, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for p in polls:
                writer.writerow([
                    p.get('timestamp', ''), p.get('app', ''), p.get('poll_type', ''),
                    p.get('metric_name', ''), p.get('value', ''), p.get('unit', ''),
                    p.get('status', ''), p.get('details', ''),
                ])
        return target

    def export_app_events_to_csv(self, app: Optional[str] = None, output_path: Optional[Union[str, Path]] = None, limit: int = 50000) -> Path:
        """Экспортирует историю событий приложений в CSV-файл."""
        events = self.get_app_events(app=app, limit=limit)
        target = Path(output_path) if output_path else Path('app_events.csv')
        target.parent.mkdir(parents=True, exist_ok=True)
        headers = ['timestamp', 'app', 'event_type', 'status', 'user', 'details']
        with open(target, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for e in events:
                writer.writerow([
                    e.get('timestamp', ''), e.get('app', ''), e.get('event_type', ''),
                    e.get('status', ''), e.get('user', ''), e.get('details', ''),
                ])
        return target

    def export_app_param_changes_to_csv(self, app: Optional[str] = None, output_path: Optional[Union[str, Path]] = None, limit: int = 50000) -> Path:
        """Экспортирует историю изменения параметров в CSV-файл."""
        params = self.get_app_param_changes(app=app, limit=limit)
        target = Path(output_path) if output_path else Path('app_param_changes.csv')
        target.parent.mkdir(parents=True, exist_ok=True)
        headers = ['timestamp', 'app', 'param_name', 'old_value', 'new_value', 'status', 'user', 'details']
        with open(target, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for p in params:
                writer.writerow([
                    p.get('timestamp', ''), p.get('app', ''), p.get('param_name', ''),
                    p.get('old_value', ''), p.get('new_value', ''), p.get('status', ''),
                    p.get('user', ''), p.get('details', ''),
                ])
        return target

    def get_custom_records(self, source_file: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Извлекает кастомные записи логов."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            if source_file:
                cursor.execute('SELECT * FROM custom_records WHERE source_file = ? ORDER BY id DESC LIMIT ?', (source_file, limit))
            else:
                cursor.execute('SELECT * FROM custom_records ORDER BY id DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_device_events(self, event_type: Optional[str] = None, device_instance_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Извлекает события устройств."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            if event_type and device_instance_id:
                cursor.execute('SELECT * FROM device_events WHERE event_type = ? AND device_instance_id = ? ORDER BY id DESC LIMIT ?', (event_type, device_instance_id, limit))
            elif event_type:
                cursor.execute('SELECT * FROM device_events WHERE event_type = ? ORDER BY id DESC LIMIT ?', (event_type, limit))
            elif device_instance_id:
                cursor.execute('SELECT * FROM device_events WHERE device_instance_id = ? ORDER BY id DESC LIMIT ?', (device_instance_id, limit))
            else:
                cursor.execute('SELECT * FROM device_events ORDER BY id DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_device_install_date(self, device_instance_id: str) -> Optional[str]:
        """Возвращает дату установки устройства из таблицы device_inventory."""
        norm_id = str(device_instance_id).strip().upper()
        if not norm_id:
            return None
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT install_date FROM device_inventory WHERE UPPER(device_instance_id) = ?', (norm_id,))
            row = cursor.fetchone()
            return str(row[0]) if (row and row[0]) else None

    def get_w64_events(self, event_type: Optional[str] = None, provider: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Извлекает системные события W64/ETW."""
        query = 'SELECT raw_json FROM w64_events WHERE 1=1'
        params: List[Any] = []
        if event_type:
            query += ' AND event_type = ?'
            params.append(event_type)
        if provider:
            query += ' AND provider = ?'
            params.append(provider)
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(max(1, limit))

        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            results = []
            for row in cursor.fetchall():
                try:
                    results.append(json.loads(row[0]))
                except Exception:
                    continue
            return results

    def get_incidents(self, limit: int = 50, trigger_type: Optional[str] = None, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Возвращает список зафиксированных инцидентов."""
        query = 'SELECT * FROM incidents WHERE 1=1'
        params: List[Any] = []
        if trigger_type:
            query += ' AND trigger_type = ?'
            params.append(trigger_type)
        if severity:
            query += ' AND severity = ?'
            params.append(severity)
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)

        results: List[Dict[str, Any]] = []
        try:
            with self._cm.lock, self._cm.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(params))
                for row in cursor.fetchall():
                    item = dict(row)
                    for f in ('trigger_metrics_json', 'suspect_processes_json', 'related_events_json', 'metrics_summary_json', 'raw_window_json'):
                        if item.get(f):
                            try:
                                item[f.replace('_json', '')] = json.loads(item[f])
                            except Exception:
                                item[f.replace('_json', '')] = []
                    results.append(item)
        except Exception as ex:
            logger.error(f'Ошибка при получении инцидентов: {ex}')
        return results

    def get_system_rollups(self, tier: str = '1m', start_epoch: Optional[float] = None, end_epoch: Optional[float] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Возвращает сжатые бакеты метрик за период."""
        query = 'SELECT * FROM telemetry_rollups WHERE tier = ?'
        params: List[Any] = [tier]
        if start_epoch is not None:
            query += ' AND period_start_epoch >= ?'
            params.append(start_epoch)
        if end_epoch is not None:
            query += ' AND period_end_epoch <= ?'
            params.append(end_epoch)
        query += ' ORDER BY period_start_epoch DESC LIMIT ?'
        params.append(limit)

        results: List[Dict[str, Any]] = []
        try:
            with self._cm.lock, self._cm.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(params))
                for row in cursor.fetchall():
                    results.append(dict(row))
        except Exception as ex:
            logger.error(f'Ошибка при получении rollups: {ex}')
        return results

    def get_reboot_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Извлекает историю сессий перезагрузок."""
        results: List[Dict[str, Any]] = []
        try:
            with self._cm.lock, self._cm.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM reboot_history ORDER BY boot_time DESC, created_at DESC LIMIT ?', (limit,))
                for row in cursor.fetchall():
                    item = dict(row)
                    for f in ('bugcheck_params_json', 'evidence_json', 'events_chain_json', 'raw_json'):
                        if item.get(f):
                            try:
                                item[f.replace('_json', '')] = json.loads(item[f])
                            except Exception:
                                pass
                    results.append(item)
        except Exception as ex:
            logger.error(f'Ошибка извлечения истории перезагрузок: {ex}')
        return results

    def get_latest_reboot_session(self) -> Optional[Dict[str, Any]]:
        """Возвращает самую последнюю запись сессии перезагрузки."""
        history = self.get_reboot_history(limit=1)
        return history[0] if history else None

    def get_extended_audits(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Возвращает историю расширенных системных аудитов."""
        results: List[Dict[str, Any]] = []
        try:
            with self._cm.lock, self._cm.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM system_extended_audits ORDER BY created_at DESC LIMIT ?', (limit,))
                for row in cursor.fetchall():
                    item = dict(row)
                    if item.get('raw_json'):
                        try:
                            item['data'] = json.loads(item['raw_json'])
                        except Exception:
                            pass
                    results.append(item)
        except Exception as ex:
            logger.error(f'Ошибка извлечения расширенных аудитов: {ex}')
        return results

    def get_latest_extended_audit(self) -> Optional[Dict[str, Any]]:
        """Возвращает последний расширенный системный аудит."""
        audits = self.get_extended_audits(limit=1)
        return audits[0] if audits else None

    def get_hardware_audits(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Возвращает историю аудитов аппаратного обеспечения из таблицы hardware_audits."""
        results: List[Dict[str, Any]] = []
        try:
            with self._cm.lock, self._cm.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM hardware_audits ORDER BY created_at DESC LIMIT ?', (limit,))
                for row in cursor.fetchall():
                    item = dict(row)
                    if item.get('raw_json'):
                        try:
                            item['data'] = json.loads(item['raw_json'])
                        except Exception:
                            pass
                    results.append(item)
        except Exception as ex:
            logger.error(f'Ошибка извлечения аудитов оборудования: {ex}')
        return results

    def get_latest_hardware_audit(self) -> Optional[Dict[str, Any]]:
        """Возвращает самый последний сохраненный аудит аппаратного обеспечения."""
        audits = self.get_hardware_audits(limit=1)
        return audits[0] if audits else None

    def get_startup_archives(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Возвращает историю архивных снимков автозапуска из таблицы startup_audit_archives."""
        results: List[Dict[str, Any]] = []
        try:
            with self._cm.lock, self._cm.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM startup_audit_archives ORDER BY created_at DESC LIMIT ?', (limit,))
                for row in cursor.fetchall():
                    item = dict(row)
                    if item.get('raw_json'):
                        try:
                            item['data'] = json.loads(item['raw_json'])
                        except Exception:
                            pass
                    results.append(item)
        except Exception as ex:
            logger.error(f'Ошибка извлечения архивов автозапуска: {ex}')
        return results

    def get_latest_startup_archive(self) -> Optional[Dict[str, Any]]:
        """Возвращает самый последний сохраненный снимок автозапуска."""
        audits = self.get_startup_archives(limit=1)
        return audits[0] if audits else None

    def get_startup_changes(self, limit: int = 100, archive_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Возвращает историю зафиксированных отличий/изменений в автозапуске."""
        results: List[Dict[str, Any]] = []
        try:
            with self._cm.lock, self._cm.get_connection() as conn:
                cursor = conn.cursor()
                if archive_id:
                    cursor.execute(
                        'SELECT * FROM startup_changes WHERE archive_id = ? ORDER BY created_at DESC, id DESC LIMIT ?',
                        (archive_id, limit)
                    )
                else:
                    cursor.execute(
                        'SELECT * FROM startup_changes ORDER BY created_at DESC, id DESC LIMIT ?',
                        (limit,)
                    )
                for row in cursor.fetchall():
                    item = dict(row)
                    if item.get('previous_value'):
                        try:
                            item['previous_value'] = json.loads(item['previous_value'])
                        except Exception:
                            pass
                    if item.get('current_value'):
                        try:
                            item['current_value'] = json.loads(item['current_value'])
                        except Exception:
                            pass
                    results.append(item)
        except Exception as ex:
            logger.error(f'Ошибка извлечения изменений автозапуска: {ex}')
        return results

    def get_process_provenance_history(
        self,
        guid: Optional[str] = None,
        pid: Optional[int] = None,
        name: Optional[str] = None,
        user: Optional[str] = None,
        event_type: Optional[str] = None,
        hours: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Извлечение исторических событий provenance процессов."""
        results: List[Dict[str, Any]] = []
        query = 'SELECT * FROM process_provenance_events WHERE 1=1'
        params: List[Any] = []

        if hours is not None:
            cutoff = time.time() - (hours * 3600)
            query += ' AND created_at >= ?'
            params.append(cutoff)
        if guid:
            query += ' AND process_guid = ?'
            params.append(guid)
        if pid is not None:
            query += ' AND pid = ?'
            params.append(pid)
        if name:
            query += ' AND name LIKE ?'
            params.append(f'%{name}%')
        if user:
            query += ' AND (user LIKE ? OR sid LIKE ?)'
            params.extend([f'%{user}%', f'%{user}%'])
        if event_type:
            query += ' AND event_type = ?'
            params.append(event_type)

        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)

        try:
            with self._cm.lock, self._cm.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(params))
                for row in cursor.fetchall():
                    item = dict(row)
                    if item.get('details_json'):
                        try:
                            item['details'] = json.loads(item['details_json'])
                        except Exception:
                            item['details'] = item['details_json']
                    results.append(item)
        except Exception as ex:
            logger.error(f'Ошибка извлечения provenance процессов: {ex}')
        return results

    def get_process_lineage(self, guid_or_pid: Union[str, int]) -> List[Dict[str, Any]]:
        """Построение полной восходящей цепочки предков (lineage) процесса."""
        str_val = str(guid_or_pid)
        chain: List[Dict[str, Any]] = []
        visited_guids: set = set()
        visited_pids: set = set()

        history = self.get_process_provenance_history(guid=str_val, limit=1)
        if not history and str_val.isdigit():
            history = self.get_process_provenance_history(pid=int(str_val), limit=1)

        current_node: Optional[Dict[str, Any]] = history[0] if history else None

        while current_node:
            node_guid = current_node.get('process_guid')
            node_pid = current_node.get('pid')

            if (node_guid and node_guid in visited_guids) or (node_pid and node_pid in visited_pids):
                break

            if node_guid:
                visited_guids.add(node_guid)
            if node_pid:
                visited_pids.add(node_pid)

            chain.append(current_node)
            parent_guid = current_node.get('parent_guid')
            parent_pid = current_node.get('ppid') or current_node.get('parent_pid')

            parent_node = None
            if parent_guid:
                parent_hist = self.get_process_provenance_history(guid=parent_guid, limit=1)
                if parent_hist:
                    parent_node = parent_hist[0]

            if not parent_node and parent_pid:
                parent_hist = self.get_process_provenance_history(pid=int(parent_pid), limit=1)
                if parent_hist:
                    parent_node = parent_hist[0]

            current_node = parent_node

        chain.reverse()
        return chain

    def get_telemetry_rollups(
        self,
        level: str = 'hourly',
        sensor_id: Optional[str] = None,
        start_epoch: Optional[float] = None,
        end_epoch: Optional[float] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Извлекает агрегированные показатели сенсоров для заданного уровня (hourly, daily, weekly, monthly, yearly).

        Args:
            level: Уровень иерархии ('hourly', 'daily', 'weekly', 'monthly', 'yearly').
            sensor_id: Фильтр по идентификатору сенсора (опционально).
            start_epoch: Нижняя граница времени бакета bucket_start (опционально).
            end_epoch: Верхняя граница времени бакета bucket_start (опционально).
            limit: Максимальное число возвращаемых записей.

        Returns:
            List[Dict[str, Any]]: Список агрегированных бакетов со статистикой.
        """
        lvl_clean = str(level).strip().lower()
        table_name = f'telemetry_{lvl_clean}'
        valid_tables = {'telemetry_hourly', 'telemetry_daily', 'telemetry_weekly', 'telemetry_monthly', 'telemetry_yearly'}
        if table_name not in valid_tables:
            table_name = 'telemetry_hourly'

        conditions = []
        params: List[Any] = []

        if sensor_id is not None:
            conditions.append('sensor_id = ?')
            params.append(sensor_id)
        if start_epoch is not None:
            conditions.append('bucket_start >= ?')
            params.append(float(start_epoch))
        if end_epoch is not None:
            conditions.append('bucket_start < ?')
            params.append(float(end_epoch))

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM {table_name} {where_clause} ORDER BY bucket_start DESC LIMIT ?"
        params.append(int(limit))

        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_telemetry_spikes(
        self,
        sensor_id: Optional[str] = None,
        start_epoch: Optional[float] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Извлекает зафиксированные статистические всплески и аномалии сенсоров.

        Args:
            sensor_id: Фильтр по идентификатору сенсора (опционально).
            start_epoch: Нижняя граница времени регистрации (опционально).
            limit: Максимальное число возвращаемых записей.

        Returns:
            List[Dict[str, Any]]: Список аномальных записей.
        """
        conditions = []
        params: List[Any] = []

        if sensor_id is not None:
            conditions.append('sensor_id = ?')
            params.append(sensor_id)
        if start_epoch is not None:
            conditions.append('created_at >= ?')
            params.append(float(start_epoch))

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM telemetry_spikes {where_clause} ORDER BY created_at DESC LIMIT ?"
        params.append(int(limit))

        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_disk_inventory(self, disk_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Извлекает паспортные данные физических дисков из таблицы disk_inventory."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            if disk_id is not None:
                cursor.execute('SELECT * FROM disk_inventory WHERE disk_id = ? ORDER BY disk_id ASC', (disk_id,))
            else:
                cursor.execute('SELECT * FROM disk_inventory ORDER BY disk_id ASC')
            return [dict(row) for row in cursor.fetchall()]

    def get_volume_inventory(self) -> List[Dict[str, Any]]:
        """Извлекает паспортные данные логических томов из таблицы volume_inventory."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM volume_inventory ORDER BY drive_letter ASC')
            return [dict(row) for row in cursor.fetchall()]

    def get_disk_health_history(
        self,
        disk_id: Optional[int] = None,
        serial_number: Optional[str] = None,
        limit: int = 100,
        since_epoch: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Извлекает историю показателей здоровья и износа накопителей."""
        conditions = []
        params: List[Any] = []

        if disk_id is not None:
            conditions.append('disk_id = ?')
            params.append(disk_id)
        if serial_number is not None:
            conditions.append('serial_number = ?')
            params.append(serial_number)
        if since_epoch is not None:
            conditions.append('created_at >= ?')
            params.append(float(since_epoch))

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM disk_health_snapshots {where_clause} ORDER BY created_at DESC LIMIT ?"
        params.append(int(limit))

        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_disk_performance_samples(
        self,
        disk_name: Optional[str] = None,
        limit: int = 100,
        since_epoch: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Извлекает историю показателей производительности дисков (IOPS, MB/s)."""
        conditions = []
        params: List[Any] = []

        if disk_name is not None:
            conditions.append('disk_name = ?')
            params.append(disk_name)
        if since_epoch is not None:
            conditions.append('created_at >= ?')
            params.append(float(since_epoch))

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM disk_performance_samples {where_clause} ORDER BY created_at DESC LIMIT ?"
        params.append(int(limit))

        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_disk_io_events(
        self,
        pid: Optional[int] = None,
        disk_id: Optional[int] = None,
        limit: int = 100,
        since_epoch: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Извлекает события прямого ввода-вывода процессов."""
        conditions = []
        params: List[Any] = []

        if pid is not None:
            conditions.append('pid = ?')
            params.append(pid)
        if disk_id is not None:
            conditions.append('disk_id = ?')
            params.append(disk_id)
        if since_epoch is not None:
            conditions.append('created_at >= ?')
            params.append(float(since_epoch))

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM disk_io_events {where_clause} ORDER BY created_at DESC LIMIT ?"
        params.append(int(limit))

        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_cpu_inventory(self, processor_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Извлекает паспортные данные процессоров из таблицы cpu_inventory."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            if processor_id is not None:
                cursor.execute('SELECT * FROM cpu_inventory WHERE processor_id = ? ORDER BY processor_id ASC', (processor_id,))
            else:
                cursor.execute('SELECT * FROM cpu_inventory ORDER BY processor_id ASC')
            return [dict(row) for row in cursor.fetchall()]

    def get_ram_module_inventory(self) -> List[Dict[str, Any]]:
        """Извлекает паспортные данные физических планок памяти из таблицы ram_module_inventory."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM ram_module_inventory ORDER BY slot_id ASC')
            return [dict(row) for row in cursor.fetchall()]

    def get_gpu_inventory(self, gpu_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Извлекает паспортные данные графических ускорителей из таблицы gpu_inventory."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            if gpu_id is not None:
                cursor.execute('SELECT * FROM gpu_inventory WHERE gpu_id = ? ORDER BY gpu_id ASC', (gpu_id,))
            else:
                cursor.execute('SELECT * FROM gpu_inventory ORDER BY gpu_id ASC')
            return [dict(row) for row in cursor.fetchall()]

    def get_network_adapter_inventory(self) -> List[Dict[str, Any]]:
        """Извлекает паспортные данные сетевых интерфейсов из таблицы network_adapter_inventory."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM network_adapter_inventory ORDER BY adapter_id ASC')
            return [dict(row) for row in cursor.fetchall()]

    def get_cpu_telemetry_samples(
        self,
        processor_id: Optional[int] = None,
        limit: int = 100,
        since_epoch: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Извлекает историю показателей нагрузки и температур процессоров."""
        conditions = []
        params: List[Any] = []

        if processor_id is not None:
            conditions.append('processor_id = ?')
            params.append(processor_id)
        if since_epoch is not None:
            conditions.append('created_at >= ?')
            params.append(float(since_epoch))

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM cpu_telemetry_samples {where_clause} ORDER BY created_at DESC LIMIT ?"
        params.append(int(limit))

        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_ram_telemetry_samples(
        self,
        limit: int = 100,
        since_epoch: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Извлекает историю показателей использования оперативной памяти."""
        conditions = []
        params: List[Any] = []

        if since_epoch is not None:
            conditions.append('created_at >= ?')
            params.append(float(since_epoch))

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM ram_telemetry_samples {where_clause} ORDER BY created_at DESC LIMIT ?"
        params.append(int(limit))

        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_gpu_telemetry_samples(
        self,
        gpu_id: Optional[int] = None,
        name: Optional[str] = None,
        limit: int = 100,
        since_epoch: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Извлекает историю показателей нагрузки, памяти и температур GPU."""
        conditions = []
        params: List[Any] = []

        if gpu_id is not None:
            conditions.append('gpu_id = ?')
            params.append(gpu_id)
        if name is not None:
            conditions.append('name = ?')
            params.append(name)
        if since_epoch is not None:
            conditions.append('created_at >= ?')
            params.append(float(since_epoch))

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM gpu_telemetry_samples {where_clause} ORDER BY created_at DESC LIMIT ?"
        params.append(int(limit))

        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_network_adapter_samples(
        self,
        adapter_name: Optional[str] = None,
        limit: int = 100,
        since_epoch: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Извлекает историю показателей сетевой активности адаптеров."""
        conditions = []
        params: List[Any] = []

        if adapter_name is not None:
            conditions.append('adapter_name = ?')
            params.append(adapter_name)
        if since_epoch is not None:
            conditions.append('created_at >= ?')
            params.append(float(since_epoch))

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM network_adapter_samples {where_clause} ORDER BY created_at DESC LIMIT ?"
        params.append(int(limit))

        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]


