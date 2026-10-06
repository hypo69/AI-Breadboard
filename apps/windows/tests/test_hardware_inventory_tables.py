# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Sqlite - Hardware Inventory Tests
# =============================================================================
# Description:
#   Модульные тесты для нормализованных таблиц паспортов и телеметрии CPU, RAM (SPD), GPU и Network.
#
# File: test_hardware_inventory_tables.py
# Project: ai-breadboard
# Package: apps.windows.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 02:00:00
# =============================================================================

import gc
import tempfile
import pytest
from pathlib import Path

from apps.windows.telemetry.sqlite.storage import TelemetryStorage
from apps.windows.telemetry.models import (
    CpuInventoryInfo,
    CpuTelemetrySample,
    RamModuleInventoryInfo,
    RamTelemetrySample,
    GpuInventoryInfo,
    GpuTelemetrySample,
    NetworkAdapterInventoryInfo,
    NetworkAdapterSample,
)


@pytest.fixture
def temp_storage():
    """Создает временное хранилище TelemetryStorage для изоляции тестов."""
    tmpdir = tempfile.mkdtemp()
    db_path = Path(tmpdir) / "test_hardware_telemetry.db"
    storage = TelemetryStorage(
        db_path=db_path,
        buffer_mode='direct',
        auto_flush=False,
    )
    yield storage
    storage.close()
    gc.collect()


def test_cpu_inventory_and_samples(temp_storage):
    """Проверка сохранения паспорта процессора и сэмплов телеметрии."""
    cpu = CpuInventoryInfo(
        processor_id=0,
        name="AMD Ryzen 9 7950X 16-Core Processor",
        vendor="AuthenticAMD",
        architecture="x86_64",
        physical_cores=16,
        logical_cores=32,
        base_frequency_mhz=4500.0,
        max_frequency_mhz=5700.0,
        l2_cache_kb=16384,
        l3_cache_kb=65536,
        socket="AM5",
        features=["SSE4.2", "AVX2", "AVX-512"],
    )

    temp_storage.save_cpu_inventory(cpu)
    items = temp_storage.get_cpu_inventory(processor_id=0)
    assert len(items) == 1
    assert items[0]["name"] == "AMD Ryzen 9 7950X 16-Core Processor"
    assert items[0]["physical_cores"] == 16
    assert items[0]["vendor"] == "AuthenticAMD"

    # Проверка UPSERT (обновление частоты)
    cpu.max_frequency_mhz = 5850.0
    temp_storage.save_cpu_inventory(cpu)
    items_upd = temp_storage.get_cpu_inventory(processor_id=0)
    assert len(items_upd) == 1
    assert items_upd[0]["max_frequency_mhz"] == 5850.0

    sample = CpuTelemetrySample(
        processor_id=0,
        total_percent=24.5,
        user_percent=18.2,
        kernel_percent=6.3,
        frequency_mhz=4850.0,
        temperature_c=58.2,
        package_power_w=95.4,
        core_utilization=[20.0, 30.0, 15.0, 25.0],
        core_temperatures=[55.0, 58.0, 56.5, 60.1],
    )
    temp_storage.save_cpu_telemetry_sample(sample)
    samples = temp_storage.get_cpu_telemetry_samples(processor_id=0)
    assert len(samples) == 1
    assert samples[0]["total_percent"] == 24.5
    assert samples[0]["temperature_c"] == 58.2


def test_ram_module_inventory_and_samples(temp_storage):
    """Проверка сохранения паспорта планок памяти (SPD) и сэмплов RAM."""
    mod1 = RamModuleInventoryInfo(
        slot_id=0,
        bank_label="BANK 0",
        device_locator="DIMM_A2",
        serial_number="DDR5-GKILL-00123",
        part_number="F5-6000J3038F16G",
        manufacturer="G.Skill",
        capacity_bytes=17179869184,
        capacity_gb=16.0,
        speed_mhz=6000,
        memory_type="DDR5",
        form_factor="DIMM",
        configured_voltage=1.35,
    )
    mod2 = RamModuleInventoryInfo(
        slot_id=1,
        bank_label="BANK 1",
        device_locator="DIMM_B2",
        serial_number="DDR5-GKILL-00124",
        part_number="F5-6000J3038F16G",
        manufacturer="G.Skill",
        capacity_bytes=17179869184,
        capacity_gb=16.0,
        speed_mhz=6000,
        memory_type="DDR5",
        form_factor="DIMM",
        configured_voltage=1.35,
    )

    temp_storage.save_ram_module_inventory(mod1)
    temp_storage.save_ram_module_inventory(mod2)

    mods = temp_storage.get_ram_module_inventory()
    assert len(mods) == 2
    assert mods[0]["serial_number"] == "DDR5-GKILL-00123"
    assert mods[0]["manufacturer"] == "G.Skill"
    assert mods[1]["device_locator"] == "DIMM_B2"

    ram_sample = RamTelemetrySample(
        total_bytes=34359738368,
        total_gb=32.0,
        used_bytes=12884901888,
        used_gb=12.0,
        available_bytes=21474836480,
        available_gb=20.0,
        percent_used=37.5,
        swap_total_gb=36.0,
        swap_used_gb=4.5,
        swap_percent=12.5,
        pool_paged_mb=650.0,
        pool_nonpaged_mb=480.0,
    )
    temp_storage.save_ram_telemetry_sample(ram_sample)
    samples = temp_storage.get_ram_telemetry_samples()
    assert len(samples) == 1
    assert samples[0]["total_gb"] == 32.0
    assert samples[0]["percent_used"] == 37.5


