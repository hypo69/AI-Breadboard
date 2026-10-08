# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Ai_Breadboard_Admin Tests - Test Admin Config
# =============================================================================
# Description:
#   Фикстура создания временной структуры каталогов проекта.
#
# Usage Examples:
#   Python API:
#     from apps.ai_breadboard_admin.tests.test_admin_config import temp_root
#
#     res = temp_root()
#
# File: test_admin_config.py
# Project: ai-breadboard
# Package: apps.ai_breadboard_admin.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Фикстура создания временной структуры каталогов проекта."""

import json
from pathlib import Path
import pytest
from apps.ai_breadboard_admin.src.config_manager import AdminConfigManager

@pytest.fixture
def temp_root(tmp_path: Path) -> Path:
    """Фикстура создания временной структуры каталогов проекта."""
    config_file = tmp_path / 'config.json'
    initial_data = {'rag': {'mode': 'rag+model'}, 'web_search': {'engine': 'playwright', 'gemini_model': 'gemini-3.1-flash', 'gemini_cli_model': 'gemini-3.1-flash-lite', 'agy_model': 'agy-flash'}}
    config_file.write_text(json.dumps(initial_data, indent=2), encoding='utf-8')
    test_app_dir = tmp_path / 'apps' / 'test_app'
    test_app_dir.mkdir(parents=True, exist_ok=True)
    (test_app_dir / 'config.json').write_text(json.dumps({'enabled': True, 'port': 9000}), encoding='utf-8')
    return tmp_path

def test_get_rag_config_happy_path(temp_root: Path) -> None:
    """Happy Path: проверка успешного получения текущего режима RAG."""
    manager = AdminConfigManager(root_dir=temp_root)
    rag_cfg = manager.get_rag_config()
    assert rag_cfg == {'mode': 'rag+model'}, f"Ожидался режим 'rag+model', получено: {rag_cfg}"

def test_set_rag_config_happy_path(temp_root: Path) -> None:
    """Happy Path: проверка успешного сохранения нового режима RAG."""
    manager = AdminConfigManager(root_dir=temp_root)
    success = manager.set_rag_config('model')
    updated_cfg = manager.get_rag_config()
    assert success is True, 'Запись конфигурации RAG должна вернуть True'
    assert updated_cfg['mode'] == 'model', f"Ожидался режим 'model', получено: {updated_cfg['mode']}"

def test_get_web_search_config_happy_path(temp_root: Path) -> None:
    """Happy Path: проверка получения параметров веб-поиска."""
    manager = AdminConfigManager(root_dir=temp_root)
    search_cfg = manager.get_web_search_config()
    assert search_cfg['engine'] == 'playwright', "Ожидался engine 'playwright'"
    assert search_cfg['gemini_model'] == 'gemini-3.1-flash'

def test_set_web_search_config(temp_root: Path) -> None:
    """Type Variants & Modification: изменение поискового движка и моделей."""
    manager = AdminConfigManager(root_dir=temp_root)
    success = manager.set_web_search_config(engine='langchain', gemini_model='gemini-3.1-flash', gemini_cli_model='gemini-cli-fast', agy_model='agy-pro')
    search_cfg = manager.get_web_search_config()
    assert success is True
    assert search_cfg['engine'] == 'langchain'
    assert search_cfg['gemini_model'] == 'gemini-1.5-pro'

def test_get_app_config_existing_and_missing(temp_root: Path) -> None:
    """Edge Case & Error Scenario: чтение существующего и отсутствующего приложения."""
    manager = AdminConfigManager(root_dir=temp_root)
    existing_cfg = manager.get_app_config('test_app')
    missing_cfg = manager.get_app_config('non_existent_app_xyz')
    assert existing_cfg is not None, 'Конфигурация test_app должна существовать'
    assert existing_cfg.get('port') == 9000
    assert missing_cfg is None, 'Несуществующее приложение должно вернуть None'

def test_set_app_config(temp_root: Path) -> None:
    """Boundary & Happy Path: обновление параметров приложения."""
    manager = AdminConfigManager(root_dir=temp_root)
    new_data = {'enabled': False, 'port': 9050, 'custom_key': 'val'}
    success = manager.set_app_config('test_app', new_data)
    read_data = manager.get_app_config('test_app')
    assert success is True
    assert read_data == new_data