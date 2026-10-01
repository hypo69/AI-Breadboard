# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Main
# =============================================================================
# Description:
#   Главная точка входа для сервиса сбора телеметрии Windows.
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.telemetry.main
#   Python API:
#     from apps.windows.telemetry.main import parse_arguments
#
#     res = parse_arguments()
#
# File: main.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Главная точка входа для сервиса сбора телеметрии Windows."""

import argparse
import os
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
_project_root = str(Path(__file__).resolve().parents[3])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if __package__ in (None, ''):
    __package__ = 'apps.windows.telemetry'
if sys.stdout is None or sys.stderr is None:
    _early_log_dir = Path(os.environ.get('APPDATA', os.path.expanduser('~\\AppData\\Roaming'))) / 'AI-Breadboard' / 'apps' / 'windows' / 'telemetry' / 'logs'
    _early_log_dir.mkdir(parents=True, exist_ok=True)
    _stdout_file = _early_log_dir / 'telemetry_stdout.log'
    try:
        _stream = open(_stdout_file, 'a', encoding='utf-8', buffering=1)
        if sys.stdout is None:
            sys.stdout = _stream
        if sys.stderr is None:
            sys.stderr = _stream
    except Exception:
        pass
try:
    from logger import logger
except ImportError:
    from logger import logger
_stop_event = threading.Event()

