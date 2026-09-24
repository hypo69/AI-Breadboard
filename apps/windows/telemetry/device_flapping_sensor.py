# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Device Telemetry & Flapping Sensor
# =============================================================================
# Description:
#   Сенсор телеметрии аппаратных устройств и периферии (USB, дисконкеи, мыши,
#   клавиатуры, Wacom pen, принтеры, HDMI/DP мониторы, Bluetooth).
#   Выполняет непрерывный опрос, детектирует дребезг (flapping), внезапные
#   отключения, изменения кодов ошибок PnP (Code 43, 10, 28) и ведёт потоковое
#   логирование в JSONL в соответствии со стандартами телеметрии.
#
# Examples:
#   >>> from apps.windows.telemetry.device_flapping_sensor import DeviceFlappingSensor
#   >>> sensor = DeviceFlappingSensor(poll_interval_sec=1.0)
#   >>> sensor.start()
#   >>> ...
#   >>> sensor.stop()
#
# File: device_flapping_sensor.py
# Project: AI-Breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Сенсор непрерывного мониторинга периферии, обнаружения дребезга и PnP-телеметрии."""

from __future__ import annotations

import os
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from logger import logger
from apps.windows.api.setupapi import PnPDeviceInfo, SetupAPI
from apps.windows.telemetry.json_logger import TelemetryJsonLogger


