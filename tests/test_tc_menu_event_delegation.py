# -*- coding: utf-8 -*-
# =============================================================================
# Test Suite: Тестирование делегирования событий меню /tc и /apps
# =============================================================================
# Description:
#   Проверяет корректность работы меню и вкладок в /tc:
#   1. Единое делегирование кликов по кнопкам data-tab через tab-core.js.
#   2. Загрузка HTML и JS содержимого для всех кнопок вкладок (верхнее и боковое меню).
#   3. Наличие всех контейнеров вкладок в index.html.
#   4. Валидность конфигурации меню tc_menu_config.json.
#
# File: test_tc_menu_event_delegation.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты делегирования событий меню /tc — проверка работы кнопок меню и загрузки вкладок."""

import json
from pathlib import Path
import pytest
from header import __root__


WEBGUI_DIR = __root__ / "src" / "api" / "webgui"
APPS_MAIN_JS = WEBGUI_DIR / "apps" / "main.js"
TAB_CORE_JS = WEBGUI_DIR / "js" / "tab-core.js"
TABS_CONFIG_JS = WEBGUI_DIR / "apps" / "modules" / "tabs-config.js"
APPS_INDEX_HTML = WEBGUI_DIR / "apps" / "index.html"
TC_MENU_CONFIG = WEBGUI_DIR / "config" / "tc_menu_config.json"


# =============================================================================
# 1. HAPPY PATH — делегирование и загрузка вкладок присутствуют в файлах
# =============================================================================

class TestEventDelegationHappyPath:
    """Проверяет, что файлы содержат делегирование событий и загрузку всех вкладок."""

    def test_tab_core_uses_delegation_happy_path(self):
        """tab-core.js должен использовать глобальное делегирование кликов."""
        content = TAB_CORE_JS.read_text(encoding="utf-8")
        assert "document.addEventListener('click'" in content, (
            "tab-core.js должен содержать document.addEventListener('click')"
        )
        assert "e.target.closest(" in content, (
            "tab-core.js должен использовать closest() для обработки кликов"
        )

    def test_main_js_loads_all_tabs_happy_path(self):
        """apps/main.js должен загружать все вкладки, включая верхнее меню."""
        content = APPS_MAIN_JS.read_text(encoding="utf-8")
        assert "querySelectorAll('[data-tab]')" in content, (
            "apps/main.js должен выбирать все элементы с [data-tab] для загрузки HTML/JS, "
            "а не только #appsNavTabs"
        )

    def test_apps_main_js_calls_setup_tab_clicks_happy_path(self):
        """apps/main.js должен вызывать setupTabClicks()."""
        content = APPS_MAIN_JS.read_text(encoding="utf-8")
        assert "setupTabClicks()" in content, (
            "apps/main.js должен инициализировать обработчик кликов через setupTabClicks()"
        )


# =============================================================================
# 2. EDGE CASES — граничные случаи делегирования
# =============================================================================

class TestEventDelegationEdgeCases:
    """Граничные случаи: пустые контейнеры, кнопки без data-tab."""

    def test_delegation_handles_missing_data_tab_edge_case(self):
        """Делегирование должно искать только элементы с data-tab."""
        content = TAB_CORE_JS.read_text(encoding="utf-8")
        has_closest_guard = "closest('button[data-tab], a[data-tab]')" in content or "closest('[data-tab]')" in content
        assert has_closest_guard, (
            "Делегирование должно использовать closest() с селектором data-tab"
        )

    def test_tc_menu_config_has_top_buttons_edge_case(self):
        """tc_menu_config.json должен содержать topButtons для верхнего меню."""
        assert TC_MENU_CONFIG.exists(), f"tc_menu_config.json не найден: {TC_MENU_CONFIG}"
        config = json.loads(TC_MENU_CONFIG.read_text(encoding="utf-8"))
        top_buttons = config.get("menu", {}).get("topButtons", [])
        top_button_ids = [btn["id"] for btn in top_buttons]

        assert len(top_buttons) >= 4, (
            f"Ожидается минимум 4 кнопки верхнего меню, найдено: {len(top_buttons)}"
        )
        assert "system_inspector" in top_button_ids
        assert "system_control_center" in top_button_ids
        assert "windows_defender" in top_button_ids
        assert "windows_sysadmin" in top_button_ids


# =============================================================================
# 3. TYPE VARIANTS — клик по дочернему элементу (иконка внутри кнопки)
# =============================================================================

