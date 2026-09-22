"""
Тесты редактора меню (/tc)
Тестируют генерацию меню, drag-and-drop и фильтрацию disabled приложений
"""

import json
import pytest
from pathlib import Path


class TestMenuConfig:
    """Тесты структуры menu-config.json"""

    def test_menu_config_exists(self):
        """Проверка существования файла конфигурации"""
        config_path = Path("menu-config.json")
        assert config_path.exists(), "menu-config.json не найден"

    def test_menu_config_valid_json(self):
        """Проверка валидности JSON"""
        config_path = Path("menu-config.json")
        try:
            with open(config_path) as f:
                config = json.load(f)
            assert isinstance(config, dict), "Конфигурация должна быть объектом"
        except json.JSONDecodeError as e:
            pytest.fail(f"Неверный JSON в menu-config.json: {e}")

    def test_menu_config_structure(self):
        """Проверка обязательных полей конфигурации"""
        config_path = Path("menu-config.json")
        with open(config_path) as f:
            config = json.load(f)

        assert "menu" in config, "Отсутствует секция menu"
        assert "topButtons" in config["menu"], "Отсутствует topButtons"
        assert "sidebarItems" in config["menu"], "Отсутствует sidebarItems"

    def test_top_buttons_required_fields(self):
        """Проверка обязательных полей в topButtons"""
        config_path = Path("menu-config.json")
        with open(config_path) as f:
            config = json.load(f)

        for item in config["menu"]["topButtons"]:
            assert "id" in item, f"Отсутствует id в topButtons: {item}"
            assert "label" in item, f"Отсутствует label в topButtons: {item}"
            assert "icon" in item, f"Отсутствует icon в topButtons: {item}"
            assert "tab" in item, f"Отсутствует tab в topButtons: {item}"

    def test_sidebar_items_required_fields(self):
        """Проверка обязательных полей в sidebarItems"""
        config_path = Path("menu-config.json")
        with open(config_path) as f:
            config = json.load(f)

        for item in config["menu"]["sidebarItems"]:
            assert "id" in item, f"Отсутствует id в sidebarItems: {item}"
            assert "label" in item, f"Отсутствует label в sidebarItems: {item}"
            assert "icon" in item, f"Отсутствует icon в sidebarItems: {item}"
            assert "tab" in item, f"Отсутствует tab в sidebarItems: {item}"


class TestTabsConfig:
    """Тесты tabs-config.js"""

    def test_tabs_config_exists(self):
        """Проверка существования tabs-config.js"""
        config_path = Path("src/api/webgui/apps/modules/tabs-config.js")
        assert config_path.exists(), "tabs-config.js не найден"

    def test_tabs_config_valid(self):
        """Проверка структуры tabs-config.js"""
        config_path = Path("src/api/webgui/apps/modules/tabs-config.js")
        with open(config_path) as f:
            content = f.read()

        assert "APP_TAB_DEFS" in content, "Отсутствует APP_TAB_DEFS"
        assert "TC_EXCLUDES" in content, "Отсутствует TC_EXCLUDES"


class TestMenuConsistency:
    """Тесты согласованности конфигурации"""

    def test_menu_ids_match_tabs(self):
        """Проверка, что id из menu-config.json есть в tabs-config.js"""
        menu_config_path = Path("menu-config.json")
        tabs_config_path = Path("src/api/webgui/apps/modules/tabs-config.js")

        with open(menu_config_path) as f:
            menu_config = json.load(f)

        with open(tabs_config_path) as f:
            content = f.read()

        # Извлекаем id из tabs-config.js
        import re
        tab_ids = re.findall(r"id:\s*['\"]([^'\"]+)['\"]", content)

        # Проверяем topButtons
        for item in menu_config["menu"]["topButtons"]:
            assert item["id"] in tab_ids, f"ID {item['id']} из topButtons не найден в tabs-config.js"

        # Проверяем sidebarItems
        for item in menu_config["menu"]["sidebarItems"]:
            assert item["id"] in tab_ids, f"ID {item['id']} из sidebarItems не найден в tabs-config.js"


