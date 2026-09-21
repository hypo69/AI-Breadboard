# -*- coding: utf-8 -*-
import pytest
from unittest.mock import patch
from apps.windows.core.models import DomainAuditResult
from apps.windows.core.modules.performance_collector import PerformanceCollector


def test_performance_collector_sensors():
    """Тест регистрации сенсоров производительности."""
    collector = PerformanceCollector()
    
    mock_result = DomainAuditResult(
        domain_name="performance",
        title_ru="Производительность",
        status="ok",
        findings=[],
        metrics={
            "cpu_percent": 10.5,
            "memory_percent": 20.0,
            "uptime_hours": 1.5,
        },
        scan_duration_ms=10.0
    )
    
    # Мокаем collect так, чтобы он устанавливал _last_result
    with patch.object(collector, 'collect', side_effect=lambda: setattr(collector, '_last_result', mock_result) or mock_result):
        collector.collect()
        
        # Получаем сенсоры
        sensors = collector.get_sensors()
        
        # Проверяем наличие ожидаемых сенсоров
        sensor_ids = [s.sensor_id for s in sensors]
        assert "perf_cpu_percent" in sensor_ids
        assert "perf_memory_percent" in sensor_ids
        assert "perf_uptime_hours" in sensor_ids
        
        # Проверяем значения
        for s in sensors:
            if s.sensor_id == "perf_cpu_percent":
                assert s.value == 10.5
