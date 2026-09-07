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

from pathlib import Path

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


def test_oauth_state_with_telegram():
    """Verify Google OAuth state generation stores and retrieves Telegram ID."""
    from src.fastapi.router_auth import generate_state_token, get_state_payload, validate_state_token

    state = generate_state_token(tg_id=12345678, tg_username="alex_user")
    assert isinstance(state, str)
    assert validate_state_token(state) is True

    payload = get_state_payload(state)
    assert payload is not None
    assert payload["tg_id"] == 12345678
    assert payload["tg_username"] == "alex_user"


def test_user_manager_telegram_linking_and_dialog_storage(tmp_path):
    """Verify direct Telegram account linking and user workspace dialogue file storage."""
    from src.user_manager import UserManager

    db_file = tmp_path / "test_users.db"
    users_dir = tmp_path / "data" / "users"
    mgr = UserManager(db_path=db_file, users_dir=users_dir)

    user_id = mgr.add_user(email="test_user@example.com", name="Test User", role="user")
    assert user_id > 0

    # Direct Telegram link
    ok = mgr.link_telegram_account_direct(user_id=user_id, telegram_id=987654321, telegram_username="tg_tester")
    assert ok is True

    # Retrieve user by Telegram ID
    fetched = mgr.get_user_by_telegram_id(987654321)
    assert fetched["id"] == user_id
    assert fetched["email"] == "test_user@example.com"
    assert fetched["telegram_username"] == "tg_tester"

    # Save dialogue recording file
    file_bytes = b"sample dialogue audio audio content"
    saved_meta = mgr.save_user_dialog_file(
        user_id=user_id,
        filename="conversation_recording.ogg",
        content=file_bytes,
        subfolder="dialogs"
    )

    assert "conversation_recording.ogg" in saved_meta["filename"]
    assert saved_meta["size_bytes"] == len(file_bytes)
    assert Path(saved_meta["absolute_path"]).exists()
    assert Path(saved_meta["absolute_path"]).read_bytes() == file_bytes


def test_bot_engine_oauth_url_and_format_size():
    """Verify TelegramBotEngine OAuth URL construction and size formatting."""
    bot_plugin = plugin(config={"api_base_url": "http://127.0.0.1:8000"})
    url = bot_plugin.bot_engine._get_oauth_url(tg_id=555444, tg_username="tg_user")
    assert "tg_id=555444" in url
    assert "tg_username=tg_user" in url
    assert url.startswith("http://127.0.0.1:8000/auth/google?")

    assert bot_plugin.bot_engine._format_size(500) == "500 B"
    assert bot_plugin.bot_engine._format_size(2048) == "2.0 KB"
    assert bot_plugin.bot_engine._format_size(1048576) == "1.0 MB"

