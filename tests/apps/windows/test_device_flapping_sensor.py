# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Device Telemetry & Flapping Sensor Tests
# =============================================================================
# Description:
#   Модульные тесты для сенсора телеметрии оборудования и периферии
#   DeviceFlappingSensor: валидация детекции подключений, отключений,
#   дребезга (flapping), изменения кодов ошибок и классификации устройств.
#
# File: test_device_flapping_sensor.py
# Project: AI-Breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты для сенсора телеметрии и детекции дребезга устройств."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from apps.windows.api.setupapi import PnPDeviceInfo
from apps.windows.telemetry.device_flapping_sensor import (
    DeviceFlappingSensor,
    DeviceTransitionEvent,
)
from apps.windows.telemetry.json_logger import TelemetryJsonLogger


def test_device_transition_event_model() -> None:
    """Проверка модели события перехода состояния оборудования."""
    evt = DeviceTransitionEvent(
        timestamp="2026-09-23T19:00:00Z",
        event_type="CONNECTED",
        device_instance_id="USB\\VID_056A&PID_0357\\01",
        friendly_name="Wacom Intuos Pro M",
        device_class="HIDClass",
        category="Wacom / Графический планшет",
        has_problem=False,
        problem_code=0,
        status_code=0,
        manufacturer="Wacom Technology Corp.",
        flapping_count_in_window=0,
        uptime_seconds=0.0,
    )

    data = evt.to_dict()
    assert data["event_type"] == "CONNECTED"
    assert data["friendly_name"] == "Wacom Intuos Pro M"
    assert data["category"] == "Wacom / Графический планшет"
    assert data["has_problem"] is False


def test_device_category_resolution() -> None:
    """Проверка корректной классификации типов периферии."""
    sensor = DeviceFlappingSensor()

    assert sensor._resolve_category("HIDClass", "Wacom Tablet", "USB\\VID_056A") == "Wacom / Графический планшет"
    assert sensor._resolve_category("Mouse", "HID Mouse", "HID\\VID_046D") == "Мышь / Указатель"
    assert sensor._resolve_category("Keyboard", "Standard PS/2 Keyboard", "ACPI\\PNP0303") == "Клавиатура"
    assert sensor._resolve_category("DiskDrive", "SanDisk Ultra USB 3.0", "USBSTOR\\DISK") == "Дисконкей / Накопитель"
    assert sensor._resolve_category("Monitor", "Dell U2720Q (HDMI)", "DISPLAY\\DEL4174") == "HDMI / DP / Монитор"
    assert sensor._resolve_category("Bluetooth", "Intel Wireless Bluetooth", "USB\\VID_8087") == "Bluetooth"
    assert sensor._resolve_category("Printer", "HP LaserJet Pro", "DOT4PRT\\HP") == "Принтер"


