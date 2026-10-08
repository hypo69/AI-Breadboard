# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Telemetry
# =============================================================================
# Description:
#   Tests for UserManager telemetry batch storage and statistics.
#
# Usage Examples:
#   Python API:
#     from tests.test_telemetry import TestUserManagerTelemetry
#
#     service = TestUserManagerTelemetry()
#
# File: test_telemetry.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 13:36:00
# =============================================================================

"""Тесты телеметрии пользователя и подсистемы временных интервалов SQLite."""

import time
import pytest
from src.user_manager import user_manager
from apps.windows.telemetry.sqlite import TelemetryStorage


class TestUserManagerTelemetry:
    """Тесты пакетного логирования и выборки статистики пользовательской телеметрии."""

    def test_log_telemetry_batch_and_stats(self):
        """Проверка вставки пакета событий телеметрии и агрегации."""
        user_id = 1
        events = [{'action': 'Entered tab tab-chat', 'event_type': 'tab_view', 'tab_name': 'tab-chat', 'target_element': 'tab:tab-chat', 'duration_ms': 0, 'details': {'source': 'test'}}, {'action': 'Left tab tab-chat', 'event_type': 'tab_view', 'tab_name': 'tab-chat', 'target_element': 'tab:tab-chat', 'duration_ms': 15400, 'details': {'transition_to': 'tab-rag'}}, {'action': 'Click: Send Message', 'event_type': 'click', 'tab_name': 'tab-chat', 'target_element': 'button#send-button', 'duration_ms': 0, 'details': {'label': 'Send Message'}}]
        inserted = user_manager.log_telemetry_batch(user_id=user_id, events=events, ip_address='127.0.0.1', user_agent='PyTestClient')
        assert inserted == 3
        stats = user_manager.get_telemetry_stats(days=30, user_id=user_id)
        assert stats['total_events'] >= 3
        assert 'tab-chat' in stats['tab_views']
        assert stats['tab_views']['tab-chat']['count'] >= 2
        assert 'button#send-button' in stats['top_clicks']
        assert len(stats['recent_events']) > 0

    def test_telemetry_time_ranges_filtering(self, tmp_path):
        """Проверка динамического вычисления доступных интервалов по размаху данных в БД."""
        db_file = tmp_path / "test_tel.db"
        storage = TelemetryStorage(db_path=db_file, buffer_mode='direct', read_only=False)

        # 1. При пустой базе доступны только 'seconds' и 'all'
        res_empty = storage.get_telemetry_time_ranges()
        assert res_empty['status'] == 'ok'
        assert 'seconds' in res_empty['available_ids']
        assert 'all' in res_empty['available_ids']
        assert 'months' not in res_empty['available_ids']

        # 2. Добавляем снимок с временем 2 часа назад
        now = time.time()
        with storage._lock, storage._get_connection() as conn:
            conn.execute(
                "INSERT INTO system_snapshots (timestamp, created_at, cpu_total_percent) VALUES (?, ?, ?);",
                (time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now - 7200)), now - 7200, 25.0)
            )
            conn.execute(
                "INSERT INTO system_snapshots (timestamp, created_at, cpu_total_percent) VALUES (?, ?, ?);",
                (time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now)), now, 35.0)
            )
            conn.commit()

        res_2h = storage.get_telemetry_time_ranges()
        # При размахе в 2 часа должны быть: seconds, minutes, hours, all (но НЕ days, weeks, months)
        assert 'seconds' in res_2h['available_ids']
        assert 'minutes' in res_2h['available_ids']
        assert 'hours' in res_2h['available_ids']
        assert 'days' not in res_2h['available_ids']
        assert 'weeks' not in res_2h['available_ids']
        assert 'months' not in res_2h['available_ids']

        # 3. Проверка выборки истории по интервалу
        history_secs = storage.get_history_by_interval('seconds')
        assert len(history_secs) >= 1
        history_all = storage.get_history_by_interval('all')
        assert len(history_all) == 2