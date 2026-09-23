# -*- coding: utf-8 -*-
# =============================================================================
# Test Suite: Тестирование делегирования событий меню /tc и /apps
# =============================================================================
# Description:
#   Проверяет корректность исправления бага: кнопки верхнего меню и бокового
#   меню в /tc не реагировали на клики, потому что обработчики событий
#   привязывались напрямую к кнопкам до их динамической генерации из
#   tc_menu_config.json. Исправление заменило прямую привязку на делегирование
#   событий через родительский контейнер.
#
# Bug: Кнопки верхнего меню /tc не открывали приложения (нет данных).
# Fix: Делегирование событий в setupTopMenuButtons(), setupSidebarButtons(),
#      setupNavTabs() — обработчик на контейнере, а не на каждой кнопке.
#
# Test Categories:
#   1. Happy Path     — Делегирование работает для статических кнопок
#   2. Edge Cases     — Кнопки без data-tab, пустые контейнеры
#   3. Type Variants  — Клик по дочернему элементу (иконка внутри кнопки)
#   4. Boundary Values — Множественные обработчики, повторная инициализация
#   5. Error Scenarios — Отсутствующий контейнер, disabled-вкладка
#   6. Regression     — JS-файлы содержат делегирование, не прямую привязку
#
# File: test_tc_menu_event_delegation.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты делегирования событий меню /tc — исправление бага с кнопками верхнего меню."""

import json
from pathlib import Path
import pytest
from header import __root__


WEBGUI_DIR = __root__ / "src" / "api" / "webgui"
APPS_MAIN_JS = WEBGUI_DIR / "apps" / "main.js"
TAB_MANAGER_JS = WEBGUI_DIR / "apps" / "modules" / "tab-manager.js"
TABS_CONFIG_JS = WEBGUI_DIR / "apps" / "modules" / "tabs-config.js"
APPS_INDEX_HTML = WEBGUI_DIR / "apps" / "index.html"
TC_MENU_CONFIG = WEBGUI_DIR / "config" / "tc_menu_config.json"


# =============================================================================
# 1. HAPPY PATH — делегирование присутствует в исправленных файлах
# =============================================================================

class TestEventDelegationHappyPath:
    """Проверяет, что исправленные файлы содержат делегирование событий."""

    def test_main_js_top_menu_uses_delegation_happy_path(self):
        """setupTopMenuButtons должна использовать делегирование через контейнер.

        Validates: addEventListener на контейнере, а не querySelectorAll по кнопкам.
        Dependencies: Кнопки верхнего меню /tc генерируются динамически из tc_menu_config.json.
        """
        # --- Arrange: читаем исправленный файл ---
        # Содержимое main.js после исправления бага
        content = APPS_MAIN_JS.read_text(encoding="utf-8")

        # --- Act: ищем паттерн делегирования ---
        # Делегирование: addEventListener на контейнере
        has_delegation = "topMenuContainer.addEventListener('click'" in content
        # Старый паттерн прямой привязки (должен отсутствовать)
        has_direct_binding = "querySelectorAll('.main-nav-container button[data-tab]')" in content

        # --- Assert ---
        assert has_delegation, (
            "setupTopMenuButtons() должна использовать делегирование событий "
            "(addEventListener на контейнере), а не прямую привязку к кнопкам"
        )
        assert not has_direct_binding, (
            "Старый паттерн querySelectorAll по кнопкам должен быть удалён — "
            "он не работает для динамически созданных кнопок"
        )

    def test_main_js_sidebar_uses_delegation_happy_path(self):
        """setupSidebarButtons должна использовать делегирование через #appsNavTabs.

        Validates: addEventListener на navTabs, а не forEach по .list-group-item.
        Dependencies: Боковое меню /tc генерируется динамически из tc_menu_config.json.
        """
        # --- Arrange ---
        content = APPS_MAIN_JS.read_text(encoding="utf-8")

        # --- Act ---
        # Делегирование на контейнере бокового меню
        has_delegation = (
            "navTabs.addEventListener('click'" in content
            or ("appsNavTabs" in content and "addEventListener" in content)
        )
        # Старый паттерн прямой привязки: forEach + addEventListener на каждой кнопке
        # (querySelectorAll для чтения списка вкладок — легитимно, проверяем именно forEach-привязку)
        has_direct_foreach_binding = (
            "sidebarButtons.forEach" in content
            and "btn.addEventListener" in content
        )

        # --- Assert ---
        assert has_delegation, (
            "setupSidebarButtons() должна использовать делегирование событий на #appsNavTabs"
        )
        assert not has_direct_foreach_binding, (
            "Старый паттерн sidebarButtons.forEach + btn.addEventListener должен быть удалён — "
            "он не работает для динамически созданных кнопок"
        )

    def test_tab_manager_setup_nav_tabs_uses_delegation_happy_path(self):
        """setupNavTabs() в tab-manager.js должна использовать делегирование.

        Validates: addEventListener на navTabs вместо forEach + btn.onclick.
        Dependencies: setupNavTabs вызывается из initAppsHub при инициализации.
        """
        # --- Arrange ---
        content = TAB_MANAGER_JS.read_text(encoding="utf-8")

        # --- Act ---
        has_delegation = "navTabs.addEventListener('click'" in content
        # Старый паттерн: btn.onclick = ...
        has_direct_onclick = "btn.onclick = " in content

        # --- Assert ---
        assert has_delegation, (
            "setupNavTabs() в tab-manager.js должна использовать делегирование событий"
        )
        assert not has_direct_onclick, (
            "btn.onclick = ... не работает для динамически созданных кнопок — "
            "должно быть заменено на делегирование"
        )


