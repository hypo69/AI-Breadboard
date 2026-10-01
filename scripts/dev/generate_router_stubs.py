# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Root - Generate Router Stubs
# =============================================================================
# Description:
#   Скрипт/модуль системы AI-Breadboard (`generate_router_stubs`).
#
# Usage Examples:
#   Python API:
#     import generate_router_stubs
#
# File: generate_router_stubs.py
# Project: ai-breadboard
# Package: root
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:20:26
# =============================================================================

"""Скрипт/модуль системы AI-Breadboard (`generate_router_stubs`)."""

import os
import shutil
from pathlib import Path
ROOT = Path('C:/Users/onela/AppData/Local/AI-Breadboard')
SRC_API = ROOT / 'src' / 'api'
ROUTERS_CORE = SRC_API / 'routers' / 'core'
ROUTERS_TC = SRC_API / 'routers' / 'tc'
ROUTERS_TELEMETRY = ROUTERS_TC / 'telemetry'
router_map = {'router_auth.py': f'src.api.routers.core.router_auth', 'router_chat.py': f'src.api.routers.core.router_chat', 'router_control.py': f'src.api.routers.core.router_control', 'router_diagnostics.py': f'src.api.routers.core.router_diagnostics', 'router_google_accounts.py': f'src.api.routers.core.router_google_accounts', 'router_ifttt.py': f'src.api.routers.core.router_ifttt', 'router_keys.py': f'src.api.routers.core.router_keys', 'router_logs.py': f'src.api.routers.core.router_logs', 'router_mcp.py': f'src.api.routers.core.router_mcp', 'router_menu.py': f'src.api.routers.core.router_menu', 'router_news.py': f'src.api.routers.core.router_news', 'router_ninite.py': f'src.api.routers.core.router_ninite', 'router_openai.py': f'src.api.routers.core.router_openai', 'router_rag.py': f'src.api.routers.core.router_rag', 'router_recovery.py': f'src.api.routers.core.router_recovery', 'router_registry_viewer.py': f'src.api.routers.core.router_registry_viewer', 'router_scenarios.py': f'src.api.routers.core.router_scenarios', 'router_sync.py': f'src.api.routers.core.router_sync', 'router_sysautologging.py': f'src.api.routers.core.router_sysautologging', 'router_system.py': f'src.api.routers.core.router_system', 'router_system_logs.py': f'src.api.routers.core.router_system_logs', 'router_tts.py': f'src.api.routers.core.router_tts', 'router_user_directories.py': f'src.api.routers.core.router_user_directories', 'router_user_storage.py': f'src.api.routers.core.router_user_storage', 'router_version.py': f'src.api.routers.core.router_version', 'router_admin.py': f'src.api.routers.core.router_admin', 'router_agents.py': f'src.api.routers.core.router_agents', 'router_audio.py': f'src.api.routers.core.router_audio', 'router_tc.py': f'src.api.routers.tc.router_tc', 'router_windows_admin.py': f'src.api.routers.tc.router_windows_admin', 'router_telemetry.py': f'src.api.routers.tc.telemetry.router_telemetry'}
for filename, full_import in router_map.items():
    stub_path = SRC_API / filename
    stub_content = f'# Auto‑generated stub for backward compatibility\nfrom {full_import} import *  # noqa: F403,F401\n'
    stub_path.write_text(stub_content, encoding='utf-8')
print(f'Created {len(router_map)} stub modules in {SRC_API}')