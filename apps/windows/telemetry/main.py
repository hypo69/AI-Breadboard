# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Telemetry Stream Aggregator Main Entry Point
# =============================================================================
# Description:
#   Главная входная точка CLI для запуска сервиса сбора системной телеметрии
#   в режимах:
#     - minimal (ультралегковесный: базовая телеметрия, 28 мс замер, 120 МБ RAM)
#     - hybrid  (минимал + периодический опрос тяжелых сенсоров раз в 60-300 с)
#     - full    (полный стек сенсоров на каждом тике)
#   Параметры читаются из config.json или передаются аргументами командной строки.
#
# File: main.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Главная точка входа для сервиса сбора телеметрии Windows."""

from __future__ import annotations

import argparse
import os
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Резолвинг корня проекта для абсолютных импортов
_project_root = str(Path(__file__).resolve().parents[3])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Безопасная инициализация stdout/stderr для фонового headless-режима (pythonw.exe / ai-telemetry.exe)
if sys.stdout is None or sys.stderr is None:
    _early_log_dir = Path(
        os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
    ) / "AI-Breadboard" / "apps" / "windows" / "telemetry" / "logs"
    _early_log_dir.mkdir(parents=True, exist_ok=True)
    _stdout_file = _early_log_dir / "telemetry_stdout.log"
    try:
        _stream = open(_stdout_file, "a", encoding="utf-8", buffering=1)
        if sys.stdout is None:
            sys.stdout = _stream
        if sys.stderr is None:
            sys.stderr = _stream
    except Exception:
        pass

try:
    from src.logger.logger import logger
except ImportError:
    from logger import logger

# Глобальный флаг остановки сервиса
_stop_event = threading.Event()


def parse_arguments() -> argparse.Namespace:
    """Парсит аргументы командной строки.

    Returns:
        argparse.Namespace: Распарсенные аргументы.
    """
    parser = argparse.ArgumentParser(
        description="Windows Telemetry Service (Minimal, Hybrid, Full)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["minimal", "hybrid", "full"],
        default=None,
        help="Режим работы: minimal (легковесный), hybrid (минимал + тяжелые периодически), full (полный стек)",
    )
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Запустить в легковесном режиме (эквивалентно --mode minimal)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=None,
        help="Интервал сбора быстрой телеметрии в секундах (по умолчанию из config.json)",
    )
    parser.add_argument(
        "--heavy-interval",
        type=float,
        default=None,
        help="Интервал сбора тяжелых сенсоров для hybrid режима в секундах (по умолчанию из config.json)",
    )
    parser.add_argument(
        "--top-processes",
        type=int,
        default=None,
        help="Количество сохраняемых процессов с наибольшей нагрузкой (по умолчанию 10)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Путь к файлу конфигурации config.json",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help="Путь к директории для логов и SQLite БД телеметрии",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Включить подробный вывод (DEBUG)",
    )
    return parser.parse_args()


def signal_handler(signum: int, frame: Optional[object]) -> None:
    """Обработчик сигналов для корректной остановки сервиса.

    Args:
        signum: Номер сигнала.
        frame: Стек вызовов.
    """
    logger.info(f"Получен сигнал {signum}, остановка телеметрии...")
    _stop_event.set()


def _set_low_priority() -> None:
    """Устанавливает пониженный приоритет процессу для экономии ресурсов CPU."""
    try:
        import psutil
        p = psutil.Process()
        p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        logger.debug("Установлен приоритет процесса: BELOW_NORMAL")
    except Exception as ex:
        logger.debug(f"Не удалось понизить приоритет процесса: {ex}")