# =============================================================================
# 2. EDGE CASES — граничные случаи делегирования
# =============================================================================

class TestEventDelegationEdgeCases:
    """Граничные случаи: пустые контейнеры, кнопки без data-tab."""

    def test_delegation_handles_missing_data_tab_edge_case(self):
        """Делегирование должно игнорировать клики по элементам без data-tab.

        Validates: closest('button[data-tab]') возвращает null для элементов без атрибута.
        Dependencies: В контейнере могут быть другие элементы (разделители, иконки).
        """
        # --- Arrange: читаем код делегирования ---
        content = APPS_MAIN_JS.read_text(encoding="utf-8")

        # --- Act: проверяем наличие защитной проверки ---
        # closest() автоматически возвращает null если атрибут отсутствует
        has_closest_guard = "closest('button[data-tab]')" in content or "closest('[data-tab]')" in content

        # --- Assert ---
        assert has_closest_guard, (
            "Делегирование должно использовать closest() для поиска кнопки с data-tab, "
            "чтобы игнорировать клики по другим элементам контейнера"
        )

    def test_delegation_handles_null_container_edge_case(self):
        """Функции setupTopMenuButtons и setupSidebarButtons должны проверять наличие контейнера.

        Validates: Нет ошибки если контейнер отсутствует в DOM.
        Dependencies: На некоторых страницах контейнер может отсутствовать.
        """
        # --- Arrange ---
        content = APPS_MAIN_JS.read_text(encoding="utf-8")

        # --- Act: проверяем null-guard перед addEventListener ---
        # Паттерн: if (container) { container.addEventListener(...) }
        has_null_guard = (
            "if (topMenuContainer)" in content
            and "if (navTabs)" in content
        )

        # --- Assert ---
        assert has_null_guard, (
            "setupTopMenuButtons() и setupSidebarButtons() должны проверять "
            "наличие контейнера перед вызовом addEventListener"
        )

    def test_tc_menu_config_has_top_buttons_edge_case(self):
        """tc_menu_config.json должен содержать topButtons для верхнего меню.

        Validates: Конфиг содержит все 4 кнопки верхнего меню.
        Dependencies: initMenuFromConfig() читает этот файл для генерации кнопок.
        """
        # --- Arrange ---
        assert TC_MENU_CONFIG.exists(), f"tc_menu_config.json не найден: {TC_MENU_CONFIG}"
        config = json.loads(TC_MENU_CONFIG.read_text(encoding="utf-8"))

        # --- Act ---
        top_buttons = config.get("menu", {}).get("topButtons", [])
        top_button_ids = [btn["id"] for btn in top_buttons]

        # --- Assert ---
        assert len(top_buttons) >= 4, (
            f"Ожидается минимум 4 кнопки верхнего меню, найдено: {len(top_buttons)}"
        )
        assert "system_inspector" in top_button_ids, "Кнопка system_inspector должна быть в topButtons"
        assert "system_control_center" in top_button_ids, "Кнопка system_control_center должна быть в topButtons"
        assert "windows_defender" in top_button_ids, "Кнопка windows_defender должна быть в topButtons"
        assert "windows_sysadmin" in top_button_ids, "Кнопка windows_sysadmin должна быть в topButtons"


