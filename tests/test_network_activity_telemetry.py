# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Process Network Activity Telemetry
# =============================================================================
# Description:
#   Тесты для проверки сбора сетевой активности процессов, расчета переданного
#   и скачанного объема данных за измеряемый период, скорости и отображения в UI.
#
# File: test_network_activity_telemetry.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from pathlib import Path
from unittest.mock import patch, MagicMock
import time
import pytest

from apps.windows.telemetry.models import ProcessNetworkActivity
from apps.windows.telemetry.collector import SystemCollector


def test_process_network_activity_model_fields():
    """Проверяет наличие полей замера объема скачанного/отправленного трафика в модели."""
    act = ProcessNetworkActivity(
        pid=1234,
        name="chrome.exe",
        user="SYSTEM",
        local_address="192.168.1.10:54321",
        remote_address="142.250.180.206:443",
        protocol="TCP",
        status="ESTABLISHED",
        is_internet=True,
        service_type="HTTPS",
        sent_kb=10240.0,
        recv_kb=51200.0,
        delta_sent_kb=128.5,
        delta_recv_kb=1024.0,
        sent_rate_kbs=64.25,
        recv_rate_kbs=512.0,
        sent_summary="HTTPS запросы",
        recv_summary="Веб-контент и видеопоток",
    )
    assert act.pid == 1234
    assert act.name == "chrome.exe"
    assert act.sent_kb == 10240.0
    assert act.recv_kb == 51200.0
    assert act.delta_sent_kb == 128.5
    assert act.delta_recv_kb == 1024.0
    assert act.sent_rate_kbs == 64.25
    assert act.recv_rate_kbs == 512.0


def test_collector_process_network_activity_delta_calculation():
    """Проверяет расчет дельты переданного/скачанного объема между замерами в SystemCollector."""
    collector = SystemCollector()

    # Симулируем соединение psutil
    mock_conn = MagicMock()
    mock_conn.pid = 9999
    mock_conn.laddr = MagicMock(ip="127.0.0.1", port=12345)
    mock_conn.raddr = MagicMock(ip="8.8.8.8", port=443)
    mock_conn.type = 1  # SOCK_STREAM
    mock_conn.status = "ESTABLISHED"

    mock_io_1 = MagicMock(read_bytes=1024 * 100, write_bytes=1024 * 50)
    mock_io_2 = MagicMock(read_bytes=1024 * 200, write_bytes=1024 * 90)

    mock_proc = MagicMock()
    mock_proc.name.return_value = "curl.exe"
    mock_proc.username.return_value = "TestUser"
    mock_proc.io_counters.return_value = mock_io_1

    with patch("apps.windows.telemetry.collector.psutil.net_connections", return_value=[mock_conn]), \
         patch("apps.windows.telemetry.collector.psutil.Process", return_value=mock_proc):
        
        # Первый замер
        res1 = collector.get_process_network_activity(limit=10)
        assert len(res1) == 1
        assert res1[0].name == "curl.exe"
        assert res1[0].sent_kb == 50.0
        assert res1[0].recv_kb == 100.0
        assert res1[0].delta_sent_kb == 0.0
        assert res1[0].delta_recv_kb == 0.0

        # Второй замер с новыми объемами трафика
        time.sleep(0.05)
        mock_proc.io_counters.return_value = mock_io_2
        res2 = collector.get_process_network_activity(limit=10)
        assert len(res2) == 1
        assert res2[0].sent_kb == 90.0
        assert res2[0].recv_kb == 200.0
        assert res2[0].delta_sent_kb == 40.0
        assert res2[0].delta_recv_kb == 100.0
        assert res2[0].sent_rate_kbs >= 0.0
        assert res2[0].recv_rate_kbs >= 0.0


def test_system_inspector_html_contains_traffic_period_columns():
    """Проверяет наличие столбцов и индикаторов трафика за период в index.html вкладки."""
    html_path = Path("src/api/webgui/system_inspector_tab/index.html")
    assert html_path.exists(), "Файл index.html вкладки system_inspector_tab не найден"
    content = html_path.read_text(encoding="utf-8")

    assert "Отправка (За период / Всего / Данные)" in content
    assert "Прием (Скачано за период / Всего / Данные)" in content
    assert "sys-net-tbody" in content
    assert "Период замера" in content


def test_system_inspector_main_js_contains_delta_rendering():
    """Проверяет наличие логики рендеринга дельты трафика и суммарного объема в main.js."""
    js_path = Path("src/api/webgui/system_inspector_tab/main.js")
    assert js_path.exists(), "Файл main.js вкладки system_inspector_tab не найден"
    content = js_path.read_text(encoding="utf-8")

    assert "delta_sent_kb" in content
    assert "delta_recv_kb" in content
    assert "formatNetKb" in content
    assert "formatNetRate" in content
    assert "Отправлено за измеряемый период" in content
    assert "Скачано/получено за измеряемый период" in content