def test_gpu_inventory_and_samples(temp_storage):
    """Проверка паспорта GPU и сэмплов телеметрии нагрузки/памяти."""
    gpu = GpuInventoryInfo(
        gpu_id=0,
        pci_device_id="PCI\\VEN_10DE&DEV_2684&SUBSYS_00000000&REV_A1",
        name="NVIDIA GeForce RTX 4090",
        vendor="NVIDIA",
        driver_version="555.99",
        driver_date="2026-05-15",
        vram_bytes=25769803776,
        vram_gb=24.0,
        pci_bus_id="0000:01:00.0",
        bios_version="95.02.18.00.01",
        cuda_cores=16384,
        directml_supported=True,
    )

    temp_storage.save_gpu_inventory(gpu)
    gpus = temp_storage.get_gpu_inventory(gpu_id=0)
    assert len(gpus) == 1
    assert gpus[0]["name"] == "NVIDIA GeForce RTX 4090"
    assert gpus[0]["vram_gb"] == 24.0
    assert gpus[0]["pci_device_id"] == "PCI\\VEN_10DE&DEV_2684&SUBSYS_00000000&REV_A1"

    gpu_sample = GpuTelemetrySample(
        gpu_id=0,
        name="NVIDIA GeForce RTX 4090",
        load_percent=68.5,
        memory_used_mb=8192.0,
        memory_total_mb=24576.0,
        memory_percent=33.3,
        temperature_gpu_c=62.0,
        temperature_memory_c=68.0,
        fan_speed_pct=45.0,
        power_draw_w=280.5,
        clock_graphics_mhz=2520.0,
        clock_memory_mhz=10500.0,
    )
    temp_storage.save_gpu_telemetry_sample(gpu_sample)
    samples = temp_storage.get_gpu_telemetry_samples(gpu_id=0)
    assert len(samples) == 1
    assert samples[0]["load_percent"] == 68.5
    assert samples[0]["temperature_gpu_c"] == 62.0
    assert samples[0]["power_draw_w"] == 280.5


def test_network_adapter_inventory_and_samples(temp_storage):
    """Проверка паспорта сетевых интерфейсов и показателей трафика."""
    adapter = NetworkAdapterInventoryInfo(
        adapter_id=1,
        adapter_guid="{98765432-1234-5678-ABCD-EF0123456789}",
        name="Intel(R) Ethernet Controller I225-V",
        interface_name="Ethernet 1",
        mac_address="00:1A:2B:3C:4D:5E",
        adapter_type="Ethernet",
        is_physical=True,
        is_wireless=False,
        max_speed_mbps=2500,
        driver_name="e2fexpress",
        driver_version="1.1.4.38",
    )

    temp_storage.save_network_adapter_inventory(adapter)
    adapters = temp_storage.get_network_adapter_inventory()
    assert len(adapters) == 1
    assert adapters[0]["name"] == "Intel(R) Ethernet Controller I225-V"
    assert adapters[0]["mac_address"] == "00:1A:2B:3C:4D:5E"
    assert adapters[0]["max_speed_mbps"] == 2500

    net_sample = NetworkAdapterSample(
        adapter_name="Ethernet 1",
        bytes_recv_sec=52428800.0,
        bytes_sent_sec=10485760.0,
        packets_recv_sec=35000.0,
        packets_sent_sec=12000.0,
        errors_in_sec=0.0,
        errors_out_sec=0.0,
        link_speed_mbps=2500,
        is_connected=True,
    )
    temp_storage.save_network_adapter_sample(net_sample)
    samples = temp_storage.get_network_adapter_samples(adapter_name="Ethernet 1")
    assert len(samples) == 1
    assert samples[0]["bytes_recv_sec"] == 52428800.0
    assert samples[0]["link_speed_mbps"] == 2500


def test_maintenance_storage_stats_and_cleanup(temp_storage):
    """Проверка подсчета статистики по всем таблицам оборудования и очистки."""
    # Сохраняем по одной записи в каждую таблицу
    temp_storage.save_cpu_inventory(CpuInventoryInfo(name="Test CPU"))
    temp_storage.save_ram_module_inventory(RamModuleInventoryInfo(serial_number="RAM-TEST-1"))
    temp_storage.save_gpu_inventory(GpuInventoryInfo(name="Test GPU", pci_device_id="PCI_TEST_1"))
    temp_storage.save_network_adapter_inventory(NetworkAdapterInventoryInfo(adapter_guid="GUID_TEST_1", name="Test Net"))

    temp_storage.save_cpu_telemetry_sample(CpuTelemetrySample(total_percent=10.0))
    temp_storage.save_ram_telemetry_sample(RamTelemetrySample(total_gb=16.0))
    temp_storage.save_gpu_telemetry_sample(GpuTelemetrySample(name="Test GPU", load_percent=50.0))
    temp_storage.save_network_adapter_sample(NetworkAdapterSample(adapter_name="Test Net", bytes_recv_sec=100.0))

    stats = temp_storage.get_storage_stats()
    assert stats["cpu_inventory_count"] >= 1
    assert stats["ram_module_inventory_count"] >= 1
    assert stats["gpu_inventory_count"] >= 1
    assert stats["network_adapter_inventory_count"] >= 1
    assert stats["cpu_samples_count"] >= 1
    assert stats["ram_samples_count"] >= 1
    assert stats["gpu_samples_count"] >= 1
    assert stats["network_samples_count"] >= 1
