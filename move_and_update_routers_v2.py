import os
import shutil
from pathlib import Path
ROOT = Path('C:/Users/onela/AppData/Local/AI-Breadboard')
SRC_API = ROOT / 'src' / 'api'
DEST_CORE = SRC_API / 'routers' / 'core'
DEST_TC = SRC_API / 'routers' / 'tc'
DEST_TELEMETRY = DEST_TC / 'telemetry'
for d in (DEST_CORE, DEST_TC, DEST_TELEMETRY):
    d.mkdir(parents=True, exist_ok=True)
core_files = {'router_auth.py', 'router_chat.py', 'router_control.py', 'router_diagnostics.py', 'router_google_accounts.py', 'router_ifttt.py', 'router_keys.py', 'router_logs.py', 'router_mcp.py', 'router_menu.py', 'router_news.py', 'router_ninite.py', 'router_openai.py', 'router_rag.py', 'router_recovery.py', 'router_registry_viewer.py', 'router_scenarios.py', 'router_sync.py', 'router_sysautologging.py', 'router_system.py', 'router_system_logs.py', 'router_tts.py', 'router_user_directories.py', 'router_user_storage.py', 'router_version.py', 'router_admin.py', 'router_agents.py', 'router_audio.py', 'router_windows_admin.py'}
tc_files = {'router_tc.py', 'router_windows_admin.py'}
telemetry_files = {'router_telemetry.py'}
for file_path in SRC_API.glob('router_*.py'):
    name = file_path.name
    if name.startswith('~'):
        continue
    if name in tc_files:
        dest_dir = DEST_TC
    elif name in telemetry_files:
        dest_dir = DEST_TELEMETRY
    else:
        dest_dir = DEST_CORE
    dest_path = dest_dir / name
    shutil.move(str(file_path), str(dest_path))

def safe_read_text(p: Path) -> str:
    try:
        return p.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return ''

def replace_imports_in_file(file_path: Path):
    content = safe_read_text(file_path)
    if not content:
        return
    original = content
    for name in core_files:
        if name == 'router_windows_admin.py':
            continue
        module = name[:-3]
        old = f'src.api.{module}'
        new = f'src.api.routers.core.{module}'
        content = content.replace(old, new)
    for name in tc_files:
        module = name[:-3]
        old = f'src.api.{module}'
        new = f'src.api.routers.tc.{module}'
        content = content.replace(old, new)
    for name in telemetry_files:
        module = name[:-3]
        old = f'src.api.{module}'
        new = f'src.api.routers.tc.telemetry.{module}'
        content = content.replace(old, new)
    if content != original:
        file_path.write_text(content, encoding='utf-8')
for py_file in ROOT.rglob('*.py'):
    replace_imports_in_file(py_file)
print('All routers moved and import statements updated.')