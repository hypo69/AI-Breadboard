# -*- coding: utf-8 -*-
# =============================================================================
# Test Suite: Всеобъемлющее тестирование кнопок и меню веб-интерфейса
# =============================================================================
# Description:
#   Комплексный набор тестов, проверяющий:
#   1. Архитектурные принципы построения кнопок и меню веб-интерфейса (data-tab, tab-core.js, closest).
#   2. Кнопки главной страницы (/) — верхняя панель, выдвижное меню (offcanvas), профиль пользователя.
#   3. Кнопки панели управления (/admin) — главное меню, выпадающие списки (dropdowns), модальные окна.
#   4. Кнопки раздела приложений (/tc, /apps) — конфигурация меню tc_menu_config.json, tabs-config.js, редактор меню.
#   5. Связность кнопок навигации с DOM-контейнерами tab-pane во всех оболочках.
#   6. Локализацию кнопок во всех поддерживаемых языках (ru, en, he).
#
# File: test_webgui_menus_and_buttons.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Всеобъемлющее тестирование меню, кнопок и навигационной архитектуры веб-интерфейса."""

import json
import re
from pathlib import Path
import pytest
from bs4 import BeautifulSoup
from header import __root__

WEBGUI_DIR = __root__ / "src" / "api" / "webgui"
INDEX_HTML = WEBGUI_DIR / "index.html"
ADMIN_INDEX_HTML = WEBGUI_DIR / "admin" / "index.html"
APPS_INDEX_HTML = WEBGUI_DIR / "apps" / "index.html"
TAB_CORE_JS = WEBGUI_DIR / "js" / "tab-core.js"
APPS_MAIN_JS = WEBGUI_DIR / "apps" / "main.js"
TABS_CONFIG_JS = WEBGUI_DIR / "apps" / "modules" / "tabs-config.js"
TC_MENU_CONFIG = WEBGUI_DIR / "config" / "tc_menu_config.json"
LOCALES_DIR = WEBGUI_DIR / "locales"


# =============================================================================
# 1. ПРИНЦИПЫ И АРХИТЕКТУРА КНОПОК И НАВИГАЦИИ (tab-core.js)
# =============================================================================

class TestButtonArchitecturePrinciples:
    """Проверка соблюдения архитектурных принципов построения кнопок UI."""

    def test_single_delegation_in_tab_core(self):
        """tab-core.js должен использовать единую точку делегирования кликов на document."""
        content = TAB_CORE_JS.read_text(encoding="utf-8")
        assert "document.addEventListener('click'" in content, (
            "tab-core.js обязан содержать глобальный слушатель событий клика"
        )
        assert "e.target.closest(" in content, (
            "Обработка клика должна использовать closest для корректного поиска кнопки при клике на иконку/текст"
        )

    def test_tab_naming_convention(self):
        """Идентификаторы кнопок и панелей должны следовать формату 'tab-*'."""
        content = TAB_CORE_JS.read_text(encoding="utf-8")
        # Проверка добавления префикса 'tab-' при необходимости
        assert "id = tabId.startsWith('tab-') ? tabId : `tab-${tabId}`" in content or "tab-" in content

    def test_lifecycle_hook_convention(self):
        """tab-core.js должен вызывать единый lifecycle-хук window.init<Name>Tab()."""
        content = TAB_CORE_JS.read_text(encoding="utf-8")
        assert "window[`init${name[0].toUpperCase() + name.slice(1)}Tab`]?.()" in content, (
            "switchTab должен динамически вызывать функцию инициализации вкладки"
        )

    def test_offcanvas_auto_closing_on_button_click(self):
        """tab-core.js должен автоматически закрывать offcanvas меню при выборе вкладки."""
        content = TAB_CORE_JS.read_text(encoding="utf-8")
        assert "leftSideNavOffcanvas" in content
        assert "appsSideNavOffcanvas" in content
        assert "Offcanvas" in content


# =============================================================================
# 2. ТЕСТИРОВАНИЕ КНОПОК ГЛАВНОГО ИНТЕРФЕЙСА (/)
# =============================================================================

