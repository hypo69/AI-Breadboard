# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Hardware - Gpu Prober
# =============================================================================
# Description:
#   GPU hardware prober supporting NVIDIA (nvidia-smi), AMD (amd-smi), Intel Arc (xpu-smi) and WMI.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.hardware.gpu_prober import GpuDeviceTelemetry
#
#     service = GpuDeviceTelemetry()
#
# File: gpu_prober.py
# Project: ai-breadboard
# Package: apps.windows.modules.hardware
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 06:15:00
# =============================================================================

from __future__ import annotations
"""GPU hardware prober supporting NVIDIA (nvidia-smi), AMD (amd-smi), Intel Arc (xpu-smi) and WMI."""

import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from logger import logger

@dataclass
class GpuDeviceTelemetry:
    """Detailed GPU telemetry metrics."""
    index: int
    name: str
    vendor: str
    driver_version: str
    temperature_gpu_c: Optional[float] = None
    temperature_memory_c: Optional[float] = None
    utilization_gpu_pct: Optional[float] = None
    utilization_memory_pct: Optional[float] = None
    memory_used_mb: Optional[float] = None
    memory_total_mb: Optional[float] = None
    power_draw_w: Optional[float] = None
    power_limit_w: Optional[float] = None
    fan_speed_pct: Optional[float] = None
    throttle_reasons: List[str] = field(default_factory=list)


def _normalize_name_tokens(name: str) -> set[str]:
    """Извлекает значимые буквенно-цифровые токены названия GPU для сопоставления."""
    cleaned = re.sub(r'[^a-zA-Z0-9]+', ' ', name.lower())
    ignore_tokens = {'corporation', 'corp', 'inc', 'graphics', 'series', 'display', 'adapter', 'video', 'controller'}
    return {t for t in cleaned.split() if t and t not in ignore_tokens}


def _is_same_gpu_device(name_a: str, name_b: str) -> bool:
    """Проверяет, относятся ли два строковых названия к одному и тому же GPU адаптеру."""
    toks_a = _normalize_name_tokens(name_a)
    toks_b = _normalize_name_tokens(name_b)
    if not toks_a or not toks_b:
        return False
    # Если одно является подмножеством другого или пересечение содержит ключевые номера моделей
    intersection = toks_a & toks_b
    # Ключевые модельные токены (например gt 710, 4080, uhd 630, rtx, rx)
    if len(intersection) >= 2:
        return True
    if toks_a.issubset(toks_b) or toks_b.issubset(toks_a):
        return True
    return False


