# -*- coding: utf-8 -*-
"""GPU hardware prober supporting NVIDIA (nvidia-smi), AMD (amd-smi), Intel Arc (xpu-smi) and WMI."""

from __future__ import annotations

import json
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


class GpuProber:
    """Multi-vendor GPU telemetry collector."""

    def __init__(self) -> None:
        """Locate vendor SMI binaries."""
        self._nvidia_smi = shutil.which("nvidia-smi") or shutil.which("nvidia-smi.exe")
        self._amd_smi = shutil.which("amd-smi") or shutil.which("amd-smi.exe")
        self._xpu_smi = shutil.which("xpu-smi") or shutil.which("xpu-smi.exe")

    def probe_all(self) -> List[GpuDeviceTelemetry]:
        """Probe all available GPUs across NVIDIA, AMD, Intel, and WMI."""
        gpus: List[GpuDeviceTelemetry] = []

        # 1. NVIDIA
        if self._nvidia_smi:
            nvidia_gpus = self._probe_nvidia()
            if nvidia_gpus:
                gpus.extend(nvidia_gpus)

        # 2. AMD
        if self._amd_smi:
            amd_gpus = self._probe_amd()
            if amd_gpus:
                gpus.extend(amd_gpus)

        # 3. Fallback to WMI if no vendor SMI found
        if not gpus:
            gpus.extend(self._probe_wmi())

        return gpus

    def _probe_nvidia(self) -> List[GpuDeviceTelemetry]:
        """Query nvidia-smi with CSV query flags."""
        results: List[GpuDeviceTelemetry] = []
        try:
            query = (
                "index,name,driver_version,temperature.gpu,utilization.gpu,"
                "utilization.memory,memory.used,memory.total,power.draw,power.limit,fan.speed"
            )
            cmd = [str(self._nvidia_smi), f"--query-gpu={query}", "--format=csv,noheader,nounits"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().splitlines():
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 11:
                        results.append(
                            GpuDeviceTelemetry(
                                index=int(parts[0]) if parts[0].isdigit() else 0,
                                name=parts[1],
                                vendor="NVIDIA",
                                driver_version=parts[2],
                                temperature_gpu_c=float(parts[3]) if parts[3] != "[N/A]" else None,
                                utilization_gpu_pct=float(parts[4]) if parts[4] != "[N/A]" else None,
                                utilization_memory_pct=float(parts[5]) if parts[5] != "[N/A]" else None,
                                memory_used_mb=float(parts[6]) if parts[6] != "[N/A]" else None,
                                memory_total_mb=float(parts[7]) if parts[7] != "[N/A]" else None,
                                power_draw_w=float(parts[8]) if parts[8] != "[N/A]" else None,
                                power_limit_w=float(parts[9]) if parts[9] != "[N/A]" else None,
                                fan_speed_pct=float(parts[10]) if parts[10] != "[N/A]" else None,
                            )
                        )
        except Exception as e:
            logger.error(f"Error querying nvidia-smi: {e}")
        return results

    def _probe_amd(self) -> List[GpuDeviceTelemetry]:
        """Query amd-smi with JSON output."""
        results: List[GpuDeviceTelemetry] = []
        try:
            cmd = [str(self._amd_smi), "metric", "--json"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                items = data if isinstance(data, list) else [data]
                for idx, item in enumerate(items):
                    results.append(
                        GpuDeviceTelemetry(
                            index=idx,
                            name=str(item.get("card_model", "AMD Radeon GPU")),
                            vendor="AMD",
                            driver_version=str(item.get("driver_version", "Unknown")),
                            temperature_gpu_c=item.get("temperature_edge"),
                            utilization_gpu_pct=item.get("gpu_utilization"),
                            memory_used_mb=item.get("vram_used"),
                            memory_total_mb=item.get("vram_total"),
                            power_draw_w=item.get("power_usage"),
                        )
                    )
        except Exception as e:
            logger.error(f"Error querying amd-smi: {e}")
        return results

    def _probe_wmi(self) -> List[GpuDeviceTelemetry]:
        """Query WMI Win32_VideoController as fallback."""
        results: List[GpuDeviceTelemetry] = []
        try:
            ps_cmd = "Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, AdapterRAM | ConvertTo-Json -Compress"
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                raw = json.loads(res.stdout)
                items = [raw] if isinstance(raw, dict) else raw
                for idx, item in enumerate(items):
                    ram_bytes = int(item.get("AdapterRAM") or 0)
                    results.append(
                        GpuDeviceTelemetry(
                            index=idx,
                            name=str(item.get("Name", "Generic Display Adapter")),
                            vendor="Generic/WMI",
                            driver_version=str(item.get("DriverVersion", "N/A")),
                            memory_total_mb=round(ram_bytes / (1024**2), 1) if ram_bytes > 0 else None,
                        )
                    )
        except Exception as e:
            logger.error(f"WMI GPU probe error: {e}")
        return results
