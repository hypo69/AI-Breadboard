# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Accounts & Identity Module Tests
# =============================================================================
# Description:
#   Комплексные модульные и интеграционные тесты подсистемы Accounts & Identity,
#   каталога операций (~180 позиций), Windows Identity Graph и REST API.
#
# Usage Examples:
#   pytest tests/test_accounts_identity.py -v
#
# File: test_accounts_identity.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 02:10:00
# =============================================================================

"""Тесты подсистемы Accounts & Identity Windows."""

from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient

from apps.windows.sdk.modules.accounts_identity.models import (
    RiskLevel,
    PrincipalType,
    AccountSource,
    IntegrityLevel,
    Principal,
    GroupRef,
    TokenDetails,
)
from apps.windows.sdk.modules.accounts_identity.catalog import (
    get_full_catalog,
    get_operation_by_id,
    get_operations_by_subsystem,
    get_operations_by_risk,
    search_catalog,
)
from apps.windows.sdk.modules.accounts_identity.win32_bridge import (
    Win32IdentityBridge,
    WELL_KNOWN_SIDS,
)
from apps.windows.sdk.modules.accounts_identity.graph_engine import IdentityGraphEngine
from apps.windows.sdk.modules.accounts_identity.service import get_accounts_identity_service
from apps.windows.sdk.modules.accounts_identity.tui import format_principal_tree, format_pid_tree
from apps.windows.router import router as windows_router
from fastapi import FastAPI


@pytest.fixture
def api_client() -> TestClient:
    """Фикстура тестового клиента FastAPI."""
    app = FastAPI()
    app.include_router(windows_router)
    return TestClient(app)


class TestAccountsIdentityCatalog:
    """Тестирование официального каталога операций Accounts & Identity."""

    def test_full_catalog_count(self) -> None:
        """Проверка общего количества зарегистрированных операций в каталоге."""
        catalog = get_full_catalog()
        assert len(catalog) >= 150
        assert catalog[0].id == 1
        assert catalog[-1].id == 181

    def test_catalog_subsystems_filter(self) -> None:
        """Проверка фильтрации операций по подсистемам."""
        identity_ops = get_operations_by_subsystem("01_identity")
        assert len(identity_ops) == 12

        users_ops = get_operations_by_subsystem("02_users")
        assert len(users_ops) == 20

        groups_ops = get_operations_by_subsystem("05_groups")
        assert len(groups_ops) == 18

    def test_catalog_risk_levels(self) -> None:
        """Проверка распределения операций по уровням риска."""
        safe_ops = get_operations_by_risk(RiskLevel.SAFE)
        assert len(safe_ops) > 100

        admin_ops = get_operations_by_risk(RiskLevel.ADMIN)
        assert len(admin_ops) > 10

        dangerous_ops = get_operations_by_risk(RiskLevel.DANGEROUS)
        assert len(dangerous_ops) > 5

    def test_search_catalog(self) -> None:
        """Проверка поиска операций по ключевым словам."""
        res_whoami = search_catalog("whoami")
        assert len(res_whoami) >= 5

        res_lsa = search_catalog("Lsa")
        assert len(res_lsa) >= 3


class TestWin32BridgeAndSID:
    """Тестирование низкоуровневого моста и трансляции SID."""

    def test_well_known_sids_lookup(self) -> None:
        """Проверка разрешения стандартных Well-Known SID."""
        bridge = Win32IdentityBridge()
        system_info = bridge.lookup_sid_to_name("S-1-5-18")
        assert system_info is not None
        assert "SYSTEM" in system_info[0].upper()

        admins_info = bridge.lookup_sid_to_name("S-1-5-32-544")
        assert admins_info is not None
        assert "ADMINISTRATOR" in admins_info[0].upper()

    def test_sid_validity_check(self) -> None:
        """Проверка валидации структуры SID."""
        bridge = Win32IdentityBridge()
        assert bridge.check_is_valid_sid("S-1-5-18") is True
        assert bridge.check_is_valid_sid("S-1-5-32-544") is True
        assert bridge.check_is_valid_sid("invalid-sid-string") is False
        assert bridge.check_is_valid_sid("") is False


