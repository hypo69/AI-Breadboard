# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Facebook Publisher Plugin
# =============================================================================
# Description:
#   Comprehensive test suite covering FacebookPlugin lifecycle, dynamic loading,
#   manifest schema, configuration updates, Graph API client methods, and action dispatch.
#
# File: test_plugin_facebook.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit test suite for plugins.facebook package."""

from __future__ import annotations

import json
from typing import Any, Dict
from unittest.mock import AsyncMock, patch

import pytest
import httpx

from plugins import load_plugins
from plugins.facebook import FacebookGraphClient, FacebookPlugin, plugin


def test_facebook_plugin_instantiation_and_manifest():
    """Verify FacebookPlugin initializes with default manifest and tools."""
    fb_plugin = plugin()
    assert isinstance(fb_plugin, FacebookPlugin)
    assert fb_plugin.name == "facebook"
    assert fb_plugin.category == "communication"

    manifest = fb_plugin.get_manifest()
    assert manifest["name"] == "facebook"
    assert manifest["title"] == "Facebook Publisher"
    assert "actions" in manifest
    assert "tools" in manifest
    assert "fields" in manifest

    action_ids = [a["id"] for a in manifest["actions"]]
    assert "test_connection" in action_ids
    assert "publish_post" in action_ids
    assert "get_page_info" in action_ids

    tool_names = [t["function"]["name"] for t in manifest["tools"]]
    assert "post_to_facebook" in tool_names
    assert "get_facebook_page_info" in tool_names
    assert "get_facebook_accounts" in tool_names


def test_facebook_plugin_discovery():
    """Verify load_plugins dynamically discovers the facebook plugin."""
    all_plugins = load_plugins()
    assert "facebook" in all_plugins
    fb = all_plugins["facebook"]
    assert isinstance(fb, FacebookPlugin)
    assert fb.enabled is True


def test_facebook_config_update_and_client_sync():
    """Verify updating plugin configuration correctly propagates to FacebookGraphClient."""
    fb_plugin = plugin()
    assert fb_plugin.client.is_configured() is False

    fb_plugin.update_config({
        "page_id": "1009988776655",
        "page_access_token": "EAABtesttoken123",
        "api_version": "v19.0",
    })

    assert fb_plugin.config["page_id"] == "1009988776655"
    assert fb_plugin.client.page_id == "1009988776655"
    assert fb_plugin.client.access_token == "EAABtesttoken123"
    assert fb_plugin.client.api_version == "v19.0"
    assert fb_plugin.client.is_configured() is True