class GpuProber:
    """Multi-vendor GPU telemetry collector."""

    def __init__(self) -> None:
        """Locate vendor SMI binaries."""
        self._nvidia_smi = shutil.which('nvidia-smi') or shutil.which('nvidia-smi.exe')
        self._amd_smi = shutil.which('amd-smi') or shutil.which('amd-smi.exe')
        self._xpu_smi = shutil.which('xpu-smi') or shutil.which('xpu-smi.exe')

    def probe_all(self) -> List[GpuDeviceTelemetry]:
        """Опрашивает все доступные GPU в системе (NVIDIA, AMD, Intel Arc и WMI адаптеры).

        Returns:
            List[GpuDeviceTelemetry]: Список обнаруженных видеокарт без дублирования.
        """
        gpus: List[GpuDeviceTelemetry] = []
        if self._nvidia_smi:
            nvidia_gpus = self._probe_nvidia()
            if nvidia_gpus:
                gpus.extend(nvidia_gpus)
        if self._amd_smi:
            amd_gpus = self._probe_amd()
            if amd_gpus:
                gpus.extend(amd_gpus)

        # Опрашиваем WMI для обнаружения встроенных видеокарт (например Intel UHD)
        wmi_gpus = self._probe_wmi()
        for w_gpu in wmi_gpus:
            # Проверяем, не найдена ли уже эта видеокарта через SMI
            already_exists = any(_is_same_gpu_device(w_gpu.name, existing.name) for existing in gpus)
            if not already_exists:
                gpus.append(w_gpu)

        # Переиндексируем список
        for idx, g in enumerate(gpus):
            g.index = idx

        return gpus

    def _probe_nvidia(self) -> List[GpuDeviceTelemetry]:
        """Query nvidia-smi with CSV query flags."""
        results: List[GpuDeviceTelemetry] = []
        try:
            query = 'index,name,driver_version,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.total,power.draw,power.limit,fan.speed'
            cmd = [str(self._nvidia_smi), f'--query-gpu={query}', '--format=csv,noheader,nounits']
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().splitlines():
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 11:
                        results.append(GpuDeviceTelemetry(index=int(parts[0]) if parts[0].isdigit() else 0, name=parts[1], vendor='NVIDIA', driver_version=parts[2], temperature_gpu_c=float(parts[3]) if parts[3] != '[N/A]' else None, utilization_gpu_pct=float(parts[4]) if parts[4] != '[N/A]' else None, utilization_memory_pct=float(parts[5]) if parts[5] != '[N/A]' else None, memory_used_mb=float(parts[6]) if parts[6] != '[N/A]' else None, memory_total_mb=float(parts[7]) if parts[7] != '[N/A]' else None, power_draw_w=float(parts[8]) if parts[8] != '[N/A]' else None, power_limit_w=float(parts[9]) if parts[9] != '[N/A]' else None, fan_speed_pct=float(parts[10]) if parts[10] != '[N/A]' else None))
        except Exception as e:
            logger.error(f'Error querying nvidia-smi: {e}')
        return results

    def _probe_amd(self) -> List[GpuDeviceTelemetry]:
        """Query amd-smi with JSON output."""
        results: List[GpuDeviceTelemetry] = []
        try:
            cmd = [str(self._amd_smi), 'metric', '--json']
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                items = data if isinstance(data, list) else [data]
                for idx, item in enumerate(items):
                    results.append(GpuDeviceTelemetry(index=idx, name=str(item.get('card_model', 'AMD Radeon GPU')), vendor='AMD', driver_version=str(item.get('driver_version', 'Unknown')), temperature_gpu_c=item.get('temperature_edge'), utilization_gpu_pct=item.get('gpu_utilization'), memory_used_mb=item.get('vram_used'), memory_total_mb=item.get('vram_total'), power_draw_w=item.get('power_usage')))
        except Exception as e:
            logger.error(f'Error querying amd-smi: {e}')
        return results

    def _probe_wmi(self) -> List[GpuDeviceTelemetry]:
        """Query WMI Win32_VideoController as fallback or multi-adapter prober."""
        results: List[GpuDeviceTelemetry] = []
        try:
            ps_cmd = 'Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, AdapterRAM | ConvertTo-Json -Compress'
            res = subprocess.run(['powershell', '-NoProfile', '-Command', ps_cmd], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                raw = json.loads(res.stdout)
                items = [raw] if isinstance(raw, dict) else raw
                for idx, item in enumerate(items):
                    name = str(item.get('Name', 'Generic Display Adapter')).strip()
                    ram_bytes = int(item.get('AdapterRAM') or 0)
                    name_l = name.lower()
                    if 'nvidia' in name_l or 'geforce' in name_l:
                        vendor = 'NVIDIA'
                    elif 'amd' in name_l or 'radeon' in name_l:
                        vendor = 'AMD'
                    elif 'intel' in name_l or 'arc' in name_l or 'uhd' in name_l or 'hd graphics' in name_l:
                        vendor = 'Intel'
                    else:
                        vendor = 'Generic'
                    results.append(GpuDeviceTelemetry(
                        index=idx,
                        name=name,
                        vendor=vendor,
                        driver_version=str(item.get('DriverVersion', 'N/A')),
                        memory_total_mb=round(ram_bytes / 1024 ** 2, 1) if ram_bytes > 0 else None
                    ))
        except Exception as e:
            logger.error(f'WMI GPU probe error: {e}')
        return results