class TestSubsystemsAndIdentityGraph:
    """Тестирование подсистем и движка Identity Graph."""

    def test_identity_subsystem(self) -> None:
        """Тестирование подсистемы 01 Identity."""
        engine = IdentityGraphEngine()
        user_name = engine.identity.get_current_user()
        assert bool(user_name)

        dom_user = engine.identity.get_domain_and_user()
        assert "\\" in dom_user

        sid_str = engine.identity.get_current_user_sid()
        assert sid_str.startswith("S-1-")

        token_ctx = engine.identity.get_current_identity_context()
        assert token_ctx.pid == os.getpid()
        assert token_ctx.user_name.lower() == user_name.lower()

    def test_users_and_groups_subsystems(self) -> None:
        """Тестирование перечисления пользователей и групп."""
        engine = IdentityGraphEngine()
        users = engine.users.list_users()
        assert len(users) > 0

        groups = engine.groups.list_groups()
        assert len(groups) > 0

    def test_explain_principal(self) -> None:
        """Тестирование формирования полного досье Principal."""
        engine = IdentityGraphEngine()
        cur_user = engine.identity.get_current_user()
        principal = engine.explain_principal(cur_user)

        assert isinstance(principal, Principal)
        assert principal.name.lower() == cur_user.lower()
        assert principal.sid.startswith("S-1-")
        assert isinstance(principal.is_admin, bool)

    def test_explain_pid(self) -> None:
        """Тестирование инспекции процесса по PID."""
        engine = IdentityGraphEngine()
        pid_info = engine.explain_pid(os.getpid())

        assert pid_info["pid"] == os.getpid()
        assert "account" in pid_info
        assert "integrity" in pid_info
        assert "elevated" in pid_info

    def test_who_is_admin(self) -> None:
        """Тестирование поиска всех администраторов системы."""
        engine = IdentityGraphEngine()
        admins = engine.who_is_admin()
        assert isinstance(admins, list)
        for adm in admins:
            assert "username" in adm
            assert "path_to_admin" in adm

    def test_identity_graph_builder(self) -> None:
        """Тестирование построения Windows Identity Graph."""
        engine = IdentityGraphEngine()
        graph = engine.build_identity_graph()

        assert len(graph.nodes) > 0
        assert "total_users" in graph.summary
        assert "total_groups" in graph.summary

    def test_tui_formatters(self) -> None:
        """Тестирование форматирования досье в виде дерева ASCII."""
        engine = IdentityGraphEngine()
        principal = engine.explain_principal(engine.identity.get_current_user())
        tree_str = format_principal_tree(principal)
        assert "Principal" in tree_str
        assert "SID:" in tree_str

        pid_info = engine.explain_pid(os.getpid())
        pid_tree_str = format_pid_tree(pid_info)
        assert "PID" in pid_tree_str
        assert "Integrity:" in pid_tree_str


class TestAccountsIdentityFastAPI:
    """Интеграционные тесты REST API эндпоинтов."""

    def test_api_catalog(self, api_client: TestClient) -> None:
        """GET /api/windows/identity/catalog"""
        resp = api_client.get("/api/windows/identity/catalog")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 150

    def test_api_current_identity(self, api_client: TestClient) -> None:
        """GET /api/windows/identity/current"""
        resp = api_client.get("/api/windows/identity/current")
        assert resp.status_code == 200
        data = resp.json()
        assert "user_name" in data
        assert "user_sid" in data

    def test_api_users(self, api_client: TestClient) -> None:
        """GET /api/windows/identity/users"""
        resp = api_client.get("/api/windows/identity/users")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_api_groups(self, api_client: TestClient) -> None:
        """GET /api/windows/identity/groups"""
        resp = api_client.get("/api/windows/identity/groups")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_api_who_is_admin(self, api_client: TestClient) -> None:
        """GET /api/windows/identity/who-is-admin"""
        resp = api_client.get("/api/windows/identity/who-is-admin")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_api_explain_pid(self, api_client: TestClient) -> None:
        """GET /api/windows/identity/explain-pid/{pid}"""
        resp = api_client.get(f"/api/windows/identity/explain-pid/{os.getpid()}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pid"] == os.getpid()

    def test_api_identity_graph(self, api_client: TestClient) -> None:
        """GET /api/windows/identity/graph"""
        resp = api_client.get("/api/windows/identity/graph")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data

    def test_api_audit(self, api_client: TestClient) -> None:
        """GET /api/windows/identity/audit"""
        resp = api_client.get("/api/windows/identity/audit?limit=10")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_webgui_tab_files_exist(self) -> None:
        """Проверка наличия файлов HTML и JS вкладки accounts_identity_tab."""
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        tab_dir = root / "apps" / "windows" / "api" / "webgui" / "accounts_identity_tab"
        assert (tab_dir / "index.html").is_file()
        assert (tab_dir / "main.js").is_file()
        assert (tab_dir / "README.md").is_file()


