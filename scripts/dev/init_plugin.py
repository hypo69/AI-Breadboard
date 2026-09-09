# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Plugin Initializer and Scaffolder
# =============================================================================
# Description:
#   Scaffolds a new standard AI Breadboard plugin in plugins/<name> with
#   __init__.py, plugin.py, README.md, and tests/test_plugin.py.
#
# Examples:
#   python scripts/dev/init_plugin.py audit_logger --title "Audit Logger"
#
# File: init_plugin.py
# Project: AI Breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Plugin scaffolding utility for AI Breadboard."""

import argparse
import re
import sys
from pathlib import Path

# Find project root
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parents[1]
PLUGINS_ROOT = PROJECT_ROOT / "plugins"


def _to_snake_case(name: str) -> str:
    """Converts kebab-case or mixed string to snake_case."""
    s = re.sub(r"[-\s]+", "_", name.strip())
    return re.sub(r"[^\w]", "", s).lower()


def _to_pascal_case(name: str) -> str:
    """Converts snake_case or kebab-case to PascalCase."""
    words = re.split(r"[_\-\s]+", name.strip())
    return "".join(w.capitalize() for w in words if w)


def create_plugin(
    name: str,
    title: str = "",
    title_ru: str = "",
    description: str = "",
    description_ru: str = "",
    category: str = "general",
    icon: str = "🧩",
    scope: str = "system",
    plugins_root: Path | None = None,
) -> Path:
    """Create a new standard plugin directory structure in plugins/<snake_name>.

    Args:
        name (str): Plugin folder/module identifier.
        title (str): English display title.
        title_ru (str): Russian display title.
        description (str): English description.
        description_ru (str): Russian description.
        category (str): Category (e.g., 'tools', 'monitoring', 'communication').
        icon (str): Emoji or icon representation.
        scope (str): Plugin scope ('system' or 'user').
        plugins_root (Path | None): Override root folder for testing.

    Returns:
        Path: Created plugin directory.
    """
    root_dir = plugins_root or PLUGINS_ROOT
    snake_name = _to_snake_case(name)
    class_prefix = _to_pascal_case(snake_name)

    title_en = title.strip() or f"{class_prefix} Plugin"
    title_ru_val = title_ru.strip() or title_en
    desc_en = description.strip() or f"Modular plugin for {title_en.lower()}."
    desc_ru_val = description_ru.strip() or f"Модульный плагин для {title_ru_val.lower()}."

    plugin_dir = root_dir / snake_name
    if plugin_dir.exists():
        print(f"⚠️ Plugin directory already exists: {plugin_dir}")
        return plugin_dir

    plugin_dir.mkdir(parents=True, exist_ok=True)
    tests_dir = plugin_dir / "tests"
    tests_dir.mkdir(exist_ok=True)

    # 1. __init__.py
    init_content = f"""# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: {title_en} Package Entry Point
# =============================================================================

\"\"\"{title_en} plugin package.\"\"\"

from plugins.{snake_name}.plugin import {class_prefix}Plugin

plugin = {class_prefix}Plugin
__all__ = ["plugin", "{class_prefix}Plugin"]
"""

    # 2. plugin.py
    plugin_py_content = f"""# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: {title_en} Implementation
# =============================================================================
# Description:
#   {desc_en}
#
# File: plugin.py
# Package: plugins.{snake_name}
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

\"\"\"{title_en} implementation module.\"\"\"

from __future__ import annotations

from typing import Any, Dict, List, Optional
from plugins.base import BasePlugin
from src.logger import logger


class {class_prefix}Plugin(BasePlugin):
    \"\"\"{title_en} extending AI Breadboard platform.\"\"\"

    name: str = "{snake_name}"
    title: str = "{title_en}"
    title_i18n: Dict[str, str] = {{
        "en": "{title_en}",
        "ru": "{title_ru_val}",
    }}
    version: str = "1.0.0"
    description: str = "{desc_en}"
    description_i18n: Dict[str, str] = {{
        "en": "{desc_en}",
        "ru": "{desc_ru_val}",
    }}
    icon: str = "{icon}"
    category: str = "{category}"
    enabled: bool = True
    is_system: bool = {scope == 'system'}
    scope: str = "{scope}"

    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        \"\"\"Initialize {title_en} instance.\"\"\"
        super().__init__(ai_model=ai_model, config=config)
        self.is_running: bool = False

    def get_config_fields(self) -> List[Dict[str, Any]]:
        \"\"\"Return configurable settings schema for Admin UI.\"\"\"
        return [
            {{
                "name": "auto_start",
                "label": "Auto Start",
                "label_i18n": {{"en": "Auto Start", "ru": "Автозапуск"}},
                "type": "boolean",
                "default": False,
                "description": "Start plugin automatically on server startup",
            }},
        ]

    def get_actions(self) -> List[Dict[str, Any]]:
        \"\"\"Return actionable triggers for Admin UI.\"\"\"
        return [
            {{
                "id": "ping",
                "label": "Health Check",
                "label_i18n": {{"en": "Health Check", "ru": "Проверка состояния"}},
                "icon": "⚡",
                "variant": "primary",
                "description": "Check if plugin backend is active",
            }},
        ]

    async def execute_action(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        \"\"\"Execute an interactive action requested from Admin Web UI.\"\"\"
        logger.info(f"[{class_prefix}Plugin] Executing action '{{action}}' with params: {{params}}")
        if action == "ping":
            return {{
                "status": "success",
                "message": f"{title_en} is healthy and responsive.",
                "data": {{"plugin": self.name, "version": self.version}},
            }}
        return {{"status": "error", "message": f"Unknown action: '{{action}}'"}}

    async def handle(self, message: str, **kwargs: Any) -> Any:
        \"\"\"Handle message stream for AI processing.\"\"\"
        yield {{"status": "complete", "text": f"Response from {title_en}: {{message}}"}}

    def get_tools(self) -> List[Dict[str, Any]]:
        \"\"\"Return LLM Function Calling tool declarations.\"\"\"
        return [
            {{
                "name": "{snake_name}_status",
                "description": "{desc_en}",
                "parameters": {{
                    "type": "object",
                    "properties": {{
                        "query": {{"type": "string", "description": "Status query parameter"}},
                    }},
                }},
            }},
        ]
"""

    # 3. README.md
    readme_content = f"""# {title_en}

## Overview
{desc_en}

## Localization (i18n)
- **English Title**: {title_en}
- **Russian Title**: {title_ru_val}
- **English Description**: {desc_en}
- **Russian Description**: {desc_ru_val}

## Configuration
| Option | Type | Default | Description |
|---|---|---|---|
| `auto_start` | `boolean` | `false` | Enable automatic background initialization |

## Actions
- `ping`: Health check verification trigger.
"""

    # 4. tests/test_plugin.py
    test_content = f"""# -*- coding: utf-8 -*-
\"\"\"Tests for {title_en}.\"\"\"

import pytest
from plugins.{snake_name}.plugin import {class_prefix}Plugin


def test_plugin_manifest_and_i18n() -> None:
    \"\"\"Verify plugin initialization and multilingual manifest output.\"\"\"
    inst = {class_prefix}Plugin()
    assert inst.name == "{snake_name}"
    assert inst.get_title("en") == "{title_en}"
    assert inst.get_title("ru") == "{title_ru_val}"
    assert inst.get_description("ru") == "{desc_ru_val}"

    manifest = inst.get_manifest(lang="ru")
    assert manifest["title"] == "{title_ru_val}"
    assert manifest["description"] == "{desc_ru_val}"
    assert manifest["icon"] == "{icon}"


@pytest.mark.asyncio
async def test_plugin_execute_action() -> None:
    \"\"\"Verify interactive action execution.\"\"\"
    inst = {class_prefix}Plugin()
    res = await inst.execute_action("ping")
    assert res["status"] == "success"
    assert "{title_en}" in res["message"]
"""

    (plugin_dir / "__init__.py").write_text(init_content, encoding="utf-8")
    (plugin_dir / "plugin.py").write_text(plugin_py_content, encoding="utf-8")
    (plugin_dir / "README.md").write_text(readme_content, encoding="utf-8")
    (tests_dir / "test_plugin.py").write_text(test_content, encoding="utf-8")

    print(f"✅ Successfully created plugin '{snake_name}' at:\n   {plugin_dir}")
    return plugin_dir


def main() -> int:
    """CLI entry point for plugin scaffolding."""
    parser = argparse.ArgumentParser(description="Create a new AI Breadboard plugin.")
    parser.add_argument("name", help="Name of the plugin (e.g. audit_logger)")
    parser.add_argument("--title", "-t", default="", help="English display title")
    parser.add_argument("--title-ru", "-tru", default="", help="Russian display title")
    parser.add_argument("--description", "-d", default="", help="English description")
    parser.add_argument("--description-ru", "-ru", default="", help="Russian description")
    parser.add_argument("--category", "-c", default="general", help="Category (e.g. tools, monitoring, media)")
    parser.add_argument("--icon", "-i", default="🧩", help="Emoji icon")
    parser.add_argument("--scope", "-s", default="system", choices=["system", "user"], help="Plugin scope")
    args = parser.parse_args()

    create_plugin(
        name=args.name,
        title=args.title,
        title_ru=args.title_ru,
        description=args.description,
        description_ru=args.description_ru,
        category=args.category,
        icon=args.icon,
        scope=args.scope,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