def test_sensor_connect_disconnect_and_flapping_flow(tmp_path: Path) -> None:
    """Проверка жизненного цикла: подключение, отключение и детекция дребезга."""
    json_logger = TelemetryJsonLogger(log_dir=str(tmp_path), filename="test_events.jsonl")
    emitted_events: list[DeviceTransitionEvent] = []

    def callback(evt: DeviceTransitionEvent) -> None:
        emitted_events.append(evt)

    sensor = DeviceFlappingSensor(
        poll_interval_sec=0.1,
        flapping_window_sec=10.0,
        flapping_threshold=2,
        json_logger=json_logger,
        on_event_callback=callback,
    )

    # 1. Первый такт: Базовый снимок (2 устройства)
    dev_mouse = PnPDeviceInfo(
        device_instance_id="USB\\VID_046D&PID_C077\\01",
        friendly_name="Logitech USB Mouse",
        hardware_id="USB\\VID_046D",
        device_class="Mouse",
        manufacturer="Logitech",
        has_problem=False,
        status_code=0,
        problem_code=0,
    )
    dev_wacom = PnPDeviceInfo(
        device_instance_id="USB\\VID_056A&PID_0357\\02",
        friendly_name="Wacom Pen Tablet",
        hardware_id="USB\\VID_056A",
        device_class="HIDClass",
        manufacturer="Wacom",
        has_problem=False,
        status_code=0,
        problem_code=0,
    )

    sensor._get_current_devices_snapshot = MagicMock(return_value={
        dev_mouse.device_instance_id: dev_mouse,
        dev_wacom.device_instance_id: dev_wacom,
    })

    # Базовый такт не генерирует алертов на отключение
    evts_init = sensor.poll_once()
    assert len(evts_init) == 0
    assert sensor.get_status()["active_devices_count"] == 2

    # 2. Второй такт: Wacom отключился (1-е отключение)
    sensor._get_current_devices_snapshot = MagicMock(return_value={
        dev_mouse.device_instance_id: dev_mouse,
    })
    evts_disc1 = sensor.poll_once()
    assert len(evts_disc1) == 1
    assert evts_disc1[0].event_type == "DISCONNECTED"
    assert evts_disc1[0].device_instance_id == dev_wacom.device_instance_id
    assert evts_disc1[0].flapping_count_in_window == 1

    # 3. Третий такт: Wacom снова подключился (CONNECTED)
    sensor._get_current_devices_snapshot = MagicMock(return_value={
        dev_mouse.device_instance_id: dev_mouse,
        dev_wacom.device_instance_id: dev_wacom,
    })
    evts_conn = sensor.poll_once()
    assert len(evts_conn) == 1
    assert evts_conn[0].event_type == "CONNECTED"

    # 4. Четвертый такт: Wacom снова отключился (2-е отключение -> FLAPPING_ALERT)
    sensor._get_current_devices_snapshot = MagicMock(return_value={
        dev_mouse.device_instance_id: dev_mouse,
    })
    evts_disc2 = sensor.poll_once()
    # Должно быть 2 события: DISCONNECTED и FLAPPING_ALERT
    assert len(evts_disc2) == 2
    types = [e.event_type for e in evts_disc2]
    assert "DISCONNECTED" in types
    assert "FLAPPING_ALERT" in types

    # Проверяем, что в лог-файле сохранены записи
    log_file = tmp_path / "test_events.jsonl"
    assert log_file.exists()
    assert len(log_file.read_text(encoding="utf-8").strip().splitlines()) >= 4


def test_device_error_state_transition() -> None:
    """Проверка обнаружения перехода устройства в состояние сбоя (Code 43)."""
    sensor = DeviceFlappingSensor(poll_interval_sec=0.1)

    normal_dev = PnPDeviceInfo(
        device_instance_id="USB\\VID_1234&PID_5678\\03",
        friendly_name="USB Flash Drive (Дисконкей)",
        hardware_id="USB\\VID_1234",
        device_class="DiskDrive",
        manufacturer="Generic",
        has_problem=False,
        status_code=0,
        problem_code=0,
    )

    # 1. Инициализация
    sensor._get_current_devices_snapshot = MagicMock(return_value={
        normal_dev.device_instance_id: normal_dev,
    })
    sensor.poll_once()

    # 2. Устройство выбросило ошибку Code 43 (Windows остановила устройство)
    problem_dev = PnPDeviceInfo(
        device_instance_id="USB\\VID_1234&PID_5678\\03",
        friendly_name="USB Flash Drive (Дисконкей)",
        hardware_id="USB\\VID_1234",
        device_class="DiskDrive",
        manufacturer="Generic",
        has_problem=True,
        status_code=0x400,
        problem_code=43,
    )
    sensor._get_current_devices_snapshot = MagicMock(return_value={
        problem_dev.device_instance_id: problem_dev,
    })
    events = sensor.poll_once()

    assert len(events) == 1
    assert events[0].event_type == "ERROR_STATE_CHANGED"
    assert events[0].has_problem is True
    assert events[0].problem_code == 43


def test_sensor_lifecycle() -> None:
    """Проверка запуска и корректной остановки фонового потока сенсора."""
    sensor = DeviceFlappingSensor(poll_interval_sec=0.05)
    sensor.start()
    assert sensor.get_status()["is_running"] is True

    time.sleep(0.15)
    sensor.stop()
    assert sensor.get_status()["is_running"] is False
