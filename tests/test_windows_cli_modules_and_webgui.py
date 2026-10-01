# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Windows Cli Modules And Webgui
# =============================================================================
# Description:
#   Скрипт/модуль системы AI-Breadboard (`test_windows_cli_modules_and_webgui`).
#
# Usage Examples:
#   Python API:
#     from tests.test_windows_cli_modules_and_webgui import test_tabs_config_contains_all_new_modules
#
#     res = test_tabs_config_contains_all_new_modules()
#
# File: test_windows_cli_modules_and_webgui.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:43
# =============================================================================

"""Скрипт/модуль системы AI-Breadboard (`test_windows_cli_modules_and_webgui`)."""

# -*- coding: utf-8 -*-
# =============================================================================
# Test Name: Windows CLI Modules & WebGUI Tabs Integration Test
# =============================================================================
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.windows.main import create_windows_app

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULES = [
    'storage_manager',
    'boot_recovery',
    'servicing_integrity',
    'services_manager',
    'task_scheduler',
    'process_manager',
    'firewall_manager',
    'security_acl',
    'performance_tracing',
    'event_logs',
    'software_manager',
]

TAB_MAPPINGS = {
    'storage_manager': ('tab-storage-manager', 'storage_manager_tab'),
    'boot_recovery': ('tab-boot-recovery', 'boot_recovery_tab'),
    'servicing_integrity': ('tab-servicing-integrity', 'servicing_integrity_tab'),
    'services_manager': ('tab-services-manager', 'services_manager_tab'),
    'task_scheduler': ('tab-task-scheduler', 'task_scheduler_tab'),
    'process_manager': ('tab-process-manager', 'process_manager_tab'),
    'firewall_manager': ('tab-firewall-manager', 'firewall_manager_tab'),
    'security_acl': ('tab-security-acl', 'security_acl_tab'),
    'performance_tracing': ('tab-performance-tracing', 'performance_tracing_tab'),
    'event_logs': ('tab-event-logs', 'event_logs_tab'),
    'software_manager': ('tab-software-manager', 'software_manager_tab'),
}


def test_tabs_config_contains_all_new_modules():
    """Проверка регистрации всех 11 модулей в tabs-config.js."""
    tabs_cfg_path = PROJECT_ROOT / 'apps' / 'windows' / 'api' / 'webgui' / 'apps' / 'modules' / 'tabs-config.js'
    assert tabs_cfg_path.exists()
    content = tabs_cfg_path.read_text(encoding='utf-8')

    for mod, (tab_id, tab_dir) in TAB_MAPPINGS.items():
        assert mod in content, f"Модуль {mod} отсутствует в tabs-config.js"
        assert tab_id in content, f"Идентификатор {tab_id} отсутствует в tabs-config.js"
        assert tab_dir in content, f"Директория {tab_dir} отсутствует в tabs-config.js"


def test_apps_index_contains_all_tab_panes():
    """Проверка наличия tab-pane контейнеров для всех 11 модулей в apps/index.html."""
    index_path = PROJECT_ROOT / 'apps' / 'windows' / 'api' / 'webgui' / 'apps' / 'index.html'
    assert index_path.exists()
    content = index_path.read_text(encoding='utf-8')

    for mod, (tab_id, _) in TAB_MAPPINGS.items():
        expected_tag = f'id="{tab_id}"'
        assert expected_tag in content, f"Контейнер {expected_tag} для модуля {mod} отсутствует в apps/index.html"


def test_tc_menu_config_contains_all_sidebar_items():
    """Проверка наличия пунктов навигации для всех 11 модулей в tc_menu_config.json."""
    menu_cfg_path = PROJECT_ROOT / 'apps' / 'windows' / 'api' / 'webgui' / 'config_menues' / 'tc_menu_config.json'
    assert menu_cfg_path.exists()
    with open(menu_cfg_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    sidebar_items = data.get('menu', {}).get('sidebarItems', [])
    sidebar_tabs = {item.get('tab'): item for item in sidebar_items}

    for mod, (tab_id, _) in TAB_MAPPINGS.items():
        assert tab_id in sidebar_tabs, f"Вкладка {tab_id} ({mod}) отсутствует в sidebarItems"
        item = sidebar_tabs[tab_id]
        assert item.get('visible') is True, f"Вкладка {tab_id} скрыта (visible != True)"
        assert item.get('icon'), f"У вкладки {tab_id} нет иконки"


def test_tab_files_existence_and_structure():
    """Проверка наличия файлов index.html и main.js для каждой вкладки."""
    webgui_dir = PROJECT_ROOT / 'apps' / 'windows' / 'api' / 'webgui'

    for mod, (tab_id, tab_dir) in TAB_MAPPINGS.items():
        html_file = webgui_dir / tab_dir / 'index.html'
        js_file = webgui_dir / tab_dir / 'main.js'

        assert html_file.exists(), f"Файл {html_file} не найден"
        assert js_file.exists(), f"Файл {js_file} не найден"

        html_content = html_file.read_text(encoding='utf-8')
        js_content = js_file.read_text(encoding='utf-8')

        assert len(html_content.strip()) > 50, f"HTML файл {html_file} слишком короткий"
        assert 'export function' in js_content or 'window.init' in js_content, f"JS файл {js_file} не содержит функции инициализации"


def test_fastapi_endpoints_availability():
    """Проверка работы эндпоинтов новых модулей через FastAPI TestClient."""
    app = create_windows_app()
    client = TestClient(app)

    endpoints = [
        '/api/storage-manager/summary',
        '/api/boot-recovery/summary',
        '/api/servicing-integrity/summary',
        '/api/services-manager/summary',
        '/api/task-scheduler/summary',
        '/api/process-manager/summary',
        '/api/firewall-manager/summary',
        '/api/security-acl/summary',
        '/api/performance-tracing/summary',
        '/api/event-logs/summary',
        '/api/software-manager/summary',
    ]

    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 200, f"Эндпоинт {ep} вернул {res.status_code}: {res.text}"
        data = res.json()
        assert isinstance(data, dict), f"Ответ от {ep} не является JSON-словарем"
