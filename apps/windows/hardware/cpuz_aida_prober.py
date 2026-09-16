# -*- coding: utf-8 -*-
"""CPU-Z and AIDA64 external report parser."""

from __future__ import annotations

import csv
import io
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from src.logger import logger


@dataclass
class HardwareAuditReport:
    """Consolidated hardware audit report."""
    source: str  # CPU-Z, AIDA64, WMI
    cpu_name: str
    cpu_code_name: Optional[str] = None
    cpu_socket: Optional[str] = None
    motherboard_model: Optional[str] = None
    motherboard_chipset: Optional[str] = None
    memory_type: Optional[str] = None
    memory_frequency_mhz: Optional[float] = None
    memory_timings: Optional[str] = None
    raw_sections: Dict[str, Any] = field(default_factory=dict)


class CpuzAidaProber:
    """Probe CPU and motherboard details via CPU-Z or AIDA64."""

    def __init__(self) -> None:
        """Locate executable binaries."""
        self._cpuz_bin = shutil.which("cpuz") or shutil.which("cpuz.exe")
        self._aida64_bin = shutil.which("aida64") or shutil.which("aida64.exe")

    def generate_report(self) -> HardwareAuditReport:
        """Generate audit report from available tool or fallback to WMI."""
        if self._cpuz_bin:
            report = self._run_cpuz()
            if report:
                return report

        if self._aida64_bin:
            report = self._run_aida64()
            if report:
                return report

        return self._wmi_fallback()

    def _run_cpuz(self) -> Optional[HardwareAuditReport]:
        """Run CPU-Z in ghost report mode."""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                report_prefix = os.path.join(tmpdir, "cpuz_out")
                cmd = [str(self._cpuz_bin), f"-txt={report_prefix}"]
                subprocess.run(cmd, capture_output=True, timeout=15)
                txt_path = f"{report_prefix}.txt"
                if os.path.exists(txt_path):
                    with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    return self._parse_cpuz_txt(content)
        except Exception as e:
            logger.error(f"Failed to generate CPU-Z report: {e}")
        return None

    def _parse_cpuz_txt(self, content: str) -> HardwareAuditReport:
        """Parse raw CPU-Z text export."""
        cpu_name = "Unknown CPU"
        socket = None
        code_name = None
        for line in content.splitlines():
            line_str = line.strip()
            if line_str.startswith("Name") and "Specification" not in line_str:
                parts = line_str.split("\t")
                if len(parts) > 1:
                    cpu_name = parts[-1]
            elif "Package (platform ID)" in line_str or "Package" in line_str:
                parts = line_str.split("\t")
                if len(parts) > 1:
                    socket = parts[-1]
            elif "Codename" in line_str:
                parts = line_str.split("\t")
                if len(parts) > 1:
                    code_name = parts[-1]

        return HardwareAuditReport(
            source="CPU-Z",
            cpu_name=cpu_name,
            cpu_code_name=code_name,
            cpu_socket=socket,
        )

    def _run_aida64(self) -> Optional[HardwareAuditReport]:
        """Run AIDA64 silent audit report."""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                csv_path = os.path.join(tmpdir, "aida_report.csv")
                cmd = [str(self._aida64_bin), "/R", csv_path, "/CSV", "/AUDIT", "/SILENT"]
                subprocess.run(cmd, capture_output=True, timeout=20)
                if os.path.exists(csv_path):
                    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    return HardwareAuditReport(
                        source="AIDA64",
                        cpu_name="Audited via AIDA64",
                        raw_sections={"csv_summary": content[:1000]},
                    )
        except Exception as e:
            logger.error(f"Failed to run AIDA64: {e}")
        return None

    def _wmi_fallback(self) -> HardwareAuditReport:
        """Fallback to WMI query."""
        cpu_name = "Generic Windows CPU"
        mobo = "Generic Motherboard"
        try:
            cmd = "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name"
            res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                cpu_name = res.stdout.strip()

            cmd_mobo = "Get-CimInstance Win32_BaseBoard | Select-Object -ExpandProperty Product"
            res_m = subprocess.run(["powershell", "-NoProfile", "-Command", cmd_mobo], capture_output=True, text=True, timeout=5)
            if res_m.returncode == 0 and res_m.stdout.strip():
                mobo = res_m.stdout.strip()
        except Exception as e:
            logger.error(f"WMI processor fallback error: {e}")

        return HardwareAuditReport(
            source="WMI",
            cpu_name=cpu_name,
            motherboard_model=mobo,
        )
