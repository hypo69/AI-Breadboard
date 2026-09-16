# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Testing Plugin Initializer and Factory
# =============================================================================

"""Tests for Plugin Initializer and scaffolding utility."""

from pathlib import Path
import pytest
from scripts.dev.init_plugin import create_plugin
from plugins.base import BasePlugin


def test_create_plugin_scaffolds_proper_structure(tmp_path: Path) -> None:
    """Verify create_plugin generates all expected files with i18n support."""
    plugin_dir = create_plugin(
        name="test_audit_logger",
        title="Audit Logger",
        title_ru="Аудит логов",
        description="Audit logger plugin for tracking admin actions",
        description_ru="Плагин аудита для отслеживания действий администратора",
        category="security",
        icon="🛡️",
        scope="system",
        plugins_root=tmp_path,
    )

    assert (plugin_dir / "__init__.py").exists()
    assert (plugin_dir / "plugin.py").exists()
    assert (plugin_dir / "README.md").exists()
    assert (plugin_dir / "tests" / "test_plugin.py").exists()

    init_text = (plugin_dir / "__init__.py").read_text(encoding="utf-8")
    assert "TestAuditLoggerPlugin" in init_text

    plugin_text = (plugin_dir / "plugin.py").read_text(encoding="utf-8")
    assert '"ru": "Аудит логов"' in plugin_text
    assert '"en": "Audit Logger"' in plugin_text
    assert 'category: str = "security"' in plugin_text
    assert 'icon: str = "🛡️"' in plugin_text


def test_base_plugin_i18n_fallback() -> None:
    """Verify BasePlugin title and description localization and fallback."""
    class CustomPlugin(BasePlugin):
        name = "custom_demo"
        title = "Demo Title"
        title_i18n = {"en": "Demo Title", "ru": "Демо заголовок"}
        description = "Demo Description"
        description_i18n = {"en": "Demo Description", "ru": "Демо описание"}

        async def handle(self, message: str, **kwargs):
            yield {"status": "complete", "text": message}

    plugin = CustomPlugin()
    assert plugin.get_title("ru") == "Демо заголовок"
    assert plugin.get_title("en") == "Demo Title"
    assert plugin.get_title("es") == "Demo Title"  # fallback

    manifest_ru = plugin.get_manifest(lang="ru")
    assert manifest_ru["title"] == "Демо заголовок"
    assert manifest_ru["description"] == "Демо описание"
    assert manifest_ru["title_i18n"]["en"] == "Demo Title"


def test_parse_plugins_config_lists() -> None:
    """Проверка парсинга списков enabled и disabled."""
    from plugins import _parse_plugins_config
    cfg = {
        "enabled": ["user_storage", "telegram_bot", "log_analyzer"],
        "disabled": ["generate_rag_from_codebase", "rag_cleaner", "log_analyzer"],
    }
    enabled, disabled, plugin_configs = _parse_plugins_config(cfg)
    assert enabled == {"user_storage", "telegram_bot", "log_analyzer"}
    assert disabled == {"generate_rag_from_codebase", "rag_cleaner", "log_analyzer"}


def test_load_plugins_with_enabled_disabled_priorities(monkeypatch, tmp_path) -> None:
    """Проверка загрузки только включенных в enabled плагинов и игнорирования disabled."""
    import json
    from plugins import load_plugins

    test_cfg = {
        "plugins": {
            "enabled": [
                "user_storage",
                "telegram_bot",
                "log_analyzer"
            ],
            "disabled": [
                "generate_rag_from_codebase",
                "rag_cleaner",
                "telegram_channel_rag",
                "log_analyzer",
                "invoice_processor"
            ]
        }
    }
    cfg_file = tmp_path / "config_plugins_test.json"
    cfg_file.write_text(json.dumps(test_cfg), encoding="utf-8")

    monkeypatch.setenv("CONFIG_FILE", str(cfg_file))
    monkeypatch.delenv("DISABLED_PLUGINS", raising=False)

    plugins = load_plugins()
    assert len(plugins) > 0

    if "user_storage" in plugins:
        assert plugins["user_storage"].enabled is True
    if "telegram_bot" in plugins:
        assert plugins["telegram_bot"].enabled is True

    # log_analyzer в обоих списках (disabled имеет приоритет) -> не должен загрузиться
    assert "log_analyzer" not in plugins

    # Не включенные или отключенные плагины не загружаются
    assert "generate_rag_from_codebase" not in plugins
    assert "rag_cleaner" not in plugins
    assert "facebook" not in plugins


def test_load_plugins_empty_enabled(monkeypatch, tmp_path) -> None:
    """Проверка того, что если enabled: [] (пустой список), ни один плагин не загружается."""
    import json
    from plugins import load_plugins

    test_cfg = {
        "plugins": {
            "enabled": [],
            "disabled": ["facebook", "telegram_bot"]
        }
    }
    cfg_file = tmp_path / "config_tc_empty_test.json"
    cfg_file.write_text(json.dumps(test_cfg), encoding="utf-8")

    monkeypatch.setenv("CONFIG_FILE", str(cfg_file))
    monkeypatch.delenv("DISABLED_PLUGINS", raising=False)

    plugins = load_plugins()
    assert len(plugins) == 0

