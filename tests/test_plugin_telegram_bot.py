# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Telegram Bot Plugin and Dynamic Loader
# =============================================================================
# Description:
#   Test suite covering BasePlugin architecture, load_plugins discovery,
#   TelegramBotPlugin manifest, admin actions, configuration updates, and fail-fast behavior.
#
# File: test_plugin_telegram_bot.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Test suite for plugins.base, plugins.__init__, and plugins.telegram_bot."""

import pytest
from plugins import BasePlugin, load_plugins
from plugins.telegram_bot import TelegramBotPlugin, plugin


def test_base_plugin_interface():
    """Verify that BasePlugin cannot be directly instantiated without handle()."""
    class IncompletePlugin(BasePlugin):
        pass

    with pytest.raises(TypeError):
        IncompletePlugin()


def test_telegram_bot_plugin_manifest():
    """Verify TelegramBotPlugin metadata and manifest structure."""
    bot_plugin = plugin()
    assert isinstance(bot_plugin, TelegramBotPlugin)
    assert bot_plugin.name == "telegram_bot"
    assert bot_plugin.category == "communication"

    manifest = bot_plugin.get_manifest()
    assert manifest["name"] == "telegram_bot"
    assert manifest["title"] == "Telegram Bot & Mini App"
    assert "actions" in manifest
    assert "fields" in manifest
    assert "config" in manifest

    action_ids = [a["id"] for a in manifest["actions"]]
    assert "start_bot" in action_ids
    assert "stop_bot" in action_ids
    assert "get_status" in action_ids
    assert "test_message" in action_ids

    field_ids = [f["id"] for f in manifest["fields"]]
    assert "token" in field_ids
    assert "admin_ids" in field_ids


def test_plugin_discovery():
    """Verify that load_plugins dynamically discovers and initializes telegram_bot."""
    all_plugins = load_plugins()
    assert "telegram_bot" in all_plugins
    tg = all_plugins["telegram_bot"]
    assert isinstance(tg, TelegramBotPlugin)
    assert tg.enabled is True


def test_plugin_config_update():
    """Verify updating plugin configuration updates underlying engine."""
    bot_plugin = plugin()
    bot_plugin.update_config({
        "token": "123456789:ABCDefGhIjKlMnOpQrStUvWxYz",
        "admin_ids": "1001, 1002",
        "notifications_enabled": False,
    })

    assert bot_plugin.config["token"] == "123456789:ABCDefGhIjKlMnOpQrStUvWxYz"
    assert bot_plugin.bot_engine.token == "123456789:ABCDefGhIjKlMnOpQrStUvWxYz"
    assert bot_plugin.bot_engine.admin_ids == [1001, 1002]
    assert bot_plugin.bot_engine.is_configured() is True


@pytest.mark.asyncio
async def test_plugin_actions():
    """Verify execution of admin actions on telegram_bot plugin."""
    bot_plugin = plugin(config={"token": "", "admin_ids": []})

    # Status action
    status_res = await bot_plugin.execute_action("get_status")
    assert status_res.get("success") is True
    assert "data" in status_res
    assert status_res["data"]["running"] is False

    # Start bot without token fails fast and safely
    start_res = await bot_plugin.execute_action("start_bot")
    assert start_res.get("success") is False
    assert "token is missing" in start_res.get("error", "").lower()

    # Stop bot when already stopped returns clean success
    stop_res = await bot_plugin.execute_action("stop_bot")
    assert stop_res.get("success") is True
    assert "already stopped" in stop_res.get("message", "").lower()

    # Test message without admin fails safely
    test_res = await bot_plugin.execute_action("test_message")
    assert test_res.get("success") is False


@pytest.mark.asyncio
async def test_plugin_handle_stream():
    """Verify handle() generator streams valid status responses."""
    bot_plugin = plugin()
    chunks = []
    async for chunk in bot_plugin.handle("status"):
        chunks.append(chunk)

    assert len(chunks) == 2
    assert chunks[0]["status"] == "start"
    assert chunks[1]["status"] == "complete"
    assert "Telegram Bot Plugin Status" in chunks[1]["text"]