@dataclass
class DeviceTransitionEvent:
    """Модель события изменения состояния устройства в телеметрии."""

    timestamp: str
    event_type: str  # CONNECTED, DISCONNECTED, ERROR_STATE_CHANGED, FLAPPING_ALERT
    device_instance_id: str
    friendly_name: str
    device_class: str
    category: str
    has_problem: bool
    problem_code: int
    status_code: int
    manufacturer: str
    flapping_count_in_window: int = 0
    uptime_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование события в словарь для сериализации."""
        return asdict(self)


class DeviceFlappingSensor:
    """Сенсор непрерывного мониторинга и отлова дребезга оборудования."""

    # Категоризация PnP-классов для понятной аналитики периферии
    CATEGORY_MAPPING: Dict[str, str] = {
        "HIDClass": "HID & Периферия",
        "Mouse": "Мышь / Указатель",
        "Keyboard": "Клавиатура",
        "DiskDrive": "Дисконкей / Накопитель",
        "Volume": "Том накопителя",
        "USB": "USB Устройство / Контроллер",
        "USBDevice": "USB Периферия",
        "Monitor": "HDMI / DP / Монитор",
        "Display": "Видеоадаптер / Дисплей",
        "Printer": "Принтер",
        "PrintQueue": "Очередь печати",
        "Bluetooth": "Bluetooth Адаптер / Устройство",
        "Digitizer": "Wacom / Графический планшет",
        "Media": "Аудио / Видео / Микрофон",
        "Camera": "Веб-камера",
        "Net": "Сетевой адаптер",
    }

    def __init__(
        self,
        poll_interval_sec: float = 1.0,
        flapping_window_sec: float = 60.0,
        flapping_threshold: int = 3,
        json_logger: Optional[TelemetryJsonLogger] = None,
        on_event_callback: Optional[Callable[[DeviceTransitionEvent], None]] = None,
    ) -> None:
        """Инициализирует сенсор телеметрии устройств.

        Args:
            poll_interval_sec: Интервал между опросами оборудования в секундах.
            flapping_window_sec: Временное окно для фиксации дребезга (сек).
            flapping_threshold: Количество отключений за окно для вызова тревоги FLAPPING_ALERT.
            json_logger: Логгер телеметрии (по умолчанию создает logs/device_telemetry.jsonl).
            on_event_callback: Опциональный callback-обработчик для передачи событий в UI/RAG.
        """
        self.poll_interval = max(0.1, poll_interval_sec)
        self.flapping_window = flapping_window_sec
        self.flapping_threshold = flapping_threshold
        self.on_event_callback = on_event_callback

        default_log_dir = Path("logs/telemetry")
        self.json_logger = json_logger or TelemetryJsonLogger(
            log_dir=str(default_log_dir),
            filename="device_telemetry_events.jsonl",
            max_file_size_mb=50.0,
        )

        self._setupapi = SetupAPI() if os.name == "nt" else None
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Состояние отслеживаемых устройств: {device_id: PnPDeviceInfo}
        self._active_devices: Dict[str, PnPDeviceInfo] = {}
        # История времени первого появления: {device_id: timestamp_float}
        self._connected_since: Dict[str, float] = {}
        # История отключений для детекции дребезга: {device_id: [timestamp_float, ...]}
        self._disconnect_history: Dict[str, List[float]] = {}

    def _resolve_category(self, device_class: str, friendly_name: str, instance_id: str) -> str:
        """Определяет человекочитаемую категорию устройства.

        Args:
            device_class: PnP-класс из реестра SetupAPI.
            friendly_name: Имя устройства.
            instance_id: Идентификатор инстанса (VID/PID).

        Returns:
            str: Название категории.
        """
        combined = f"{device_class} {friendly_name} {instance_id}".lower()
        if "wacom" in combined or "digitizer" in combined or "pen" in combined:
            return "Wacom / Графический планшет"
        if "hid" in combined and "keyboard" in combined:
            return "Клавиатура"
        if "hid" in combined and "mouse" in combined:
            return "Мышь / Указатель"
        if "bth" in combined or "bluetooth" in combined:
            return "Bluetooth"
        if "monitor" in combined or "display" in combined:
            return "HDMI / DP / Монитор"
        if "disk" in combined or "usbstor" in combined:
            return "Дисконкей / Накопитель"
        if "print" in combined:
            return "Принтер"

        return self.CATEGORY_MAPPING.get(device_class, device_class or "Прочее оборудование")

    def _get_current_devices_snapshot(self) -> Dict[str, PnPDeviceInfo]:
        """Получает текущий снимок активных PnP-устройств.

        Returns:
            Dict[str, PnPDeviceInfo]: Словарь активных устройств по их Device Instance ID.
        """
        if self._setupapi is None:
            return {}

        try:
            # Опрашиваем все присутствующие в данный момент устройства через SetupAPI
            devices = self._setupapi.get_all_devices(only_present=True)
            return {dev.device_instance_id: dev for dev in devices if dev.device_instance_id}
        except Exception as e:
            logger.error(f"Ошибка опроса SetupAPI в сенсоре устройств: {e}")
            return {}

    def _clean_flapping_history(self, now: float) -> None:
        """Очищает устаревшие временные метки за пределами окна дребезга."""
        cutoff = now - self.flapping_window
        for dev_id in list(self._disconnect_history.keys()):
            self._disconnect_history[dev_id] = [
                ts for ts in self._disconnect_history[dev_id] if ts >= cutoff
            ]
            if not self._disconnect_history[dev_id]:
                del self._disconnect_history[dev_id]

    def _emit_event(self, event: DeviceTransitionEvent) -> None:
        """Логирует событие телеметрии и оповещает внешние подписчики.

        Args:
            event: Экземпляр события изменения состояния устройства.
        """
        # 1. Потоковая запись в JSONL телеметрию
        self.json_logger.log(event.to_dict())

        # 2. Логирование через структурированный системный логгер
        log_msg = (
            f"[{event.event_type}] [{event.category}] '{event.friendly_name}' "
            f"(ID: {event.device_instance_id}) | Ошибка: Code {event.problem_code} | "
            f"Аптайм: {event.uptime_seconds:.1f}с | Дребезгов: {event.flapping_count_in_window}"
        )
        if event.event_type in ("DISCONNECTED", "FLAPPING_ALERT") or event.has_problem:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        # 3. Вызов callback-функции
        if self.on_event_callback:
            try:
                self.on_event_callback(event)
            except Exception as ex:
                logger.error(f"Ошибка в on_event_callback: {ex}")

    def poll_once(self) -> List[DeviceTransitionEvent]:
        """Выполняет один цикл опроса и детекции разницы состояний.

        Returns:
            List[DeviceTransitionEvent]: Список зафиксированных событий за текущий такт.
        """
        now = time.time()
        iso_time = datetime.now(timezone.utc).isoformat()
        events: List[DeviceTransitionEvent] = []

        current_snapshot = self._get_current_devices_snapshot()

        with self._lock:
            self._clean_flapping_history(now)

            # Если это первый запуск сенсора — инициализируем базу и регистрируем текущие
            if not self._active_devices and current_snapshot:
                self._active_devices = current_snapshot
                for dev_id in current_snapshot:
                    self._connected_since[dev_id] = now
                logger.info(f"Сенсор инициализирован: обнаружено {len(current_snapshot)} активных устройств")
                return events

            current_ids = set(current_snapshot.keys())
            previous_ids = set(self._active_devices.keys())

            # 1. Детектируем отключенные устройства (DISCONNECTED)
            disconnected_ids = previous_ids - current_ids
            for dev_id in disconnected_ids:
                prev_dev = self._active_devices.pop(dev_id)
                connect_time = self._connected_since.pop(dev_id, now)
                uptime = max(0.0, now - connect_time)

                # Регистрируем отключение в истории дребезга
                if dev_id not in self._disconnect_history:
                    self._disconnect_history[dev_id] = []
                self._disconnect_history[dev_id].append(now)

                flapping_count = len(self._disconnect_history[dev_id])
                category = self._resolve_category(
                    prev_dev.device_class, prev_dev.friendly_name, dev_id
                )

                evt = DeviceTransitionEvent(
                    timestamp=iso_time,
                    event_type="DISCONNECTED",
                    device_instance_id=dev_id,
                    friendly_name=prev_dev.friendly_name or prev_dev.device_class or dev_id,
                    device_class=prev_dev.device_class,
                    category=category,
                    has_problem=prev_dev.has_problem,
                    problem_code=prev_dev.problem_code,
                    status_code=prev_dev.status_code,
                    manufacturer=prev_dev.manufacturer,
                    flapping_count_in_window=flapping_count,
                    uptime_seconds=uptime,
                )
                events.append(evt)
                self._emit_event(evt)

                # Проверяем превышение порога дребезга
                if flapping_count >= self.flapping_threshold:
                    flap_evt = DeviceTransitionEvent(
                        timestamp=iso_time,
                        event_type="FLAPPING_ALERT",
                        device_instance_id=dev_id,
                        friendly_name=prev_dev.friendly_name,
                        device_class=prev_dev.device_class,
                        category=category,
                        has_problem=True,
                        problem_code=prev_dev.problem_code,
                        status_code=prev_dev.status_code,
                        manufacturer=prev_dev.manufacturer,
                        flapping_count_in_window=flapping_count,
                        uptime_seconds=uptime,
                    )
                    events.append(flap_evt)
                    self._emit_event(flap_evt)

            # 2. Детектируем подключенные устройства (CONNECTED)
            connected_ids = current_ids - previous_ids
            for dev_id in connected_ids:
                new_dev = current_snapshot[dev_id]
                self._active_devices[dev_id] = new_dev
                self._connected_since[dev_id] = now

                flapping_count = len(self._disconnect_history.get(dev_id, []))
                category = self._resolve_category(
                    new_dev.device_class, new_dev.friendly_name, dev_id
                )

                evt = DeviceTransitionEvent(
                    timestamp=iso_time,
                    event_type="CONNECTED",
                    device_instance_id=dev_id,
                    friendly_name=new_dev.friendly_name or new_dev.device_class or dev_id,
                    device_class=new_dev.device_class,
                    category=category,
                    has_problem=new_dev.has_problem,
                    problem_code=new_dev.problem_code,
                    status_code=new_dev.status_code,
                    manufacturer=new_dev.manufacturer,
                    flapping_count_in_window=flapping_count,
                    uptime_seconds=0.0,
                )
                events.append(evt)
                self._emit_event(evt)

            # 3. Детектируем изменение состояния ошибок (например, вылет в Code 43 / Code 10)
            common_ids = current_ids & previous_ids
            for dev_id in common_ids:
                old_dev = self._active_devices[dev_id]
                new_dev = current_snapshot[dev_id]

                if (old_dev.has_problem != new_dev.has_problem) or (
                    old_dev.problem_code != new_dev.problem_code
                ):
                    self._active_devices[dev_id] = new_dev
                    connect_time = self._connected_since.get(dev_id, now)
                    category = self._resolve_category(
                        new_dev.device_class, new_dev.friendly_name, dev_id
                    )

                    evt = DeviceTransitionEvent(
                        timestamp=iso_time,
                        event_type="ERROR_STATE_CHANGED",
                        device_instance_id=dev_id,
                        friendly_name=new_dev.friendly_name,
                        device_class=new_dev.device_class,
                        category=category,
                        has_problem=new_dev.has_problem,
                        problem_code=new_dev.problem_code,
                        status_code=new_dev.status_code,
                        manufacturer=new_dev.manufacturer,
                        uptime_seconds=max(0.0, now - connect_time),
                    )
                    events.append(evt)
                    self._emit_event(evt)

        return events

    def _loop(self) -> None:
        """Фоновый цикл непрерывного опроса."""
        logger.info(
            f"Запущен фоновый поток сенсора устройств (интервал: {self.poll_interval}с, "
            f"окно дребезга: {self.flapping_window}с, порог: {self.flapping_threshold})"
        )
        while self._is_running:
            try:
                self.poll_once()
            except Exception as e:
                logger.error(f"Необработанная ошибка в цикле опроса сенсора: {e}")
            time.sleep(self.poll_interval)

    def start(self) -> None:
        """Запускает непрерывный мониторинг в фоновом потоке."""
        with self._lock:
            if self._is_running:
                logger.warning("Сенсор устройств уже запущен")
                return
            self._is_running = True
            self._thread = threading.Thread(
                target=self._loop, name="DeviceFlappingSensorThread", daemon=True
            )
            self._thread.start()

    def stop(self) -> None:
        """Останавливает непрерывный мониторинг."""
        with self._lock:
            if not self._is_running:
                return
            self._is_running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
            logger.info("Сенсор устройств успешно остановлен")

    def get_status(self) -> Dict[str, Any]:
        """Возвращает текущую статистику сенсора.

        Returns:
            Dict[str, Any]: Данные о количестве активных устройств и истории дребезга.
        """
        with self._lock:
            return {
                "is_running": self._is_running,
                "poll_interval_sec": self.poll_interval,
                "active_devices_count": len(self._active_devices),
                "flapping_devices_tracked": len(self._disconnect_history),
                "devices_with_problems": sum(
                    1 for d in self._active_devices.values() if d.has_problem
                ),
            }
