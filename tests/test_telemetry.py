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
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Tests for UserManager telemetry batch storage and statistics."""

import pytest
from src.user_manager import user_manager


class TestUserManagerTelemetry:
    """Tests for UserManager telemetry batch storage and statistics."""

    def test_log_telemetry_batch_and_stats(self):
        """Test inserting a batch of telemetry events and reading aggregated stats."""
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