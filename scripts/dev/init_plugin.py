# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Scripts Dev - Init Plugin
# =============================================================================
# Description:
#   Plugin scaffolding utility for AI Breadboard.
#
# Usage Examples:
#   CLI:
#     python -m scripts.dev.init_plugin
#   Python API:
#     from scripts.dev.init_plugin import create_plugin
#
#     res = create_plugin()
#
# File: init_plugin.py
# Project: ai-breadboard
# Package: scripts.dev
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:27:07
# =============================================================================

"""Plugin scaffolding utility for AI Breadboard."""

import argparse
import re
import sys
from pathlib import Path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parents[1]
PLUGINS_ROOT = PROJECT_ROOT / 'plugins'

def _to_snake_case(name: str) -> str:
    """Converts kebab-case or mixed string to snake_case."""
    s = re.sub('[-\\s]+', '_', name.strip())
    return re.sub('[^\\w]', '', s).lower()

def _to_pascal_case(name: str) -> str:
    """Converts snake_case or kebab-case to PascalCase."""
    words = re.split('[_\\-\\s]+', name.strip())
    return ''.join((w.capitalize() for w in words if w))

def create_plugin(name: str, title: str='', title_ru: str='', description: str='', description_ru: str='', category: str='general', icon: str='🧩', scope: str='system', plugins_root: Path | None=None) -> Path:
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
    title_en = title.strip() or f'{class_prefix} Plugin'
    title_ru_val = title_ru.strip() or title_en
    desc_en = description.strip() or f'Modular plugin for {title_en.lower()}.'
    desc_ru_val = description_ru.strip() or f'Модульный плагин для {title_ru_val.lower()}.'
    plugin_dir = root_dir / snake_name
    if plugin_dir.exists():
        print(f'⚠️ Plugin directory already exists: {plugin_dir}')
        return plugin_dir
    plugin_dir.mkdir(parents=True, exist_ok=True)
    tests_dir = plugin_dir / 'tests'
    tests_dir.mkdir(exist_ok=True)
    init_content = f'# -*- coding: utf-8 -*-\n# =============================================================================\n# Process Name: {title_en} Package Entry Point\n# =============================================================================\n\n"""{title_en} plugin package."""\n\nfrom plugins.{snake_name}.plugin import {class_prefix}Plugin\n\nplugin = {class_prefix}Plugin\n__all__ = ["plugin", "{class_prefix}Plugin"]\n'
    plugin_py_content = f'''# -*- coding: utf-8 -*-\n# =============================================================================\n# Process Name: {title_en} Implementation\n# =============================================================================\n# Description:\n#   {desc_en}\n#\n# File: plugin.py\n# Package: plugins.{snake_name}\n# Author: hypo69\n# Copyright: © 2026 hypo69\n# =============================================================================\n\n"""{title_en} implementation module."""\n\nfrom __future__ import annotations\n\nfrom typing import Any, Dict, List, Optional\nfrom plugins.base import BasePlugin\nfrom logger import logger\n\n\nclass {class_prefix}Plugin(BasePlugin):\n    """{title_en} extending AI Breadboard platform."""\n\n    name: str = "{snake_name}"\n    title: str = "{title_en}"\n    title_i18n: Dict[str, str] = {{\n        "en": "{title_en}",\n        "ru": "{title_ru_val}",\n    }}\n    version: str = "1.0.0"\n    description: str = "{desc_en}"\n    description_i18n: Dict[str, str] = {{\n        "en": "{desc_en}",\n        "ru": "{desc_ru_val}",\n    }}\n    icon: str = "{icon}"\n    category: str = "{category}"\n    enabled: bool = True\n    is_system: bool = {scope == 'system'}\n    scope: str = "{scope}"\n\n    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:\n        """Initialize {title_en} instance."""\n        super().__init__(ai_model=ai_model, config=config)\n        self.is_running: bool = False\n\n    def get_config_fields(self) -> List[Dict[str, Any]]:\n        """Return configurable settings schema for Admin UI."""\n        return [\n            {{\n                "name": "auto_start",\n                "label": "Auto Start",\n                "label_i18n": {{"en": "Auto Start", "ru": "Автозапуск"}},\n                "type": "boolean",\n                "default": False,\n                "description": "Start plugin automatically on server startup",\n            }},\n        ]\n\n    def get_actions(self) -> List[Dict[str, Any]]:\n        """Return actionable triggers for Admin UI."""\n        return [\n            {{\n                "id": "ping",\n                "label": "Health Check",\n                "label_i18n": {{"en": "Health Check", "ru": "Проверка состояния"}},\n                "icon": "⚡",\n                "variant": "primary",\n                "description": "Check if plugin backend is active",\n            }},\n        ]\n\n    async def execute_action(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:\n        """Execute an interactive action requested from Admin Web UI."""\n        logger.info(f"[{class_prefix}Plugin] Executing action '{{action}}' with params: {{params}}")\n        if action == "ping":\n            return {{\n                "status": "success",\n                "message": f"{title_en} is healthy and responsive.",\n                "data": {{"plugin": self.name, "version": self.version}},\n            }}\n        return {{"status": "error", "message": f"Unknown action: '{{action}}'"}}\n\n    async def handle(self, message: str, **kwargs: Any) -> Any:\n        """Handle message stream for AI processing."""\n        yield {{"status": "complete", "text": f"Response from {title_en}: {{message}}"}}\n\n    def get_tools(self) -> List[Dict[str, Any]]:\n        """Return LLM Function Calling tool declarations."""\n        return [\n            {{\n                "name": "{snake_name}_status",\n                "description": "{desc_en}",\n                "parameters": {{\n                    "type": "object",\n                    "properties": {{\n                        "query": {{"type": "string", "description": "Status query parameter"}},\n                    }},\n                }},\n            }},\n        ]\n'''
    readme_content = f'# {title_en}\n\n## Overview\n{desc_en}\n\n## Localization (i18n)\n- **English Title**: {title_en}\n- **Russian Title**: {title_ru_val}\n- **English Description**: {desc_en}\n- **Russian Description**: {desc_ru_val}\n\n## Configuration\n| Option | Type | Default | Description |\n|---|---|---|---|\n| `auto_start` | `boolean` | `false` | Enable automatic background initialization |\n\n## Actions\n- `ping`: Health check verification trigger.\n'
    test_content = f'# -*- coding: utf-8 -*-\n"""Tests for {title_en}."""\n\nimport pytest\nfrom plugins.{snake_name}.plugin import {class_prefix}Plugin\n\n\ndef test_plugin_manifest_and_i18n() -> None:\n    """Verify plugin initialization and multilingual manifest output."""\n    inst = {class_prefix}Plugin()\n    assert inst.name == "{snake_name}"\n    assert inst.get_title("en") == "{title_en}"\n    assert inst.get_title("ru") == "{title_ru_val}"\n    assert inst.get_description("ru") == "{desc_ru_val}"\n\n    manifest = inst.get_manifest(lang="ru")\n    assert manifest["title"] == "{title_ru_val}"\n    assert manifest["description"] == "{desc_ru_val}"\n    assert manifest["icon"] == "{icon}"\n\n\n@pytest.mark.asyncio\nasync def test_plugin_execute_action() -> None:\n    """Verify interactive action execution."""\n    inst = {class_prefix}Plugin()\n    res = await inst.execute_action("ping")\n    assert res["status"] == "success"\n    assert "{title_en}" in res["message"]\n'
    (plugin_dir / '__init__.py').write_text(init_content, encoding='utf-8')
    (plugin_dir / 'plugin.py').write_text(plugin_py_content, encoding='utf-8')
    (plugin_dir / 'README.md').write_text(readme_content, encoding='utf-8')
    (tests_dir / 'test_plugin.py').write_text(test_content, encoding='utf-8')
    print(f"✅ Successfully created plugin '{snake_name}' at:\n   {plugin_dir}")
    return plugin_dir

def main() -> int:
    """CLI entry point for plugin scaffolding."""
    parser = argparse.ArgumentParser(description='Create a new AI Breadboard plugin.')
    parser.add_argument('name', help='Name of the plugin (e.g. audit_logger)')
    parser.add_argument('--title', '-t', default='', help='English display title')
    parser.add_argument('--title-ru', '-tru', default='', help='Russian display title')
    parser.add_argument('--description', '-d', default='', help='English description')
    parser.add_argument('--description-ru', '-ru', default='', help='Russian description')
    parser.add_argument('--category', '-c', default='general', help='Category (e.g. tools, monitoring, media)')
    parser.add_argument('--icon', '-i', default='🧩', help='Emoji icon')
    parser.add_argument('--scope', '-s', default='system', choices=['system', 'user'], help='Plugin scope')
    args = parser.parse_args()
    create_plugin(name=args.name, title=args.title, title_ru=args.title_ru, description=args.description, description_ru=args.description_ru, category=args.category, icon=args.icon, scope=args.scope)
    return 0
if __name__ == '__main__':
    sys.exit(main())