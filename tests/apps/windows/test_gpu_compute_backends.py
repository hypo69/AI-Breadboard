# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Tests - Test Gpu Compute Backends
# =============================================================================
# Description:
#   Тесты унифицированной модели GPU для NVIDIA, AMD и Intel с поддержкой
#   вычислительных API (CUDA, ROCm/HIP, DirectML, Vulkan, OpenCL, oneAPI)
#   и AI бэкендов в дереве оборудования и телеметрии.
#
# Usage Examples:
#   pytest tests/apps/windows/test_gpu_compute_backends.py -v
#
# File: test_gpu_compute_backends.py
# Project: ai-breadboard
# Package: tests.apps.windows
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 08:42:00
# =============================================================================

import pytest
from unittest.mock import patch, MagicMock
from apps.windows.modules.hardware.gpu_prober import (
    GpuDeviceTelemetry,
    NpuDeviceTelemetry,
    determine_gpu_compute_backends,
)
from apps.windows.telemetry.models import GpuMetrics, NpuMetrics, GpuInventoryInfo
from apps.windows.telemetry.collector import SystemCollector
from apps.windows.api.routers.router_gpu_load import GpuSpecsInfo


class TestGpuComputeBackends:
    """Набор тестов для мульти-вендорной модели GPU, NPU и вычислительных API."""

    def test_nvidia_capabilities(self):
        """Проверка определения возможностей для видеокарт NVIDIA."""
        caps = determine_gpu_compute_backends("NVIDIA", "GeForce RTX 4080")
        assert caps["vendor"] == "NVIDIA"
        assert caps["gpu_type"] == "Discrete"
        assert caps["has_cuda"] is True
        assert caps["has_rocm"] is False
        assert caps["has_oneapi"] is False
        assert caps["has_directml"] is True
        assert caps["has_vulkan"] is True
        assert caps["has_opencl"] is True
        assert "CUDA" in caps["compute_apis"]
        assert "DirectML" in caps["compute_apis"]
        assert "Vulkan" in caps["compute_apis"]
        assert "OpenCL" in caps["compute_apis"]
        assert "ROCm / HIP" not in caps["compute_apis"]
        assert "CUDA" in caps["ai_backends"]
        assert "CPU" in caps["ai_backends"]

    def test_amd_capabilities(self):
        """Проверка определения возможностей для видеокарт AMD (Radeon)."""
        caps = determine_gpu_compute_backends("AMD", "Radeon RX 6800")
        assert caps["vendor"] == "AMD"
        assert caps["gpu_type"] == "Discrete"
        assert caps["has_cuda"] is False
        assert caps["has_rocm"] is True
        assert caps["has_oneapi"] is False
        assert caps["has_directml"] is True
        assert caps["has_vulkan"] is True
        assert caps["has_opencl"] is True
        assert "CUDA" not in caps["compute_apis"]
        assert "ROCm / HIP" in caps["compute_apis"]
        assert "DirectML" in caps["compute_apis"]
        assert "Vulkan" in caps["compute_apis"]
        assert "OpenCL" in caps["compute_apis"]
        assert "ROCm / HIP" in caps["ai_backends"]
        assert "DirectML" in caps["ai_backends"]
        assert "CPU" in caps["ai_backends"]

    def test_intel_capabilities(self):
        """Проверка определения возможностей для видеокарт Intel (Arc / UHD)."""
        caps_arc = determine_gpu_compute_backends("Intel", "Intel Arc A770")
        assert caps_arc["vendor"] == "Intel"
        assert caps_arc["gpu_type"] == "Discrete"
        assert caps_arc["has_cuda"] is False
        assert caps_arc["has_rocm"] is False
        assert caps_arc["has_oneapi"] is True
        assert caps_arc["has_directml"] is True
        assert caps_arc["has_vulkan"] is True
        assert caps_arc["has_opencl"] is True
        assert "oneAPI" in caps_arc["compute_apis"]
        assert "DirectML" in caps_arc["compute_apis"]
        assert "Vulkan" in caps_arc["compute_apis"]
        assert "OpenCL" in caps_arc["compute_apis"]
        assert "Intel GPU runtime (oneAPI/OpenVINO)" in caps_arc["ai_backends"]
        assert "DirectML" in caps_arc["ai_backends"]
        assert "CPU" in caps_arc["ai_backends"]

        caps_uhd = determine_gpu_compute_backends("Intel", "Intel UHD Graphics 630", memory_total_mb=128.0)
        assert caps_uhd["vendor"] == "Intel"
        assert caps_uhd["gpu_type"] == "Integrated"
        assert caps_uhd["memory_type"] == "Shared System Memory"
        assert caps_uhd["dedicated_memory_mb"] == 128.0
        assert caps_uhd["shared_memory_mb"] > 0

    def test_collector_gpu_metrics_unified(self):
        """Проверка сбора метрик SystemCollector с мульти-вендорными GPU."""
        collector = SystemCollector()
        mock_devices = [
            GpuDeviceTelemetry(
                index=0,
                name="Radeon RX 6800",
                vendor="AMD",
                driver_version="31.0.12027.7000",
                memory_total_mb=16384.0,
                memory_used_mb=2048.0,
                utilization_gpu_pct=15.0,
                temperature_gpu_c=45.0,
            ),
            GpuDeviceTelemetry(
                index=1,
                name="GeForce RTX 3080",
                vendor="NVIDIA",
                driver_version="551.86",
                memory_total_mb=10240.0,
                memory_used_mb=4096.0,
                utilization_gpu_pct=60.0,
                temperature_gpu_c=65.0,
            ),
            GpuDeviceTelemetry(
                index=2,
                name="Intel UHD Graphics 630",
                vendor="Intel",
                driver_version="30.0.100.9999",
                memory_total_mb=128.0,
                memory_used_mb=64.0,
                utilization_gpu_pct=5.0,
                temperature_gpu_c=40.0,
            ),
        ]

        with patch("apps.windows.modules.hardware.gpu_prober.GpuProber.probe_all", return_value=mock_devices):
            gpus = collector.get_gpu_metrics()
            assert len(gpus) == 3

            # AMD GPU
            amd_gpu = gpus[0]
            assert amd_gpu.name == "Radeon RX 6800"
            assert amd_gpu.vendor == "AMD"
            assert amd_gpu.gpu_type == "Discrete"
            assert amd_gpu.memory_total_gb == 16.0
            assert amd_gpu.has_cuda is False
            assert amd_gpu.has_rocm is True
            assert amd_gpu.has_directml is True
            assert "ROCm / HIP" in amd_gpu.compute_apis

            # NVIDIA GPU
            nvidia_gpu = gpus[1]
            assert nvidia_gpu.name == "GeForce RTX 3080"
            assert nvidia_gpu.vendor == "NVIDIA"
            assert nvidia_gpu.gpu_type == "Discrete"
            assert nvidia_gpu.memory_total_gb == 10.0
            assert nvidia_gpu.has_cuda is True
            assert nvidia_gpu.has_rocm is False
            assert "CUDA" in nvidia_gpu.compute_apis

            # Intel Integrated GPU
            intel_gpu = gpus[2]
            assert intel_gpu.name == "Intel UHD Graphics 630"
            assert intel_gpu.vendor == "Intel"
            assert intel_gpu.gpu_type == "Integrated"
            assert intel_gpu.memory_type == "Shared System Memory"
            assert intel_gpu.has_oneapi is True
            assert "oneAPI" in intel_gpu.compute_apis

    @pytest.mark.asyncio
    async def test_hardware_tree_node_gpu_and_npu_properties(self):
        """Проверка формирования свойств HardwareNode для GPU и NPU."""
        collector = SystemCollector()
        mock_gpu = GpuMetrics(
            name="Intel UHD Graphics 630",
            vendor="Intel",
            gpu_type="Integrated",
            memory_total_gb=0.13,
            memory_used_gb=0.06,
            dedicated_memory_mb=128.0,
            shared_memory_mb=8192.0,
            memory_type="Shared System Memory",
            directx_version="DirectX 12",
            load_percent=10.0,
            temperature_celsius=42.0,
            has_cuda=False,
            has_rocm=False,
            has_oneapi=True,
            has_directml=True,
            has_vulkan=True,
            has_opencl=True,
            compute_apis=["DirectML", "Vulkan", "OpenCL", "oneAPI"],
            ai_backends=["DirectML", "Intel GPU runtime (oneAPI/OpenVINO)", "CPU"],
        )
        mock_npu = NpuMetrics(
            name="Intel AI Boost",
            vendor="Intel",
            driver_version="32.0.100.1",
            pnp_device_id=r"PCI\VEN_8086&DEV_7D1D",
            status="OK (Активно)",
            tops=11.5,
        )

        with patch.object(collector, "get_gpu_metrics", return_value=[mock_gpu]), \
             patch.object(collector, "get_npu_metrics", return_value=[mock_npu]), \
             patch.object(collector, "get_monitors", return_value=[]), \
             patch.object(collector, "get_system_identity", return_value={"hostname": "INTEL-TEST"}), \
             patch.object(collector, "get_cpu_metrics", return_value=MagicMock(model="Intel Core Ultra 7", physical_cores=16, logical_cores=22, total_percent=10.0, frequency_mhz=3800.0)), \
             patch.object(collector, "get_memory_metrics", return_value=MagicMock(total_gb=32.0, used_gb=12.0, available_gb=20.0, percent=37.5, swap_total_gb=16.0, swap_used_gb=2.0, swap_percent=12.5)), \
             patch.object(collector, "get_disk_metrics", return_value=([], MagicMock())), \
             patch.object(collector, "get_network_metrics", return_value=[]), \
             patch.object(collector, "get_updates_info", return_value=MagicMock(status="Up to date", installed_kb_count=10, recent_hotfixes=[], latest_installed_on="")):

            tree = await collector.get_hardware_tree_async(force=True)
            gpu_nodes = [n for n in tree if n.category == "Display Adapter"]
            assert len(gpu_nodes) == 1

            props = gpu_nodes[0].properties
            assert props["Индекс устройства"] == 0
            assert props["Модель видеокарты"] == "Intel UHD Graphics 630"
            assert props["Производитель (Вендор)"] == "Intel"
            assert props["Тип GPU"] == "Integrated"
            assert props["Выделенная VRAM"] == "128 MB"
            assert props["Shared GPU Memory"] == "8.0 GB"
            assert props["Тип памяти"] == "Shared System Memory"
            assert props["Поддержка DirectX"] == "DirectX 12"
            assert props["Поддержка CUDA"] == "Нет"
            assert props["Поддержка ROCm"] == "Нет"
            assert props["Поддержка DirectML"] == "Да"
            assert props["Поддержка Vulkan"] == "Да"
            assert props["Поддержка OpenCL"] == "Да"
            assert props["Поддержка oneAPI"] == "Да"
            assert props["Вычислительные API"] == "DirectML, Vulkan, OpenCL, oneAPI"
            assert props["AI Бэкенды"] == "DirectML, Intel GPU runtime (oneAPI/OpenVINO), CPU"
            assert props["Статус устройства"] == "OK (Активно)"

            # NPU Node
            npu_nodes = [n for n in tree if n.category == "Neural Processing Unit (NPU)"]
            assert len(npu_nodes) == 1
            npu_props = npu_nodes[0].properties
            assert npu_props["Индекс устройства"] == 0
            assert npu_props["Модель NPU"] == "Intel AI Boost"
            assert npu_props["Производитель (Вендор)"] == "Intel"
            assert npu_props["Тип устройства"] == "Нейропроцессор (NPU / AI Accelerator)"
            assert npu_props["Версия драйвера"] == "32.0.100.1"
            assert npu_props["Производительность (TOPS)"] == "11.5 TOPS"
            assert npu_props["Статус устройства"] == "OK (Активно)"

    def test_gpu_specs_info_model(self):
        """Проверка модели GpuSpecsInfo с новыми полями бэкендов."""
        specs = GpuSpecsInfo(
            name="Radeon RX 6800",
            vendor="AMD",
            vram_gb=16.0,
            cuda_supported=False,
            rocm_supported=True,
            oneapi_supported=False,
            directml_supported=True,
            vulkan_supported=True,
            opencl_supported=True,
            compute_apis=["ROCm / HIP", "DirectML", "Vulkan", "OpenCL"],
            ai_backends=["ROCm / HIP", "DirectML", "Vulkan", "CPU"],
        )
        assert specs.rocm_supported is True
        assert specs.cuda_supported is False
        assert "ROCm / HIP" in specs.compute_apis