class TestEventDelegationTypeVariants:
    """Проверяет, что делегирование работает при клике по дочерним элементам."""

    def test_delegation_uses_closest_for_child_click_type_variant(self):
        """closest() должен подниматься вверх по DOM при клике на иконку внутри кнопки."""
        content = TAB_CORE_JS.read_text(encoding="utf-8")
        assert "e.target.closest(" in content, (
            "Делегирование должно использовать e.target.closest() для обработки кликов"
        )


# =============================================================================
# 4. BOUNDARY VALUES — валидация конфигурации меню
# =============================================================================

class TestEventDelegationBoundaryValues:
    """Граничные значения: структура конфига меню."""

    def test_tc_menu_config_sidebar_items_count_boundary(self):
        """tc_menu_config.json должен содержать все элементы бокового меню."""
        config = json.loads(TC_MENU_CONFIG.read_text(encoding="utf-8"))
        sidebar_items = config.get("menu", {}).get("sidebarItems", [])
        assert len(sidebar_items) >= 10, (
            f"Ожидается минимум 10 элементов бокового меню, найдено: {len(sidebar_items)}"
        )

    def test_all_top_buttons_have_required_fields_boundary(self):
        """Каждая кнопка верхнего меню должна иметь id, label, icon, tab."""
        config = json.loads(TC_MENU_CONFIG.read_text(encoding="utf-8"))
        top_buttons = config.get("menu", {}).get("topButtons", [])

        for btn in top_buttons:
            assert "id" in btn, f"Кнопка без id: {btn}"
            assert "label" in btn, f"Кнопка {btn.get('id')} без label"
            assert "icon" in btn, f"Кнопка {btn.get('id')} без icon"
            assert "tab" in btn, f"Кнопка {btn.get('id')} без tab"
            assert btn["tab"].startswith("tab-"), (
                f"Значение tab кнопки {btn['id']} должно начинаться с 'tab-', получено: {btn['tab']}"
            )


# =============================================================================
# 5. ERROR SCENARIOS — наличие DOM-контейнеров
# =============================================================================

class TestEventDelegationErrorScenarios:
    """Проверяет корректную структуру DOM для вкладок верхнего меню."""

    def test_apps_index_html_has_top_menu_container_error_scenario(self):
        """index.html должен содержать контейнер верхнего меню с нужным классом."""
        content = APPS_INDEX_HTML.read_text(encoding="utf-8")
        assert "main-nav-container" in content, "index.html должен содержать main-nav-container"
        assert 'id="appsNavTabs"' in content, "index.html должен содержать appsNavTabs"

    def test_apps_index_html_has_top_buttons_panes(self):
        """index.html должен содержать контейнеры tab-pane для всех верхних кнопок."""
        content = APPS_INDEX_HTML.read_text(encoding="utf-8")
        assert 'id="tab-system-inspector"' in content
        assert 'id="tab-system-control"' in content
        assert 'id="tab-defender"' in content
        assert 'id="tab-windows-admin"' in content


# =============================================================================
# 6. REGRESSION — экспорт функций навигации
# =============================================================================

class TestEventDelegationRegression:
    """Регрессионные тесты."""

    def test_apps_main_js_still_exports_switch_tab_regression(self):
        """window.switchTab должна экспортироваться глобально."""
        content = APPS_MAIN_JS.read_text(encoding="utf-8")
        assert "window.switchTab = switchTab" in content
        assert "window.switchToTab = switchTab" in content

    def test_tab_core_exports_all_functions(self):
        """tab-core.js должен экспортировать switchTab, loadTab, setupTabClicks."""
        content = TAB_CORE_JS.read_text(encoding="utf-8")
        assert "export function switchTab" in content
        assert "export async function loadTab" in content
        assert "export function setupTabClicks" in content

    def test_tc_menu_config_json_is_valid_json_regression(self):
        """tc_menu_config.json должен быть валидным JSON."""
        assert TC_MENU_CONFIG.exists(), f"tc_menu_config.json не найден: {TC_MENU_CONFIG}"
        try:
            config = json.loads(TC_MENU_CONFIG.read_text(encoding="utf-8"))
            is_valid = True
        except json.JSONDecodeError:
            is_valid = False

        assert is_valid, "tc_menu_config.json содержит невалидный JSON"
        assert "menu" in config
        assert "topButtons" in config["menu"]
        assert "sidebarItems" in config["menu"]
