# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: IFTTT Plugin Unit Tests
# =============================================================================
# Description:
#   Unit tests for IFTTTPlugin lifecycle, tools schema, actions, configuration,
#   and handle streaming.
#
# Examples:
#   pytest plugins/ifttt/tests/test_plugin.py -v
#
# File: test_plugin.py
# Project: ai-breadboard
# Package: plugins.ifttt.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from plugins.ifttt import IFTTTPlugin, plugin


class TestIFTTTPlugin:
    """Test suite for IFTTTPlugin implementation."""

    def test_plugin_instantiation_and_manifest(self):
        """Test plugin factory creation and manifest metadata (Happy Path)."""
        # --- Arrange & Act ---
        p: IFTTTPlugin = plugin()
        manifest: dict = p.get_manifest(lang="en")

        # --- Assert ---
        assert p.name == "ifttt", f"Expected plugin name 'ifttt', got {p.name}"
        assert manifest["name"] == "ifttt", "Manifest name mismatch"
        assert manifest["category"] == "automation", "Category should be automation"
        assert len(p.get_tools()) >= 1, "Plugin must provide at least one tool"
        assert len(p.get_actions()) >= 2, "Plugin must provide test_connection and trigger_event actions"
        assert len(p.get_config_fields()) >= 2, "Plugin must provide config fields"

    def test_plugin_config_update(self):
        """Test updating plugin runtime configuration."""
        # --- Arrange ---
        p: IFTTTPlugin = plugin(config={"webhook_key": "initial_key", "timeout_seconds": 5})

        # --- Act ---
        p.update_config({"webhook_key": "updated_key", "timeout_seconds": 15})

        # --- Assert ---
        assert p.config["webhook_key"] == "updated_key", "Config webhook_key not updated"
        assert p.client.webhook_key == "updated_key", "Client webhook_key not updated"
        assert p.client.timeout_seconds == 15, "Client timeout not updated"

    @pytest.mark.asyncio
    async def test_plugin_actions_test_connection(self):
        """Test executing test_connection action."""
        # --- Arrange ---
        p: IFTTTPlugin = plugin(config={"webhook_key": "valid_key"})
        with patch.object(p.client, "test_connection", new_callable=AsyncMock) as mock_test:
            mock_test.return_value = {"success": True, "message": "Connection OK"}

            # --- Act ---
            res: dict = await p.execute_action("test_connection")

            # --- Assert ---
            assert res["success"] is True, "test_connection should succeed"

    @pytest.mark.asyncio
    async def test_plugin_actions_trigger_event(self):
        """Test executing trigger_event action with parameters."""
        # --- Arrange ---
        p: IFTTTPlugin = plugin(config={"webhook_key": "valid_key"})
        with patch.object(p.client, "trigger_event", new_callable=AsyncMock) as mock_trigger:
            mock_trigger.return_value = {"status": "success", "event": "living_room_lights_on"}

            # --- Act ---
            res: dict = await p.execute_action("trigger_event", params={"event_name": "living_room_lights_on", "value1": "blue"})

            # --- Assert ---
            assert res["success"] is True, "trigger_event action should succeed"

    @pytest.mark.asyncio
    async def test_plugin_handle_stream(self):
        """Test handle streaming output."""
        # --- Arrange ---
        p: IFTTTPlugin = plugin()

        # --- Act ---
        events: list = []
        async for evt in p.handle("status"):
            events.append(evt)

        # --- Assert ---
        assert len(events) >= 2, "Stream should emit at least start and complete events"
        assert events[-1]["status"] == "complete", "Final event status should be complete"
