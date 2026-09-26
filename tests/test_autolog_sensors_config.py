# -*- coding: utf-8 -*-
"""Тесты для load_autolog_config — чтение из autolog_sensors.json."""

import json
import tempfile
import pytest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _make_sensors_file(data: dict) -> Path:
    """Создаёт временный autolog_sensors.json и возвращает путь к нему."""
    d = tempfile.mkdtemp()
    cfg_dir = Path(d) / "config"
    cfg_dir.mkdir()
    p = cfg_dir / "autolog_sensors.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


class TestLoadAutologConfig:

    def test_reads_autolog_sensors_json(self):
        """Читает конфиг из autolog_sensors.json."""
        from apps.common.autolog_engine import load_autolog_config
        p = _make_sensors_file({
            "enable_autolog": True,
            "default_interval": "1 minute",
            "loggers": {
                "system_inspector": {"interval": "5 seconds", "enabled": True},
                "hardware_monitor":  {"interval": "5 seconds", "enabled": True},
            }
        })
        result = load_autolog_config(p)
        assert result["enable_autolog"] is True
        assert result["default_interval"] == "1 minute"
        assert "system_inspector" in result["loggers"]
        assert "hardware_monitor" in result["loggers"]

    def test_loggers_have_interval_and_enabled(self):
        """Каждый логгер содержит interval и enabled."""
        from apps.common.autolog_engine import load_autolog_config
        p = _make_sensors_file({
            "enable_autolog": True,
            "default_interval": "1 minute",
            "loggers": {
                "system_inspector": {"interval": "5 seconds", "enabled": True},
                "hardware_monitor":  {"interval": "10 seconds", "enabled": False},
            }
        })
        result = load_autolog_config(p)
        for name, cfg in result["loggers"].items():
            assert "interval" in cfg, f"{name}: нет поля interval"
            assert "enabled" in cfg, f"{name}: нет поля enabled"

    def test_autolog_disabled(self):
        """enable_autolog=false корректно читается."""
        from apps.common.autolog_engine import load_autolog_config
        p = _make_sensors_file({"enable_autolog": False, "loggers": {}})
        result = load_autolog_config(p)
        assert result["enable_autolog"] is False

    def test_fallback_on_missing_file(self):
        """Возвращает дефолтный конфиг если файл не найден."""
        from apps.common.autolog_engine import load_autolog_config
        result = load_autolog_config(Path("nonexistent_xyz_123.json"))
        assert result["enable_autolog"] is True
        assert isinstance(result["loggers"], dict)

    def test_real_autolog_sensors_json_exists(self):
        """apps/windows/telemetry/config.json существует в проекте и содержит все настройки."""
        telemetry_cfg = ROOT / "apps" / "windows" / "telemetry" / "config.json"
        assert telemetry_cfg.exists(), "Файл apps/windows/telemetry/config.json должен существовать"

    def test_real_autolog_sensors_json_valid(self):
        """apps/windows/telemetry/config.json валидный JSON с нужными полями."""
        telemetry_cfg = ROOT / "apps" / "windows" / "telemetry" / "config.json"
        data = json.loads(telemetry_cfg.read_text(encoding="utf-8"))
        assert "enable_autolog" in data, "Должно быть поле enable_autolog"
        assert "loggers" in data, "Должна быть секция loggers"
        assert "sensors" in data, "Должна быть секция sensors"
        assert len(data["loggers"]) > 0, "Логгеры не должны быть пустыми"
        assert len(data["sensors"]) > 0, "Сенсоры не должны быть пустыми"

    def test_dashboard_json_has_no_logging_block(self):
        """apps/windows/telemetry/config.json содержит настройки логгеров и сенсоров."""
        telemetry_cfg = ROOT / "apps" / "windows" / "telemetry" / "config.json"
        data = json.loads(telemetry_cfg.read_text(encoding="utf-8"))
        assert "loggers" in data, "Должна быть секция loggers"
        assert isinstance(data["loggers"], dict), "loggers должен быть словарем"
        assert "sensors" in data, "Должна быть секция sensors"
        assert isinstance(data["sensors"], dict), "sensors должен быть словарем"

    def test_tc_json_has_no_logging_block(self):
        """start_scenarios_config/tc.json не содержит блок logging."""
        data = json.loads((ROOT / "start_scenarios_config" / "tc.json").read_text(encoding="utf-8"))
        assert "logging" not in data
