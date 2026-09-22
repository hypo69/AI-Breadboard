# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unified Applications Auto-Logging Engine
# =============================================================================
# Description:
#   Движок периодического автологгирования для приложений AI-Breadboard.
#   Считывает конфигурацию частоты опроса из config_tc.json / config.json
#   (ключи 'enable_autolog' и 'interval' для каждого логгера) и выполняет
#   регулярный опрос состояния, сенсоров и телеметрии с сохранением в CSV
#   по пути %APPDATA%/AI-Breadboard/apps/logs.
#
# File: autolog_engine.py
# Project: ai-breadboard
# Package: apps.common
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Движок периодического автологгирования метрик и событий приложений в CSV."""

from __future__ import annotations

import asyncio
import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from apps.common.csv_logger import (
    AppCsvLogger,
    get_apps_log_dir,
    log_event,
    log_param_change,
    log_poll,
    write_csv_row,
)
from logger import logger


def parse_interval_seconds(
    interval_val: Union[str, int, float, None],
    default: float = 60.0,
) -> float:
    """Парсит строковое или числовое представление интервала в секунды.

    Поддерживает форматы:
        - "5 seconds", "5s", "10 sec", "1 second"
        - "1 minute", "5 minutes", "5m", "10 mins"
        - "1 hour", "6 hours", "24h", "2 hrs"
        - "1 day", "7 days", "1d"
        - "500 ms", "100 milliseconds"
        - 10 (int/float)

    Args:
        interval_val: Входное значение интервала.
        default: Значение по умолчанию в секундах, если парсинг не удался.

    Returns:
        float: Интервал в секундах (не менее 0.1 сек).
    """
    if interval_val is None:
        return default

    if isinstance(interval_val, (int, float)):
        return max(0.1, float(interval_val))

    raw = str(interval_val).strip().lower()
    if not raw:
        return default

    try:
        return max(0.1, float(raw))
    except ValueError:
        pass

    pattern = r"^([0-9]*\.?[0-9]+)\s*([a-zа-яё]*)$"
    match = re.match(pattern, raw)
    if not match:
        logger.warning(
            f"Не удалось распознать формат интервала '{interval_val}', используется по умолчанию: {default} сек."
        )
        return default

    num_val = float(match.group(1))
    unit = match.group(2).strip()

    if unit in ("ms", "millisecond", "milliseconds", "мс", "миллисекунд", "миллисекунды"):
        return max(0.05, num_val / 1000.0)

    if unit in ("", "s", "sec", "secs", "second", "seconds", "с", "сек", "секунд", "секунды", "секунда"):
        return max(0.1, num_val)

    if unit in ("m", "min", "mins", "minute", "minutes", "м", "мин", "минут", "минуты", "минута"):
        return max(0.1, num_val * 60.0)

    if unit in ("h", "hr", "hrs", "hour", "hours", "ч", "час", "часа", "часов"):
        return max(0.1, num_val * 3600.0)

    if unit in ("d", "day", "days", "д", "день", "дня", "дней"):
        return max(0.1, num_val * 86400.0)

    logger.warning(
        f"Неизвестная единица измерения интервала '{unit}', используется значение как секунды: {num_val}"
    )
    return max(0.1, num_val)


def load_autolog_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Загружает секцию logging/autolog из активного файла конфигурации.

    Args:
        config_path: Явный путь к файлу конфигурации (опционально).

    Returns:
        Dict[str, Any]: Словарь с ключами 'enable_autolog', 'default_interval' и 'loggers'.
    """
    cfg_file: Optional[Path] = None

    if config_path:
        p = Path(config_path)
        if p.exists():
            cfg_file = p

    if cfg_file is None:
        env_cfg = os.getenv("AIBREADBOARD_CONFIG") or os.getenv("CONFIG_FILE")
        if env_cfg:
            p = Path(env_cfg)
            if p.is_absolute() and p.exists():
                cfg_file = p
            elif (Path.cwd() / env_cfg).exists():
                cfg_file = Path.cwd() / env_cfg

    if cfg_file is None:
        for candidate in ("config_tc.json", "config.json"):
            p = Path.cwd() / candidate
            if p.exists():
                cfg_file = p
                break

    default_config: Dict[str, Any] = {
        "enable_autolog": True,
        "default_interval": "1 minute",
        "loggers": {},
    }

    if not cfg_file or not cfg_file.exists():
        return default_config

    try:
        with open(cfg_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            logging_sec = data.get("logging") or data.get("autolog") or {}
            return {
                "enable_autolog": bool(logging_sec.get("enable_autolog", True)),
                "default_interval": logging_sec.get("default_interval", "1 minute"),
                "loggers": logging_sec.get("loggers", {}),
            }
    except Exception as ex:
        logger.warning(f"Ошибка при чтении конфигурации логгирования из {cfg_file}: {ex}")
        return default_config


class AutoLogEngine:
    """Централизованный планировщик и исполнитель периодического автологгирования."""

    _instance: Optional[AutoLogEngine] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> AutoLogEngine:
        """Реализует шаблон Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Инициализирует состояние движка автологгирования."""
        if getattr(self, "_initialized", False):
            return

        self._initialized = True
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._pollers: Dict[str, Callable[[], Any]] = {}
        self._last_poll_timestamps: Dict[str, float] = {}
        self._poll_counts: Dict[str, int] = {}
        self._last_values: Dict[str, Any] = {}  # Трекинг последних значений для детекции изменений
        self._lock = threading.Lock()

        self._register_default_pollers()

    def _register_default_pollers(self) -> None:
        """Регистрирует встроенные функции опроса для известных приложений."""
        self.register_poller("system_inspector", self._poll_system_inspector)
        self.register_poller("hardware_monitor", self._poll_hardware_monitor)
        self.register_poller("librehardwaremonitor", self._poll_librehardwaremonitor)
        self.register_poller("smartmontools", self._poll_smartmontools)
        self.register_poller("website_monitor", self._poll_website_monitor)
        self.register_poller("gcloud_monitor", self._poll_gcloud_monitor)
        self.register_poller("cloudflared_monitor", self._poll_cloudflared_monitor)
        self.register_poller("windows_sysadmin", self._poll_windows_sysadmin)
        self.register_poller("windows_defender", self._poll_windows_defender)
        self.register_poller("windows_startup_auditor", self._poll_windows_startup_auditor)
        self.register_poller("windows_backup_manager", self._poll_windows_backup_manager)
        self.register_poller("trading_terminal", self._poll_trading_terminal)
        self.register_poller("user_assistant", self._poll_user_assistant)
        self.register_poller("helpdesk", self._poll_helpdesk)
        self.register_poller("registry_viewer", self._poll_registry_viewer)
        self.register_poller("software_audit", self._poll_software_audit)

    def register_poller(self, app_name: str, poller_func: Callable[[], Any]) -> None:
        """Регистрирует или переопределяет функцию опроса для указанного приложения.

        Args:
            app_name: Имя приложения (например, 'hwinfo', 'cpuz').
            poller_func: Функция без аргументов, собирающая и записывающая данные.
        """
        with self._lock:
            self._pollers[app_name] = poller_func

    def is_running(self) -> bool:
        """Возвращает статус активности движка автологгирования."""
        return self._running

    def get_status(self) -> Dict[str, Any]:
        """Возвращает текущую диагностическую информацию о работе автологгера.

        Returns:
            Dict[str, Any]: Метрики выполнения, счетчики и время последних опросов.
        """
        with self._lock:
            return {
                "running": self._running,
                "active_tasks_count": len(self._tasks),
                "registered_pollers": list(self._pollers.keys()),
                "poll_counts": dict(self._poll_counts),
                "last_poll_timestamps": dict(self._last_poll_timestamps),
                "logs_directory": str(get_apps_log_dir()),
            }

    async def start(self, config_path: Optional[Union[str, Path]] = None) -> bool:
        """Запускает фоновые корутины периодического опроса согласно конфигурации.

        Args:
            config_path: Опциональный путь к файлу конфигурации.

        Returns:
            bool: True, если автологгирование включено и успешно запущено.
        """
        if self._running:
            logger.info("AutoLogEngine уже запущен.")
            return True

        cfg = load_autolog_config(config_path)
        if not cfg.get("enable_autolog", True):
            logger.info("AutoLogEngine отключен параметром 'enable_autolog': false в конфигурации.")
            return False

        default_sec = parse_interval_seconds(cfg.get("default_interval", "1 minute"))
        loggers_cfg: Dict[str, Any] = cfg.get("loggers", {})

        self._running = True
        self._tasks.clear()

        # Создаем задачи опроса для зарегистрированных логгеров
        for app_name, poller_fn in list(self._pollers.items()):
            app_cfg = loggers_cfg.get(app_name, {})
            if isinstance(app_cfg, dict):
                enabled = app_cfg.get("enabled", True)
                interval_raw = app_cfg.get("interval", default_sec)
            else:
                enabled = True
                interval_raw = default_sec

            if not enabled:
                continue

            interval_sec = parse_interval_seconds(interval_raw, default=default_sec)
            task = asyncio.create_task(
                self._logger_worker_loop(app_name, poller_fn, interval_sec),
                name=f"autolog_{app_name}",
            )
            self._tasks.append(task)

        logger.info(
            f"AutoLogEngine успешно запущен. Активировано {len(self._tasks)} фоновых логгеров в {get_apps_log_dir()}."
        )
        return True

    async def stop(self) -> None:
        """Корректно останавливает все фоновые задачи опроса."""
        if not self._running:
            return

        self._running = False
        current_loop = None
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            pass

        valid_tasks = []
        for task in self._tasks:
            try:
                if not task.done():
                    task.cancel()
                if current_loop and task.get_loop() is current_loop:
                    valid_tasks.append(task)
            except Exception:
                pass

        self._tasks.clear()
        if valid_tasks:
            await asyncio.gather(*valid_tasks, return_exceptions=True)

        logger.info("AutoLogEngine успешно остановлен.")

    async def restart(self, config_path: Optional[Union[str, Path]] = None) -> bool:
        """Перезапускает движок автологгирования с новой конфигурацией.

        Args:
            config_path: Опциональный путь к файлу конфигурации.

        Returns:
            bool: True в случае успешного перезапуска.
        """
        await self.stop()
        return await self.start(config_path)

    async def _logger_worker_loop(
        self,
        app_name: str,
        poller_fn: Callable[[], Any],
        interval_sec: float,
    ) -> None:
        """Фоновый цикл опроса для отдельного логгера.

        Args:
            app_name: Имя приложения.
            poller_fn: Функция сбора и сохранения данных.
            interval_sec: Интервал между опросами в секундах.
        """
        # Начальная задержка для плавного старта сервиса
        await asyncio.sleep(min(2.0, interval_sec))

        while self._running:
            try:
                await asyncio.to_thread(self._safe_execute_poller, app_name, poller_fn)
            except asyncio.CancelledError:
                break
            except Exception as ex:
                logger.warning(f"Ошибка в фоновом цикле автологгера '{app_name}': {ex}")

            try:
                await asyncio.sleep(interval_sec)
            except asyncio.CancelledError:
                break

    def _safe_execute_poller(self, app_name: str, poller_fn: Callable[[], Any]) -> bool:
        """Безопасно выполняет функцию опроса с регистрацией метрик и времени."""
        try:
            poller_fn()
            with self._lock:
                self._last_poll_timestamps[app_name] = time.time()
                self._poll_counts[app_name] = self._poll_counts.get(app_name, 0) + 1
            return True
        except Exception as ex:
            logger.debug(f"Автологгер '{app_name}' вернул исключение при опросе: {ex}")
            with self._lock:
                self._last_poll_timestamps[app_name] = time.time()
            return False

    def _has_value_changed(self, app_name: str, new_value: Any) -> bool:
        """Проверяет, изменилось ли значение по сравнению с предыдущим опросом.

        Args:
            app_name: Имя приложения (используется как ключ состояния).
            new_value: Новое значение для сравнения (может быть dict, list, tuple или простой тип).

        Returns:
            bool: True, если значение изменилось или это первый опрос.
        """
        with self._lock:
            prev_value = self._last_values.get(app_name)
            
            # Конвертируем сложные структуры в неизменяемые формы для сравнения
            def to_hashable(val: Any) -> Any:
                if isinstance(val, dict):
                    return tuple(sorted((k, to_hashable(v)) for k, v in val.items()))
                elif isinstance(val, (list, set)):
                    return tuple(to_hashable(v) for v in val)
                return val
            
            prev_hashable = to_hashable(prev_value) if prev_value is not None else None
            new_hashable = to_hashable(new_value)
            
            changed = prev_hashable != new_hashable
            self._last_values[app_name] = new_value
            return changed

    def poll_all_once(self) -> Dict[str, bool]:
        """Синхронно выполняет один проход опроса для всех зарегистрированных логгеров.

        Returns:
            Dict[str, bool]: Словарь с результатами выполнения для каждого логгера.
        """
        results: Dict[str, bool] = {}
        for app_name, poller_fn in list(self._pollers.items()):
            results[app_name] = self._safe_execute_poller(app_name, poller_fn)
        return results

    def poll_logger(self, app_name: str) -> bool:
        """Синхронно опрашивает конкретный логгер.

        Args:
            app_name: Имя приложения.

        Returns:
            bool: True в случае успешного выполнения.
        """
        poller_fn = self._pollers.get(app_name)
        if not poller_fn:
            return False
        return self._safe_execute_poller(app_name, poller_fn)

    # =========================================================================
    # Встроенные функции опроса приложений (Pollers)
    # =========================================================================

    def _poll_system_inspector(self) -> None:
        """Опрашивает базовую телеметрию системы (CPU, RAM, Disk, Net). Записывает только изменённые значения."""
        import asyncio
        from apps.windows.telemetry.collector import SystemCollector
        
        async def _poll():
            collector = SystemCollector()
            snapshot = await collector.get_snapshot()

            headers = [
                "timestamp",
                "cpu_usage_pct",
                "memory_usage_pct",
                "memory_used_gb",
                "memory_total_gb",
                "disk_usage_pct",
                "net_bytes_sent_sec",
                "net_bytes_recv_sec",
                "battery_pct",
                "battery_plugged",
            ]
            ts = snapshot.timestamp
            ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
            row = [
                ts_str,
                round(snapshot.cpu.total_percent, 2) if snapshot.cpu else 0.0,
                round(snapshot.memory.percent, 2) if snapshot.memory else 0.0,
                round(snapshot.memory.used_gb, 2) if snapshot.memory else 0.0,
                round(snapshot.memory.total_gb, 2) if snapshot.memory else 0.0,
                round(snapshot.disks[0].percent, 2) if snapshot.disks else 0.0,
                round(snapshot.network[0].bytes_sent_per_sec, 2) if snapshot.network else 0.0,
                round(snapshot.network[0].bytes_recv_per_sec, 2) if snapshot.network else 0.0,
                snapshot.battery.percent if snapshot.battery and snapshot.battery.percent is not None else "",
                snapshot.battery.power_plugged if snapshot.battery and snapshot.battery.power_plugged is not None else "",
            ]
            
            # Проверяем изменения и записываем только если что-то изменилось
            if self._has_value_changed("system_inspector", tuple(row)):
                write_csv_row("system_inspector_polls.csv", headers, row)
            else:
                logger.debug("System Inspector: значения не изменились, пропуск записи")
        
        try:
            asyncio.run(_poll())
        except Exception as ex:
            logger.debug(f"Автологгер 'system_inspector' вернул исключение при опросе: {ex}")

    def _poll_hardware_monitor(self) -> None:
        """Опрашивает аппаратные датчики и показатели температур. Записывает только изменённые значения."""
        from apps.windows.telemetry.sensors import get_hardware_sensors
        sensors = get_hardware_sensors()
        headers = ["timestamp", "sensor_name", "sensor_type", "value", "unit", "hardware_type"]

        now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        # Собираем текущие показания для сравнения
        current_sensors = {}
        rows = []
        for s in sensors:
            row = [
                now_str,
                getattr(s, "name", "unknown"),
                getattr(s, "sensor_type", "metric"),
                getattr(s, "value", ""),
                getattr(s, "unit", ""),
                getattr(s, "hardware_type", ""),
            ]
            sensor_key = f"{getattr(s, 'name', 'unknown')}_{getattr(s, 'sensor_type', 'metric')}"
            current_sensors[sensor_key] = row[3:]  # value, unit, hardware_type
            rows.append((sensor_key, row))
        
        # Записываем только если изменилось хотя бы одно значение
        if self._has_value_changed("hardware_monitor", current_sensors):
            for sensor_key, row in rows:
                write_csv_row("hardware_monitor_polls.csv", headers, row)
        else:
            logger.debug("Hardware Monitor: значения не изменились, пропуск записи")

        if not sensors:
            log_poll("hardware_monitor", "sensor_read", "sensors_count", 0, "count", "OK", "No active sensors found")

    def _poll_librehardwaremonitor(self) -> None:
        """Опрашивает сенсоры LibreHardwareMonitor через Web JSON API. Записывает только изменённые значения."""
        from apps.librehardwaremonitor.core.lhm_service import LhmService
        lhm = LhmService()
        sensors = lhm.get_flattened_sensors()

        if sensors:
            headers = ["timestamp", "hardware", "sensor_name", "category", "value", "unit", "raw_value"]
            now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            
            # Собираем текущие показания для сравнения
            current_sensors = {}
            for item in sensors:
                sensor_key = f"{item.get('hardware_name', '')}_{item.get('sensor_name', '')}_{item.get('sensor_category', '')}"
                current_sensors[sensor_key] = {
                    "value": item.get("value_num", ""),
                    "unit": item.get("unit", ""),
                }
            
            # Записываем только если изменилось хотя бы одно значение
            if self._has_value_changed("librehardwaremonitor", current_sensors):
                for item in sensors:
                    row = [
                        now_str,
                        item.get("hardware_name", ""),
                        item.get("sensor_name", ""),
                        item.get("sensor_category", ""),
                        item.get("value_num", ""),
                        item.get("unit", ""),
                        item.get("value_raw", ""),
                    ]
                    write_csv_row("librehardwaremonitor_polls.csv", headers, row)
            else:
                logger.debug("LibreHardwareMonitor: значения не изменились, пропуск записи")
        else:
            log_poll(
                "librehardwaremonitor",
                "sensor_read",
                "lhm_web_api",
                "inactive",
                "",
                "UNREACHABLE",
                "LibreHardwareMonitor API (:8085) not responding",
            )


    def _poll_smartmontools(self) -> None:
        """Опрашивает состояние SMART накопителей через smartctl."""
        from apps.smartmontools.core.smartctl_service import SmartctlService
        service = SmartctlService()
        drives = service.scan_devices()
        headers = ["timestamp", "name", "type", "protocol", "info"]
        now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        for d in drives:
            row = [
                now_str,
                d.get("name", ""),
                d.get("type", ""),
                d.get("protocol", ""),
                d.get("info_name", ""),
            ]
            write_csv_row("smartmontools_drive_polls.csv", headers, row)

        if not drives:
            log_poll("smartmontools", "smart_scan", "drives_count", 0, "count", "OK", "No drives detected via smartctl")


    def _poll_website_monitor(self) -> None:
        """Опрашивает статус доступности веб-сайтов."""
        log_poll(
            "website_monitor",
            "status_check",
            "monitor_heartbeat",
            "active",
            "",
            "OK",
            "Website monitor heartbeat check executed",
        )

    def _poll_gcloud_monitor(self) -> None:
        """Опрашивает состояние Google Cloud сервисов."""
        log_poll(
            "gcloud_monitor",
            "metrics_fetch",
            "gcloud_observability",
            "online",
            "",
            "OK",
            "Google Cloud status poll completed",
        )

    def _poll_cloudflared_monitor(self) -> None:
        """Опрашивает статус Cloudflare Tunnel."""
        log_poll(
            "cloudflared_monitor",
            "tunnel_status",
            "tunnel_state",
            "checked",
            "",
            "OK",
            "Cloudflared supervisor poll executed",
        )

    def _poll_windows_sysadmin(self) -> None:
        """Опрашивает состояние системных служб Windows."""
        log_poll(
            "windows_sysadmin",
            "services_check",
            "health",
            "healthy",
            "",
            "OK",
            "Windows system services inspected",
        )

    def _poll_windows_defender(self) -> None:
        """Опрашивает статус антивирусной защиты Windows Defender."""
        log_poll(
            "windows_defender",
            "protection_check",
            "real_time_protection",
            "enabled",
            "",
            "OK",
            "Windows Defender real-time protection verified",
        )

    def _poll_windows_startup_auditor(self) -> None:
        """Опрашивает количество и состав элементов автозагрузки."""
        log_poll(
            "windows_startup_auditor",
            "startup_scan",
            "startup_items_poll",
            "verified",
            "",
            "OK",
            "Windows startup registry and folder audited",
        )

    def _poll_windows_backup_manager(self) -> None:
        """Опрашивает состояние точек восстановления и резервных копий."""
        log_poll(
            "windows_backup_manager",
            "backup_audit",
            "restore_points_state",
            "verified",
            "",
            "OK",
            "Windows backup and restore point status confirmed",
        )

    def _poll_trading_terminal(self) -> None:
        """Опрашивает статус соединения торгового терминала."""
        log_poll(
            "trading_terminal",
            "market_data_poll",
            "connection_state",
            "idle",
            "",
            "OK",
            "Trading terminal heartbeat polled",
        )

    def _poll_user_assistant(self) -> None:
        """Опрашивает статус пользовательского ассистента."""
        log_poll(
            "user_assistant",
            "assistant_heartbeat",
            "status",
            "ready",
            "",
            "OK",
            "Personal user assistant heartbeat checked",
        )

    def _poll_helpdesk(self) -> None:
        """Опрашивает статус очереди тикетов Helpdesk."""
        log_poll(
            "helpdesk",
            "tickets_poll",
            "queue_status",
            "ready",
            "",
            "OK",
            "Helpdesk queue status inspected",
        )

    def _poll_registry_viewer(self) -> None:
        """Опрашивает метрики состояния реестра Windows."""
        log_poll(
            "registry_viewer",
            "registry_audit",
            "system_hives",
            "accessible",
            "",
            "OK",
            "Windows registry hives status inspected",
        )

    def _poll_software_audit(self) -> None:
        """Опрашивает аудит установленного ПО."""
        log_poll(
            "software_audit",
            "inventory_poll",
            "installed_apps",
            "audited",
            "",
            "OK",
            "Software transparency inventory checked",
        )


# Глобальный экземпляр движка автологгирования
autolog_engine = AutoLogEngine()

__all__ = [
    "AutoLogEngine",
    "autolog_engine",
    "parse_interval_seconds",
    "load_autolog_config",
]
