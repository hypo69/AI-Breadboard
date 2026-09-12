# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Testing MCP Server Management Endpoints in Admin Panel
# =============================================================================
# Description:
#   Pytest test suite for REST API endpoints /api/admin/mcp/* and /api/mcp/*
#   covering listing, creating, updating, toggling, deleting, and testing MCP servers.
#
# File: test_router_admin_mcp.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from fastapi.testclient import TestClient
from header import __root__
from main import app

client = TestClient(app)


class TestAdminMCPAPI:
    """Test suite for MCP server configuration and diagnostics endpoints."""

    def test_list_mcp_servers(self):
        """Verify retrieving list of MCP servers."""
        response = client.get("/api/admin/mcp/servers")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert isinstance(data["servers"], list)
        assert data["total"] >= 1

        server_ids = [s["id"] for s in data["servers"]]
        assert "playwright" in server_ids

    def test_list_mcp_servers_user_endpoint(self):
        """Verify retrieving list of MCP servers via user alias route."""
        response = client.get("/api/mcp/servers")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert isinstance(data["servers"], list)
        assert data["total"] >= 1

    def test_get_single_mcp_server(self):
        """Verify retrieving single server configuration."""
        response = client.get("/api/admin/mcp/servers/playwright")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert "server" in data
        assert data["server"]["id"] == "playwright"
        assert data["server"]["transport"] == "stdio"
        assert data["server"]["command"] == "npx"

    def test_get_nonexistent_mcp_server(self):
        """Verify 404 response for nonexistent server ID."""
        response = client.get("/api/admin/mcp/servers/non_existent_server_xyz")
        assert response.status_code == 404

    def test_create_update_toggle_delete_mcp_server(self):
        """Test complete CRUD and toggle lifecycle for an MCP server."""
        test_id = "test_pytest_mcp_server"

        # 1. Clean up if already exists
        client.delete(f"/api/admin/mcp/servers/{test_id}")

        # 2. Create server
        create_payload = {
            "id": test_id,
            "name": "Pytest Test MCP Server",
            "description": "Temporary server created by automated test",
            "transport": "stdio",
            "command": "python",
            "args": ["-m", "http.server", "9999"],
            "enabled": True,
            "env": {"TEST_VAR": "1"}
        }
        create_resp = client.post("/api/admin/mcp/servers", json=create_payload)
        assert create_resp.status_code == 200
        create_data = create_resp.json()
        assert create_data["status"] == "ok"
        assert create_data["server"]["id"] == test_id

        # 3. Verify server in list
        get_resp = client.get(f"/api/admin/mcp/servers/{test_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["server"]["name"] == "Pytest Test MCP Server"

        # 4. Toggle enabled status
        toggle_resp = client.post(f"/api/admin/mcp/servers/{test_id}/toggle")
        assert toggle_resp.status_code == 200
        assert toggle_resp.json()["enabled"] is False

        # 5. Update server
        update_payload = {
            "name": "Updated Pytest MCP Server",
            "description": "Updated description",
            "enabled": True
        }
        update_resp = client.put(f"/api/admin/mcp/servers/{test_id}", json=update_payload)
        assert update_resp.status_code == 200
        assert update_resp.json()["server"]["name"] == "Updated Pytest MCP Server"
        assert update_resp.json()["server"]["enabled"] is True

        # 6. Delete server
        delete_resp = client.delete(f"/api/admin/mcp/servers/{test_id}")
        assert delete_resp.status_code == 200
        assert delete_resp.json()["status"] == "ok"

        # 7. Verify deletion
        get_deleted = client.get(f"/api/admin/mcp/servers/{test_id}")
        assert get_deleted.status_code == 404

    def test_test_adhoc_mcp_server(self):
        """Test ad-hoc MCP server connection test endpoint."""
        payload = {
            "id": "invalid_test",
            "transport": "stdio",
            "command": "nonexistent_executable_12345",
            "args": []
        }
        response = client.post("/api/admin/mcp/test", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Should return error status without crashing server
        assert data["status"] == "error"
        assert "message" in data

    def test_get_all_mcp_tools(self):
        """Test retrieving all aggregated tools from enabled MCP servers."""
        response = client.get("/api/admin/mcp/tools")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("ok", "error")
        assert "tools" in data
        assert isinstance(data["tools"], list)
