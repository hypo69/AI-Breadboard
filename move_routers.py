import os
import shutil
from pathlib import Path
ROOT = Path('C:/Users/onela/AppData/Local/AI-Breadboard')
SRC_API = ROOT / 'src' / 'api'
DEST_CORE = SRC_API / 'routers' / 'core'
DEST_TC = SRC_API / 'routers' / 'tc'
DEST_TELEMETRY = DEST_TC / 'telemetry'
for d in [DEST_CORE, DEST_TC, DEST_TELEMETRY]:
    d.mkdir(parents=True, exist_ok=True)
tc_files = {'router_tc.py', 'router_windows_admin.py'}
telemetry_files = {'router_telemetry.py'}
for file_path in SRC_API.glob('router_*.py'):
    if file_path.name.startswith('~'):
        continue
    if file_path.name == 'router_auth.py':
        continue
    if file_path.name in tc_files:
        dest_dir = DEST_TC
    elif file_path.name in telemetry_files:
        dest_dir = DEST_TELEMETRY
    else:
        dest_dir = DEST_CORE
    dest_path = dest_dir / file_path.name
    shutil.copyfile(file_path, dest_path)
    relative_import = f'from .routers.{dest_dir.relative_to(SRC_API).as_posix()}.{file_path.stem} import *  # noqa: F403,F401\n'
    file_path.write_text(relative_import, encoding='utf-8')
print('Router files moved and proxies created.')