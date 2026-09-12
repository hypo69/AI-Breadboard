# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Hardware and Accelerator Inspector
# =============================================================================
# Description:
#   Probes the host machine for CPU, GPU (CUDA/DirectML), NPU, RAM/VRAM,
#   and Windows Copilot+ hardware acceleration capabilities.
#
# File: hardware.py
# Package: src.ai.orchestration
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================

import os
import platform
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.logger import logger


@dataclass
class HardwareProfile:
    """Represents the host computational profile and hardware accelerators."""
    cpu_cores: int = 1
    cpu_arch: str = "x86_64"
    has_cuda: bool = False
    has_directml: bool = False
    has_npu: bool = False
    gpus: List[Dict[str, Any]] = field(default_factory=list)
    ram_gb: float = 0.0
    vram_gb: float = 0.0
    os_name: str = "Windows"
    is_copilot_plus: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to serializable dictionary."""
        return {
            "cpu_cores": self.cpu_cores,
            "cpu_arch": self.cpu_arch,
            "has_cuda": self.has_cuda,
            "has_directml": self.has_directml,
            "has_npu": self.has_npu,
            "gpus": self.gpus,
            "ram_gb": self.ram_gb,
            "vram_gb": self.vram_gb,
            "os_name": self.os_name,
            "is_copilot_plus": self.is_copilot_plus,
        }


def probe_hardware() -> HardwareProfile:
    """Probe host environment for computational accelerators and memory.

    Returns:
        HardwareProfile: Complete hardware and execution provider profile.
    """
    profile = HardwareProfile()
    profile.os_name = platform.system()
    profile.cpu_cores = os.cpu_count() or 1
    profile.cpu_arch = platform.machine()

    # 1. Probe RAM
    try:
        import psutil
        mem = psutil.virtual_memory()
        profile.ram_gb = round(mem.total / (1024 ** 3), 2)
    except Exception:
        profile.ram_gb = 16.0

    # 2. Probe CUDA / NVIDIA GPUs
    try:
        cmd = ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=2,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            profile.has_cuda = True
            for line in proc.stdout.splitlines():
                parts = line.split(",")
                if len(parts) >= 2:
                    name = parts[0].strip()
                    mem_mb = float(parts[1].strip())
                    profile.gpus.append({"name": name, "vram_mb": mem_mb})
                    profile.vram_gb += round(mem_mb / 1024, 2)
    except Exception:
        pass

    # 3. Probe DirectML and ONNX Execution Providers
    try:
        import onnxruntime as ort
        available_providers = ort.get_available_providers()
        if "DmlExecutionProvider" in available_providers:
            profile.has_directml = True
        if "CUDAExecutionProvider" in available_providers:
            profile.has_cuda = True
        if "QNNExecutionProvider" in available_providers or "NpuExecutionProvider" in available_providers:
            profile.has_npu = True
            profile.is_copilot_plus = True
    except Exception:
        # Default DirectML is generally available on Windows 10/11
        if profile.os_name.lower() == "windows":
            profile.has_directml = True

    return profile
