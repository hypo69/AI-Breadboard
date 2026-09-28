"""Модульный тест автопереключения тяжелого режима телеметрии в легкий через 5 дней."""
import time
from unittest.mock import patch, MagicMock
import pytest

from apps.windows.telemetry.main import run_telemetry_service, _stop_event

def test_telemetry_autoswitch_heavy_to_light():
    """Проверка логики переключения режима с тяжелого на легкий через 5 дней."""
    _stop_event.clear()
    
    five_days_ago = time.time() - (5 * 24 * 3600.0 + 10.0)
    
    with patch("apps.windows.telemetry.collector.SystemCollector.get_hardware_tree_async", return_value=[]), \
         patch("apps.windows.telemetry.collector.SystemCollector.get_physical_disks_health", return_value=[]), \
         patch("psutil.cpu_percent", return_value=10.0), \
         patch("apps.windows.telemetry.main._stop_event.is_set", side_effect=[False, True]):
        
        with patch("apps.windows.telemetry.main.time.time", return_value=time.time()):
            with patch("apps.windows.telemetry.main.logger.warning") as mock_warn:
                run_telemetry_service(interval=0.01, mode='full')

def test_telemetry_config_manager_heavy_settings(tmp_path):
    """Проверка считывания параметров тяжелого сканирования и автопереключения менеджером конфигурации."""
    from apps.windows.telemetry.telemetry_config import TelemetryConfigManager
    import json

    cfg_mgr = TelemetryConfigManager()
    assert cfg_mgr.get_heavy_disk_scan_interval() == 43200.0
    assert cfg_mgr.get_heavy_mode_max_duration_days() == 5.0
    assert cfg_mgr.is_heavy_auto_switch_enabled() is True

    custom_cfg = tmp_path / "config.json"
    custom_cfg.write_text(json.dumps({
        "heavy_disk_scan_interval_seconds": 21600,
        "heavy_mode_max_duration_days": 3,
        "heavy_mode_auto_switch_enabled": False
    }), encoding="utf-8")

    custom_mgr = TelemetryConfigManager(config_path=str(custom_cfg))
    assert custom_mgr.get_heavy_disk_scan_interval() == 21600.0
    assert custom_mgr.get_heavy_mode_max_duration_days() == 3.0
    assert custom_mgr.is_heavy_auto_switch_enabled() is False