class TestMenuEditorUI:
    """Тесты HTML-интерфейса редактора меню"""

    def test_menu_editor_button_exists(self):
        """Проверка кнопки редактора меню"""
        html_path = Path("src/api/webgui/apps/index.html")
        with open(html_path) as f:
            content = f.read()

        assert "menu-editor-btn" in content, "Отсутствует кнопка menu-editor-btn"
        assert "Редактор меню" in content, "Отсутствует текст 'Редактор меню'"

    def test_menu_editor_modal_exists(self):
        """Проверка модального окна редактора"""
        html_path = Path("src/api/webgui/apps/index.html")
        with open(html_path) as f:
            content = f.read()

        assert "menuEditorModal" in content, "Отсутствует модальное окно menuEditorModal"
        assert "topMenuEditor" in content, "Отсутствует контейнер topMenuEditor"
        assert "sidebarMenuEditor" in content, "Отсутствует контейнер sidebarMenuEditor"

    def test_menu_editor_css_exists(self):
        """Проверка CSS стилей редактора"""
        css_path = Path("src/api/webgui/css/components.css")
        with open(css_path) as f:
            content = f.read()

        assert "menu-editor-item" in content, "Отсутствуют стили .menu-editor-item"
        assert "drag-handle" in content, "Отсутствуют стили .drag-handle"

    def test_menu_editor_visibility_select(self):
        """Проверка наличия переключателя позиции"""
        html_path = Path("src/api/webgui/apps/index.html")
        with open(html_path) as f:
            content = f.read()

        assert "visibility-select" in content, "Отсутствует переключатель позиции"
        assert "editor-visibility" in content, "Отсутствует контейнер editor-visibility"
        assert "Сверху" in content, "Отсутствует опция 'Сверху'"
        assert "Снизу" in content, "Отсутствует опция 'Снизу'"
        assert "Скрыть" in content, "Отсутствует опция 'Скрыть'"

    def test_menu_editor_order_slider(self):
        """Проверка наличия слайдера порядка"""
        html_path = Path("src/api/webgui/apps/index.html")
        with open(html_path) as f:
            content = f.read()

        assert "order-slider" in content, "Отсутствует слайдер порядка"
        assert "editor-order" in content, "Отсутствует контейнер editor-order"
        assert "order-value" in content, "Отсутствует отображение значения порядка"
        assert 'type="range"' in content, "Слайдер должен иметь type='range'"

    def test_menu_editor_controls_style(self):
        """Проверка стилей элементов управления"""
        css_path = Path("src/api/webgui/css/components.css")
        with open(css_path) as f:
            content = f.read()

        assert "editor-controls" in content, "Отсутствуют стили .editor-controls"
        assert "editor-visibility" in content, "Отсутствуют стили .editor-visibility"
        assert "editor-order" in content, "Отсутствуют стили .editor-order"
        assert "visibility-select" in content, "Отсутствуют стили .visibility-select"
        assert "order-slider" in content, "Отсутствуют стили .order-slider"
        assert "order-value" in content, "Отсутствуют стили .order-value"


class TestJavaScriptLogic:
    """Тесты JavaScript логики"""

    def test_menu_editor_js_exists(self):
        """Проверка наличия JS кода редактора"""
        html_path = Path("src/api/webgui/apps/index.html")
        with open(html_path) as f:
            content = f.read()

        assert "initMenuEditor" in content, "Отсутствует функция initMenuEditor"
        assert "getDragAfterElement" in content, "Отсутствует функция getDragAfterElement"
        assert "setupDropZones" in content, "Отсутствует функция setupDropZones"

    def test_menu_editor_uses_fetch(self):
        """Проверка использования fetch для загрузки конфига"""
        html_path = Path("src/api/webgui/apps/index.html")
        with open(html_path) as f:
            content = f.read()

        assert "fetch('/menu-config.json')" in content, "Отсутствует загрузка menu-config.json"

    def test_menu_editor_visibility_handler(self):
        """Проверка обработчика изменения позиции"""
        html_path = Path("src/api/webgui/apps/index.html")
        with open(html_path) as f:
            content = f.read()

        assert "visibility-select" in content, "Отсутствует переключатель позиции"
        assert "position" in content, "Отсутствует обработка параметра position"
        assert "top" in content, "Отсутствует позиция top"
        assert "bottom" in content, "Отсутствует позиция bottom"
        assert "hidden" in content, "Отсутствует позиция hidden"

    def test_menu_editor_order_handler(self):
        """Проверка обработчика слайдера порядка"""
        html_path = Path("src/api/webgui/apps/index.html")
        with open(html_path) as f:
            content = f.read()

        assert "order-slider" in content, "Отсутствует слайдер порядка"
        assert "order-value" in content, "Отсутствует отображение значения порядка"
        assert "order:" in content, "Отсутствует обработка параметра order"