# =============================================================================
# 3. TYPE VARIANTS — клик по дочернему элементу (иконка внутри кнопки)
# =============================================================================

class TestEventDelegationTypeVariants:
    """Проверяет, что делегирование работает при клике по дочерним элементам."""

    def test_delegation_uses_closest_for_child_click_type_variant(self):
        """closest() должен подниматься вверх по DOM при клике на иконку внутри кнопки.

        Validates: e.target.closest('button[data-tab]') находит кнопку даже при клике на <i>.
        Dependencies: Кнопки содержат <i class="bi ..."> и <span> — клик может попасть на них.
        """
        # --- Arrange ---
        content = APPS_MAIN_JS.read_text(encoding="utf-8")

        # --- Act: проверяем использование e.target.closest() ---
        # closest() поднимается по DOM-дереву — решает проблему клика по дочерним элементам
        uses_closest = "e.target.closest(" in content

        # --- Assert ---
        assert uses_closest, (
            "Делегирование должно использовать e.target.closest() для обработки "
            "кликов по дочерним элементам кнопки (иконки, текст)"
        )

    def test_tab_manager_delegation_handles_data_bs_target_type_variant(self):
        """setupNavTabs должна обрабатывать как data-tab, так и data-bs-target.

        Validates: Поддержка обоих атрибутов для совместимости с Bootstrap.
        Dependencies: Некоторые кнопки используют data-bs-target вместо data-tab.
        """
        # --- Arrange ---
        content = TAB_MANAGER_JS.read_text(encoding="utf-8")

        # --- Act ---
        handles_data_tab = "data-tab" in content
        handles_data_bs_target = "data-bs-target" in content

        # --- Assert ---
        assert handles_data_tab, "setupNavTabs должна обрабатывать атрибут data-tab"
        assert handles_data_bs_target, (
            "setupNavTabs должна обрабатывать атрибут data-bs-target для совместимости с Bootstrap"
        )


# =============================================================================
# 4. BOUNDARY VALUES — множественные обработчики, повторная инициализация
# =============================================================================

class TestEventDelegationBoundaryValues:
    """Граничные значения: повторный вызов setup-функций, много кнопок."""

    def test_delegation_single_listener_per_container_boundary(self):
        """Каждый контейнер должен получать ровно один addEventListener.

        Validates: Нет дублирования обработчиков при повторном вызове setup-функций.
        Dependencies: initAppsHub вызывается один раз, но это важно для будущих изменений.
        """
        # --- Arrange ---
        content = APPS_MAIN_JS.read_text(encoding="utf-8")

        # --- Act: считаем количество addEventListener для topMenuContainer ---
        top_menu_listeners = content.count("topMenuContainer.addEventListener")
        sidebar_listeners = content.count("navTabs.addEventListener")

        # --- Assert ---
        assert top_menu_listeners == 1, (
            f"topMenuContainer должен получать ровно 1 обработчик, найдено: {top_menu_listeners}"
        )
        assert sidebar_listeners == 1, (
            f"navTabs должен получать ровно 1 обработчик, найдено: {sidebar_listeners}"
        )

    def test_tc_menu_config_sidebar_items_count_boundary(self):
        """tc_menu_config.json должен содержать все элементы бокового меню.

        Validates: Конфиг содержит минимум 10 элементов sidebar.
        Dependencies: Боковое меню генерируется из sidebarItems.
        """
        # --- Arrange ---
        config = json.loads(TC_MENU_CONFIG.read_text(encoding="utf-8"))

        # --- Act ---
        sidebar_items = config.get("menu", {}).get("sidebarItems", [])

        # --- Assert ---
        assert len(sidebar_items) >= 10, (
            f"Ожидается минимум 10 элементов бокового меню, найдено: {len(sidebar_items)}"
        )

    def test_all_top_buttons_have_required_fields_boundary(self):
        """Каждая кнопка верхнего меню должна иметь id, label, icon, tab.

        Validates: Структура данных корректна для генерации кнопок.
        Dependencies: initMenuFromConfig() использует эти поля для создания кнопок.
        """
        # --- Arrange ---
        config = json.loads(TC_MENU_CONFIG.read_text(encoding="utf-8"))
        top_buttons = config.get("menu", {}).get("topButtons", [])

        # --- Act & Assert ---
        for btn in top_buttons:
            assert "id" in btn, f"Кнопка без id: {btn}"
            assert "label" in btn, f"Кнопка {btn.get('id')} без label"
            assert "icon" in btn, f"Кнопка {btn.get('id')} без icon"
            assert "tab" in btn, f"Кнопка {btn.get('id')} без tab"
            assert btn["tab"].startswith("tab-"), (
                f"Значение tab кнопки {btn['id']} должно начинаться с 'tab-', "
                f"получено: {btn['tab']}"
            )


