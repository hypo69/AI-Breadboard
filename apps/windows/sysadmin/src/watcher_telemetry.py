# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Real-time File Watcher Telemetry & Hardware Sensors Engine
# =============================================================================
# Description:
#   Движок телеметрии дляИзменения файлов в реальном времени (ReadDirectoryChangesW)
#   с поддержкой множественных отслеживаемых папок и накопителей:
#   - Программные сенсоры: темп файловых операций (events/sec, created/sec, deleted/sec),
#     детекторы всплесков удалений (Ransomware heuristic), сопоставление с Event ID 4660/4663.
#   - Аппаратные дисковые сенсоры: определение накопителей всех отслеживаемых папок,
#     замер скорости чтения/записи (KB/s), температуры накопителей через LHM/S.M.A.R.T.
#   - CSV-логгирование телеметрии в %APPDATA%/AI-Breadboard/apps/logs.
#
# File: watcher_telemetry.py
# Project: ai-breadboard
# Package: apps.windows.sysadmin.src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль программных и аппаратных сенсоров телеметрии для Real-time Directory Watcher."""

from __future__ import annotations

import os
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import psutil

from logger import logger
from apps.common.csv_logger import write_csv_row
from apps.windows.hardware.lhm_service import LhmService


@dataclass
class WatcherTelemetrySnapshot:
    """Снимок программных и аппаратных сенсоров файлового наблюдателя."""

    timestamp: str
    watch_dirs: List[str] = field(default_factory=list)
    watch_dir: str = ""
    drive_letters: List[str] = field(default_factory=list)
    drive_letter: str = ""
    drive_model: str = "Physical Storage"
    drives_info: List[Dict[str, Any]] = field(default_factory=list)
    # Программные метрики темпа
    total_events_count: int = 0
    events_rate_per_sec: float = 0.0
    created_rate_per_sec: float = 0.0
    modified_rate_per_sec: float = 0.0
    deleted_rate_per_sec: float = 0.0
    renamed_rate_per_sec: float = 0.0
    # Детекторы аномалий
    burst_deletions_alert: bool = False
    high_activity_alert: bool = False
    status_label: str = "🟢 Штатный режим мониторинга"
    # Аппаратные сенсоры диска
    disk_read_kbs: float = 0.0
    disk_write_kbs: float = 0.0
    disk_read_iops: float = 0.0
    disk_write_iops: float = 0.0
    drive_temperature_c: Optional[float] = None
    # Безопасность и сопоставление
    security_audit_matched_count: int = 0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать снапшот в словарь."""
        return asdict(self)


class FileWatcherTelemetryEngine:
    """Движок сбора телеметрии, расчета темпа файловых операций и аппаратных сенсоров диска."""

    def __init__(self, window_seconds: float = 5.0) -> None:
        """Инициализация движка телеметрии.

        Args:
            window_seconds (float): Скользящее временное окно для расчета темпа (по умолчанию 5 сек).
        """
        self.window_seconds = window_seconds
        self._event_timestamps: deque[Tuple[float, str, str]] = deque()
        self._lock = threading.Lock()
        self._lhm_service = LhmService()

        # Для расчета дельт дискового ввода-вывода
        self._last_disk_sample_time: float = time.time()
        self._last_disk_read_bytes: int = 0
        self._last_disk_write_bytes: int = 0
        self._last_disk_read_count: int = 0
        self._last_disk_write_count: int = 0
        self._init_disk_counters()

    def _init_disk_counters(self) -> None:
        """Инициализировать начальные счетчики дискового I/O."""
        try:
            counters = psutil.disk_io_counters()
            if counters:
                self._last_disk_read_bytes = counters.read_bytes
                self._last_disk_write_bytes = counters.write_bytes
                self._last_disk_read_count = counters.read_count
                self._last_disk_write_count = counters.write_count
                self._last_disk_sample_time = time.time()
        except Exception as e:
            logger.debug(f"Не удалось получить начальные дисковые счетчики: {e}")

    def record_event(self, action: str, watch_dir: str = "") -> None:
        """Зафиксировать событие файловой системы в телеметрии.

        Args:
            action (str): Тип действия ('Created', 'Modified', 'Deleted', 'Renamed').
            watch_dir (str): Каталог, в котором произошло событие.
        """
        now = time.time()
        with self._lock:
            self._event_timestamps.append((now, action.lower(), watch_dir))
            # Очистка устаревших меток времени старше окна 60 сек
            cutoff = now - 60.0
            while self._event_timestamps and self._event_timestamps[0][0] < cutoff:
                self._event_timestamps.popleft()

    def compute_rates(self) -> Dict[str, float]:
        """Вычислить текущую скорость файловых операций (в секунду) за скользящее окно.

        Returns:
            Dict[str, float]: Словарь скоростей: total, created, modified, deleted, renamed.
        """
        now = time.time()
        cutoff = now - self.window_seconds
        window_duration = max(1.0, self.window_seconds)

        with self._lock:
            recent = [item for item in self._event_timestamps if item[0] >= cutoff]

        total = len(recent)
        created = sum(1 for _, a, _ in recent if "create" in a or "add" in a)
        modified = sum(1 for _, a, _ in recent if "mod" in a)
        deleted = sum(1 for _, a, _ in recent if "del" in a or "remov" in a)
        renamed = sum(1 for _, a, _ in recent if "renam" in a)

        return {
            "total_rate": round(total / window_duration, 2),
            "created_rate": round(created / window_duration, 2),
            "modified_rate": round(modified / window_duration, 2),
            "deleted_rate": round(deleted / window_duration, 2),
            "renamed_rate": round(renamed / window_duration, 2),
            "window_events_count": total,
        }

    def get_drive_hardware_metrics(
        self, watch_dirs: Union[str, List[str]]
    ) -> Dict[str, Any]:
        """Собрать показатели накопителей, на которых расположены отслеживаемые папки.

        Args:
            watch_dirs: Путь или список путей к отслеживаемым каталогам.

        Returns:
            Dict[str, Any]: Показатели чтения/записи, температуры и моделей дисков.
        """
        if isinstance(watch_dirs, str):
            dirs_list = [watch_dirs] if watch_dirs else ["C:\\"]
        else:
            dirs_list = watch_dirs if watch_dirs else ["C:\\"]

        now = time.time()
        time_delta = max(0.1, now - self._last_disk_sample_time)

        # Собираем уникальные буквы дисков
        drive_letters_set = set()
        for d in dirs_list:
            try:
                drv = os.path.splitdrive(os.path.abspath(d))[0].upper()
                if drv:
                    drive_letters_set.add(drv)
            except Exception:
                pass

        if not drive_letters_set:
            drive_letters_set.add("C:")

        drive_letters = sorted(list(drive_letters_set))
        primary_drive_letter = ", ".join(drive_letters)

        read_kbs = 0.0
        write_kbs = 0.0
        read_iops = 0.0
        write_iops = 0.0

        try:
            counters = psutil.disk_io_counters()
            if counters:
                r_bytes_delta = max(0, counters.read_bytes - self._last_disk_read_bytes)
                w_bytes_delta = max(0, counters.write_bytes - self._last_disk_write_bytes)
                r_count_delta = max(0, counters.read_count - self._last_disk_read_count)
                w_count_delta = max(0, counters.write_count - self._last_disk_write_count)

                read_kbs = round((r_bytes_delta / 1024.0) / time_delta, 2)
                write_kbs = round((w_bytes_delta / 1024.0) / time_delta, 2)
                read_iops = round(r_count_delta / time_delta, 2)
                write_iops = round(w_count_delta / time_delta, 2)

                self._last_disk_read_bytes = counters.read_bytes
                self._last_disk_write_bytes = counters.write_bytes
                self._last_disk_read_count = counters.read_count
                self._last_disk_write_count = counters.write_count
                self._last_disk_sample_time = now
        except Exception as e:
            logger.debug(f"Ошибка сбора дисковых счетчиков: {e}")

        # Поиск температур и моделей накопителей в LHM
        drive_temp: Optional[float] = None
        drive_models_list: List[str] = []
        drives_info: List[Dict[str, Any]] = []

        try:
            sensors = self._lhm_service.get_flattened_sensors()
            for s in sensors:
                hw = (s.get("hardware_name") or "").strip()
                cat = (s.get("sensor_category") or "").lower()
                hw_type = (s.get("hardware_type") or "").lower()
                num = s.get("value_numeric")

                if (
                    "storage" in hw_type
                    or "ssd" in hw.lower()
                    or "hdd" in hw.lower()
                    or "nvme" in hw.lower()
                    or "wdc" in hw.lower()
                    or "toshiba" in hw.lower()
                    or "st3500" in hw.lower()
                ):
                    if hw and hw not in drive_models_list:
                        drive_models_list.append(hw)
                    if "temp" in cat and num is not None:
                        val = round(float(num), 1)
                        if drive_temp is None or val > drive_temp:
                            drive_temp = val

            for d_letter in drive_letters:
                drives_info.append(
                    {
                        "drive_letter": d_letter,
                        "model": ", ".join(drive_models_list) if drive_models_list else "Physical Storage",
                        "temperature_c": drive_temp,
                    }
                )
        except Exception as ex:
            logger.debug(f"Ошибка получения температуры накопителя LHM: {ex}")

        drive_model = ", ".join(drive_models_list) if drive_models_list else "Physical Storage"

        return {
            "drive_letter": primary_drive_letter,
            "drive_letters": drive_letters,
            "drive_model": drive_model,
            "drives_info": drives_info,
            "read_kbs": read_kbs,
            "write_kbs": write_kbs,
            "read_iops": read_iops,
            "write_iops": write_iops,
            "temperature_c": drive_temp,
        }

    def correlate_security_events(self) -> int:
        """Сопоставляет активность с недавними событиями Windows Security Audit 4660/4663.

        Returns:
            int: Количество зафиксированных аудиторских событий безопасности.
        """
        try:
            from apps.windows.sysadmin.src.event_collector import WindowsEventCollector

            collector = WindowsEventCollector()
            events = collector.get_security_events(limit=10)
            return len([e for e in events if e.get("event_id") in (4660, 4663)])
        except Exception:
            return 0

    def get_telemetry_snapshot(
        self,
        watch_dirs: Union[str, List[str]],
        total_history_events: int = 0,
    ) -> WatcherTelemetrySnapshot:
        """Сформировать полный снимок телеметрии и сенсоров файлового вотчера.

        Args:
            watch_dirs: Отслеживаемая директория или список директорий.
            total_history_events: Общее число зарегистрированных событий в буфере.

        Returns:
            WatcherTelemetrySnapshot: Заполненный объект снимка телеметрии.
        """
        if isinstance(watch_dirs, str):
            dirs_list = [watch_dirs] if watch_dirs else []
        else:
            dirs_list = list(watch_dirs) if watch_dirs else []

        rates = self.compute_rates()
        hw = self.get_drive_hardware_metrics(dirs_list)
        sec_matches = self.correlate_security_events()

        # Детекция аномалий
        burst_deletions = rates["deleted_rate"] >= 10.0 or (
            rates["deleted_rate"] >= 5.0 and rates["total_rate"] >= 25.0
        )
        high_activity = rates["total_rate"] >= 50.0

        if burst_deletions:
            status_label = "🚨 Аномальный всплеск удалений (Mass Deletions Alert)"
        elif high_activity:
            status_label = "⚡ Высокая интенсивность файлового I/O"
        else:
            status_label = "🟢 Штатный режим мониторинга"

        iso_now = datetime.now(timezone.utc).isoformat()
        primary_watch_dir = dirs_list[0] if dirs_list else ""

        snap = WatcherTelemetrySnapshot(
            timestamp=iso_now,
            watch_dirs=dirs_list,
            watch_dir=primary_watch_dir,
            drive_letters=hw.get("drive_letters", []),
            drive_letter=hw.get("drive_letter", "C:"),
            drive_model=hw.get("drive_model", "Physical Storage"),
            drives_info=hw.get("drives_info", []),
            total_events_count=total_history_events or rates["window_events_count"],
            events_rate_per_sec=rates["total_rate"],
            created_rate_per_sec=rates["created_rate"],
            modified_rate_per_sec=rates["modified_rate"],
            deleted_rate_per_sec=rates["deleted_rate"],
            renamed_rate_per_sec=rates["renamed_rate"],
            burst_deletions_alert=burst_deletions,
            high_activity_alert=high_activity,
            status_label=status_label,
            disk_read_kbs=hw["read_kbs"],
            disk_write_kbs=hw["write_kbs"],
            disk_read_iops=hw["read_iops"],
            disk_write_iops=hw["write_iops"],
            drive_temperature_c=hw["temperature_c"],
            security_audit_matched_count=sec_matches,
            details={
                "watch_dirs_count": len(dirs_list),
                "window_seconds": self.window_seconds,
                "window_events_count": rates["window_events_count"],
            },
        )

        # Логгирование в CSV
        self.log_snapshot_to_csv(snap)

        return snap

    def log_snapshot_to_csv(self, snap: WatcherTelemetrySnapshot) -> None:
        """Записать показатели снимка телеметрии в CSV-файл.

        Args:
            snap (WatcherTelemetrySnapshot): Снимок телеметрии для записи.
        """
        headers = [
            "timestamp",
            "watch_dirs",
            "drive_letter",
            "drive_model",
            "events_rate_per_sec",
            "created_rate_per_sec",
            "modified_rate_per_sec",
            "deleted_rate_per_sec",
            "burst_alert",
            "disk_read_kbs",
            "disk_write_kbs",
            "drive_temp_c",
            "sec_audit_matches",
            "status",
        ]
        dirs_str = ";".join(snap.watch_dirs) if snap.watch_dirs else snap.watch_dir
        row = [
            snap.timestamp,
            dirs_str,
            snap.drive_letter,
            snap.drive_model,
            snap.events_rate_per_sec,
            snap.created_rate_per_sec,
            snap.modified_rate_per_sec,
            snap.deleted_rate_per_sec,
            "ALERT" if snap.burst_deletions_alert else "OK",
            snap.disk_read_kbs,
            snap.disk_write_kbs,
            snap.drive_temperature_c if snap.drive_temperature_c is not None else "",
            snap.security_audit_matched_count,
            snap.status_label,
        ]

        try:
            write_csv_row("file_watcher_telemetry_polls.csv", headers, row)
            if snap.burst_deletions_alert or snap.high_activity_alert:
                write_csv_row(
                    "file_watcher_anomalies.csv",
                    headers,
                    row,
                )
        except Exception as e:
            logger.debug(f"Ошибка записи лога телеметрии файлового вотчера: {e}")


# Глобальный инстанс движка телеметрии
_global_telemetry_engine: Optional[FileWatcherTelemetryEngine] = None


def get_watcher_telemetry_engine() -> FileWatcherTelemetryEngine:
    """Получить глобальный экземпляр движка телеметрии файлового наблюдателя.

    Returns:
        FileWatcherTelemetryEngine: Экземпляр движка.
    """
    global _global_telemetry_engine
    if _global_telemetry_engine is None:
        _global_telemetry_engine = FileWatcherTelemetryEngine()
    return _global_telemetry_engine