def parse_arguments() -> argparse.Namespace:
    """Парсит аргументы командной строки.

    Returns:
        argparse.Namespace: Распарсенные аргументы.
    """
    parser = argparse.ArgumentParser(description='Windows Telemetry Service (Minimal, Hybrid, Full)', formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--mode', choices=['minimal', 'hybrid', 'full'], default=None, help='Режим работы: minimal (легковесный), hybrid (минимал + тяжелые периодически), full (полный стек)')
    parser.add_argument('--minimal', action='store_true', help='Запустить в легковесном режиме (эквивалентно --mode minimal)')
    parser.add_argument('--interval', type=float, default=None, help='Интервал сбора быстрой телеметрии в секундах (по умолчанию из config.json)')
    parser.add_argument('--heavy-interval', type=float, default=None, help='Интервал сбора тяжелых сенсоров для hybrid режима в секундах (по умолчанию из config.json)')
    parser.add_argument('--top-processes', type=int, default=None, help='Количество сохраняемых процессов с наибольшей нагрузкой (по умолчанию 10)')
    parser.add_argument('--config', type=str, default=None, help='Путь к файлу конфигурации config.json')
    parser.add_argument('--log-dir', type=str, default=None, help='Путь к директории для логов и SQLite БД телеметрии')
    parser.add_argument('--verbose', '-v', action='store_true', help='Включить подробный вывод (DEBUG)')
    return parser.parse_args()

def signal_handler(signum: int, frame: Optional[object]) -> None:
    """Обработчик сигналов для корректной остановки сервиса.

    Args:
        signum: Номер сигнала.
        frame: Стек вызовов.
    """
    logger.info(f'Получен сигнал {signum}, остановка телеметрии...')
    _stop_event.set()

def _set_low_priority() -> None:
    """Устанавливает пониженный приоритет процессу для экономии ресурсов CPU."""
    try:
        import psutil
        p = psutil.Process()
        p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        logger.debug('Установлен приоритет процесса: BELOW_NORMAL')
    except Exception as ex:
        logger.debug(f'Не удалось понизить приоритет процесса: {ex}')

def run_telemetry_service(mode: str='hybrid', interval: float=5.0, heavy_interval: float=60.0, top_processes: int=10, heavy_collectors: Optional[Dict[str, bool]]=None, log_dir: Optional[str]=None, config_path: Optional[str]=None) -> int:
    """Запускает универсальный цикл сбора телеметрии (Minimal, Hybrid или Full).

    Args:
        mode: Режим сбора ('minimal', 'hybrid', 'full').
        interval: Быстрый интервал сбора базовых метрик в секундах.
        heavy_interval: Периодический интервал сбора тяжелых сенсоров (для hybrid).
        top_processes: Количество процессов в топе.
        heavy_collectors: Словарь активных тяжелых сенсоров.
        log_dir: Каталог сохранения БД и логов.
        config_path: Путь к файлу конфигурации.

    Returns:
        int: Код завершения.
    """
    import psutil
    from apps.windows.modules.hardware.gpu_prober import GpuProber
    from .models import CpuMetrics, DiskIoMetrics, DiskPartitionMetrics, GpuMetrics, MemoryMetrics, NetworkInterfaceMetrics, ProcessMetrics, SystemSnapshot
    from .sqlite import TelemetryStorage
    _set_low_priority()
    resolved_log_dir = log_dir or os.path.join(os.environ.get('APPDATA', os.path.expanduser('~\\AppData\\Roaming')), 'AI-Breadboard', 'apps', 'windows', 'telemetry', 'logs')
    os.makedirs(resolved_log_dir, exist_ok=True)
    out_log_path = Path(resolved_log_dir) / 'telemetry_stdout.log'
    if sys.stdout is None:
        try:
            sys.stdout = open(out_log_path, 'a', encoding='utf-8', buffering=1)
        except Exception:
            pass
    if sys.stderr is None:
        try:
            sys.stderr = sys.stdout if sys.stdout else open(out_log_path, 'a', encoding='utf-8', buffering=1)
        except Exception:
            pass
    try:
        import logging
        log_file = Path(resolved_log_dir) / 'telemetry_service.log'
        file_handler = logging.FileHandler(str(log_file), encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s'))
        logging.getLogger().addHandler(file_handler)
    except Exception:
        pass
    db_path = os.path.join(resolved_log_dir, 'telemetry.db')
    storage = TelemetryStorage(db_path=db_path)
    gpu_prober = GpuProber()
    hostname = os.environ.get('COMPUTERNAME', 'localhost')
    boot_time = psutil.boot_time()
    psutil.cpu_percent(interval=None)
    from .telemetry_config import TelemetryConfigManager
    cfg_mgr = TelemetryConfigManager(config_path=config_path)
    heavy_disk_interval_sec = cfg_mgr.get_heavy_disk_scan_interval()
    max_heavy_duration_sec = cfg_mgr.get_heavy_mode_max_duration_days() * 24.0 * 3600.0
    auto_switch_enabled = cfg_mgr.is_heavy_auto_switch_enabled()

    h_collectors = heavy_collectors or cfg_mgr.get_heavy_collectors()
    sensor_collector = None
    if mode in ('hybrid', 'full') and h_collectors.get('hardware_sensors', True):
        try:
            from .sensor_collector import SensorCollector
            sensor_collector = SensorCollector(config_manager=cfg_mgr)
            logger.info('SensorCollector (LHM/Hardware) инициализирован для тяжелых опросов')
        except Exception as sc_err:
            logger.debug(f'SensorCollector не доступен: {sc_err}')
    system_collector = None
    deep_diag = None
    try:
        from .collector import SystemCollector
        from apps.windows.telemetry_research.deep_diagnostics import DeepDiagnosticsEngine
        system_collector = SystemCollector(storage=storage)
        deep_diag = DeepDiagnosticsEngine()
        identity = system_collector.get_system_identity()
        disks_health = system_collector.get_physical_disks_health(force=True)
        import asyncio
        hw_tree = asyncio.run(system_collector.get_hardware_tree_async(force=True))
        logger.info(f"💻 Хост: {identity.get('hostname')} | Пользователь: {identity.get('username')} | ОС: Windows {identity.get('os_build')}")
        logger.info(f"🌐 Язык: {identity.get('system_language')} | Локаль: {identity.get('user_locale')} | Раскладки: {', '.join(identity.get('input_languages', []))}")
        if disks_health:
            d_summary = ", ".join([f"{d.model} ({d.media_type}, {d.size_gb}GB, SMART:{d.health_status})" for d in disks_health])
            logger.info(f"💾 Накопители SMART (Опрос при запуске): {d_summary}")
        if hw_tree:
            logger.info(f"🖥️ [АППАРАТНАЯ КОНФИГУРАЦИЯ] Спецификация всего железа ПК определена при старте процесса ({len(hw_tree)} компонентов)")
    except Exception as init_err:
        logger.debug(f"Инициализация системного коллектора: {init_err}")

    # Проверка критических аудитов при запуске
    try:
        from apps.windows.telemetry_research.audit_startup_checker import run_startup_audit
        startup_audit = run_startup_audit(
            check_integrity=True,
            check_performance=True,
            check_drivers=False,
            check_eventlog=False
        )
        if not startup_audit.is_healthy:
            logger.error(
                f"🚨 STARTUP AUDIT: Обнаружены критические проблемы! "
                f"Critical: {startup_audit.critical_count}, Warnings: {startup_audit.warning_count}"
            )
            for finding in startup_audit.findings:
                logger.warning(f"  - [{finding['severity'].upper()}] {finding['domain']}: {finding['title']}")
        elif startup_audit.warning_count > 0:
            logger.warning(
                f"⚠️ STARTUP AUDIT: Предупреждения: {startup_audit.warning_count} "
                f"({startup_audit.duration_ms}ms)"
            )
        else:
            logger.info(f"✅ STARTUP AUDIT: Все проверки пройдены ({startup_audit.duration_ms}ms)")
    except Exception as audit_err:
        logger.debug(f"Проверка аудитов при запуске: {audit_err}")

    # Инициализация W64/ETW сборщиков системных событий
    w64_collector = None
    w64_etw_collector = None
    w64_cfg = cfg_mgr.get_config().get('w64_collector', {}) if cfg_mgr else {}
    if w64_cfg.get('enabled', True):
        try:
            from .w64_collector import AIW64Collector
            from .w64_etw_collector import AIW64ETWCollector
            w64_collector = AIW64Collector(
                storage=storage,
                enable_file_monitoring=w64_cfg.get('enable_file_monitoring', True),
                enable_process_monitoring=w64_cfg.get('enable_process_monitoring', True),
                enable_registry_monitoring=w64_cfg.get('enable_registry_monitoring', True),
                enable_network_monitoring=w64_cfg.get('enable_network_monitoring', True),
                enable_event_log_monitoring=w64_cfg.get('enable_event_log_monitoring', True),
            )
            w64_collector.start()
            w64_etw_collector = AIW64ETWCollector(
                storage=storage,
                enable_process_trace=w64_cfg.get('enable_process_trace', True),
                enable_disk_trace=w64_cfg.get('enable_disk_trace', True),
                enable_network_trace=w64_cfg.get('enable_network_trace', True),
                enable_registry_trace=w64_cfg.get('enable_registry_trace', True),
            )
            w64_etw_collector.start()
            logger.info('🛰️ Сборщики событий W64 и ETW запущены в составе телеметрии')
        except Exception as w64_err:
            logger.debug(f'Не удалось запустить W64 сборщики: {w64_err}')

    logger.info('=' * 60)
    logger.info(f'Запущен сервис телеметрии Windows [Режим: {mode.upper()}]')
    logger.info(f'Быстрый интервал: {interval} с | Топ процессов: {top_processes}')
    if mode == 'hybrid':
        logger.info(f'Периодический тяжелый опрос: каждые {heavy_interval} с')
    logger.info(f'База данных: {db_path}')
    logger.info('=' * 60)
    tick = 0
    prev_disk_io = psutil.disk_io_counters()
    prev_net_io = psutil.net_io_counters()
    prev_io_time = time.time()
    last_gpu_probe_time: Optional[float] = None
    cached_gpu_metrics: List[GpuMetrics] = []
    last_partition_check: float = 0.0
    cached_part_list: List[Any] = []
    last_heavy_time = time.time()
    last_heavy_disk_scan_time = time.time()
    heavy_mode_start_time: Optional[float] = time.time() if mode.lower() in ('full', 'heavy') else None
    db_cleanup_interval_sec = cfg_mgr.get_db_cleanup_interval_seconds()
    last_db_cleanup_time = time.time()
    known_pids: Dict[int, str] = {}
    flashing_log_path = Path(resolved_log_dir) / 'flashing_processes.log'

    try:
        while not _stop_event.is_set():
            loop_start = time.time()
            now_dt = datetime.now(timezone.utc)
            now_iso = now_dt.isoformat()
            tick += 1
            cpu_pct = psutil.cpu_percent(interval=None)
            cpu_freq = psutil.cpu_freq()
            freq_mhz = cpu_freq.current if cpu_freq else 0.0
            cpu_model = ''
            try:
                cpu_model = os.environ.get('PROCESSOR_IDENTIFIER', '')
            except Exception:
                pass
            cpu_metrics = CpuMetrics(load_percent=cpu_pct, load_user=0.0, load_system=0.0, frequency_mhz=freq_mhz, temperature_celsius=None, voltage_volts=None, model_name=cpu_model, cores_physical=psutil.cpu_count(logical=False) or 1, cores_logical=psutil.cpu_count(logical=True) or 1)
            mem = psutil.virtual_memory()
            mem_metrics = MemoryMetrics(total_gb=round(mem.total / (1024 ** 3), 2), used_gb=round(mem.used / (1024 ** 3), 2), available_gb=round(mem.available / (1024 ** 3), 2), percent=mem.percent)
            now_sec = time.time()
            if last_gpu_probe_time is None or now_sec - last_gpu_probe_time >= 10.0:
                try:
                    gpu_data = gpu_prober.probe()
                    cached_gpu_metrics = [GpuMetrics(name=g.name, load_percent=g.load_percent, memory_total_mb=g.memory_total_mb, memory_used_mb=g.memory_used_mb, temperature_celsius=g.temperature_celsius, power_watts=g.power_watts) for g in gpu_data]
                except Exception:
                    cached_gpu_metrics = []
                last_gpu_probe_time = now_sec
            gpu_metrics_list = cached_gpu_metrics
            io_elapsed = max(0.001, now_sec - prev_io_time)
            cur_disk_io = psutil.disk_io_counters()
            disk_read_kb = 0.0
            disk_write_kb = 0.0
            if cur_disk_io and prev_disk_io:
                disk_read_kb = round((cur_disk_io.read_bytes - prev_disk_io.read_bytes) / 1024.0 / io_elapsed, 1)
                disk_write_kb = round((cur_disk_io.write_bytes - prev_disk_io.write_bytes) / 1024.0 / io_elapsed, 1)
            prev_disk_io = cur_disk_io
            if not cached_part_list or now_sec - last_partition_check >= 60.0:
                try:
                    cached_part_list = psutil.disk_partitions(all=False)
                    last_partition_check = now_sec
                except Exception:
                    pass
            disk_partitions: List[DiskPartitionMetrics] = []
            for part in cached_part_list:
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disk_partitions.append(DiskPartitionMetrics(device=part.device, mountpoint=part.mountpoint, fstype=part.fstype, total_gb=round(usage.total / 1024 ** 3, 2), used_gb=round(usage.used / 1024 ** 3, 2), free_gb=round(usage.free / 1024 ** 3, 2), load_percent=usage.percent, io=DiskIoMetrics(read_kb_s=disk_read_kb, write_kb_s=disk_write_kb)))
                except (PermissionError, OSError):
                    continue
            cur_net_io = psutil.net_io_counters()
            net_recv_kb = 0.0
            net_sent_kb = 0.0
            if cur_net_io and prev_net_io:
                net_recv_kb = round((cur_net_io.bytes_recv - prev_net_io.bytes_recv) / 1024.0 / io_elapsed, 1)
                net_sent_kb = round((cur_net_io.bytes_sent - prev_net_io.bytes_sent) / 1024.0 / io_elapsed, 1)
            prev_net_io = cur_net_io
            prev_io_time = now_sec
            net_metrics_list = [NetworkInterfaceMetrics(interface_name='total', bytes_sent_sec=net_sent_kb * 1024.0, bytes_recv_sec=net_recv_kb * 1024.0, packets_sent_sec=0.0, packets_recv_sec=0.0, errors_in=cur_net_io.errin if cur_net_io else 0, errors_out=cur_net_io.errout if cur_net_io else 0)]
            raw_procs = []
            current_proc_map: Dict[int, Dict[str, Any]] = {}
            for p in psutil.process_iter(['pid', 'name', 'memory_info', 'username']):
                try:
                    info = p.info
                    pid = info.get('pid', 0)
                    name = info.get('name') or 'unknown'
                    if pid:
                        current_proc_map[pid] = {'name': name, 'proc': p, 'info': info}
                    mem_rss = (info.get('memory_info') or getattr(p, 'memory_info', lambda: None)()).rss if info.get('memory_info') else 0
                    raw_procs.append((mem_rss, p, info))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Детектор вспыхивающих процессов (новые PID, зарегистрированные на текущем тике)
            if tick > 1:
                new_pids = set(current_proc_map.keys()) - set(known_pids.keys())
                if new_pids:
                    for n_pid in new_pids:
                        p_entry = current_proc_map[n_pid]
                        p_obj = p_entry['proc']
                        p_name = p_entry['name']
                        exe_path = 'N/A'
                        cmdline_str = 'N/A'
                        parent_info = 'N/A'
                        try:
                            exe_path = p_obj.exe()
                        except Exception:
                            pass
                        try:
                            cmdline_str = " ".join(p_obj.cmdline())
                        except Exception:
                            pass
                        try:
                            ppid = p_obj.ppid()
                            parent_name = psutil.Process(ppid).name() if ppid else 'Unknown'
                            parent_info = f"{parent_name} (PID: {ppid})"
                        except Exception:
                            pass
                        
                        alert_msg = (
                            f"⚡ [ВСПЫШКА / НОВЫЙ ПРОЦЕСС] PID: {n_pid} | {p_name} | "
                            f"Путь: {exe_path} | Родитель: {parent_info} | Команда: {cmdline_str}"
                        )
                        logger.warning(alert_msg)
                        try:
                            with open(flashing_log_path, 'a', encoding='utf-8') as f_out:
                                f_out.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] PID: {n_pid} | {p_name} | Exe: {exe_path} | Parent: {parent_info} | Cmd: {cmdline_str}\n")
                        except Exception:
                            pass

            known_pids = {pid: data['name'] for pid, data in current_proc_map.items()}

            raw_procs.sort(key=lambda x: x[0], reverse=True)
            top_candidates = raw_procs[:top_processes]
            top_procs: List[ProcessMetrics] = []
            for mem_rss, p, info in top_candidates:
                proc_cpu = 0.0
                try:
                    proc_cpu = p.cpu_percent(interval=None)
                except Exception:
                    pass
                mem_mb = round(mem_rss / (1024 * 1024), 1)
                raw_user = info.get('username')
                clean_user = raw_user if isinstance(raw_user, str) else ''
                top_procs.append(ProcessMetrics(pid=info.get('pid', 0), name=info.get('name') or 'unknown', cpu_percent=proc_cpu, memory_mb=mem_mb, threads_count=1, status='running', username=clean_user))
            snapshot = SystemSnapshot(timestamp=now_iso, hostname=hostname, uptime_seconds=round(time.time() - boot_time, 1), cpu=cpu_metrics, memory=mem_metrics, gpus=gpu_metrics_list, disks=disk_partitions, network=net_metrics_list, top_processes=top_procs)
            try:
                storage.save_snapshot(snapshot, top_n=top_processes)
            except Exception as db_err:
                logger.warning(f'Ошибка сохранения снимка в SQLite: {db_err}')
            sensor_items = [{'id': 'cpu_util_total', 'hardware_name': 'CPU', 'hardware_type': 'cpu', 'sensor_category': 'Load', 'sensor_name': 'CPU Total', 'unit': '%', 'value': cpu_pct}, {'id': 'ram_util_pct', 'hardware_name': 'RAM', 'hardware_type': 'memory', 'sensor_category': 'Load', 'sensor_name': 'Memory Used', 'unit': '%', 'value': mem.percent}]
            if gpu_metrics_list:
                g0 = gpu_metrics_list[0]
                if g0.temperature_celsius is not None:
                    sensor_items.append({'id': 'gpu_0_temp', 'hardware_name': g0.name, 'hardware_type': 'gpu', 'sensor_category': 'Temperatures', 'sensor_name': 'GPU Core Temp', 'unit': '°C', 'value': g0.temperature_celsius})
                if g0.load_percent is not None:
                    sensor_items.append({'id': 'gpu_0_load', 'hardware_name': g0.name, 'hardware_type': 'gpu', 'sensor_category': 'Load', 'sensor_name': 'GPU Load', 'unit': '%', 'value': g0.load_percent})
            # Автоматическое переключение из тяжелого режима в легкий при непрерывной работе 5 дней (432 000с)
            if auto_switch_enabled and heavy_mode_start_time is not None and mode.lower() in ('full', 'heavy'):
                if now_sec - heavy_mode_start_time >= max_heavy_duration_sec:
                    days_run = round((now_sec - heavy_mode_start_time) / (24 * 3600), 1)
                    logger.warning(
                        f"⏳ [АВТО-ПЕРЕКЛЮЧЕНИЕ] Телеметрия непрерывно работала {days_run} дн. в тяжелом режиме ({mode.upper()}). "
                        f"Для оптимизации ресурсов режим автоматически переключен в легкий (LIGHT)."
                    )
                    mode = 'light'
                    heavy_mode_start_time = None

            is_heavy_due = mode.lower() in ('full', 'heavy') or (mode.lower() == 'hybrid' and now_sec - last_heavy_time >= heavy_interval)
            if is_heavy_due:
                heavy_start = time.time()
                try:
                    if sensor_collector and h_collectors.get('hardware_sensors', True):
                        heavy_readings = sensor_collector.collect_all_sensors()
                        if heavy_readings:
                            sensor_items.extend(heavy_readings)
                            try:
                                storage.save_sensor_polls(heavy_readings)
                            except Exception as sp_err:
                                logger.debug(f'Ошибка сохранения sensor_polls в БД: {sp_err}')

                            # Разгруппировка и красивый вывод 200+ LHM сенсоров в консоль
                            lhm_temps = [f"{s.get('sensor_name')}: {s.get('value')}{s.get('unit')}" for s in heavy_readings if s.get('sensor_category') in ('Temperatures', 'Temperature')]
                            lhm_powers = [f"{s.get('sensor_name')}: {s.get('value')}{s.get('unit')}" for s in heavy_readings if s.get('sensor_category') in ('Powers', 'Power')]
                            lhm_fans = [f"{s.get('sensor_name')}: {s.get('value')}{s.get('unit')}" for s in heavy_readings if s.get('sensor_category') in ('Fans', 'Fan')]
                            lhm_clocks = [f"{s.get('sensor_name')}: {s.get('value')}{s.get('unit')}" for s in heavy_readings if s.get('sensor_category') in ('Clocks', 'Clock')]

                            logger.info(f"🌡️ [LHM WEB API http://127.0.0.1:8085/data.json] Собрано {len(heavy_readings)} сенсоров:")
                            if lhm_temps:
                                logger.info(f"   ├─ Температуры ({len(lhm_temps)}): {', '.join(lhm_temps[:8])}")
                            if lhm_powers:
                                logger.info(f"   ├─ Энергопотребление ({len(lhm_powers)}): {', '.join(lhm_powers[:6])}")
                            if lhm_fans:
                                logger.info(f"   ├─ Вентиляторы ({len(lhm_fans)}): {', '.join(lhm_fans)}")
                            if lhm_clocks:
                                logger.info(f"   └─ Частоты ({len(lhm_clocks)}): {', '.join(lhm_clocks[:6])}")

                    # Детальный аудит портов, сетевых соединений и утечек дескрипторов
                    if system_collector:
                        try:
                            ports = system_collector.get_listening_ports(limit=10)
                            if ports:
                                p_str = ", ".join([f"{p.port}/{p.protocol} ({p.process_name or 'System'})" for p in ports[:5]])
                                logger.info(f"🌐 [ТЯЖЕЛЫЙ ОПРОС] Открытые слушающие порты ({len(ports)}): {p_str}")
                        except Exception:
                            pass
                        try:
                            net_conns = system_collector.get_process_network_activity(limit=5, only_internet=True)
                            if net_conns:
                                c_str = ", ".join([f"{c.name}->{c.remote_address} ({c.service_type})" for c in net_conns[:3]])
                                logger.info(f"📡 [ТЯЖЕЛЫЙ ОПРОС] Активные соединения с Интернет ({len(net_conns)}): {c_str}")
                        except Exception:
                            pass

                    if deep_diag:
                        try:
                            leaks = deep_diag.collect_process_leaks(limit=5)
                            if leaks and leaks.top_handle_hogs:
                                top_h = leaks.top_handle_hogs[0]
                                logger.info(f"🔍 [ТЯЖЕЛЫЙ ОПРОС] Топ процесса по дескрипторам: {top_h.name} (PID:{top_h.pid}) -> {top_h.handles_count} handles, {top_h.gdi_objects} GDI, {top_h.user_objects} USER")
                        except Exception:
                            pass

                    # Тяжелый опрос накопителей SMART и надежности (2 раза в день / каждые 12 часов)
                    if system_collector and h_collectors.get('storage_smart', True) and (now_sec - last_heavy_disk_scan_time >= heavy_disk_interval_sec):
                        try:
                            heavy_disks = system_collector.get_physical_disks_health(force=True)
                            if heavy_disks:
                                d_summary = ", ".join([f"{d.model} ({d.media_type}, {d.size_gb}GB, SMART:{d.health_status})" for d in heavy_disks])
                                logger.info(f"💾 [ТЯЖЕЛЫЙ ОПРОС (2 раза в день)] Накопители SMART: {d_summary}")
                            last_heavy_disk_scan_time = now_sec
                        except Exception as d_err:
                            logger.debug(f"Ошибка тяжелого сканирования накопителей: {d_err}")

                    heavy_dur = time.time() - heavy_start
                    logger.info(f'[{mode.upper()}] Периодический тяжелый опрос завершен за {heavy_dur:.2f}с (Всего сенсоров в срезе: {len(sensor_items)})')
                    last_heavy_time = now_sec
                except Exception as h_err:
                    logger.debug(f'Ошибка периодического тяжелого опроса: {h_err}')

            # Фоновый периодический контроль размера SQLite базы данных telemetry.db
            if now_sec - last_db_cleanup_time >= db_cleanup_interval_sec:
                try:
                    prune_res = storage.enforce_size_limit()
                    if prune_res.get('pruned'):
                        logger.warning(
                            f"🗄️ [КОНТРОЛЬ РАЗМЕРА БД] Усечение базы данных telemetry.db: "
                            f"{prune_res.get('initial_size_mb')} МБ -> {prune_res.get('final_size_mb')} МБ "
                            f"(удалено снимков: {prune_res.get('deleted_snapshots')})"
                        )
                    last_db_cleanup_time = now_sec
                except Exception as db_clean_err:
                    logger.debug(f"Ошибка периодического контроля размера БД: {db_clean_err}")

            active_win_str = ""
            if deep_diag:
                try:
                    forensics = deep_diag.collect_forensics_activity()
                    win_info = forensics.foreground_window
                    if win_info and win_info.get('title'):
                        active_win_str = f"Активное окно: \"{win_info.get('title')}\" ({win_info.get('process_name') or 'N/A'}, PID:{win_info.get('pid', 0)}) | Idle: {forensics.user_idle_seconds:.1f}с"
                except Exception:
                    pass

            elapsed = time.time() - loop_start
            sleep_time = max(0.05, interval - elapsed)

            used_mb = round(mem.used / (1024 * 1024), 0)
            total_mb = round(mem.total / (1024 * 1024), 0)

            logger.info(
                f"══════════════════════════════════════════════════════════════════════════════\n"
                f"📊 ТЕЛЕМЕТРИЯ #{tick} [{mode.upper()}] | {datetime.now().strftime('%H:%M:%S')}\n"
                f"   • CPU: {cpu_pct:.1f}% ({freq_mhz:.0f} МГц) | RAM: {mem.percent:.1f}% ({used_mb:.0f}/{total_mb:.0f} МБ)\n"
                f"   • Диск R/W: {disk_read_kb}/{disk_write_kb} КБ/с | Сеть R/S: {net_recv_kb}/{net_sent_kb} КБ/с"
            )
            if active_win_str:
                logger.info(f"   • 🪟 {active_win_str}")

            if gpu_metrics_list:
                for g in gpu_metrics_list:
                    mem_used = getattr(g, 'memory_used_mb', getattr(g, 'memory_used_gb', 0.0) * 1024.0)
                    mem_total = getattr(g, 'memory_total_mb', getattr(g, 'memory_total_gb', 0.0) * 1024.0)
                    vram_str = f"{mem_used:.0f}/{mem_total:.0f} МБ" if mem_total else "N/A"
                    temp_str = f"{g.temperature_celsius:.0f}°C" if g.temperature_celsius is not None else "N/A"
                    load_pct = getattr(g, 'load_percent', getattr(g, 'utilization_gpu_pct', 0.0)) or 0.0
                    logger.info(f"   • 🎮 GPU: {g.name} | Load: {load_pct:.1f}% | Temp: {temp_str} | VRAM: {vram_str}")

            if disk_partitions:
                p_str = ", ".join([f"{p.mountpoint} ({getattr(p, 'percent', getattr(p, 'load_percent', 0.0)):.1f}%, своб: {p.free_gb} ГБ)" for p in disk_partitions])
                logger.info(f"   • 💾 Диски: {p_str}")

            if top_procs:
                logger.info(f"   • 📋 Процессы (Топ-{len(top_procs)} по RAM & CPU):")
                for idx, p in enumerate(top_procs[:top_processes], 1):
                    try:
                        u_str = p.username if isinstance(p.username, str) and p.username else ""
                        user_info = f" ({u_str})" if u_str else ""
                        logger.info(f"      {idx:2d}. [PID {p.pid:6d}] {p.name:<24s} | RAM: {p.memory_mb:7.1f} МБ | CPU: {p.cpu_percent:5.1f}%{user_info}")
                    except Exception as p_err:
                        logger.debug(f"Ошибка вывода процесса #{idx}: {p_err}")

            logger.info("══════════════════════════════════════════════════════════════════════════════")

            elapsed = time.time() - loop_start
            sleep_time = max(0.05, interval - elapsed)
            if _stop_event.wait(timeout=sleep_time):
                logger.info('Получен сигнал остановки (_stop_event установлен)')
                break
    except KeyboardInterrupt:
        logger.info('Прервано пользователем (KeyboardInterrupt)')
    except Exception as ex:
        logger.error(f'Критическая ошибка в цикле телеметрии: {ex}', exc_info=True)
    finally:
        if w64_collector:
            try:
                w64_collector.stop()
            except Exception:
                pass
        if w64_etw_collector:
            try:
                w64_etw_collector.stop()
            except Exception:
                pass
        logger.info('Процесс телеметрии успешно завершен')
    return 0

def run_minimal_telemetry(interval: float=5.0, top_processes: int=10, log_dir: Optional[str]=None) -> int:
    """Обертка для обратной совместимости: запуск в режиме minimal."""
    return run_telemetry_service(mode='minimal', interval=interval, top_processes=top_processes, log_dir=log_dir)

def main() -> int:
    """Главная точка входа сервиса телеметрии.

    Returns:
        int: Код завершения.
    """
    args = parse_arguments()
    if args.verbose:
        logger.setLevel('DEBUG')
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    from .telemetry_config import TelemetryConfigManager
    try:
        config_manager = TelemetryConfigManager(config_path=args.config)
    except Exception as e:
        logger.warning(f'Не удалось загрузить конфигурацию ({e}), используются значения по умолчанию')
        config_manager = None
    if args.minimal:
        mode = 'minimal'
    elif args.mode:
        mode = args.mode
    elif config_manager:
        mode = config_manager.get_mode()
    else:
        mode = 'hybrid'
    interval = args.interval or (config_manager.get_interval_seconds() if config_manager else 5.0)
    heavy_interval = args.heavy_interval or (config_manager.get_heavy_interval_seconds() if config_manager else 60.0)
    top_processes = args.top_processes or (config_manager.get_top_processes() if config_manager else 10)
    heavy_collectors = config_manager.get_heavy_collectors() if config_manager else None
    return run_telemetry_service(mode=mode, interval=interval, heavy_interval=heavy_interval, top_processes=top_processes, heavy_collectors=heavy_collectors, log_dir=args.log_dir, config_path=args.config)
if __name__ == '__main__':
    sys.exit(main())