# -*- coding: utf-8 -*-
# =============================================================================
# Test Suite: Тесты редактора меню (/tc) и API конфигурации меню
# =============================================================================
# Description:
#   Тестирует чтение, валидацию, сохранение через /api/menu/config,
#   структуру конфигурации tc_menu_config.json и интеграцию с интерфейсом.
#
# File: test_menu_editor.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты редактора меню (/tc) и эндпоинтов управления конфигурацией меню."""

import json
import re
from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from header import __root__
from src.api.router_menu import init_router as init_menu_router, TC_MENU_CONFIG_PATH


WEBGUI_DIR = __root__ / "src" / "api" / "webgui"
APPS_MAIN_JS = WEBGUI_DIR / "apps" / "main.js"
TABS_CONFIG_JS = WEBGUI_DIR / "apps" / "modules" / "tabs-config.js"
STATUS_MANAGER_JS = WEBGUI_DIR / "apps" / "modules" / "status-manager.js"
APPS_INDEX_HTML = WEBGUI_DIR / "apps" / "index.html"


class TestMenuConfig:
    """Тесты структуры tc_menu_config.json"""

    def test_menu_config_exists(self):
        """Проверка существования файла конфигурации tc_menu_config.json"""
        assert TC_MENU_CONFIG_PATH.exists(), f"Файл {TC_MENU_CONFIG_PATH} не найден"

    def test_menu_config_valid_json(self):
        """Проверка валидности JSON в файле конфигурации"""
        try:
            with open(TC_MENU_CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            assert isinstance(config, dict), "Конфигурация должна быть объектом"
        except json.JSONDecodeError as e:
            pytest.fail(f"Неверный JSON в tc_menu_config.json: {e}")

    def test_menu_config_structure(self):
        """Проверка обязательных разделов конфигурации меню"""
        with open(TC_MENU_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)

        assert "menu" in config, "Отсутствует секция menu"
        assert "topButtons" in config["menu"], "Отсутствует topButtons"
        assert "sidebarItems" in config["menu"], "Отсутствует sidebarItems"

    def test_top_buttons_required_fields(self):
        """Проверка обязательных полей в topButtons"""
        with open(TC_MENU_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)

        for item in config["menu"]["topButtons"]:
            assert "id" in item, f"Отсутствует id в topButtons: {item}"
            assert "label" in item, f"Отсутствует label в topButtons: {item}"
            assert "tab" in item, f"Отсутствует tab в topButtons: {item}"

    def test_sidebar_items_required_fields(self):
        """Проверка обязательных полей в sidebarItems"""
        with open(TC_MENU_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)

        for item in config["menu"]["sidebarItems"]:
            assert "id" in item, f"Отсутствует id в sidebarItems: {item}"
            assert "label" in item, f"Отсутствует label в sidebarItems: {item}"
            assert "tab" in item, f"Отсутствует tab в sidebarItems: {item}"


class TestTabsConfig:
    """Тесты tabs-config.js"""

    def test_tabs_config_exists(self):
        """Проверка существования tabs-config.js"""
        assert TABS_CONFIG_JS.exists(), "tabs-config.js не найден"

    def test_tabs_config_valid(self):
        """Проверка структуры tabs-config.js"""
        content = TABS_CONFIG_JS.read_text(encoding="utf-8")
        assert "APP_TAB_DEFS" in content, "Отсутствует APP_TAB_DEFS"


class TestMenuConsistency:
    """Тесты согласованности конфигурации с зарегистрированными вкладками"""

    def test_menu_ids_match_tabs(self):
        """Проверка, что id из меню присутствуют в tabs-config.js"""
        with open(TC_MENU_CONFIG_PATH, "r", encoding="utf-8") as f:
            menu_config = json.load(f)

        content = TABS_CONFIG_JS.read_text(encoding="utf-8")
        tab_ids = re.findall(r"id:\s*['\"]([^'\"]+)['\"]", content)

        for item in menu_config["menu"]["topButtons"]:
            assert item["id"] in tab_ids, f"ID {item['id']} из topButtons не найден в tabs-config.js"

        for item in menu_config["menu"]["sidebarItems"]:
            assert item["id"] in tab_ids, f"ID {item['id']} из sidebarItems не найден в tabs-config.js"


class TestMenuEditorUI:
    """Тесты HTML-интерфейса редактора меню"""

    def test_menu_editor_button_exists(self):
        """Проверка кнопки редактора меню"""
        content = APPS_INDEX_HTML.read_text(encoding="utf-8")
        assert "menu-editor-btn" in content, "Отсутствует кнопка menu-editor-btn"
        assert "Редактор меню" in content, "Отсутствует текст 'Редактор меню'"

    def test_menu_editor_modal_exists(self):
        """Проверка модального окна редактора"""
        content = APPS_INDEX_HTML.read_text(encoding="utf-8")
        assert "menuEditorModal" in content, "Отсутствует модальное окно menuEditorModal"
        assert "allMenuEditor" in content, "Отсутствует контейнер allMenuEditor"
        assert "saveMenuConfig" in content, "Отсутствует кнопка saveMenuConfig"


class TestJavaScriptLogic:
    """Тесты логики JavaScript редактора меню"""

    def test_menu_editor_js_functions(self):
        """Проверка наличия функций управления меню в main.js"""
        content = APPS_MAIN_JS.read_text(encoding="utf-8")
        assert "initMenuEditor" in content, "Отсутствует функция initMenuEditor"
        assert "buildMenu" in content, "Отсутствует функция buildMenu"
        assert "loadRequiredTabs" in content, "Отсутствует функция loadRequiredTabs"

    def test_menu_editor_endpoint_and_instant_apply(self):
        """Проверка вызова эндпоинта /api/menu/config и мгновенного обновления интерфейса"""
        content = APPS_MAIN_JS.read_text(encoding="utf-8")
        assert "/api/menu/config" in content, "Отсутствует обращение к /api/menu/config"
        assert "buildMenu(appsMap, cfg)" in content or "buildMenu(" in content, "Отсутствует вызов buildMenu для мгновенного переопределения"

    def test_status_manager_fetches_apps_status(self):
        """Проверка получения статуса приложений в status-manager.js"""
        assert STATUS_MANAGER_JS.exists(), "status-manager.js не найден"
        content = STATUS_MANAGER_JS.read_text(encoding="utf-8")
        assert "apps/status" in content or "fetchAppsStatus" in content


class TestMenuAPI:
    """Тесты FastAPI роутера /api/menu/config"""

    @pytest.fixture
    def client(self):
        """Создает тестовый клиент FastAPI."""
        app = FastAPI()
        app.include_router(init_menu_router())
        return TestClient(app)

    def test_get_menu_config(self, client):
        """GET /api/menu/config должен возвращать валидную конфигурацию."""
        response = client.get("/api/menu/config")
        assert response.status_code == 200
        data = response.json()
        assert "menu" in data
        assert "topButtons" in data["menu"]
        assert "sidebarItems" in data["menu"]

    def test_post_menu_config_invalid(self, client):
        """POST /api/menu/config с невалидным телом должен возвращать ошибку 400."""
        response = client.post("/api/menu/config", json={"invalid": 123})
        assert response.status_code == 400

    def test_post_menu_config_success(self, client, monkeypatch, tmp_path):
        """POST /api/menu/config должен успешно сохранять конфигурацию."""
        fake_config_file = tmp_path / "tc_menu_config.json"
        fake_config_file.write_text(json.dumps({"version": "test", "menu": {"topButtons": [], "sidebarItems": []}}), encoding="utf-8")
        
        import src.api.router_menu as router_menu_module
        monkeypatch.setattr(router_menu_module, "TC_MENU_CONFIG_PATH", fake_config_file)

        payload = {
            "version": "test_v2",
            "menu": {
                "topButtons": [{"id": "system_inspector", "label": "Потребление", "tab": "tab-system-inspector", "order": 1, "visible": True}],
                "sidebarItems": [{"id": "about_system", "label": "О Системе", "tab": "tab-about-system", "order": 1, "visible": True}]
            }
        }
        response = client.post("/api/menu/config", json=payload)
        assert response.status_code == 200
        assert response.json().get("status") == "ok"

        saved_data = json.loads(fake_config_file.read_text(encoding="utf-8"))
        assert saved_data["version"] == "test_v2"
        assert len(saved_data["menu"]["topButtons"]) == 1

    def test_get_menu_config_su_target(self, client):
        """GET /api/menu/config?target=su должен возвращать конфигурацию для su без 'О системе'."""
        response = client.get("/api/menu/config?target=su")
        assert response.status_code == 200
        data = response.json()
        assert "menu" in data
        assert any(x.get("id") == "user_assistant" for x in data["menu"].get("sidebarItems", []))
        # Проверка отсутствия приложения 'О системе' у сценария su
        top_ids = [x.get("id") for x in data["menu"].get("topButtons", [])]
        sidebar_ids = [x.get("id") for x in data["menu"].get("sidebarItems", [])]
        assert "about_system" not in top_ids, "Приложение about_system не должно присутствовать в topButtons сценария su"
        assert "about_system" not in sidebar_ids, "Приложение about_system не должно присутствовать в sidebarItems сценария su"