def run_telemetry_service(
    mode: str = "hybrid",
    interval: float = 5.0,
    heavy_interval: float = 60.0,
    top_processes: int = 10,
    heavy_collectors: Optional[Dict[str, bool]] = None,
    log_dir: Optional[str] = None,
    config_path: Optional[str] = None,
) -> int:
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
    from apps.windows.hardware.gpu_prober import GpuProber
    from apps.windows.telemetry.models import (
        CpuMetrics,
        DiskIoMetrics,
        DiskPartitionMetrics,
        GpuMetrics,
        MemoryMetrics,
        NetworkInterfaceMetrics,
        ProcessMetrics,
        SystemSnapshot,
    )
    from apps.windows.telemetry.storage import TelemetryStorage

    _set_low_priority()

    resolved_log_dir = log_dir or os.path.join(
        os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming")),
        "AI-Breadboard",
        "apps",
        "windows",
        "telemetry",
        "logs",
    )
    os.makedirs(resolved_log_dir, exist_ok=True)

    # Безопасная инициализация stdout/stderr для фонового режима без консоли
    out_log_path = Path(resolved_log_dir) / "telemetry_stdout.log"
    if sys.stdout is None:
        try:
            sys.stdout = open(out_log_path, "a", encoding="utf-8", buffering=1)
        except Exception:
            pass
    if sys.stderr is None:
        try:
            sys.stderr = sys.stdout if sys.stdout else open(out_log_path, "a", encoding="utf-8", buffering=1)
        except Exception:
            pass

    # Запись логов в telemetry_service.log
    try:
        import logging
        log_file = Path(resolved_log_dir) / "telemetry_service.log"
        file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
        logging.getLogger().addHandler(file_handler)
    except Exception:
        pass

    db_path = os.path.join(resolved_log_dir, "telemetry.db")
    storage = TelemetryStorage(db_path=db_path)
    gpu_prober = GpuProber()

    hostname = os.environ.get("COMPUTERNAME", "localhost")
    boot_time = psutil.boot_time()

    # Первичный холостой замер CPU для инициализации psutil
    psutil.cpu_percent(interval=None)

    # Флаги тяжелых сенсоров
    h_collectors = heavy_collectors or {
        "hardware_sensors": True,
        "storage_smart": True,
        "network_ping": True,
        "inventory_wmi": False,
    }

    sensor_collector = None
    if mode in ("hybrid", "full") and h_collectors.get("hardware_sensors", True):
        try:
            from apps.windows.telemetry.sensor_collector import SensorCollector
            from apps.windows.telemetry.telemetry_config import TelemetryConfigManager
            cfg_mgr = TelemetryConfigManager(config_path=config_path)
            sensor_collector = SensorCollector(config_manager=cfg_mgr)
            logger.info("SensorCollector (LHM/Hardware) инициализирован для тяжелых опросов")
        except Exception as sc_err:
            logger.debug(f"SensorCollector не доступен: {sc_err}")

    logger.info("=" * 60)
    logger.info(f"Запущен сервис телеметрии Windows [Режим: {mode.upper()}]")
    logger.info(f"Быстрый интервал: {interval} с | Топ процессов: {top_processes}")
    if mode == "hybrid":
        logger.info(f"Периодический тяжелый опрос: каждые {heavy_interval} с")
    logger.info(f"База данных: {db_path}")
    logger.info("=" * 60)

    tick = 0
    prev_disk_io = psutil.disk_io_counters()
    prev_net_io = psutil.net_io_counters()
    prev_io_time = time.time()
    last_gpu_probe_time: Optional[float] = None
    cached_gpu_metrics: List[GpuMetrics] = []
    last_heavy_time = time.time()

    try:
        while not _stop_event.is_set():
            loop_start = time.time()
            now_dt = datetime.now(timezone.utc)
            now_iso = now_dt.isoformat()
            tick += 1

            # 1. CPU
            cpu_pct = psutil.cpu_percent(interval=None)
            cpu_freq = psutil.cpu_freq()
            freq_mhz = cpu_freq.current if cpu_freq else 0.0

            cpu_model = ""
            try:
                cpu_model = os.environ.get("PROCESSOR_IDENTIFIER", "")
            except Exception:
                pass

            cpu_metrics = CpuMetrics(
                load_percent=cpu_pct,
                load_user=0.0,
                load_system=0.0,
                frequency_mhz=freq_mhz,
                temperature_celsius=None,
                voltage_volts=None,
                model_name=cpu_model,
                cores_physical=psutil.cpu_count(logical=False) or 1,
                cores_logical=psutil.cpu_count(logical=True) or 1,
            )

            # 2. RAM
            mem = psutil.virtual_memory()
            mem_metrics = MemoryMetrics(
                total_mb=round(mem.total / (1024 * 1024), 1),
                used_mb=round(mem.used / (1024 * 1024), 1),
                free_mb=round(mem.available / (1024 * 1024), 1),
                load_percent=mem.percent,
            )

            # 3. GPU (с кэшированием на 10 сек)
            now_sec = time.time()
            if last_gpu_probe_time is None or (now_sec - last_gpu_probe_time) >= 10.0:
                try:
                    gpu_data = gpu_prober.probe()
                    cached_gpu_metrics = [
                        GpuMetrics(
                            name=g.name,
                            load_percent=g.load_percent,
                            memory_total_mb=g.memory_total_mb,
                            memory_used_mb=g.memory_used_mb,
                            temperature_celsius=g.temperature_celsius,
                            power_watts=g.power_watts,
                        )
                        for g in gpu_data
                    ]
                except Exception:
                    cached_gpu_metrics = []
                last_gpu_probe_time = now_sec

            gpu_metrics_list = cached_gpu_metrics

            # 4. Диски
            io_elapsed = max(0.001, now_sec - prev_io_time)
            cur_disk_io = psutil.disk_io_counters()
            disk_read_kb = 0.0
            disk_write_kb = 0.0
            if cur_disk_io and prev_disk_io:
                disk_read_kb = round((cur_disk_io.read_bytes - prev_disk_io.read_bytes) / 1024.0 / io_elapsed, 1)
                disk_write_kb = round((cur_disk_io.write_bytes - prev_disk_io.write_bytes) / 1024.0 / io_elapsed, 1)
            prev_disk_io = cur_disk_io

            disk_partitions: List[DiskPartitionMetrics] = []
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disk_partitions.append(
                        DiskPartitionMetrics(
                            device=part.device,
                            mountpoint=part.mountpoint,
                            fstype=part.fstype,
                            total_gb=round(usage.total / (1024**3), 2),
                            used_gb=round(usage.used / (1024**3), 2),
                            free_gb=round(usage.free / (1024**3), 2),
                            load_percent=usage.percent,
                            io=DiskIoMetrics(read_kb_s=disk_read_kb, write_kb_s=disk_write_kb),
                        )
                    )
                except (PermissionError, OSError):
                    continue

            # 5. Сеть
            cur_net_io = psutil.net_io_counters()
            net_recv_kb = 0.0
            net_sent_kb = 0.0
            if cur_net_io and prev_net_io:
                net_recv_kb = round((cur_net_io.bytes_recv - prev_net_io.bytes_recv) / 1024.0 / io_elapsed, 1)
                net_sent_kb = round((cur_net_io.bytes_sent - prev_net_io.bytes_sent) / 1024.0 / io_elapsed, 1)
            prev_net_io = cur_net_io
            prev_io_time = now_sec

            net_metrics_list = [
                NetworkInterfaceMetrics(
                    interface_name="total",
                    bytes_sent_sec=net_sent_kb * 1024.0,
                    bytes_recv_sec=net_recv_kb * 1024.0,
                    packets_sent_sec=0.0,
                    packets_recv_sec=0.0,
                    errors_in=cur_net_io.errin if cur_net_io else 0,
                    errors_out=cur_net_io.errout if cur_net_io else 0,
                )
            ]

            # 6. Процессы (быстрый сбор без опроса потоков ядра)
            raw_procs = []
            for p in psutil.process_iter(["pid", "name", "memory_info", "username"]):
                try:
                    info = p.info
                    mem_rss = (info.get("memory_info") or getattr(p, "memory_info", lambda: None)()).rss if info.get("memory_info") else 0
                    raw_procs.append((mem_rss, p, info))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

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
                top_procs.append(
                    ProcessMetrics(
                        pid=info.get("pid", 0),
                        name=info.get("name") or "unknown",
                        cpu_percent=proc_cpu,
                        memory_mb=mem_mb,
                        threads_count=1,
                        status="running",
                        username=info.get("username") or "",
                    )
                )

            # 7. Формирование SystemSnapshot и запись в SQLite
            snapshot = SystemSnapshot(
                timestamp=now_iso,
                hostname=hostname,
                uptime_seconds=round(time.time() - boot_time, 1),
                cpu=cpu_metrics,
                memory=mem_metrics,
                gpus=gpu_metrics_list,
                disks=disk_partitions,
                network=net_metrics_list,
                top_processes=top_procs,  # исправлено: было processes (несуществующее поле)
            )

            try:
                storage.save_snapshot(snapshot, top_n=top_processes)
            except Exception as db_err:
                logger.warning(f"Ошибка сохранения снимка в SQLite: {db_err}")

            # 8. Запись компактных сенсоров в БД
            sensor_items = [
                {"id": "cpu_util_total", "hardware_name": "CPU", "hardware_type": "cpu", "sensor_category": "Load", "sensor_name": "CPU Total", "unit": "%", "value": cpu_pct},
                {"id": "ram_util_pct", "hardware_name": "RAM", "hardware_type": "memory", "sensor_category": "Load", "sensor_name": "Memory Used", "unit": "%", "value": mem.percent},
            ]
            if gpu_metrics_list:
                g0 = gpu_metrics_list[0]
                if g0.temperature_celsius is not None:
                    sensor_items.append({"id": "gpu_0_temp", "hardware_name": g0.name, "hardware_type": "gpu", "sensor_category": "Temperatures", "sensor_name": "GPU Core Temp", "unit": "°C", "value": g0.temperature_celsius})
                if g0.load_percent is not None:
                    sensor_items.append({"id": "gpu_0_load", "hardware_name": g0.name, "hardware_type": "gpu", "sensor_category": "Load", "sensor_name": "GPU Load", "unit": "%", "value": g0.load_percent})

            try:
                storage.save_sensor_polls_batch(sensor_items, timestamp=now_iso)
            except Exception as sp_err:
                logger.debug(f"Ошибка сохранения sensor_polls в БД: {sp_err}")

            # 9. ПЕРИОДИЧЕСКИЙ ТЯЖЕЛЫЙ ОПРОС (Hybrid / Full)
            is_heavy_due = (mode == "full") or (mode == "hybrid" and (now_sec - last_heavy_time >= heavy_interval))
            if is_heavy_due:
                heavy_start = time.time()
                try:
                    if sensor_collector and h_collectors.get("hardware_sensors", True):
                        heavy_readings = sensor_collector.collect_all_sensors()
                        if heavy_readings:
                            sensor_items.extend(heavy_readings)
                            try:
                                storage.save_sensor_polls(heavy_readings)
                            except Exception as sp_err:
                                logger.debug(f"Ошибка сохранения sensor_polls в БД: {sp_err}")

                    heavy_dur = time.time() - heavy_start
                    logger.debug(f"[{mode.upper()}] Периодический тяжелый опрос завершен за {heavy_dur:.2f}с")
                    last_heavy_time = now_sec
                except Exception as h_err:
                    logger.debug(f"Ошибка периодического тяжелого опроса: {h_err}")

            # Периодический лог каждые 12 тиков
            if tick % 12 == 1:
                cur_proc = psutil.Process()
                ram_mb = round(cur_proc.memory_info().rss / (1024 * 1024), 1)
                logger.info(
                    f"Телеметрия #{tick} [{mode}]: CPU {cpu_pct}% | RAM {mem.percent}% | "
                    f"Процесс телеметрии занимает {ram_mb} МБ RAM"
                )

            elapsed = time.time() - loop_start
            sleep_time = max(0.05, interval - elapsed)
            logger.debug(f"Тик #{tick} завершен за {elapsed:.3f}с, сон {sleep_time:.3f}с")
            if _stop_event.wait(timeout=sleep_time):
                logger.info("Получен сигнал остановки (_stop_event установлен)")
                break

    except KeyboardInterrupt:
        logger.info("Прервано пользователем (KeyboardInterrupt)")
    except Exception as ex:
        logger.error(f"Критическая ошибка в цикле телеметрии: {ex}", exc_info=True)
    finally:
        logger.info("Процесс телеметрии успешно завершен")

    return 0