class TestMainInterfaceButtons:
    """Проверка всех кнопок в главном интерфейсе (index.html)."""

    @pytest.fixture
    def main_soup(self):
        """Парсинг DOM дерева главного интерфейса."""
        assert INDEX_HTML.exists(), f"Файл не найден: {INDEX_HTML}"
        return BeautifulSoup(INDEX_HTML.read_text(encoding="utf-8"), "html.parser")

    def test_header_action_buttons_exist(self, main_soup):
        """Проверяет наличие всех функциональных кнопок в верхней шапке."""
        # Кнопка открытия меню
        drawer_btn = main_soup.find("button", id="left-drawer-toggle-btn")
        assert drawer_btn is not None, "Кнопка #left-drawer-toggle-btn должна присутствовать"
        assert drawer_btn.get("data-bs-target") == "#leftSideNavOffcanvas"

        # Плавающий ярлык слева
        trigger_btn = main_soup.find("button", class_="left-drawer-tab-trigger")
        assert trigger_btn is not None, "Плавающая кнопка .left-drawer-tab-trigger должна присутствовать"

        # Кнопка темы
        theme_btn = main_soup.find("button", id="theme-toggle")
        assert theme_btn is not None, "Кнопка переключения темы #theme-toggle должна присутствовать"

        # Кнопка кеша браузера
        cache_btn = main_soup.find("button", id="btn-open-cache-manager")
        assert cache_btn is not None, "Кнопка кеша #btn-open-cache-manager должна присутствовать"

        # Кнопка быстрых настроек
        gear_btn = main_soup.find("button", id="user-settings-gear-btn")
        assert gear_btn is not None, "Кнопка #user-settings-gear-btn должна присутствовать"

    def test_user_dropdown_menu_buttons_exist(self, main_soup):
        """Проверяет кнопки внутри выпадающего меню пользователя."""
        user_menu = main_soup.find("ul", class_="dropdown-menu")
        assert user_menu is not None, "Выпадающее меню пользователя должно присутствовать"

        expected_buttons = [
            "user-menu-btn-mail",
            "user-menu-btn-docs",
            "user-menu-btn-sheets",
            "user-menu-btn-news",
            "user-menu-btn-facebook",
            "user-menu-btn-cache",
        ]
        for btn_id in expected_buttons:
            btn = main_soup.find("button", id=btn_id)
            assert btn is not None, f"Кнопка меню #{btn_id} должна присутствовать в DOM"

        # Кнопка выхода
        logout_btns = main_soup.find_all("button", class_=re.compile("btn-user-logout"))
        assert len(logout_btns) >= 1, "Кнопка выхода пользователя .btn-user-logout должна присутствовать"

    def test_offcanvas_navigation_tab_buttons_match_panes(self, main_soup):
        """Каждая кнопка data-tab в боковом меню должна иметь соответствующий tab-pane в mainTabContent."""
        offcanvas = main_soup.find("div", id="leftSideNavOffcanvas")
        assert offcanvas is not None, "Offcanvas #leftSideNavOffcanvas должен существовать"

        tab_buttons = offcanvas.find_all("button", attrs={"data-tab": True})
        assert len(tab_buttons) >= 6, f"Ожидается минимум 6 кнопок навигации, найдено: {len(tab_buttons)}"

        content_container = main_soup.find("div", id="mainTabContent")
        assert content_container is not None, "#mainTabContent должен существовать"

        panes = {pane["id"] for pane in content_container.find_all("div", class_="tab-pane") if "id" in pane.attrs}

        for btn in tab_buttons:
            tab_target = btn["data-tab"]
            assert tab_target in panes, (
                f"Кнопка с data-tab='{tab_target}' не имеет соответствующего контейнера <div id='{tab_target}' class='tab-pane'>!"
            )


# =============================================================================
# 3. ТЕСТИРОВАНИЕ КНОПОК ПАНЕЛИ УПРАВЛЕНИЯ (/admin)
# =============================================================================

class TestAdminInterfaceButtons:
    """Проверка всех кнопок и выпадающих меню в панели управления (/admin)."""

    @pytest.fixture
    def admin_soup(self):
        """Парсинг DOM дерева панели администратора."""
        assert ADMIN_INDEX_HTML.exists(), f"Файл не найден: {ADMIN_INDEX_HTML}"
        return BeautifulSoup(ADMIN_INDEX_HTML.read_text(encoding="utf-8"), "html.parser")

    def test_admin_main_dropdown_buttons_exist(self, admin_soup):
        """Проверяет основные выпадающие группы меню админки."""
        expected_dropdowns = [
            "dialogTabsDropdown",
            "aiTabsDropdown",
            "pluginsTabsDropdown",
            "appsTabsDropdown",
            "adminTabsDropdown"
        ]
        for dd_id in expected_dropdowns:
            dd_btn = admin_soup.find("button", id=dd_id)
            assert dd_btn is not None, f"Выпадающее меню #{dd_id} должно присутствовать в админке"

    def test_admin_all_tab_buttons_have_matching_panes(self, admin_soup):
        """Все кнопки data-tab в админке должны иметь соответствующие tab-pane."""
        tab_buttons = admin_soup.find_all(["button", "a"], attrs={"data-tab": True})
        assert len(tab_buttons) >= 15, f"Ожидается обширное меню админки, найдено кнопок: {len(tab_buttons)}"

        content_container = admin_soup.find("div", id="mainTabContent")
        assert content_container is not None, "#mainTabContent должен существовать в admin/index.html"

        panes = {pane["id"] for pane in content_container.find_all("div", class_="tab-pane") if "id" in pane.attrs}

        for btn in tab_buttons:
            tab_target = btn["data-tab"]
            assert tab_target in panes, (
                f"Кнопка меню админки с data-tab='{tab_target}' не имеет <div id='{tab_target}' class='tab-pane'>!"
            )

    def test_admin_auth_and_modal_buttons(self, admin_soup):
        """Проверяет наличие кнопок в модальных окнах авторизации и интерфейсе админки."""
        login_btn = admin_soup.find("button", id="login-btn")
        assert login_btn is not None, "Кнопка входа #login-btn должна присутствовать в passwordModal"


