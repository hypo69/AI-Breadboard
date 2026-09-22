# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: GPU Hardware & Installed Driver Detector
# =============================================================================
# Description:
#   Модуль обнаружения установленных графических адаптеров в Windows (NVIDIA, AMD,
#   Intel), чтения текущих версий драйверов через WMI, реестр и утилиту nvidia-smi.
#
# File: hardware_detector.py
# Project: ai-breadboard
# Package: apps.gpu_driver_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Детектор оборудования GPU и установленных версий драйверов."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from logger import logger
from apps.gpu_driver_manager.core.models import GpuDevice, VendorType


class GpuHardwareDetector:
    """Инструмент сканирования и извлечения параметров видеокарт и версий драйверов."""

    def __init__(self) -> None:
        """Инициализация детектора оборудования."""
        self._cached_devices: Optional[List[GpuDevice]] = None

    def detect_gpus(self, force_refresh: bool = False) -> List[GpuDevice]:
        """Обнаружить все видеоадаптеры в системе.

        Args:
            force_refresh: Принудительное обновление кэша сканирования.

        Returns:
            Список объектов GpuDevice с информацией о GPU и версиях драйверов.
        """
        if self._cached_devices is not None and not force_refresh:
            return self._cached_devices

        devices: List[GpuDevice] = []

        # 1. Попытка сканирования через PowerShell CIM / WMI
        try:
            wmi_devices = self._query_wmi_video_controllers()
            if wmi_devices:
                devices.extend(wmi_devices)
        except Exception as e:
            logger.warning(f"Ошибка при запросе WMI видеоконтроллеров: {e}")

        # 2. Если WMI не вернул устройств, резервный запрос через реестр Windows
        if not devices:
            try:
                reg_devices = self._query_registry_video_controllers()
                if reg_devices:
                    devices.extend(reg_devices)
            except Exception as e:
                logger.warning(f"Ошибка при чтении реестра видеоконтроллеров: {e}")

        # 3. Дополнительное обогащение данными для NVIDIA через nvidia-smi
        self._enrich_nvidia_details(devices)

        # 4. Если в окружении нет физических GPU (например, виртуалка/тестовый стенд),
        # гарантируем непустой список только при реальном запросе
        self._cached_devices = devices
        return devices

    def _query_wmi_video_controllers(self) -> List[GpuDevice]:
        """Получить список видеоконтроллеров через PowerShell Get-CimInstance."""
        ps_cmd = (
            "Get-CimInstance Win32_VideoController | "
            "Select-Object DeviceID, Name, DriverVersion, DriverDate, PNPDeviceID, Status, AdapterRAM | "
            "ConvertTo-Json -Compress"
        )
        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode != 0 or not proc.stdout.strip():
                return []

            raw_output = proc.stdout.strip()
            data = json.loads(raw_output)
            items = data if isinstance(data, list) else [data]

            devices: List[GpuDevice] = []
            for item in items:
                name = str(item.get("Name") or "").strip()
                if not name or "Microsoft Basic Display" in name or "RDP" in name:
                    continue

                raw_ver = str(item.get("DriverVersion") or "").strip()
                vendor = self._classify_vendor(name, str(item.get("PNPDeviceID") or ""))
                formatted_ver = self.format_driver_version(raw_ver, vendor)
                driver_date_str = self._format_driver_date(str(item.get("DriverDate") or ""))

                ram_bytes = item.get("AdapterRAM")
                ram_mb = int(ram_bytes // (1024 * 1024)) if isinstance(ram_bytes, int) and ram_bytes > 0 else None

                dev = GpuDevice(
                    id=str(item.get("DeviceID") or f"gpu_{len(devices)}"),
                    name=name,
                    vendor=vendor,
                    pnp_device_id=item.get("PNPDeviceID"),
                    driver_version_raw=raw_ver,
                    driver_version_formatted=formatted_ver,
                    driver_date=driver_date_str,
                    status=str(item.get("Status") or "OK"),
                    memory_mb=ram_mb,
                )
                devices.append(dev)

            return devices
        except Exception as e:
            logger.debug(f"WMI discovery exception: {e}")
            return []

    def _query_registry_video_controllers(self) -> List[GpuDevice]:
        """Резервный поиск видеокарт через системный реестр Windows."""
        devices: List[GpuDevice] = []
        try:
            import winreg

            key_path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as root_key:
                subkeys_count, _, _ = winreg.QueryInfoKey(root_key)
                for idx in range(subkeys_count):
                    subkey_name = winreg.EnumKey(root_key, idx)
                    if not subkey_name.isdigit():
                        continue
                    try:
                        with winreg.OpenKey(root_key, subkey_name) as dev_key:
                            driver_desc, _ = winreg.QueryValueEx(dev_key, "DriverDesc")
                            driver_version, _ = winreg.QueryValueEx(dev_key, "DriverVersion")
                            driver_date, _ = winreg.QueryValueEx(dev_key, "DriverDate")
                            matching_id, _ = winreg.QueryValueEx(dev_key, "MatchingDeviceId")

                            vendor = self._classify_vendor(driver_desc, matching_id)
                            formatted_ver = self.format_driver_version(driver_version, vendor)

                            dev = GpuDevice(
                                id=f"reg_gpu_{subkey_name}",
                                name=driver_desc,
                                vendor=vendor,
                                pnp_device_id=matching_id,
                                driver_version_raw=driver_version,
                                driver_version_formatted=formatted_ver,
                                driver_date=driver_date,
                                status="OK",
                            )
                            devices.append(dev)
                    except Exception:
                        continue
        except Exception as e:
            logger.debug(f"Registry video controller query failed: {e}")

        return devices

    def _enrich_nvidia_details(self, devices: List[GpuDevice]) -> None:
        """Обогатить сведения о NVIDIA GPU через утилиту nvidia-smi."""
        nvsmi_paths = [
            shutil.which("nvidia-smi"),
            r"C:\Windows\System32\nvidia-smi.exe",
            r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe",
        ]
        smi_bin = next((p for p in nvsmi_paths if p and Path(p).exists()), None)
        if not smi_bin:
            return

        try:
            proc = subprocess.run(
                [smi_bin, "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                lines = [ln.strip() for ln in proc.stdout.strip().splitlines() if ln.strip()]
                for idx, line in enumerate(lines):
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 2:
                        smi_name, smi_ver = parts[0], parts[1]
                        smi_mem = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else None

                        # Привязка к существующему NVIDIA устройству в списке
                        nv_devs = [d for d in devices if d.vendor == VendorType.NVIDIA]
                        if idx < len(nv_devs):
                            target = nv_devs[idx]
                            target.driver_version_formatted = smi_ver
                            if smi_mem:
                                target.memory_mb = smi_mem
                        elif not nv_devs:
                            # Добавляем обнаруженное устройство, если WMI его пропустил
                            devices.append(
                                GpuDevice(
                                    id=f"nvidia_smi_{idx}",
                                    name=smi_name,
                                    vendor=VendorType.NVIDIA,
                                    driver_version_raw=smi_ver,
                                    driver_version_formatted=smi_ver,
                                    memory_mb=smi_mem,
                                    status="OK",
                                )
                            )
        except Exception as e:
            logger.debug(f"nvidia-smi enrichment skipped: {e}")

    @staticmethod
    def _classify_vendor(name: str, pnp_id: str) -> VendorType:
        """Определить производителя GPU по имени и PNP ID."""
        text = f"{name} {pnp_id}".lower()
        if "nvidia" in text or "geforce" in text or "quadro" in text or "rtx" in text or "gtx" in text or "ven_10de" in text:
            return VendorType.NVIDIA
        if "amd" in text or "radeon" in text or "advanced micro devices" in text or "ven_1002" in text:
            return VendorType.AMD
        if "intel" in text or "arc" in text or "iris" in text or "uhd graphics" in text or "ven_8086" in text:
            return VendorType.INTEL
        return VendorType.OTHER

    @staticmethod
    def format_driver_version(raw_version: str, vendor: VendorType) -> str:
        """Преобразовать сырой номер версии Windows WMI в стандартный маркетинговый номер.

        Например:
            NVIDIA: '32.0.15.6094' -> '560.94'
            AMD:    '31.0.24033.1003' -> '24.3.1' (или аккуратный сокращенный номер)
        """
        if not raw_version:
            return "Unknown"

        raw = raw_version.strip()

        if vendor == VendorType.NVIDIA:
            # Драйверы NVIDIA в WMI имеют вид XX.XX.1X.XXXX (например 32.0.15.6094)
            # Последние 5 цифр без точки: 56094 -> 560.94
            digits_only = re.sub(r"[^\d]", "", raw)
            if len(digits_only) >= 5:
                last_five = digits_only[-5:]
                major = last_five[:3]
                minor = last_five[3:]
                return f"{int(major)}.{minor}"

        if vendor == VendorType.AMD:
            # Для AMD возвращаем версию как есть или чистим
            parts = raw.split(".")
            if len(parts) >= 3:
                # Например 31.0.24033 -> 24.3.3
                sub = parts[2]
                if len(sub) >= 4:
                    year = sub[:2]
                    month = sub[2:4]
                    return f"{year}.{int(month)}.1"
            return raw

        return raw

    @staticmethod
    def _format_driver_date(raw_date: str) -> Optional[str]:
        """Преобразовать строку даты WMI в формат YYYY-MM-DD."""
        if not raw_date:
            return None
        # Формат WMI: 20240815000000.000000+000
        match = re.match(r"^(\d{4})(\d{2})(\d{2})", raw_date)
        if match:
            y, m, d = match.groups()
            return f"{y}-{m}-{d}"
        return raw_date[:10] if len(raw_date) >= 10 else raw_date
