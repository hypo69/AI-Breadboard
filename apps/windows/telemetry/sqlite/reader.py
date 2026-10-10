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
# Updated: 2026-10-10 05:41:00
# =============================================================================

from __future__ import annotations

"""Класс TelemetryReader для выполнения выборок, аналитики и чтения данных телеметрии."""

import csv
import json
import sqlite3
import time
from datetime import datetime, timezone
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
        elif sort_key in ('memory', 'ram', 'memory_mb'):
            order_col = 'memory_mb DESC, cpu_percent DESC'
        elif sort_key == 'memory_percent':
            order_col = 'memory_percent DESC, cpu_percent DESC'
        elif sort_key == 'name':
            order_col = 'name ASC'
        elif sort_key == 'pid':
            order_col = 'pid ASC'
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
                       num_threads, num_handles, username, read_bytes_sec, write_bytes_sec,
                       integrity_level, elevation, ppid, parent_name, executable, cmdline, timestamp
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

    # =========================================================================
    # Подсистемы рефакторинга: Data-First SQLite Readers
    # =========================================================================

    # 1. Windows Event Logs
    def get_latest_event_log_channels(self) -> List[Dict[str, Any]]:
        """Извлечение последнего снимка каналов журналов событий."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT snapshot_id FROM event_log_channel_snapshots
                ORDER BY id DESC LIMIT 1
            ''')
            row = cursor.fetchone()
            if not row:
                return []
            snap_id = row['snapshot_id'] if isinstance(row, sqlite3.Row) else row[0]
            cursor.execute('''
                SELECT channel_name AS name, is_enabled AS enabled, record_count,
                       size_bytes, channel_type, display_name, description
                FROM event_log_channel_snapshots
                WHERE snapshot_id = ?
                ORDER BY record_count DESC
            ''', (snap_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_event_log_entries(
        self,
        channel: str = 'System',
        level: str = '',
        limit: int = 50,
        hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """Выборка записей журнала событий из кеша по каналу и уровню."""
        conditions = ['channel = ?']
        params: List[Any] = [channel]

        if level:
            conditions.append('LOWER(level) = LOWER(?)')
            params.append(level)

        if hours > 0:
            since_time = time.time() - (hours * 3600)
            conditions.append('created_at >= ?')
            params.append(since_time)

        where_clause = f"WHERE {' AND '.join(conditions)}"
        query = f'''
            SELECT channel, event_id, level, provider_name, time_created, message
            FROM event_log_entries_cache
            {where_clause}
            ORDER BY id DESC
            LIMIT ?
        '''
        params.append(int(limit))

        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = [dict(r) for r in cursor.fetchall()]
            if not rows and hours > 0:
                # Fallback без фильтра по времени, если база была заполнена раньше
                params[-2] = 0.0
                cursor.execute(query, params)
                rows = [dict(r) for r in cursor.fetchall()]
            return rows

    def get_latest_event_log_intelligence_profile(self, channel: str = 'System') -> Optional[Dict[str, Any]]:
        """Извлечение последнего сохраненного профиля Log Intelligence."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM event_log_intelligence_profiles
                WHERE channel = ?
                ORDER BY id DESC LIMIT 1
            ''', (channel,))
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d['critical_incidents'] = json.loads(d['critical_incidents_json']) if d.get('critical_incidents_json') else []
            d['top_clusters'] = json.loads(d['top_clusters_json']) if d.get('top_clusters_json') else []
            d['bursts'] = json.loads(d['bursts_json']) if d.get('bursts_json') else []
            decision_gate = json.loads(d['decision_gate_json']) if d.get('decision_gate_json') else {}
            profile_data = {
                'total_events': d.get('total_analyzed', 0),
                'unique_templates_count': d.get('unique_patterns_count', 0),
                'critical_count': len(d['critical_incidents']),
                'health_score': 100 - min(100, len(d['critical_incidents']) * 10),
                'top_patterns': d['top_clusters'],
                'bursts': d['bursts'],
            }
            d['profile'] = profile_data
            d['decision'] = decision_gate
            return d

    def get_latest_event_log_report(self) -> Optional[Dict[str, Any]]:
        """Формирование сводного отчета о журналах и ошибках из базы данных."""
        channels = self.get_latest_event_log_channels()
        if not channels:
            return None
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT channel, event_id, level, provider_name, time_created, message
                FROM event_log_entries_cache
                WHERE LOWER(level) IN ('error', 'critical', 'warning')
                ORDER BY id DESC LIMIT 20
            ''')
            errors = [dict(r) for r in cursor.fetchall()]

            crit_count = sum(1 for e in errors if str(e.get('level', '')).lower() == 'critical')
            err_count = sum(1 for e in errors if str(e.get('level', '')).lower() == 'error')
            warn_count = sum(1 for e in errors if str(e.get('level', '')).lower() == 'warning')

            return {
                'total_channels': len(channels),
                'critical_events_24h': crit_count,
                'error_events_24h': err_count,
                'warning_events_24h': warn_count,
                'channels': channels,
                'recent_errors': errors,
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }

    # 2. Windows Firewall Manager
    def get_latest_firewall_profiles(self) -> Optional[Dict[str, Any]]:
        """Извлечение состояния профилей брандмауэра Windows."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT domain_enabled, private_enabled, public_enabled,
                       domain_default_inbound, private_default_inbound, public_default_inbound,
                       stealth_mode_enabled, timestamp
                FROM firewall_profile_snapshots
                ORDER BY id DESC LIMIT 1
            ''')
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_latest_firewall_rules(self, direction: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
        """Выборка правил фильтрации брандмауэра Windows из последнего снимка."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT snapshot_id FROM firewall_rule_snapshots ORDER BY id DESC LIMIT 1')
            row = cursor.fetchone()
            if not row:
                return []
            snap_id = row['snapshot_id'] if isinstance(row, sqlite3.Row) else row[0]

            conditions = ['snapshot_id = ?']
            params: List[Any] = [snap_id]
            if direction:
                conditions.append('LOWER(direction) = LOWER(?)')
                params.append(direction)

            where_clause = f"WHERE {' AND '.join(conditions)}"
            query = f'''
                SELECT rule_name AS name, display_name, direction, action, enabled,
                       protocol, local_port, remote_port, program_path, profile_mask
                FROM firewall_rule_snapshots
                {where_clause}
                ORDER BY id ASC
                LIMIT ?
            '''
            params.append(int(limit))
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]

    # 3. Windows Services Manager
    def get_latest_services_list(self, status: Optional[str] = None, limit: int = 500) -> List[Dict[str, Any]]:
        """Извлечение списка служб Windows из последнего снимка."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT snapshot_id FROM services_snapshots ORDER BY id DESC LIMIT 1')
            row = cursor.fetchone()
            if not row:
                return []
            snap_id = row['snapshot_id'] if isinstance(row, sqlite3.Row) else row[0]

            conditions = ['snapshot_id = ?']
            params: List[Any] = [snap_id]
            if status:
                conditions.append('LOWER(state) = LOWER(?)')
                params.append(status)

            where_clause = f"WHERE {' AND '.join(conditions)}"
            query = f'''
                SELECT service_name AS name, display_name, state AS status,
                       start_type AS startup_type, pid, binary_path AS binpath,
                       account AS user_account, is_orphaned
                FROM services_snapshots
                {where_clause}
                ORDER BY service_name ASC
                LIMIT ?
            '''
            params.append(int(limit))
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]

    def get_latest_services_report(self) -> Optional[Dict[str, Any]]:
        """Формирование сводного отчета о службах Windows."""
        services = self.get_latest_services_list(limit=1000)
        if not services:
            return None
        total = len(services)
        running = sum(1 for s in services if str(s.get('status', '')).upper() in ('RUNNING', '4', 'SERVICE_RUNNING'))
        stopped = sum(1 for s in services if str(s.get('status', '')).upper() in ('STOPPED', '1', 'SERVICE_STOPPED'))
        orphaned = sum(1 for s in services if s.get('is_orphaned'))

        return {
            'total_services': total,
            'running_services': running,
            'stopped_services': stopped,
            'orphaned_services': orphaned,
            'services': services,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

    def get_service_change_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Извлечение истории изменений служб."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, service_name, display_name, action,
                       old_state, new_state, performed_by, details_json
                FROM service_change_events
                ORDER BY id DESC LIMIT ?
            ''', (int(limit),))
            rows = []
            for r in cursor.fetchall():
                d = dict(r)
                if d.get('details_json'):
                    d['details'] = json.loads(d['details_json'])
                rows.append(d)
            return rows

    # 4. CPU Throttling & Power Limits
    def get_latest_throttling_snapshot(self) -> Optional[Dict[str, Any]]:
        """Извлечение последнего снимка троттлинга процессора и термических зон."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT snapshot_id, timestamp, prochot_active, pl1_limit_watts,
                       pl2_limit_watts, current_power_watts, max_core_temp_c,
                       package_temp_c, dpc_latency_us, isr_latency_us,
                       throttling_reasons_json
                FROM cpu_throttling_snapshots
                ORDER BY id DESC LIMIT 1
            ''')
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d['throttling_reasons'] = json.loads(d['throttling_reasons_json']) if d.get('throttling_reasons_json') else []

            snap_id = d['snapshot_id']
            cursor.execute('''
                SELECT zone_name, temperature_c, critical_limit_c, throttling_limit_c, sensor_provider
                FROM thermal_zone_snapshots
                WHERE snapshot_id = ?
            ''', (snap_id,))
            d['thermal_zones'] = [dict(z) for z in cursor.fetchall()]
            return d

    # 5. Behavioral Forensics
    def get_latest_forensics_snapshot(self) -> Optional[Dict[str, Any]]:
        """Извлечение последнего снимка поведенческой форензики."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT foreground_window_title, foreground_process_name,
                       foreground_pid, user_idle_seconds, camera_active_apps_json,
                       microphone_active_apps_json, userassist_top_apps_json, timestamp
                FROM forensics_snapshots
                ORDER BY id DESC LIMIT 1
            ''', )
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d['camera_active_apps'] = json.loads(d['camera_active_apps_json']) if d.get('camera_active_apps_json') else []
            d['microphone_active_apps'] = json.loads(d['microphone_active_apps_json']) if d.get('microphone_active_apps_json') else []
            d['userassist_top_apps'] = json.loads(d['userassist_top_apps_json']) if d.get('userassist_top_apps_json') else []
            return d

    # 6. Process Leaks & Resource Starvation
    def get_latest_process_leak_report(self, limit: int = 20) -> Optional[Dict[str, Any]]:
        """Извлечение последнего снимка утечек ресурсов процессов."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT snapshot_id, timestamp, total_processes, suspicious_count
                FROM process_leak_snapshots
                ORDER BY id DESC LIMIT 1
            ''')
            row = cursor.fetchone()
            if not row:
                return None
            snap_id = row['snapshot_id'] if isinstance(row, sqlite3.Row) else row[0]
            report = dict(row)

            cursor.execute('''
                SELECT pid, name, handles_count, gdi_objects, user_objects,
                       page_faults, working_set_mb, leak_risk_score, leak_risk_reasons_json
                FROM process_leak_items
                WHERE snapshot_id = ?
                ORDER BY handles_count DESC
                LIMIT ?
            ''', (snap_id, int(limit)))
            items = []
            for r in cursor.fetchall():
                d = dict(r)
                d['leak_risk_reasons'] = json.loads(d['leak_risk_reasons_json']) if d.get('leak_risk_reasons_json') else []
                items.append(d)
            report['all_processes'] = items
            report['top_handle_hogs'] = sorted(items, key=lambda x: x.get('handles_count', 0), reverse=True)[:10]
            report['top_gdi_hogs'] = sorted(items, key=lambda x: x.get('gdi_objects', 0), reverse=True)[:10]
            report['top_page_fault_hogs'] = sorted(items, key=lambda x: x.get('page_faults', 0), reverse=True)[:10]
            report['suspicious_processes'] = [x for x in items if x.get('leak_risk_score') != 'normal']
            return report

    # 7. Defender Security
    def get_latest_defender_status(self) -> Optional[Dict[str, Any]]:
        """Извлечение статуса Защитника Windows."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM defender_snapshots
                ORDER BY id DESC LIMIT 1
            ''')
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            if d.get('raw_status_json'):
                try:
                    d.update(json.loads(d['raw_status_json']))
                except Exception:
                    pass
            return d

    def get_latest_defender_exclusions(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Извлечение исключений антивируса Defender."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT snapshot_id FROM defender_exclusions ORDER BY id DESC LIMIT 1')
            row = cursor.fetchone()
            if not row:
                return []
            snap_id = row['snapshot_id'] if isinstance(row, sqlite3.Row) else row[0]
            cursor.execute('''
                SELECT exclusion_type, exclusion_value, risk_level
                FROM defender_exclusions
                WHERE snapshot_id = ?
                LIMIT ?
            ''', (snap_id, limit))
            items = []
            for r in cursor.fetchall():
                d = dict(r)
                d['type'] = d.get('exclusion_type', 'path')
                d['value'] = d.get('exclusion_value', '')
                items.append(d)
            return items

    def get_latest_defender_asr_rules(self) -> List[Dict[str, Any]]:
        """Извлечение правил ASR Защитника Windows."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT snapshot_id FROM defender_asr_rules ORDER BY id DESC LIMIT 1')
            row = cursor.fetchone()
            if not row:
                return []
            snap_id = row['snapshot_id'] if isinstance(row, sqlite3.Row) else row[0]
            cursor.execute('''
                SELECT rule_guid, rule_name, rule_action
                FROM defender_asr_rules
                WHERE snapshot_id = ?
            ''', (snap_id,))
            items = []
            for r in cursor.fetchall():
                d = dict(r)
                d['guid'] = d.get('rule_guid', '')
                d['name'] = d.get('rule_name', '')
                d['state'] = d.get('rule_action', 'not_configured')
                items.append(d)
            return items

    def get_latest_defender_threats(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Извлечение обнаруженных угроз Defender."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT threat_id, threat_name, severity, category, resources_json, detection_time
                FROM defender_threats
                ORDER BY id DESC LIMIT ?
            ''', (limit,))
            rows = []
            for r in cursor.fetchall():
                d = dict(r)
                d['resources'] = json.loads(d['resources_json']) if d.get('resources_json') else []
                d['status'] = d.get('status', 'Cleaned')
                d['initial_detection_time'] = d.get('detection_time')
                rows.append(d)
            return rows

    def get_latest_defender_diagnostics(self) -> Dict[str, Any]:
        """Сводная диагностика безопасности Defender."""
        status = self.get_latest_defender_status() or {}
        exclusions = self.get_latest_defender_exclusions()
        asr_rules = self.get_latest_defender_asr_rules()
        threats = self.get_latest_defender_threats()
        return {
            'status': status,
            'exclusions': exclusions,
            'asr_rules': asr_rules,
            'threats': threats,
            'total_exclusions': len(exclusions),
            'total_asr_rules': len(asr_rules),
            'active_threats_count': len(threats),
        }

    # 8. Process Network & Process Manager
    def get_latest_process_network_activity(
        self,
        limit: int = 100,
        only_internet: bool = True,
    ) -> List[Dict[str, Any]]:
        """Извлечение сетевой активности процессов из process_network_snapshots."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT snapshot_id FROM process_network_snapshots ORDER BY id DESC LIMIT 1')
            row = cursor.fetchone()
            if not row:
                return []
            snap_id = row['snapshot_id'] if isinstance(row, sqlite3.Row) else row[0]

            conditions = ['snapshot_id = ?']
            params: List[Any] = [snap_id]
            if only_internet:
                conditions.append("LOWER(service_type) = 'internet' OR remote_address != ''")

            where_clause = f"WHERE {' AND '.join(conditions)}"
            query = f'''
                SELECT pid, process_name, local_address, remote_address, protocol,
                       status, service_type, sent_kb, recv_kb, read_speed_kbs, write_speed_kbs
                FROM process_network_snapshots
                {where_clause}
                ORDER BY sent_kb + recv_kb DESC
                LIMIT ?
            '''
            params.append(int(limit))
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]

    # 9. Software Transparency Scanner
    def get_software_inventory_from_db(self, limit: int = 200, offset: int = 0) -> List[Dict[str, Any]]:
        """Извлечение инвентаря установленного ПО с агрегацией данных из SQLite."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.*,
                       (SELECT COUNT(*) FROM software_storage_locations l WHERE l.app_id = s.app_id) AS storage_locations_count,
                       (SELECT COALESCE(SUM(size_bytes), 0) FROM software_storage_locations l WHERE l.app_id = s.app_id) AS total_storage_bytes,
                       (SELECT summary FROM software_ai_research r WHERE r.app_id = s.app_id) AS ai_summary,
                       (SELECT confidence_level FROM software_ai_research r WHERE r.app_id = s.app_id) AS ai_confidence
                FROM software_inventory s
                ORDER BY s.display_name ASC
                LIMIT ? OFFSET ?
            ''', (int(limit), int(offset)))
            return [dict(r) for r in cursor.fetchall()]

    def get_software_app_details_from_db(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Извлечение полной карточки установленной программы со всеми связанными данными."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM software_inventory WHERE app_id = ?', (app_id,))
            row = cursor.fetchone()
            if not row:
                return None
            app_data = dict(row)

            cursor.execute('SELECT category, path, size_bytes, file_count, last_updated FROM software_storage_locations WHERE app_id = ?', (app_id,))
            app_data['storage_locations'] = [dict(r) for r in cursor.fetchall()]

            cursor.execute('SELECT file_path, format, size_bytes, snippet FROM software_config_files WHERE app_id = ?', (app_id,))
            app_data['config_files'] = [dict(r) for r in cursor.fetchall()]

            cursor.execute('SELECT * FROM software_ai_research WHERE app_id = ?', (app_id,))
            ai_row = cursor.fetchone()
            if ai_row:
                ai_dict = dict(ai_row)
                ai_dict['confirmed_facts'] = json.loads(ai_dict['confirmed_facts_json']) if ai_dict.get('confirmed_facts_json') else []
                ai_dict['inferred_facts'] = json.loads(ai_dict['inferred_facts_json']) if ai_dict.get('inferred_facts_json') else []
                app_data['ai_research'] = ai_dict
            else:
                app_data['ai_research'] = None

            return app_data

    def get_security_events(
        self,
        event_id: Optional[int] = None,
        user: Optional[str] = None,
        process_name: Optional[str] = None,
        pid: Optional[int] = None,
        channel: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        since_epoch: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Выборка нормализованных событий журнала безопасности Windows с фильтрами.

        Args:
            event_id: Фильтр по Event ID (например, 4688, 4624, 1116).
            user: Фильтр по имени субъекта или целевого пользователя (подстрока).
            process_name: Фильтр по имени процесса.
            pid: Фильтр по идентификатору процесса PID.
            channel: Фильтр по имени журнала (Security или Defender).
            limit: Максимальное количество возвращаемых записей.
            offset: Смещение выборки.
            since_epoch: Нижняя граница времени epoch.

        Returns:
            List[Dict[str, Any]]: Список событий безопасности.
        """
        conditions: List[str] = []
        params: List[Any] = []

        if channel:
            conditions.append('channel = ?')
            params.append(str(channel))

        if event_id is not None:
            conditions.append('event_id = ?')
            params.append(int(event_id))

        if user:
            conditions.append('(subject_user LIKE ? OR target_user LIKE ?)')
            params.extend([f'%{user}%', f'%{user}%'])

        if process_name:
            conditions.append('(process_name LIKE ? OR parent_process_name LIKE ?)')
            params.extend([f'%{process_name}%', f'%{process_name}%'])

        if pid is not None:
            conditions.append('(process_id = ? OR parent_process_id = ?)')
            params.extend([int(pid), int(pid)])

        if since_epoch is not None:
            conditions.append('created_at >= ?')
            params.append(float(since_epoch))

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f'''
            SELECT * FROM security_events
            {where_clause}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        '''
        params.extend([int(limit), int(offset)])

        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = [dict(r) for r in cursor.fetchall()]
            for r in rows:
                if r.get('event_data_json'):
                    try:
                        r['event_data'] = json.loads(r['event_data_json'])
                    except Exception:
                        r['event_data'] = {}
                else:
                    r['event_data'] = {}
            return rows

    def get_security_failed_logons(self, limit: int = 50, hours: int = 24) -> List[Dict[str, Any]]:
        """Выборка событий неудачных попыток входа и сбоев аутентификации (4625, 4771).

        Args:
            limit: Лимит записей.
            hours: Глубина выборки в часах.

        Returns:
            List[Dict[str, Any]]: Список неудачных попыток входа.
        """
        since_time = time.time() - (hours * 3600) if hours > 0 else 0.0
        query = '''
            SELECT * FROM security_events
            WHERE event_id IN (4625, 4771) AND created_at >= ?
            ORDER BY id DESC
            LIMIT ?
        '''
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (since_time, int(limit)))
            return [dict(r) for r in cursor.fetchall()]

    def get_security_process_creations(
        self,
        process_name: Optional[str] = None,
        user: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Выборка событий создания процессов (Event ID 4688) с информацией о родителях и командной строке.

        Args:
            process_name: Подстрока имени процесса.
            user: Имя пользователя инициатора.
            limit: Лимит записей.

        Returns:
            List[Dict[str, Any]]: Список запусков процессов.
        """
        conditions = ['event_id = 4688']
        params: List[Any] = []

        if process_name:
            conditions.append('(process_name LIKE ? OR command_line LIKE ?)')
            params.extend([f'%{process_name}%', f'%{process_name}%'])

        if user:
            conditions.append('subject_user LIKE ?')
            params.append(f'%{user}%')

        where_clause = f"WHERE {' AND '.join(conditions)}"
        query = f'''
            SELECT id, event_record_id, timestamp, subject_user, process_id,
                   process_name, parent_process_id, parent_process_name,
                   command_line, logon_id, message
            FROM security_events
            {where_clause}
            ORDER BY id DESC
            LIMIT ?
        '''
        params.append(int(limit))

        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]

    def get_security_bookmark(self, channel: str = 'Security') -> Optional[Dict[str, Any]]:
        """Извлечение последней сохраненной закладки для канала журнала событий.

        Args:
            channel: Имя канала (по умолчанию 'Security').

        Returns:
            Optional[Dict[str, Any]]: Словарь с состоянием закладки или None.
        """
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM security_collector_bookmarks WHERE channel = ?', (channel,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_security_stats(self) -> Dict[str, Any]:
        """Получить сводную статистику по событиям безопасности в базе данных SQLite.

        Returns:
            Dict[str, Any]: Словарь со счетчиками и последним record_id.
        """
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*), MAX(event_record_id), MIN(timestamp), MAX(timestamp) FROM security_events')
            row = cursor.fetchone()
            total_events = row[0] if row else 0
            max_rec_id = row[1] if row and row[1] else 0
            min_ts = row[2] if row and row[2] else ''
            max_ts = row[3] if row and row[3] else ''

            cursor.execute('''
                SELECT event_id, COUNT(*) as cnt
                FROM security_events
                GROUP BY event_id
                ORDER BY cnt DESC
                LIMIT 10
            ''')
            top_ids = {r[0]: r[1] for r in cursor.fetchall()}

            cursor.execute('SELECT COUNT(*) FROM security_events WHERE event_id = 4688')
            proc_events = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM security_events WHERE event_id = 4625')
            failed_logons = cursor.fetchone()[0]

            return {
                'total_events': total_events,
                'max_record_id': max_rec_id,
                'first_event_time': min_ts,
                'latest_event_time': max_ts,
                'process_creation_count': proc_events,
                'failed_logon_count': failed_logons,
                'top_event_ids': top_ids,
            }

    def get_power_sessions(
        self,
        limit: int = 50,
        offset: int = 0,
        shutdown_type: Optional[str] = None,
        unexpected_only: bool = False,
        clean_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Извлечь список сессий питания операционной системы из SQLite.

        Args:
            limit: Максимальное количество записей.
            offset: Смещение выборки.
            shutdown_type: Фильтрация по типу выключения (Restart, Shutdown, Unexpected, etc.).
            unexpected_only: Только внезапные завершения работы.
            clean_only: Только штатные выключения.

        Returns:
            List[Dict[str, Any]]: Список словарей с полями PowerSessionRecord.
        """
        where_clauses: List[str] = []
        params: List[Any] = []

        if shutdown_type:
            where_clauses.append("LOWER(shutdown_type) = LOWER(?)")
            params.append(shutdown_type)

        if unexpected_only:
            where_clauses.append("unexpected_shutdown = 1")
        elif clean_only:
            where_clauses.append("clean_shutdown = 1 AND unexpected_shutdown = 0")

        sql = "SELECT * FROM power_sessions"
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        sql += " ORDER BY boot_time DESC LIMIT ? OFFSET ?"
        params.extend([max(1, limit), max(0, offset)])

        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            results: List[Dict[str, Any]] = []
            for row in rows:
                item = dict(row)
                if item.get('initiator_chain_json'):
                    try:
                        item['initiator_chain'] = json.loads(item['initiator_chain_json'])
                    except Exception:
                        item['initiator_chain'] = []
                else:
                    item['initiator_chain'] = []

                if item.get('events_json'):
                    try:
                        item['events'] = json.loads(item['events_json'])
                    except Exception:
                        item['events'] = []
                else:
                    item['events'] = []

                item['clean_shutdown'] = bool(item.get('clean_shutdown'))
                item['unexpected_shutdown'] = bool(item.get('unexpected_shutdown'))
                results.append(item)
            return results

    def get_power_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Извлечь детальную информацию по конкретной сессии питания.

        Args:
            session_id: Идентификатор сессии (session_id или id).

        Returns:
            Optional[Dict[str, Any]]: Словарь с полями сессии или None.
        """
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            if session_id.isdigit():
                cursor.execute("SELECT * FROM power_sessions WHERE id = ? OR session_id = ?", (int(session_id), session_id))
            else:
                cursor.execute("SELECT * FROM power_sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if not row:
                return None
            item = dict(row)
            if item.get('initiator_chain_json'):
                try:
                    item['initiator_chain'] = json.loads(item['initiator_chain_json'])
                except Exception:
                    item['initiator_chain'] = []
            else:
                item['initiator_chain'] = []

            if item.get('events_json'):
                try:
                    item['events'] = json.loads(item['events_json'])
                except Exception:
                    item['events'] = []
            else:
                item['events'] = []

            item['clean_shutdown'] = bool(item.get('clean_shutdown'))
            item['unexpected_shutdown'] = bool(item.get('unexpected_shutdown'))
            return item

    def get_power_events(
        self,
        limit: int = 100,
        offset: int = 0,
        event_id: Optional[Union[int, List[int]]] = None,
        event_type: Optional[str] = None,
        hours: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Извлечь события питания и жизненного цикла из таблицы power_events.

        Args:
            limit: Лимит записей.
            offset: Смещение.
            event_id: Фильтр по Event ID или списку ID.
            event_type: Фильтр по типу события (boot, shutdown, etc.).
            hours: Ограничение глубины в часах.

        Returns:
            List[Dict[str, Any]]: Список событий.
        """
        where_clauses: List[str] = []
        params: List[Any] = []

        if isinstance(event_id, list) and event_id:
            placeholders = ', '.join(['?'] * len(event_id))
            where_clauses.append(f"event_id IN ({placeholders})")
            params.extend(event_id)
        elif isinstance(event_id, int) and event_id > 0:
            where_clauses.append("event_id = ?")
            params.append(event_id)

        if event_type:
            where_clauses.append("LOWER(event_type) = LOWER(?)")
            params.append(event_type)

        if hours and hours > 0:
            cutoff = time.time() - (hours * 3600)
            where_clauses.append("created_at >= ?")
            params.append(cutoff)

        sql = "SELECT * FROM power_events"
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        sql += " ORDER BY timestamp DESC, id DESC LIMIT ? OFFSET ?"
        params.extend([max(1, limit), max(0, offset)])

        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            results: List[Dict[str, Any]] = []
            for row in rows:
                item = dict(row)
                if item.get('details_json'):
                    try:
                        item['details'] = json.loads(item['details_json'])
                    except Exception:
                        item['details'] = {}
                else:
                    item['details'] = {}
                item['unexpected'] = bool(item.get('unexpected'))
                results.append(item)
            return results

    def get_power_summary(self) -> Dict[str, Any]:
        """Получить сводную статистику по сессиям и событиям питания из SQLite.

        Returns:
            Dict[str, Any]: Сводная статистика (аптайм, число сессий, сбои, последнее выключение).
        """
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM power_sessions")
            total_sessions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM power_sessions WHERE clean_shutdown = 1 AND unexpected_shutdown = 0")
            clean_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM power_sessions WHERE unexpected_shutdown = 1")
            unexpected_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM power_events WHERE event_id = 1001 OR bugcheck_code IS NOT NULL")
            bsod_count = cursor.fetchone()[0]

            cursor.execute("SELECT * FROM power_sessions WHERE shutdown_time IS NOT NULL ORDER BY boot_time DESC LIMIT 1")
            last_shutdown_row = cursor.fetchone()

            last_shutdown_type = last_shutdown_row['shutdown_type'] if last_shutdown_row else None
            last_initiator = last_shutdown_row['initiator'] if last_shutdown_row else None
            last_reason = last_shutdown_row['reason'] if last_shutdown_row else None

            # Текущая активная сессия
            cursor.execute("SELECT * FROM power_sessions WHERE shutdown_time IS NULL ORDER BY boot_time DESC LIMIT 1")
            active_row = cursor.fetchone()

            cur_boot = active_row['boot_time'] if active_row else ''
            cur_uptime_sec = active_row['uptime_seconds'] if active_row else 0.0
            cur_uptime_human = active_row['uptime_human'] if active_row else ''

            return {
                'total_sessions_count': total_sessions,
                'clean_shutdowns_count': clean_count,
                'unexpected_shutdowns_count': unexpected_count,
                'bsod_count': bsod_count,
                'current_boot_time': cur_boot,
                'current_uptime_seconds': cur_uptime_sec,
                'current_uptime_human': cur_uptime_human,
                'last_shutdown_type': last_shutdown_type,
                'last_initiator': last_initiator,
                'last_reason': last_reason,
            }

    def get_process_pid_snapshot(self, pid: int) -> Optional[Dict[str, Any]]:
        """Извлекает последний канонический снимок метрик процесса по PID (< 5 мс)."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM process_pid_snapshots WHERE pid = ? ORDER BY snapshot_id DESC LIMIT 1',
                (pid,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_process_file_events(
        self,
        pid: Optional[int] = None,
        directory: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Извлекает события файловой активности с фильтрацией по PID и/или директории."""
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params: List[Any] = []
            if pid is not None:
                conditions.append('pid = ?')
                params.append(pid)
            if directory:
                conditions.append('target_directory LIKE ?')
                params.append(f'%{directory}%')

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ''
            query = f"SELECT * FROM process_file_events {where_clause} ORDER BY event_id DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]

    def get_telemetry_time_ranges(self) -> Dict[str, Any]:
        """Определяет временные границы данных в таблице system_snapshots и формирует список доступных интервалов.

        Returns:
            Dict[str, Any]: Метаданные диапазона времени и доступные интервалы (секунды, минуты, часы, дни, недели, месяцы, все).
        """
        import time
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT MIN(created_at) as min_ts, MAX(created_at) as max_ts, COUNT(*) as cnt '
                'FROM system_snapshots;'
            )
            row = cursor.fetchone()

            min_ts = row['min_ts'] if row and row['min_ts'] is not None else None
            max_ts = row['max_ts'] if row and row['max_ts'] is not None else None
            total_cnt = int(row['cnt']) if row and row['cnt'] is not None else 0

            now = time.time()
            span_seconds = 0.0
            if min_ts is not None and max_ts is not None:
                span_seconds = max(0.0, float(max_ts - min_ts), float(now - min_ts))

            # Полное определение временных интервалов
            intervals_definition = [
                {'id': 'seconds', 'label': 'Секунды', 'seconds': 120, 'min_span': 0},
                {'id': 'minutes', 'label': 'Минуты', 'seconds': 3600, 'min_span': 60},
                {'id': 'hours', 'label': 'Часы', 'seconds': 86400, 'min_span': 3600},
                {'id': 'days', 'label': 'Дни', 'seconds': 86400 * 7, 'min_span': 86400},
                {'id': 'weeks', 'label': 'Недели', 'seconds': 86400 * 30, 'min_span': 86400 * 7},
                {'id': 'months', 'label': 'Месяцы', 'seconds': 86400 * 365, 'min_span': 86400 * 30},
                {'id': 'all', 'label': 'Все', 'seconds': None, 'min_span': 0},
            ]

            available_intervals = []
            for item in intervals_definition:
                is_avail = (span_seconds >= item['min_span']) if item['min_span'] > 0 else True
                if item['id'] == 'all':
                    is_avail = True

                if is_avail:
                    available_intervals.append({
                        'id': item['id'],
                        'label': item['label'],
                        'seconds': item['seconds'],
                        'is_available': True,
                    })

            return {
                'status': 'ok',
                'min_created_at': min_ts,
                'max_created_at': max_ts,
                'span_seconds': round(span_seconds, 1),
                'total_snapshots': total_cnt,
                'intervals': available_intervals,
                'available_ids': [i['id'] for i in available_intervals],
            }

    def get_history_by_interval(
        self,
        interval: str = 'seconds',
        metric: str = 'all',
        limit: int = 120
    ) -> List[Dict[str, Any]]:
        """Выбирает исторические точки системных снимков под указанный интервал с downsampling.

        Args:
            interval: Временной интервал ('seconds', 'minutes', 'hours', 'days', 'weeks', 'months', 'all').
            metric: Категория метрики ('all', 'cpu', 'gpu', 'ram', 'net', 'storage').
            limit: Максимальное количество возвращаемых точек.

        Returns:
            List[Dict[str, Any]]: Хронологический список точек телеметрии от старых к новым.
        """
        import time
        with self._cm.lock, self._cm.get_connection() as conn:
            cursor = conn.cursor()
            now = time.time()
            interval_lower = (interval or 'seconds').lower().strip()

            since_ts = None
            if interval_lower == 'seconds':
                since_ts = now - 120
            elif interval_lower == 'minutes':
                since_ts = now - 3600
            elif interval_lower == 'hours':
                since_ts = now - 86400
            elif interval_lower == 'days':
                since_ts = now - (86400 * 7)
            elif interval_lower == 'weeks':
                since_ts = now - (86400 * 30)
            elif interval_lower == 'months':
                since_ts = now - (86400 * 365)
            elif interval_lower == 'all':
                since_ts = None

            if since_ts is not None:
                cursor.execute(
                    'SELECT id, timestamp, created_at, cpu_total_percent, cpu_frequency_mhz, '
                    'memory_total_gb, memory_used_gb, memory_percent, swap_percent, '
                    'gpu_load_percent, gpu_temp_c, disk_read_bytes_sec, disk_write_bytes_sec, '
                    'network_sent_bytes_sec, network_recv_bytes_sec '
                    'FROM system_snapshots WHERE created_at >= ? ORDER BY id ASC;',
                    (since_ts,)
                )
            else:
                cursor.execute(
                    'SELECT id, timestamp, created_at, cpu_total_percent, cpu_frequency_mhz, '
                    'memory_total_gb, memory_used_gb, memory_percent, swap_percent, '
                    'gpu_load_percent, gpu_temp_c, disk_read_bytes_sec, disk_write_bytes_sec, '
                    'network_sent_bytes_sec, network_recv_bytes_sec '
                    'FROM system_snapshots ORDER BY id ASC;'
                )

            rows = [dict(r) for r in cursor.fetchall()]

            if not rows:
                cursor.execute(
                    'SELECT id, timestamp, created_at, cpu_total_percent, cpu_frequency_mhz, '
                    'memory_total_gb, memory_used_gb, memory_percent, swap_percent, '
                    'gpu_load_percent, gpu_temp_c, disk_read_bytes_sec, disk_write_bytes_sec, '
                    'network_sent_bytes_sec, network_recv_bytes_sec '
                    'FROM system_snapshots ORDER BY id DESC LIMIT ?;',
                    (limit,)
                )
                rows = [dict(r) for r in cursor.fetchall()]
                rows.reverse()

            if len(rows) > limit:
                step = len(rows) / float(limit)
                downsampled = [rows[int(i * step)] for i in range(limit)]
                if rows[-1] not in downsampled:
                    downsampled[-1] = rows[-1]
                rows = downsampled

            return rows






