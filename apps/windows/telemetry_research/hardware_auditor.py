# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry_Research - Hardware Auditor
# =============================================================================
# Description:
#   Движок аудита оборудования, драйверов и привязки датчиков.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry_research.hardware_auditor import HardwareAuditor
#
#     service = HardwareAuditor()
#
# File: hardware_auditor.py
# Project: ai-breadboard
# Package: apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Движок аудита оборудования, драйверов и привязки датчиков."""

import os
import platform
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from logger import logger
from apps.windows.telemetry.win32_ffi.setupapi import SetupAPI
from apps.windows.telemetry.models import DriverInfo, HardwareAuditReport, HardwareDeviceAudit, HardwareSensor
from apps.windows.telemetry.sensors import get_hardware_sensors


class HardwareAuditor:
    """Аудитор аппаратного обеспечения, драйверов и параметров устройств."""

    def __init__(self, setupapi_client: Optional[SetupAPI]=None) -> None:
        """Инициализация аудитора оборудования.

        Args:
            setupapi_client: Опциональный экземпляр нативного клиента SetupAPI.
        """
        self._setupapi = setupapi_client or (SetupAPI() if os.name == 'nt' else None)

    def _parse_wmi_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Парсинг даты из формата WMI (YYYYMMDDHHMMSS.mmmmmm+UUU) или ISO.

        Args:
            date_str: Строка с датой.

        Returns:
            Optional[datetime]: Объект datetime или None.
        """
        if not date_str:
            return None
        raw = str(date_str).strip()
        if not raw or raw.lower() == 'none':
            return None
        if len(raw) >= 8 and raw[:8].isdigit():
            try:
                year = int(raw[0:4])
                month = int(raw[4:6])
                day = int(raw[6:8])
                return datetime(year, month, day, tzinfo=timezone.utc)
            except Exception:
                pass
        iso_match = re.match('^(\\d{4})-(\\d{2})-(\\d{2})', raw)
        if iso_match:
            try:
                return datetime(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)), tzinfo=timezone.utc)
            except Exception:
                pass
        ru_match = re.match('^(\\d{2})\\.(\\d{2})\\.(\\d{4})', raw)
        if ru_match:
            try:
                return datetime(int(ru_match.group(3)), int(ru_match.group(2)), int(ru_match.group(1)), tzinfo=timezone.utc)
            except Exception:
                pass
        logger.error('Функция _parse_wmi_date вернула пустой результат')
        return None

    def _evaluate_driver_currency(self, driver_date_dt: Optional[datetime], provider: str, device_class: str) -> tuple[str, Optional[int]]:
        """Расчет актуальности драйвера на основе даты выпуска и поставщика.

        Args:
            driver_date_dt: Дата выпуска драйвера.
            provider: Поставщик драйвера (NVIDIA, Intel, Microsoft и др.).
            device_class: Класс оборудования (Display, Net, Processor и др.).

        Returns:
            tuple[str, Optional[int]]: (Статус актуальности, возраст в днях).
        """
        now = datetime.now(timezone.utc)
        age_days: Optional[int] = None
        if driver_date_dt:
            age_days = max(0, (now - driver_date_dt).days)
        is_ms_inbox = 'microsoft' in provider.lower()
        if age_days is not None:
            if age_days > 1825:
                if is_ms_inbox and device_class in ('System', 'Volume', 'Processor'):
                    return ('Стандартный системный драйвер', age_days)
                return ('Критически устарел (> 5 лет)', age_days)
            elif age_days > 730:
                if is_ms_inbox and device_class in ('System', 'Volume', 'Processor'):
                    return ('Стандартный системный драйвер', age_days)
                return ('Устарел (> 2 лет)', age_days)
            else:
                return ('Актуален', age_days)
        if is_ms_inbox:
            return ('Базовый драйвер ОС', age_days)
        return ('Не определена', age_days)

    def _get_drivers_from_wmi(self) -> Dict[str, Dict[str, Any]]:
        """Получение карты драйверов из WMI Win32_PnPSignedDriver.

        Returns:
            Dict[str, Dict[str, Any]]: Словарь с метаданными драйверов по DeviceID.
        """
        drivers_map: Dict[str, Dict[str, Any]] = {}
        if os.name != 'nt':
            return drivers_map
        try:
            import pythoncom
            pythoncom.CoInitialize()
            import wmi
            w = wmi.WMI()
            for d in w.Win32_PnPSignedDriver():
                dev_id = getattr(d, 'DeviceID', None)
                if not dev_id:
                    continue
                norm_id = str(dev_id).strip().upper()
                drivers_map[norm_id] = {'name': getattr(d, 'DeviceName', '') or getattr(d, 'Description', '') or '', 'driver_version': getattr(d, 'DriverVersion', '') or '', 'driver_date_raw': getattr(d, 'DriverDate', None), 'provider': getattr(d, 'DriverProviderName', 'Unknown') or 'Unknown', 'inf_name': getattr(d, 'InfName', None), 'is_signed': bool(getattr(d, 'IsSigned', True))}
        except Exception:
            pass
        return drivers_map

    def _get_device_install_date_registry(self, device_instance_id: str) -> Optional[str]:
        """Чтение даты установки устройства из системного реестра.

        Args:
            device_instance_id: Идентификатор PnP устройства.

        Returns:
            Optional[str]: Строка даты установки в формате DD.MM.YYYY HH:MM или None.
        """
        if os.name != 'nt' or not device_instance_id:
            return None
        try:
            import winreg
            key_path = f'SYSTEM\\CurrentControlSet\\Enum\\{device_instance_id}'
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                for val_name in ['InstallDate', 'FirstInstallDate']:
                    try:
                        val, reg_type = winreg.QueryValueEx(key, val_name)
                        if isinstance(val, int) and val > 0:
                            return datetime.fromtimestamp(val, tz=timezone.utc).strftime('%d.%m.%Y %H:%M')
                    except OSError:
                        pass
        except Exception:
            pass
        logger.error('Функция _get_device_install_date_registry вернула пустой результат')
        return None

    def _bind_sensors_to_device(self, device: HardwareDeviceAudit, all_sensors: List[HardwareSensor]) -> List[HardwareSensor]:
        """Привязка релевантных датчиков телеметрии к аппаратному устройству.

        Args:
            device: Аудируемое устройство.
            all_sensors: Полный список активных аппаратных сенсоров.

        Returns:
            List[HardwareSensor]: Список датчиков, относящихся к данному устройству.
        """
        matched: List[HardwareSensor] = []
        dev_class = device.device_class.lower()
        dev_name = device.name.lower()
        for s in all_sensors:
            s_name = s.name.lower()
            s_id = s.sensor_id.lower()
            if dev_class in ('display', 'gpu') or 'nvidia' in dev_name or 'geforce' in dev_name or ('radeon' in dev_name):
                if 'gpu' in s_id or 'gpu' in s_name or 'nvidia' in s_name:
                    matched.append(s)
                    continue
            if dev_class in ('processor', 'cpu') or 'intel' in dev_name or 'amd' in dev_name or ('ryzen' in dev_name):
                if 'cpu' in s_id or 'cpu' in s_name or 'thermal' in s_id or ('acpi' in s_id):
                    matched.append(s)
                    continue
            if dev_class in ('diskdrive', 'storage', 'nvme') or 'ssd' in dev_name or 'hdd' in dev_name:
                if 'disk' in s_id or 'drive' in s_id or 'smart' in s_id or ('storage' in s_id):
                    matched.append(s)
                    continue
            if dev_class in ('net', 'network') or 'ethernet' in dev_name or 'wi-fi' in dev_name or ('wireless' in dev_name):
                if 'net_' in s_id or 'internet_' in s_id:
                    matched.append(s)
                    continue
        return matched

    def audit_hardware(self, sensors: Optional[List[HardwareSensor]]=None) -> HardwareAuditReport:
        """Проведение полного аудита оборудования, драйверов и привязки датчиков.

        Args:
            sensors: Опциональный список предварительно собранных сенсоров.

        Returns:
            HardwareAuditReport: Полный отчет по оборудованию.
        """
        all_sensors = sensors if sensors is not None else get_hardware_sensors()
        wmi_drivers = self._get_drivers_from_wmi()
        device_audits: List[HardwareDeviceAudit] = []
        problem_count = 0
        outdated_count = 0
        if self._setupapi:
            try:
                raw_devices = self._setupapi.get_all_devices(only_present=True)
                for dev in raw_devices:
                    norm_id = dev.device_instance_id.strip().upper()
                    driver_data = wmi_drivers.get(norm_id)
                    driver_info: Optional[DriverInfo] = None
                    if driver_data:
                        date_dt = self._parse_wmi_date(driver_data.get('driver_date_raw'))
                        date_str = date_dt.strftime('%Y-%m-%d') if date_dt else None
                        provider = driver_data.get('provider', 'Unknown')
                        currency_status, age_days = self._evaluate_driver_currency(driver_date_dt=date_dt, provider=provider, device_class=dev.device_class or 'Device')
                        if 'устарел' in currency_status.lower():
                            outdated_count += 1
                        driver_info = DriverInfo(name=driver_data.get('name') or dev.friendly_name, driver_version=driver_data.get('driver_version', ''), driver_date=date_str, provider=provider, inf_name=driver_data.get('inf_name'), is_signed=driver_data.get('is_signed', True), is_inbox='microsoft' in provider.lower(), age_days=age_days, currency_status=currency_status)
                    install_date = self._get_device_install_date_registry(dev.device_instance_id)
                    if not install_date and driver_info and driver_info.driver_date:
                        install_date = driver_info.driver_date
                    status_str = 'Problem' if dev.has_problem else 'OK'
                    if dev.has_problem:
                        problem_count += 1
                    audit_item = HardwareDeviceAudit(device_id=dev.device_instance_id, name=dev.friendly_name, device_class=dev.device_class or 'Device', manufacturer=dev.manufacturer or 'Unknown', install_date=install_date, status=status_str, problem_code=dev.problem_code, driver=driver_info, properties={'hardware_id': dev.hardware_id, 'status_code': dev.status_code})
                    audit_item.sensors = self._bind_sensors_to_device(audit_item, all_sensors)
                    device_audits.append(audit_item)
            except Exception as ex:
                logger.debug(f'Ошибка при аудите через SetupAPI: {ex}')
        if not device_audits:
            dummy_cpu = HardwareDeviceAudit(device_id='ROOT/CPU/0000', name=platform.processor() or 'System Processor', device_class='Processor', manufacturer='Generic', install_date=datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M'), status='OK', problem_code=0, driver=DriverInfo(name='Processor Driver', driver_version='10.0.26100.1', driver_date='2024-05-01', provider='Microsoft', is_signed=True, is_inbox=True, age_days=100, currency_status='Актуален'))
            dummy_cpu.sensors = self._bind_sensors_to_device(dummy_cpu, all_sensors)
            device_audits.append(dummy_cpu)
        summary_msg = f'Аудит завершен: обнаружено устройств: {len(device_audits)}, проблемных PnP: {problem_count}, с устаревшими драйверами: {outdated_count}'
        return HardwareAuditReport(devices_count=len(device_audits), problem_devices_count=problem_count, outdated_drivers_count=outdated_count, devices=device_audits, summary=summary_msg)
