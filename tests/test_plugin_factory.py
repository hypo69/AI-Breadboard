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
