import pathlib, re, sys
apps_root = pathlib.Path('C:\\Users\\onela\\AppData\\Local\\AI-Breadboard\\apps')
init_file = pathlib.Path('C:\\Users\\onela\\AppData\\Local\\AI-Breadboard\\src\\app\\__init__.py')
content = init_file.read_text(encoding='utf-8')
for app_dir in apps_root.iterdir():
    if not app_dir.is_dir():
        continue
    name = app_dir.name
    if name.startswith('~') or name == 'windows':
        continue
    router_path = app_dir / 'router.py'
    if router_path.is_file():
        routers_dir = app_dir / 'routers'
        routers_dir.mkdir(parents=True, exist_ok=True)
        router_new = routers_dir / 'router.py'
        router_path.replace(router_new)
        (routers_dir / '__init__.py').write_text('', encoding='utf-8')
        pattern = f'from\\s+apps\\.{re.escape(name)}\\.router\\s+import\\s+(.+)'
        replacement = f'from apps.{name}.routers.router import init_router as init_{name}_router'
        new_content, count = re.subn(pattern, replacement, content)
        if count:
            print(f'Replaced import for {name}')
        content = new_content
init_file.write_text(content, encoding='utf-8')
print('Migration completed')