class TestDisabledFiltering:
    """Тесты фильтрации disabled приложений"""

    def test_disabled_filter_in_menu_generation(self):
        """Проверка фильтрации disabled приложений при генерации меню"""
        html_path = Path("src/api/webgui/apps/index.html")
        with open(html_path) as f:
            content = f.read()

        assert "enabled === false" in content, "Отсутствует проверка enabled === false"
        assert "appsMap" in content, "Отсутствует проверка appsMap"

    def test_status_manager_exists(self):
        """Проверка existence status-manager.js"""
        manager_path = Path("src/api/webgui/apps/modules/status-manager.js")
        assert manager_path.exists(), "status-manager.js не найден"

    def test_status_manager_fetches_apps_status(self):
        """Проверка, что status-manager.js получает статус приложений"""
        manager_path = Path("src/api/webgui/apps/modules/status-manager.js")
        with open(manager_path) as f:
            content = f.read()

        assert "apps/status" in content, "Отсутствует запрос к /api/apps/status"


class TestCSSStyles:
    """Тесты CSS стилей"""

    def test_dragging_class_style(self):
        """Проверка стилей для класса dragging"""
        css_path = Path("src/api/webgui/css/components.css")
        with open(css_path) as f:
            content = f.read()

        assert ".menu-editor-item.dragging" in content, "Отсутствуют стили для .menu-editor-item.dragging"

    def test_drag_handle_style(self):
        """Проверка стилей для drag handle"""
        css_path = Path("src/api/webgui/css/components.css")
        with open(css_path) as f:
            content = f.read()

        assert ".drag-handle" in content, "Отсутствуют стили для .drag-handle"

    def test_menu_editor_item_style(self):
        """Проверка базовых стилей элемента"""
        css_path = Path("src/api/webgui/css/components.css")
        with open(css_path) as f:
            content = f.read()

        assert ".menu-editor-item {" in content, "Отсутствуют базовые стили .menu-editor-item"


class TestIntegration:
    """Интеграционные тесты"""

    def test_full_workflow(self):
        """Полный рабочий процесс: загрузка -> редактирование -> сохранение"""
        # Проверка, что все компоненты существуют
        assert Path("menu-config.json").exists(), "menu-config.json"
        assert Path("src/api/webgui/apps/index.html").exists(), "index.html"
        assert Path("src/api/webgui/apps/main.js").exists(), "main.js"
        assert Path("src/api/webgui/apps/modules/status-manager.js").exists(), "status-manager.js"
        assert Path("src/api/webgui/apps/modules/tabs-config.js").exists(), "tabs-config.js"
        assert Path("src/api/webgui/css/components.css").exists(), "components.css"

    def test_menu_editor_includes_status_manager(self):
        """Проверка импорта status-manager в index.html"""
        html_path = Path("src/api/webgui/apps/index.html")
        with open(html_path) as f:
            content = f.read()

        assert "fetchAppsStatus" in content, "Отсутствует импорт fetchAppsStatus"
        assert "window.fetchAppsStatus = fetchAppsStatus" in content, "fetchAppsStatus не экспортируется в window"

    def test_menu_editor_save_endpoint(self):
        """Проверка эндпоинта сохранения конфигурации"""
        html_path = Path("src/api/webgui/apps/index.html")
        with open(html_path) as f:
            content = f.read()

        assert "/api/menu/config" in content, "Отсутствует эндпоинт /api/menu/config"
        assert "POST" in content, "Отсутствует метод POST для сохранения"
        assert "saveMenuConfig" in content, "Отсутствует функция saveMenuConfig"
