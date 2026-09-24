# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for apps.windows.network
# =============================================================================
# Description:
#   Unit tests for Network Terminal state management, TUI rendering,
#   and FastAPI router integration in apps.windows.network.
#
# File: test_apps_network.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for apps.windows.network package."""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from apps.windows.network import (
    NetworkTerminalState,
    render_ui,
    init_router,
)
from apps.tshark.models import PacketSummary


class TestNetworkTerminalApp:
    """Test suite for apps.windows.network components."""

    def test_state_initialization(self):
        """State should initialize with clean buffers and default interface."""
        state = NetworkTerminalState(interface="1", display_filter="tcp")
        assert state.interface == "1"
        assert state.display_filter == "tcp"
        assert state.total_packets_captured == 0
        assert len(state.packet_buffer) == 0

    def test_add_packet_updates_stats(self):
        """Adding packets should update sliding window and protocol counts."""
        state = NetworkTerminalState(interface="1", max_buffer_packets=10)
        pkt = PacketSummary(
            packet_number=1,
            timestamp="2026-09-12T21:00:00Z",
            source="192.168.1.10",
            destination="1.1.1.1",
            protocol="TCP",
            length=150,
            source_port=54321,
            destination_port=443,
            info="TLS Client Hello",
        )
        state.add_packet(pkt)
        assert state.total_packets_captured == 1
        assert state.total_bytes_captured == 150
        assert state.protocol_counts.get("TCP") == 1
        assert len(state.packet_buffer) == 1

        stats = state.compute_stats()
        assert stats.total_packets == 1
        assert stats.total_bytes == 150

    def test_sliding_window_bound(self):
        """Packet buffer should respect max_buffer_packets sliding window."""
        state = NetworkTerminalState(interface="1", max_buffer_packets=5)
        for i in range(10):
            state.add_packet(
                PacketSummary(
                    packet_number=i,
                    source="192.168.1.1",
                    destination="8.8.8.8",
                    protocol="UDP",
                    length=60,
                )
            )
        assert state.total_packets_captured == 10
        assert len(state.packet_buffer) == 5

    def test_render_ui_layout(self):
        """Rich UI layout generation should succeed without exceptions."""
        from apps.windows.network.tui import RICH_AVAILABLE

        state = NetworkTerminalState(interface="1")
        state.add_packet(
            PacketSummary(
                packet_number=1,
                source="10.0.0.1",
                destination="10.0.0.2",
                protocol="TCP",
                length=64,
            )
        )
        layout = render_ui(state)
        if RICH_AVAILABLE:
            assert layout is not None
        else:
            assert layout is None


class TestNetworkFastAPIRouter:
    """Test suite for Network Terminal FastAPI router endpoints."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client with network router."""
        app = FastAPI()
        app.include_router(init_router())
        return TestClient(app)

    def test_get_status(self, client):
        """GET /api/network/status returns status dict."""
        resp = client.get("/api/network/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "interface" in data
        assert "total_packets" in data
