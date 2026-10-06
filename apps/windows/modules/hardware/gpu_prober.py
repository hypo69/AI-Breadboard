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
# Updated: 2026-10-06 08:10:00
# =============================================================================

from __future__ import annotations
"""GPU hardware prober supporting NVIDIA (nvidia-smi), AMD (amd-smi), Intel Arc (xpu-smi), WMI and WDDM Performance Counters."""

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
    engines: Dict[str, float] = field(default_factory=dict)
    shared_memory_used_mb: Optional[float] = None
    dedicated_memory_used_mb: Optional[float] = None


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
    """Multi-vendor GPU telemetry collector with WDDM Direct3D counters."""

    def __init__(self) -> None:
        """Locate vendor SMI binaries."""
        self._nvidia_smi = shutil.which('nvidia-smi') or shutil.which('nvidia-smi.exe')
        self._amd_smi = shutil.which('amd-smi') or shutil.which('amd-smi.exe')
        self._xpu_smi = shutil.which('xpu-smi') or shutil.which('xpu-smi.exe')

    def probe_all(self) -> List[GpuDeviceTelemetry]:
        """Опрашивает все доступные GPU в системе (NVIDIA, AMD, Intel Arc, WMI и WDDM счетчики).

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

        # Обогащаем данными WDDM / Direct3D счетчиков производительности (движки 3D/Decode/Copy и память)
        self._enrich_wddm_performance(gpus)

        # Переиндексируем список
        for idx, g in enumerate(gpus):
            g.index = idx

        return gpus

    def _enrich_wddm_performance(self, gpus: List[GpuDeviceTelemetry]) -> None:
        """Обогащает метрики видеокарт счетчиками WDDM/Direct3D (движки 3D/Video/Copy и память)."""
        if not gpus:
            return
        try:
            # 1. Опрос счетчиков памяти видеоадаптеров
            ps_mem = 'Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUAdapterMemory -ErrorAction SilentlyContinue | Select-Object Name, DedicatedUsage, SharedUsage, TotalCommitted | ConvertTo-Json -Compress'
            res_mem = subprocess.run(['powershell', '-NoProfile', '-Command', ps_mem], capture_output=True, text=True, timeout=5)
            mems = json.loads(res_mem.stdout) if res_mem.stdout.strip() else []
            if isinstance(mems, dict):
                mems = [mems]

            luid_memory: Dict[str, Dict[str, float]] = {}
            for m in mems:
                name = str(m.get('Name', ''))
                if 'luid_' in name:
                    luid_match = re.search(r'luid_(0x[0-9a-fA-F]+_0x[0-9a-fA-F]+)', name)
                    if luid_match:
                        luid = luid_match.group(1).lower()
                        ded = float(m.get('DedicatedUsage') or 0.0) / (1024 ** 2)
                        shared = float(m.get('SharedUsage') or 0.0) / (1024 ** 2)
                        tot = float(m.get('TotalCommitted') or 0.0) / (1024 ** 2)
                        luid_memory[luid] = {'dedicated_mb': ded, 'shared_mb': shared, 'total_mb': tot}

            # 2. Опрос счетчиков графических движков
            ps_eng = 'Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine -ErrorAction SilentlyContinue | Select-Object Name, UtilizationPercentage | ConvertTo-Json -Compress'
            res_eng = subprocess.run(['powershell', '-NoProfile', '-Command', ps_eng], capture_output=True, text=True, timeout=5)
            engs = json.loads(res_eng.stdout) if res_eng.stdout.strip() else []
            if isinstance(engs, dict):
                engs = [engs]

            luid_engines: Dict[str, Dict[str, float]] = {}
            for it in engs:
                name = str(it.get('Name', ''))
                if '_luid_' in name and '_engtype_' in name:
                    luid_match = re.search(r'luid_(0x[0-9a-fA-F]+_0x[0-9a-fA-F]+)', name)
                    if luid_match:
                        luid = luid_match.group(1).lower()
                        eng_type = name.split('_engtype_')[-1].strip()
                        if eng_type:
                            val = float(it.get('UtilizationPercentage') or 0.0)
                            luid_engines.setdefault(luid, {}).setdefault(eng_type, 0.0)
                            luid_engines[luid][eng_type] += val

            # 3. Сопоставление LUID и адаптеров
            for g in gpus:
                g_vendor = g.vendor.lower()
                is_igpu = "intel" in g_vendor or "generic" in g_vendor or (g.memory_total_mb and g.memory_total_mb <= 2048 and "intel" in g.name.lower())

                matched_luid = None
                if is_igpu:
                    igpu_candidates = [
                        (luid, m['shared_mb']) for luid, m in luid_memory.items()
                        if m.get('dedicated_mb', 0.0) == 0.0
                    ]
                    if igpu_candidates:
                        igpu_candidates.sort(key=lambda x: x[1], reverse=True)
                        matched_luid = igpu_candidates[0][0]
                else:
                    discrete_candidates = [
                        (luid, m['dedicated_mb']) for luid, m in luid_memory.items()
                        if m.get('dedicated_mb', 0.0) > 0.0
                    ]
                    if discrete_candidates:
                        discrete_candidates.sort(key=lambda x: x[1], reverse=True)
                        matched_luid = discrete_candidates[0][0]

                if matched_luid:
                    mem_info = luid_memory.get(matched_luid, {})
                    g.dedicated_memory_used_mb = round(mem_info.get('dedicated_mb', 0.0), 1)
                    g.shared_memory_used_mb = round(mem_info.get('shared_mb', 0.0), 1)
                    if g.memory_used_mb is None:
                        g.memory_used_mb = g.shared_memory_used_mb if is_igpu else g.dedicated_memory_used_mb
                    if is_igpu and (g.memory_total_mb is None or g.memory_total_mb == 0):
                        g.memory_total_mb = round(mem_info.get('total_mb', 1024.0), 1)

                    eng_info = luid_engines.get(matched_luid, {})
                    normalized_engines: Dict[str, float] = {}
                    for eng_name, eng_pct in eng_info.items():
                        clean_eng = eng_name
                        if eng_name == "3D": clean_eng = "3D Engine"
                        elif eng_name == "VideoDecode": clean_eng = "Video Decode"
                        elif eng_name == "VideoProcessing": clean_eng = "Video Processing"
                        elif eng_name == "Copy": clean_eng = "Copy Engine"
                        elif eng_name == "GDI Render": clean_eng = "GDI Render"
                        normalized_engines[clean_eng] = round(eng_pct, 1)

                    if not normalized_engines and is_igpu:
                        normalized_engines = {
                            "3D Engine": 0.0,
                            "Video Decode": 0.0,
                            "Video Processing": 0.0,
                            "Copy Engine": 0.0
                        }

                    g.engines = normalized_engines

                    if g.utilization_gpu_pct is None and normalized_engines:
                        g.utilization_gpu_pct = max(normalized_engines.values())

        except Exception as exc:
            logger.debug(f'WDDM Performance enrichment error: {exc}')

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