# =============================================================================
# 5. ERROR SCENARIOS — отсутствующий контейнер, disabled-вкладка
# =============================================================================

class TestEventDelegationErrorScenarios:
    """Проверяет корректную обработку ошибочных ситуаций."""

    def test_switch_tab_checks_disabled_status_error_scenario(self):
        """switchTab должна проверять статус enabled перед переключением.

        Validates: Отключённые вкладки не активируются при клике.
        Dependencies: appsStatusMap заполняется из /api/apps/status.
        """
        # --- Arrange ---
        content = TAB_MANAGER_JS.read_text(encoding="utf-8")

        # --- Act ---
        has_disabled_check = (
            "enabled === false" in content
            or "statusEntry.enabled" in content
        )

        # --- Assert ---
        assert has_disabled_check, (
            "switchTab() должна проверять статус enabled из appsStatusMap "
            "и не переключать отключённые вкладки"
        )

    def test_delegation_uses_e_prevent_default_error_scenario(self):
        """Делегирование должно вызывать e.preventDefault() для предотвращения стандартного поведения.

        Validates: Нет нежелательной навигации браузера при клике на кнопку.
        Dependencies: Кнопки могут иметь href или быть внутри форм.
        """
        # --- Arrange ---
        content = APPS_MAIN_JS.read_text(encoding="utf-8")

        # --- Act ---
        has_prevent_default = "e.preventDefault()" in content

        # --- Assert ---
        assert has_prevent_default, (
            "Обработчики делегирования должны вызывать e.preventDefault() "
            "для предотвращения стандартного поведения браузера"
        )

    def test_apps_index_html_has_top_menu_container_error_scenario(self):
        """index.html должен содержать контейнер верхнего меню с нужным классом.

        Validates: Контейнер .d-flex.gap-1.flex-wrap существует в DOM.
        Dependencies: setupTopMenuButtons() ищет этот контейнер через querySelector.
        """
        # --- Arrange ---
        content = APPS_INDEX_HTML.read_text(encoding="utf-8")

        # --- Act ---
        has_top_menu_container = "d-flex align-items-center gap-1 flex-wrap" in content
        has_apps_nav_tabs = 'id="appsNavTabs"' in content

        # --- Assert ---
        assert has_top_menu_container, (
            "index.html должен содержать контейнер верхнего меню "
            "с классами 'd-flex align-items-center gap-1 flex-wrap'"
        )
        assert has_apps_nav_tabs, (
            "index.html должен содержать элемент с id='appsNavTabs' "
            "для бокового меню"
        )


# =============================================================================
# 6. REGRESSION — JS-файлы не содержат старых паттернов прямой привязки
# =============================================================================