@pytest.mark.asyncio
async def test_client_publish_post_success():
    """Verify publishing a text post sends the expected request payload and returns post ID."""
    client = FacebookGraphClient(page_id="12345", access_token="TOKEN_ABC")

    mock_response = httpx.Response(
        status_code=200,
        content=json.dumps({"id": "12345_67890"}).encode("utf-8"),
        request=httpx.Request("POST", f"{client.base_url}/12345/feed"),
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await client.publish_post(message="Hello Facebook!", link="https://example.com")

        assert result["success"] is True
        assert result["id"] == "12345_67890"
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["data"]["message"] == "Hello Facebook!"
        assert call_args[1]["data"]["link"] == "https://example.com"
        assert call_args[1]["data"]["access_token"] == "TOKEN_ABC"


@pytest.mark.asyncio
async def test_client_publish_post_unconfigured():
    """Verify publishing without a token fails early with an error."""
    client = FacebookGraphClient(access_token="")
    result = await client.publish_post(message="Test unconfigured")
    assert result["success"] is False
    assert "token is missing" in result["error"].lower()


@pytest.mark.asyncio
async def test_client_publish_photo_success():
    """Verify publishing a photo via URL and raw bytes."""
    client = FacebookGraphClient(page_id="12345", access_token="TOKEN_ABC")

    mock_response = httpx.Response(
        status_code=200,
        content=json.dumps({"id": "photo_id_111", "post_id": "post_id_222"}).encode("utf-8"),
        request=httpx.Request("POST", f"{client.base_url}/12345/photos"),
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await client.publish_photo(caption="Look at this image", photo_url="https://example.com/img.png")

        assert result["success"] is True
        assert result["id"] == "photo_id_111"
        assert result["post_id"] == "post_id_222"

    # Test with bytes
    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result_bytes = await client.publish_photo(caption="Photo from bytes", photo_bytes=b"fake_image_data")

        assert result_bytes["success"] is True
        assert result_bytes["id"] == "photo_id_111"


@pytest.mark.asyncio
async def test_client_error_parsing():
    """Verify Graph API OAuth errors are extracted cleanly into user-friendly messages."""
    client = FacebookGraphClient(page_id="12345", access_token="INVALID_TOKEN")

    error_payload = {
        "error": {
            "message": "Invalid OAuth access token.",
            "type": "OAuthException",
            "code": 190,
            "fbtrace_id": "A1B2C3D4E5",
        }
    }
    mock_response = httpx.Response(
        status_code=400,
        content=json.dumps(error_payload).encode("utf-8"),
        request=httpx.Request("POST", f"{client.base_url}/12345/feed"),
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await client.publish_post(message="Test error parsing")

        assert result["success"] is False
        assert "Invalid OAuth access token" in result["error"]
        assert "code: 190" in result["error"]
        assert "A1B2C3D4E5" in result["error"]


@pytest.mark.asyncio
async def test_client_get_page_info_and_accounts():
    """Verify fetching page metadata and managed accounts list."""
    client = FacebookGraphClient(page_id="page_999", access_token="VALID_TOKEN")

    page_data = {"id": "page_999", "name": "AI Breadboard Community", "fan_count": 1500}
    mock_get_response = httpx.Response(
        status_code=200,
        content=json.dumps(page_data).encode("utf-8"),
        request=httpx.Request("GET", f"{client.base_url}/page_999"),
    )

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_get_response
        res = await client.get_page_info()
        assert res["success"] is True
        assert res["data"]["name"] == "AI Breadboard Community"

    accounts_data = {"data": [{"id": "page_999", "name": "AI Breadboard Community", "access_token": "PAGE_TOKEN"}]}
    mock_acc_response = httpx.Response(
        status_code=200,
        content=json.dumps(accounts_data).encode("utf-8"),
        request=httpx.Request("GET", f"{client.base_url}/me/accounts"),
    )

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_acc_response
        acc_res = await client.get_accounts()
        assert acc_res["success"] is True
        assert len(acc_res["accounts"]) == 1
        assert acc_res["accounts"][0]["name"] == "AI Breadboard Community"


@pytest.mark.asyncio
async def test_plugin_execute_actions():
    """Verify execution of admin actions on FacebookPlugin."""
    fb = plugin(config={"page_id": "page_123", "page_access_token": "VALID_TOKEN"})

    # Action: get_page_info
    mock_info = httpx.Response(
        status_code=200,
        content=json.dumps({"id": "page_123", "name": "Test Page", "is_published": True}).encode("utf-8"),
        request=httpx.Request("GET", f"{fb.client.base_url}/page_123"),
    )
    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_info
        info_res = await fb.execute_action("get_page_info")
        assert info_res["success"] is True
        assert info_res["data"]["name"] == "Test Page"

        # Action: test_connection
        conn_res = await fb.execute_action("test_connection")
        assert conn_res["success"] is True
        assert conn_res["configured"] is True
        assert "Test Page" in conn_res["message"]

    # Action: publish_post
    mock_pub = httpx.Response(
        status_code=200,
        content=json.dumps({"id": "page_123_post_999"}).encode("utf-8"),
        request=httpx.Request("POST", f"{fb.client.base_url}/page_123/feed"),
    )
    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_pub
        pub_res = await fb.execute_action("publish_post", {"message": "Live post test"})
        assert pub_res["success"] is True
        assert pub_res["id"] == "page_123_post_999"


@pytest.mark.asyncio
async def test_plugin_execute_action_validation_and_unconfigured():
    """Verify validation when mandatory action parameters or tokens are missing."""
    fb = plugin(config={"page_access_token": ""})

    conn_res = await fb.execute_action("test_connection")
    assert conn_res["success"] is False
    assert "token is missing" in conn_res["error"].lower()

    fb.update_config({"page_access_token": "SAMPLE_TOKEN"})
    empty_msg_res = await fb.execute_action("publish_post", {"message": "   "})
    assert empty_msg_res["success"] is False
    assert "cannot be empty" in empty_msg_res["error"].lower()


@pytest.mark.asyncio
async def test_plugin_handle_stream():
    """Verify handle() generator streams valid formatted status responses."""
    fb = plugin(config={"page_id": "test_page_id", "page_access_token": "TOKEN"})
    chunks = []
    async for chunk in fb.handle("status"):
        chunks.append(chunk)

    assert len(chunks) == 2
    assert chunks[0]["status"] == "start"
    assert chunks[1]["status"] == "complete"
    assert "Facebook Publisher Status" in chunks[1]["text"]
    assert "test_page_id" in chunks[1]["text"]
