# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: MCP (Model Context Protocol) Server Management Router
# =============================================================================
# Description:
#   FastAPI REST API router for managing Model Context Protocol (MCP) servers,
#   persisting server configurations in config.json, testing connections, and
#   discovering available tools and tool schemas.
#
# File: router_mcp.py
# Project: ai-breadboard
# Package: src.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from header import __root__
from src.ai.agents.mcp_client import MCPClientManager
from src.logger import logger

admin_mcp_router = APIRouter(prefix='/api/admin/mcp', tags=['admin_mcp'])
user_mcp_router = APIRouter(prefix='/api/mcp', tags=['mcp'])

CONFIG_PATH = __root__ / 'config.json'


# =============================================================================
# Pydantic Request Models
# =============================================================================

class MCPServerConfigModel(BaseModel):
    """Configuration model for an MCP server."""
    id: Optional[str] = Field(None, description="Unique identifier for the server (e.g., 'playwright')")
    name: Optional[str] = Field(None, description="Human-readable server name")
    description: Optional[str] = Field("", description="Optional description of server functionality")
    transport: str = Field("stdio", description="Transport protocol: 'stdio', 'sse', or 'streamable_http'")
    command: Optional[str] = Field("", description="Executable command for stdio transport (e.g., 'npx', 'python')")
    args: Optional[List[str]] = Field(default_factory=list, description="List of arguments for stdio command")
    url: Optional[str] = Field("", description="URL endpoint for sse or streamable_http transport")
    env: Optional[Dict[str, str]] = Field(default_factory=dict, description="Environment variables for stdio subprocess")
    enabled: bool = Field(True, description="Whether the MCP server is enabled for tool execution")


class MCPTestRequestModel(BaseModel):
    """Payload model for testing an arbitrary MCP server connection."""
    id: Optional[str] = Field("test_server", description="Server identifier")
    transport: str = Field("stdio", description="Transport protocol")
    command: Optional[str] = Field("", description="Command for stdio")
    args: Optional[List[str]] = Field(default_factory=list, description="Arguments for stdio")
    url: Optional[str] = Field("", description="URL for SSE / HTTP")
    env: Optional[Dict[str, str]] = Field(default_factory=dict, description="Environment variables")


# =============================================================================
# Helper Utilities
# =============================================================================

def _check_admin(request: Request) -> bool:
    """Verify administrator permissions or local loopback access."""
    if request.cookies.get('admin_password_verified') == 'true':
        return True

    from src.fastapi.router_auth import verify_jwt_token
    token: str = request.cookies.get('auth_token', '')
    if not token:
        auth_header: str = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()

    if token:
        user_data = verify_jwt_token(token)
        if user_data:
            from src.user_manager import user_manager
            db_user = user_manager.get_user_by_email(user_data.email)
            if db_user and (db_user.get('is_admin', 0) or db_user.get('role') == 'admin'):
                return True
            raise HTTPException(status_code=403, detail='Only administrators have access')

    hostname: str = request.url.hostname or ''
    is_local: bool = (
        hostname in ('127.0.0.1', 'localhost', '::1', 'testserver', '0.0.0.0')
        or hostname.startswith('192.168.')
        or hostname.startswith('10.')
        or hostname.startswith('172.')
    )
    if is_local:
        from src.user_manager import user_manager
        db_user = user_manager.get_user_by_id(1)
        if db_user and (db_user.get('is_admin', 0) or db_user.get('role') == 'admin'):
            return True

    raise HTTPException(status_code=401, detail='Not authenticated')


def _load_config_raw() -> Dict[str, Any]:
    """Load configuration dictionary from config.json."""
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as ex:
        logger.error(f"[RouterMCP] Failed to read config.json: {ex}")
        return {}


def _save_config_raw(cfg: Dict[str, Any]) -> None:
    """Save configuration dictionary to config.json with formatted indentation."""
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
    except Exception as ex:
        logger.error(f"[RouterMCP] Failed to write config.json: {ex}")
        raise HTTPException(status_code=500, detail="Failed to save server configuration to config.json")


