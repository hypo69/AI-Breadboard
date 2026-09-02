# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows AI Component and System Model Probe
# =============================================================================
# Description:
#   Probes the host operating system for Windows 11 AI Components, Windows App SDK,
#   Phi Silica, and Windows ML hardware acceleration availability.
#
# File: probe.py
# Package: core.ai.providers.windows_ai
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================

import os
import platform
import subprocess
from typing import Any, Dict, List
from core.logger import logger


def is_windows_os() -> bool:
    """Check if current operating system is Windows."""
    return platform.system().lower() == "windows"


def probe_windows_ai_components() -> Dict[str, Any]:
    """Probe host for installed Windows AI components and system models.

    Checks:
    - OS version (Windows 11 build 26100+ for Copilot+ AI components)
    - Windows App SDK / WinRT AI runtime presence
    - System AI capabilities (Phi Silica, OCR, Image Description, Super Resolution)

    Returns:
        Dict[str, Any]: Structured discovery dictionary with component status.
    """
    result: Dict[str, Any] = {
        "available": False,
        "os_version": platform.version(),
        "is_windows_11": False,
        "components": [],
        "phi_silica_available": False,
        "ocr_available": False,
        "vision_available": False,
        "details": "Windows AI components are not installed on this system.",
    }

    if not is_windows_os():
        result["details"] = "Operating system is not Windows."
        return result

    try:
        # Check Windows 11
        release = platform.release()
        if release == "11" or (release == "10" and int(platform.version().split(".")[-1]) >= 22000):
            result["is_windows_11"] = True

        # Check for installed AI components via PowerShell query if on Windows
        # We query packages safely with a short timeout
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-AppxPackage -Name '*Microsoft.Windows.AI*' | Select-Object -ExpandProperty Name",
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=4,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        if proc.returncode == 0 and proc.stdout.strip():
            packages = [p.strip() for p in proc.stdout.splitlines() if p.strip()]
            result["components"] = packages
            if packages:
                result["available"] = True
                result["details"] = f"Found {len(packages)} Windows AI packages installed."
                for pkg in packages:
                    pkg_l = pkg.lower()
                    if "silica" in pkg_l or "generative" in pkg_l:
                        result["phi_silica_available"] = True
                    if "ocr" in pkg_l:
                        result["ocr_available"] = True
                    if "vision" in pkg_l or "imaging" in pkg_l:
                        result["vision_available"] = True
        else:
            result["details"] = "There are no AI components currently installed in Windows."

    except Exception as e:
        logger.debug(f"[WindowsAIProbe] Probe check completed with fallback: {e}")
        result["details"] = f"Probe executed (no active AI components detected): {e}"

    return result