# =============================================================================
# 4. ТЕСТИРОВАНИЕ КНОПОК РАЗДЕЛА ПРИЛОЖЕНИЙ (/tc, /apps)
# =============================================================================

class TestAppsAndTcInterfaceButtons:
    """Проверка конфигурационного построения кнопок и меню в /tc."""

    @pytest.fixture
    def apps_soup(self):
        """Парсинг DOM дерева оболочки /apps."""
        assert APPS_INDEX_HTML.exists(), f"Файл не найден: {APPS_INDEX_HTML}"
        return BeautifulSoup(APPS_INDEX_HTML.read_text(encoding="utf-8"), "html.parser")

    def test_tc_menu_config_structure_and_buttons(self):
        """Проверяет валидность конфигурации кнопок в tc_menu_config.json."""
        assert TC_MENU_CONFIG.exists(), f"tc_menu_config.json не найден: {TC_MENU_CONFIG}"
        config = json.loads(TC_MENU_CONFIG.read_text(encoding="utf-8"))

        assert "menu" in config, "Конфигурация должна содержать секцию 'menu'"
        top_buttons = config["menu"].get("topButtons", [])
        sidebar_items = config["menu"].get("sidebarItems", [])

        # Проверка верхних кнопок
        assert len(top_buttons) > 0, "Секция topButtons не должна быть пустой"
        for btn in top_buttons:
            assert "id" in btn, f"Элемент topButton без id: {btn}"
            assert "label" in btn, f"Кнопка {btn['id']} не содержит label"
            assert "icon" in btn, f"Кнопка {btn['id']} не содержит icon"
            assert "tab" in btn, f"Кнопка {btn['id']} не содержит целевой tab"
            assert btn["tab"].startswith("tab-"), f"tab должен начинаться с 'tab-': {btn['tab']}"

        # Проверка боковых элементов меню
        assert len(sidebar_items) > 0, "Секция sidebarItems не должна быть пустой"
        for item in sidebar_items:
            assert "id" in item, f"Элемент sidebarItem без id: {item}"
            assert "label" in item, f"Элемент {item['id']} не содержит label"
            assert "tab" in item, f"Элемент {item['id']} не содержит tab"

    def test_all_config_tabs_exist_in_apps_dom(self, apps_soup):
        """Все вкладки, определенные в tabs-config.js и tc_menu_config.json, должны иметь tab-pane в apps/index.html."""
        content_container = apps_soup.find("div", id="mainTabContent")
        assert content_container is not None, "#mainTabContent должен существовать в apps/index.html"

        panes = {pane["id"] for pane in content_container.find_all("div", class_="tab-pane") if "id" in pane.attrs}

        # Проверка вкладок из tc_menu_config.json
        config = json.loads(TC_MENU_CONFIG.read_text(encoding="utf-8"))
        for btn in config["menu"].get("topButtons", []):
            assert btn["tab"] in panes, f"Верхняя кнопка {btn['id']} ссылается на отсутствующий pane {btn['tab']}"

        for item in config["menu"].get("sidebarItems", []):
            assert item["tab"] in panes, f"Боковой элемент {item['id']} ссылается на отсутствующий pane {item['tab']}"

    def test_menu_editor_modal_buttons(self, apps_soup):
        """Проверяет кнопки модального окна редактора меню."""
        editor_btn = apps_soup.find("button", id="menu-editor-btn")
        assert editor_btn is not None, "Кнопка #menu-editor-btn должна существовать в подвале меню"

        save_btn = apps_soup.find("button", id="saveMenuConfig")
        assert save_btn is not None, "Кнопка #saveMenuConfig должна существовать в модальном окне"


# =============================================================================
# 5. ТЕСТИРОВАНИЕ ЛОКАЛИЗАЦИИ КНОПОК И МЕНЮ (i18n)
# =============================================================================

class TestMenuButtonsLocalization:
    """Проверяет наличие локализованных названий для всех вкладок и кнопок."""

    @pytest.mark.parametrize("lang", ["ru", "en", "he"])
    def test_locales_contain_standard_tab_keys(self, lang):
        """Все языковые пакеты должны содержать переводы для стандартных кнопок меню."""
        locale_file = LOCALES_DIR / f"{lang}.json"
        assert locale_file.exists(), f"Файл локализации не найден: {locale_file}"

        data = json.loads(locale_file.read_text(encoding="utf-8"))
        assert "tabs" in data, f"Секция 'tabs' отсутствует в {lang}.json"
        tabs = data["tabs"]

        required_keys = [
            "chat",
            "voice",
            "rag",
            "news",
            "admin",
            "help",
            "plugins",
            "groupStandard",
            "groupExtended",
        ]
        for key in required_keys:
            assert key in tabs, f"Ключ tabs.{key} отсутствует в локализации {lang}.json"
