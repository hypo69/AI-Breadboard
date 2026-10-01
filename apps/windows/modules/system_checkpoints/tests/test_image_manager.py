# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules System_Checkpoints Tests - Test Image Manager
# =============================================================================
# Description:
#   Тесты менеджера WIM-образов Windows и работы с DISM.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.system_checkpoints.tests.test_image_manager import test_build_capture_command
#
#     res = test_build_capture_command()
#
# File: test_image_manager.py
# Project: ai-breadboard
# Package: apps.windows.modules.system_checkpoints.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Тесты менеджера WIM-образов Windows и работы с DISM."""

from pathlib import Path
from unittest.mock import MagicMock, patch
from apps.windows.system_checkpoints.core.image_manager import SystemImageManager


def test_build_capture_command():
    """Проверка генерации команды захвата WIM через DISM."""
    mgr = SystemImageManager(compress_level="fast")
    cmd = mgr.build_capture_command(
        source_drive="C:",
        image_path="C:\\Recovery\\test.wim",
        name="Test Image",
        description="Test description",
        append=False,
    )
    cmd_str = " ".join(cmd)
    assert "dism.exe" in cmd_str
    assert "/Capture-Image" in cmd_str
    assert "/ImageFile:C:\\Recovery\\test.wim" in cmd_str
    assert "/CaptureDir:C:\\" in cmd_str
    assert "/Compress:fast" in cmd_str
    assert "/CheckIntegrity" in cmd_str


def test_build_append_command():
    """Проверка генерации команды добавления индекса в существующий WIM."""
    mgr = SystemImageManager()
    cmd = mgr.build_capture_command(
        source_drive="C:",
        image_path="C:\\Recovery\\continuous.wim",
        name="Checkpoint 2",
        description="Periodic index",
        append=True,
    )
    cmd_str = " ".join(cmd)
    assert "/Append-Image" in cmd_str
    assert "/Compress" not in cmd_str  # Append не меняет тип сжатия существующего WIM


def test_create_baseline_image_dry_run(tmp_path):
    """Проверка симуляции создания базового эталонного образа."""
    mgr = SystemImageManager(default_dir=str(tmp_path))
    res = mgr.create_baseline_image(
        source_drive="C:",
        destination_dir=str(tmp_path),
        image_name="Recovery_Baseline_Test.wim",
        dry_run=True,
    )
    assert res["success"] is True
    assert res["dry_run"] is True
    assert res["is_baseline"] is True
    assert "Recovery_Baseline_Test.wim" in res["target_file"]


def test_create_periodic_checkpoint_dry_run(tmp_path):
    """Проверка симуляции создания периодической контрольной точки."""
    mgr = SystemImageManager(default_dir=str(tmp_path))
    res = mgr.create_periodic_checkpoint(
        source_drive="C:",
        destination_dir=str(tmp_path),
        image_name="Recovery_Periodic.wim",
        dry_run=True,
    )
    assert res["success"] is True
    assert res["dry_run"] is True
    assert res["is_append"] is False


def test_scan_recovery_images_mock(tmp_path):
    """Проверка сканирования директории на наличие WIM-файлов."""
    wim_file = tmp_path / "Recovery_2026-09-30_Baseline.wim"
    wim_file.write_bytes(b"MSWIM mock content")

    mgr = SystemImageManager(default_dir=str(tmp_path))
    found = mgr.scan_recovery_images(custom_directories=[str(tmp_path)])
    assert len(found) >= 1
    baseline_match = [f for f in found if f.is_baseline]
    assert len(baseline_match) >= 1