def _get_mcp_servers_dict(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Extract or create langchain.mcp_servers mapping."""
    if 'langchain' not in cfg or not isinstance(cfg['langchain'], dict):
        cfg['langchain'] = {}
    if 'mcp_servers' not in cfg['langchain'] or not isinstance(cfg['langchain']['mcp_servers'], dict):
        cfg['langchain']['mcp_servers'] = {}
    return cfg['langchain']['mcp_servers']


# =============================================================================
# REST Endpoints
# =============================================================================

@admin_mcp_router.get('/servers')
@user_mcp_router.get('/servers')
async def list_mcp_servers(request: Request) -> Dict[str, Any]:
    """List all configured MCP servers and their operational status."""
    _check_admin(request)
    cfg = _load_config_raw()
    mcp_servers = _get_mcp_servers_dict(cfg)

    servers_list: List[Dict[str, Any]] = []
    for s_id, s_data in mcp_servers.items():
        if isinstance(s_data, dict):
            entry = dict(s_data)
            entry['id'] = s_id
            if 'name' not in entry or not entry['name']:
                entry['name'] = s_id.replace('_', ' ').replace('-', ' ').title()
            if 'transport' not in entry:
                entry['transport'] = 'stdio'
            if 'enabled' not in entry:
                entry['enabled'] = True
            servers_list.append(entry)

    return {
        "status": "ok",
        "total": len(servers_list),
        "servers": servers_list,
    }


@admin_mcp_router.get('/servers/{server_id}')
@user_mcp_router.get('/servers/{server_id}')
async def get_mcp_server(server_id: str, request: Request) -> Dict[str, Any]:
    """Retrieve configuration details for a specific MCP server."""
    _check_admin(request)
    cfg = _load_config_raw()
    mcp_servers = _get_mcp_servers_dict(cfg)

    if server_id not in mcp_servers:
        raise HTTPException(status_code=404, detail=f"MCP Server '{server_id}' not found")

    server_data = dict(mcp_servers[server_id])
    server_data['id'] = server_id
    return {
        "status": "ok",
        "server": server_data,
    }


@admin_mcp_router.post('/servers')
@user_mcp_router.post('/servers')
async def create_mcp_server(data: MCPServerConfigModel, request: Request) -> Dict[str, Any]:
    """Register and persist a new MCP server configuration."""
    _check_admin(request)
    if not data.id:
        raise HTTPException(status_code=400, detail="Server ID is required")

    server_id = data.id.strip().lower().replace(" ", "_")
    cfg = _load_config_raw()
    mcp_servers = _get_mcp_servers_dict(cfg)

    if server_id in mcp_servers:
        raise HTTPException(status_code=409, detail=f"MCP Server '{server_id}' already exists")

    server_entry: Dict[str, Any] = {
        "name": data.name or server_id.replace('_', ' ').replace('-', ' ').title(),
        "description": data.description or "",
        "transport": data.transport or "stdio",
        "enabled": data.enabled,
    }

    if data.transport in ("sse", "streamable_http", "http"):
        if not data.url:
            raise HTTPException(status_code=400, detail="URL is required for SSE / HTTP transport")
        server_entry["url"] = data.url
    else:
        if not data.command:
            raise HTTPException(status_code=400, detail="Command is required for stdio transport")
        server_entry["command"] = data.command
        server_entry["args"] = data.args or []
        if data.env:
            server_entry["env"] = data.env

    mcp_servers[server_id] = server_entry
    _save_config_raw(cfg)
    logger.info(f"[RouterMCP] Created MCP server: {server_id}")

    return {
        "status": "ok",
        "message": f"MCP Server '{server_id}' created successfully",
        "server": {**server_entry, "id": server_id},
    }


@admin_mcp_router.put('/servers/{server_id}')
@user_mcp_router.put('/servers/{server_id}')
async def update_mcp_server(server_id: str, data: MCPServerConfigModel, request: Request) -> Dict[str, Any]:
    """Update an existing MCP server configuration."""
    _check_admin(request)
    cfg = _load_config_raw()
    mcp_servers = _get_mcp_servers_dict(cfg)

    if server_id not in mcp_servers:
        raise HTTPException(status_code=404, detail=f"MCP Server '{server_id}' not found")

    current = dict(mcp_servers[server_id])
    if data.name is not None:
        current["name"] = data.name
    if data.description is not None:
        current["description"] = data.description
    if data.transport is not None:
        current["transport"] = data.transport
    if data.enabled is not None:
        current["enabled"] = data.enabled
    if data.command is not None:
        current["command"] = data.command
    if data.args is not None:
        current["args"] = data.args
    if data.url is not None:
        current["url"] = data.url
    if data.env is not None:
        current["env"] = data.env

    mcp_servers[server_id] = current
    _save_config_raw(cfg)
    logger.info(f"[RouterMCP] Updated MCP server: {server_id}")

    return {
        "status": "ok",
        "message": f"MCP Server '{server_id}' updated successfully",
        "server": {**current, "id": server_id},
    }


@admin_mcp_router.delete('/servers/{server_id}')
@user_mcp_router.delete('/servers/{server_id}')
async def delete_mcp_server(server_id: str, request: Request) -> Dict[str, Any]:
    """Delete an MCP server from configuration."""
    _check_admin(request)
    cfg = _load_config_raw()
    mcp_servers = _get_mcp_servers_dict(cfg)

    if server_id not in mcp_servers:
        raise HTTPException(status_code=404, detail=f"MCP Server '{server_id}' not found")

    del mcp_servers[server_id]
    _save_config_raw(cfg)
    logger.info(f"[RouterMCP] Deleted MCP server: {server_id}")

    return {
        "status": "ok",
        "message": f"MCP Server '{server_id}' deleted successfully",
    }


@admin_mcp_router.post('/servers/{server_id}/toggle')
@user_mcp_router.post('/servers/{server_id}/toggle')
async def toggle_mcp_server(server_id: str, request: Request) -> Dict[str, Any]:
    """Toggle enabled status for an MCP server."""
    _check_admin(request)
    cfg = _load_config_raw()
    mcp_servers = _get_mcp_servers_dict(cfg)

    if server_id not in mcp_servers:
        raise HTTPException(status_code=404, detail=f"MCP Server '{server_id}' not found")

    current_state = mcp_servers[server_id].get("enabled", True)
    new_state = not current_state
    mcp_servers[server_id]["enabled"] = new_state
    _save_config_raw(cfg)
    logger.info(f"[RouterMCP] Toggled MCP server '{server_id}' enabled={new_state}")

    return {
        "status": "ok",
        "server_id": server_id,
        "enabled": new_state,
    }


@admin_mcp_router.post('/servers/{server_id}/test')
@user_mcp_router.post('/servers/{server_id}/test')
async def test_saved_mcp_server(server_id: str, request: Request) -> Dict[str, Any]:
    """Test connection and discover tools for a saved MCP server."""
    _check_admin(request)
    cfg = _load_config_raw()
    mcp_servers = _get_mcp_servers_dict(cfg)

    if server_id not in mcp_servers:
        raise HTTPException(status_code=404, detail=f"MCP Server '{server_id}' not found")

    server_cfg = mcp_servers[server_id]
    result = await MCPClientManager.test_server_connection(server_id, server_cfg)
    return result


@admin_mcp_router.post('/test')
@user_mcp_router.post('/test')
async def test_adhoc_mcp_server(data: MCPTestRequestModel, request: Request) -> Dict[str, Any]:
    """Test connection on-the-fly for unsaved server configurations."""
    _check_admin(request)
    server_id = data.id or "test_server"
    server_cfg = {
        "transport": data.transport,
        "command": data.command,
        "args": data.args,
        "url": data.url,
        "env": data.env,
    }
    result = await MCPClientManager.test_server_connection(server_id, server_cfg)
    return result


@admin_mcp_router.get('/tools')
@user_mcp_router.get('/tools')
async def get_all_mcp_tools(request: Request) -> Dict[str, Any]:
    """Retrieve all available tools from all currently enabled MCP servers."""
    _check_admin(request)
    try:
        async with MCPClientManager() as manager:
            tools = await manager.get_tools()

        tools_list: List[Dict[str, Any]] = []
        for t in tools:
            tool_entry: Dict[str, Any] = {
                "name": getattr(t, "name", str(t)),
                "description": getattr(t, "description", ""),
                "args_schema": getattr(t, "args", {}),
            }
            if hasattr(t, "args_schema") and t.args_schema:
                try:
                    tool_entry["args_schema"] = t.args_schema.schema() if hasattr(t.args_schema, "schema") else str(t.args_schema)
                except Exception:
                    pass
            tools_list.append(tool_entry)

        return {
            "status": "ok",
            "total": len(tools_list),
            "tools": tools_list,
        }
    except Exception as ex:
        logger.error(f"[RouterMCP] Failed to aggregate MCP tools: {ex}")
        return {
            "status": "error",
            "message": str(ex),
            "total": 0,
            "tools": [],
        }


def init_admin_mcp_router() -> APIRouter:
    """Initialize and return admin MCP router."""
    return admin_mcp_router


def init_user_mcp_router() -> APIRouter:
    """Initialize and return user MCP router."""
    return user_mcp_router
