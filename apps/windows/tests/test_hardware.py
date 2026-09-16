# -*- coding: utf-8 -*-
"""Unit tests for hardware diagnostic probers."""

import unittest
from apps.windows.hardware.smartctl_probe import SmartProber, SmartDriveInfo
from apps.windows.hardware.gpu_prober import GpuProber, GpuDeviceTelemetry
from apps.windows.hardware.cpuz_aida_prober import CpuzAidaProber, HardwareAuditReport
from apps.windows.hardware.stress_benchmark import StressBenchmarkEngine, StressTestResult


class TestHardwareProbers(unittest.TestCase):
    """Test hardware probing modules."""

    def test_smartctl_prober(self):
        """Test smartctl scanner."""
        prober = SmartProber()
        drives = prober.scan_drives()
        self.assertIsInstance(drives, list)
        if drives:
            self.assertIsInstance(drives[0], SmartDriveInfo)
            self.assertIsNotNone(drives[0].device)

    def test_gpu_prober(self):
        """Test GPU prober."""
        prober = GpuProber()
        gpus = prober.probe_all()
        self.assertIsInstance(gpus, list)
        if gpus:
            self.assertIsInstance(gpus[0], GpuDeviceTelemetry)
            self.assertIsNotNone(gpus[0].name)

    def test_cpuz_aida_prober(self):
        """Test CPU-Z and AIDA64 prober."""
        prober = CpuzAidaProber()
        report = prober.generate_report()
        self.assertIsInstance(report, HardwareAuditReport)
        self.assertIsNotNone(report.cpu_name)

    def test_stress_benchmark_cpu(self):
        """Test CPU stress benchmark execution."""
        engine = StressBenchmarkEngine()
        res = engine.run_cpu_stress(duration_sec=1)
        self.assertIsInstance(res, StressTestResult)
        self.assertEqual(res.target, "CPU")
        self.assertEqual(res.status, "COMPLETED")


if __name__ == "__main__":
    unittest.main()