def run_minimal_telemetry(
    interval: float = 5.0,
    top_processes: int = 10,
    log_dir: Optional[str] = None,
) -> int:
    """Обертка для обратной совместимости: запуск в режиме minimal."""
    return run_telemetry_service(
        mode="minimal",
        interval=interval,
        top_processes=top_processes,
        log_dir=log_dir,
    )


def main() -> int:
    """Главная точка входа сервиса телеметрии.

    Returns:
        int: Код завершения.
    """
    args = parse_arguments()

    if args.verbose:
        logger.setLevel("DEBUG")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    from apps.windows.telemetry.telemetry_config import TelemetryConfigManager

    try:
        config_manager = TelemetryConfigManager(config_path=args.config)
    except Exception as e:
        logger.warning(f"Не удалось загрузить конфигурацию ({e}), используются значения по умолчанию")
        config_manager = None

    # Определение режима: CLI аргументы переопределяют конфиг
    if args.minimal:
        mode = "minimal"
    elif args.mode:
        mode = args.mode
    elif config_manager:
        mode = config_manager.get_mode()
    else:
        mode = "hybrid"

    # Определение интервалов
    interval = args.interval or (config_manager.get_interval_seconds() if config_manager else 5.0)
    heavy_interval = args.heavy_interval or (config_manager.get_heavy_interval_seconds() if config_manager else 60.0)
    top_processes = args.top_processes or (config_manager.get_top_processes() if config_manager else 10)
    heavy_collectors = config_manager.get_heavy_collectors() if config_manager else None

    return run_telemetry_service(
        mode=mode,
        interval=interval,
        heavy_interval=heavy_interval,
        top_processes=top_processes,
        heavy_collectors=heavy_collectors,
        log_dir=args.log_dir,
        config_path=args.config,
    )


if __name__ == "__main__":
    sys.exit(main())
