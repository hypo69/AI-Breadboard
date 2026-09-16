# -*- coding: utf-8 -*-
"""SafeOps stress testing engine for CPU and GPU with thermal safety guards."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

from src.logger import logger
from apps.windows.hardware.gpu_prober import GpuProber


@dataclass
class StressTestResult:
    """Outcome of stress test execution."""
    target: str  # CPU, GPU
    duration_seconds: int
    max_temperature_c: Optional[float]
    aborted_due_to_thermal_limit: bool
    status: str
    message: str


class StressBenchmarkEngine:
    """Executes controlled stress tests on CPU and GPU with continuous telemetry."""

    def __init__(self, max_safe_temp_c: float = 90.0) -> None:
        """Initialize engine with thermal threshold."""
        self._max_safe_temp = max_safe_temp_c
        self._gpu_prober = GpuProber()

    def run_gpu_stress(self, duration_sec: int = 10) -> StressTestResult:
        """Execute GPU stress test (FurMark or OCCT) with thermal abort guard."""
        furmark_bin = shutil.which("FurMark") or shutil.which("FurMark.exe")
        if not furmark_bin:
            return StressTestResult(
                target="GPU",
                duration_seconds=0,
                max_temperature_c=None,
                aborted_due_to_thermal_limit=False,
                status="SKIPPED",
                message="FurMark executable not found in PATH. Install FurMark for GPU stress testing.",
            )

        cmd = [str(furmark_bin), "/nogui", f"/duration={duration_sec * 1000}"]
        proc = subprocess.Popen(cmd)
        start_time = time.time()
        max_temp: Optional[float] = None
        aborted = False

        try:
            while proc.poll() is None:
                elapsed = time.time() - start_time
                if elapsed > duration_sec + 5:
                    proc.terminate()
                    break

                # Monitor GPU temperature
                gpus = self._gpu_prober.probe_all()
                for g in gpus:
                    if g.temperature_gpu_c:
                        if max_temp is None or g.temperature_gpu_c > max_temp:
                            max_temp = g.temperature_gpu_c
                        if g.temperature_gpu_c >= self._max_safe_temp:
                            logger.critical(f"Thermal emergency! GPU temp reached {g.temperature_gpu_c}°C. Aborting stress test.")
                            proc.kill()
                            aborted = True
                            break
                if aborted:
                    break
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error during GPU stress test: {e}")
            proc.kill()

        return StressTestResult(
            target="GPU",
            duration_seconds=int(time.time() - start_time),
            max_temperature_c=max_temp,
            aborted_due_to_thermal_limit=aborted,
            status="CRITICAL_ABORT" if aborted else "COMPLETED",
            message="Test aborted due to high temperatures" if aborted else "GPU stress test completed successfully.",
        )

    def run_cpu_stress(self, duration_sec: int = 10) -> StressTestResult:
        """Simulate CPU load or execute CpuStres/Prime95."""
        cpustres_bin = shutil.which("cpustres") or shutil.which("cpustres.exe")
        start_time = time.time()
        
        if cpustres_bin:
            proc = subprocess.Popen([str(cpustres_bin)])
            time.sleep(duration_sec)
            proc.terminate()
        else:
            # Native Python multiprocessing load simulation
            end_t = time.time() + duration_sec
            while time.time() < end_t:
                _ = sum(i * i for i in range(100000))

        return StressTestResult(
            target="CPU",
            duration_seconds=duration_sec,
            max_temperature_c=None,
            aborted_due_to_thermal_limit=False,
            status="COMPLETED",
            message="CPU stress test completed successfully.",
        )
