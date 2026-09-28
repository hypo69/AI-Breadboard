"""Script to generate minimal FastAPI router implementations for core router placeholders.

This script overwrites the placeholder files in `src/api/routers/core/` that currently contain
invalid import lines like `from .routers.routers/core.router_chat import *`. It replaces each
file with a minimal router exposing an `init_router` function and a simple `/ping` endpoint.
Additional sub‑router initializers are added for `router_admin.py` because that module
expects `init_skills_router`, `init_plugins_router` and `init_apps_router`.
"""
import os
from pathlib import Path
ROOT = Path('C:/Users/onela/AppData/Local/AI-Breadboard')
CORE_ROUTER_DIR = ROOT / 'src' / 'api' / 'routers' / 'core'
router_definitions = {'router_chat.py': {}, 'router_agents.py': {}, 'router_audio.py': {}, 'router_autolog.py': {}, 'router_diagnostics.py': {}, 'router_ifttt.py': {}, 'router_keys.py': {}, 'router_logs.py': {}, 'router_mcp.py': {}, 'router_menu.py': {}, 'router_news.py': {}, 'router_ninite.py': {}, 'router_openai.py': {}, 'router_rag.py': {}, 'router_recovery.py': {}, 'router_registry_viewer.py': {}, 'router_scenarios.py': {}, 'router_sysautologging.py': {}, 'router_system.py': {}, 'router_system_logs.py': {}, 'router_telegram_rag.py': {}, 'router_tts.py': {}, 'router_user_directories.py': {}, 'router_version.py': {}, 'router_admin.py': {'extra_init': ['init_skills_router', 'init_plugins_router', 'init_apps_router']}}
for filename, opts in router_definitions.items():
    path = CORE_ROUTER_DIR / filename
    module_name = filename.replace('.py', '')
    lines = []
    lines.append('# -*- coding: utf-8 -*-')
    lines.append('"""')
    lines.append(f'Минимальная реализация роутера {module_name}.')
    lines.append('"""')
    lines.append('')
    lines.append('from fastapi import APIRouter')
    lines.append('')
    lines.append('router = APIRouter()')
    lines.append('')
    lines.append(f"@router.get('/{module_name}/ping', tags=['{module_name}'])")
    lines.append('async def ping() -> dict:')
    lines.append('    """Проверка доступности роутера."""')
    lines.append('    return {"status": "ok"}')
    lines.append('')
    lines.append('def init_router() -> APIRouter:')
    lines.append('    """Инициализация и возврат роутера."""')
    lines.append('    return router')
    extra_inits = opts.get('extra_init', [])
    for extra in extra_inits:
        lines.append('')
        lines.append(f'def {extra}() -> APIRouter:')
        lines.append(f'    """Инициализация под‑роутера {extra}."""')
        lines.append('    sub_router = APIRouter()')
        lines.append(f'    @sub_router.get("/{module_name}/{extra}/ping")')
        lines.append('    async def sub_ping() -> dict:')
        lines.append('        return {"status": "ok"}')
        lines.append('    return sub_router')
    content = '\n'.join(lines) + '\n'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Generated {path}')