class TestEventDelegationRegression:
    """Регрессионные тесты: старые паттерны прямой привязки удалены."""

    def test_no_direct_binding_in_setup_top_menu_regression(self):
        """setupTopMenuButtons не должна использовать forEach + addEventListener на каждой кнопке.

        Validates: Старый паттерн прямой привязки полностью удалён.
        Dependencies: Этот паттерн был причиной бага — кнопки не работали после динамической генерации.
        """
        # --- Arrange ---
        content = APPS_MAIN_JS.read_text(encoding="utf-8")

        # --- Act: ищем старый паттерн ---
        # Старый код: topMenuButtons.forEach(btn => { btn.addEventListener('click', ...) })
        old_pattern_foreach = (
            "topMenuButtons.forEach" in content
            and "btn.addEventListener" in content
        )

        # --- Assert ---
        assert not old_pattern_foreach, (
            "Старый паттерн topMenuButtons.forEach + btn.addEventListener должен быть удалён. "
            "Он не работает для динамически созданных кнопок из tc_menu_config.json"
        )

    def test_no_direct_onclick_in_setup_nav_tabs_regression(self):
        """setupNavTabs не должна использовать btn.onclick = ... для каждой кнопки.

        Validates: Старый паттерн btn.onclick удалён из tab-manager.js.
        Dependencies: btn.onclick не работает для кнопок, созданных после вызова setupNavTabs().
        """
        # --- Arrange ---
        content = TAB_MANAGER_JS.read_text(encoding="utf-8")

        # --- Act ---
        has_old_onclick = "btn.onclick = " in content

        # --- Assert ---
        assert not has_old_onclick, (
            "Старый паттерн btn.onclick = ... должен быть удалён из setupNavTabs(). "
            "Используется делегирование событий через addEventListener на контейнере"
        )

    def test_apps_main_js_still_exports_switch_tab_regression(self):
        """window.switchTab должна по-прежнему экспортироваться глобально.

        Validates: Исправление не сломало глобальный экспорт switchTab.
        Dependencies: HTML-кнопки и плагины вызывают window.switchTab() напрямую.
        """
        # --- Arrange ---
        content = APPS_MAIN_JS.read_text(encoding="utf-8")

        # --- Act ---
        has_global_switch_tab = "window.switchTab = switchTab" in content
        has_global_switch_to_tab = "window.switchToTab = switchTab" in content

        # --- Assert ---
        assert has_global_switch_tab, (
            "window.switchTab должна экспортироваться глобально — "
            "используется в HTML onclick и плагинах"
        )
        assert has_global_switch_to_tab, (
            "window.switchToTab должна экспортироваться глобально — "
            "алиас для обратной совместимости"
        )

    def test_tab_manager_still_exports_all_functions_regression(self):
        """tab-manager.js должен экспортировать все 4 публичные функции.

        Validates: Рефакторинг не удалил ни одну из экспортируемых функций.
        Dependencies: main.js импортирует setupNavTabs, switchTab, loadTabContent.
        """
        # --- Arrange ---
        content = TAB_MANAGER_JS.read_text(encoding="utf-8")

        # --- Act ---
        exports = {
            "onTabSwitched": "export function onTabSwitched" in content,
            "switchTab": "export function switchTab" in content,
            "setupNavTabs": "export function setupNavTabs" in content,
            "loadTabContent": "export async function loadTabContent" in content,
        }

        # --- Assert ---
        for func_name, is_exported in exports.items():
            assert is_exported, (
                f"Функция {func_name} должна быть экспортирована из tab-manager.js"
            )

    def test_tc_menu_config_json_is_valid_json_regression(self):
        """tc_menu_config.json должен быть валидным JSON.

        Validates: Файл конфигурации не повреждён.
        Dependencies: initMenuFromConfig() парсит этот файл через fetch + .json().
        """
        # --- Arrange ---
        assert TC_MENU_CONFIG.exists(), f"tc_menu_config.json не найден: {TC_MENU_CONFIG}"

        # --- Act ---
        try:
            config = json.loads(TC_MENU_CONFIG.read_text(encoding="utf-8"))
            is_valid = True
        except json.JSONDecodeError as e:
            is_valid = False
            error_msg = str(e)

        # --- Assert ---
        assert is_valid, (
            f"tc_menu_config.json содержит невалидный JSON: {error_msg if not is_valid else ''}"
        )
        assert "menu" in config, "tc_menu_config.json должен содержать ключ 'menu'"
        assert "topButtons" in config["menu"], "menu должен содержать 'topButtons'"
        assert "sidebarItems" in config["menu"], "menu должен содержать 'sidebarItems'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
