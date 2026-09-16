# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for Admin Configuration Manager
# =============================================================================
# Description:
#   Тестирование функционала AdminConfigManager: чтение/запись конфигураций,
#   управление параметрами RAG, веб-поиска и локальными конфигурациями приложений.
#
# File: test_admin_config.py
# Project: AI-Breadboard
# Package: apps.ai_breadboard_admin.tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
from pathlib import Path
import pytest

from apps.ai_breadboard_admin.src.config_manager import AdminConfigManager


@pytest.fixture
def temp_root(tmp_path: Path) -> Path:
    """Фикстура создания временной структуры каталогов проекта."""
    config_file = tmp_path / "config.json"
    initial_data = {
        "rag": {"mode": "rag+model"},
        "web_search": {
            "engine": "playwright",
            "gemini_model": "gemini-2.5-flash",
            "gemini_cli_model": "gemini-3.1-flash-lite",
            "agy_model": "agy-flash",
        },
    }
    config_file.write_text(json.dumps(initial_data, indent=2), encoding="utf-8")

    # Создание директории приложения
    test_app_dir = tmp_path / "apps" / "test_app"
    test_app_dir.mkdir(parents=True, exist_ok=True)
    (test_app_dir / "config.json").write_text(json.dumps({"enabled": True, "port": 9000}), encoding="utf-8")

    return tmp_path


def test_get_rag_config_happy_path(temp_root: Path) -> None:
    """Happy Path: проверка успешного получения текущего режима RAG."""
    # Arrange: инициализируем менеджер с временным корнем
    manager = AdminConfigManager(root_dir=temp_root)

    # Act: считываем конфигурацию RAG
    rag_cfg = manager.get_rag_config()

    # Assert: проверяем соответствие возвращенного режима
    assert rag_cfg == {"mode": "rag+model"}, f"Ожидался режим 'rag+model', получено: {rag_cfg}"


def test_set_rag_config_happy_path(temp_root: Path) -> None:
    """Happy Path: проверка успешного сохранения нового режима RAG."""
    # Arrange: создаем экземпляр менеджера
    manager = AdminConfigManager(root_dir=temp_root)

    # Act: обновляем режим RAG на 'model'
    success = manager.set_rag_config("model")
    updated_cfg = manager.get_rag_config()

    # Assert: проверяем успешность записи и новое значение
    assert success is True, "Запись конфигурации RAG должна вернуть True"
    assert updated_cfg["mode"] == "model", f"Ожидался режим 'model', получено: {updated_cfg['mode']}"


def test_get_web_search_config_happy_path(temp_root: Path) -> None:
    """Happy Path: проверка получения параметров веб-поиска."""
    # Arrange: менеджер конфигурации
    manager = AdminConfigManager(root_dir=temp_root)

    # Act: получение настроек поиска
    search_cfg = manager.get_web_search_config()

    # Assert: валидация словаря параметров
    assert search_cfg["engine"] == "playwright", "Ожидался engine 'playwright'"
    assert search_cfg["gemini_model"] == "gemini-2.5-flash"


def test_set_web_search_config(temp_root: Path) -> None:
    """Type Variants & Modification: изменение поискового движка и моделей."""
    # Arrange: менеджер конфигураций
    manager = AdminConfigManager(root_dir=temp_root)

    # Act: сохранение новых параметров поиска
    success = manager.set_web_search_config(
        engine="langchain",
        gemini_model="gemini-1.5-pro",
        gemini_cli_model="gemini-cli-fast",
        agy_model="agy-pro",
    )
    search_cfg = manager.get_web_search_config()

    # Assert: проверка сохранения
    assert success is True
    assert search_cfg["engine"] == "langchain"
    assert search_cfg["gemini_model"] == "gemini-1.5-pro"


def test_get_app_config_existing_and_missing(temp_root: Path) -> None:
    """Edge Case & Error Scenario: чтение существующего и отсутствующего приложения."""
    # Arrange: инициализация менеджера
    manager = AdminConfigManager(root_dir=temp_root)

    # Act: чтение существующего и несуществующего приложения
    existing_cfg = manager.get_app_config("test_app")
    missing_cfg = manager.get_app_config("non_existent_app_xyz")

    # Assert: проверяем валидность результатов
    assert existing_cfg is not None, "Конфигурация test_app должна существовать"
    assert existing_cfg.get("port") == 9000
    assert missing_cfg is None, "Несуществующее приложение должно вернуть None"


def test_set_app_config(temp_root: Path) -> None:
    """Boundary & Happy Path: обновление параметров приложения."""
    # Arrange: менеджер конфигураций
    manager = AdminConfigManager(root_dir=temp_root)
    new_data = {"enabled": False, "port": 9050, "custom_key": "val"}

    # Act: запись новой конфигурации
    success = manager.set_app_config("test_app", new_data)
    read_data = manager.get_app_config("test_app")

    # Assert: проверяем успешное обновление
    assert success is True
    assert read_data == new_data
