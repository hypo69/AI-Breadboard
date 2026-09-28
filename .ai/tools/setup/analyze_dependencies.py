"""
Скрипт для анализа зависимостей между скриптами в проекте.
Помогает определить, какие скрипты используются другими и какие можно безопасно удалить.
"""
import os
import re
import sys
from pathlib import Path
from collections import defaultdict, Counter
PROJECT_ROOT = Path(__file__).resolve().parents[3]

def find_python_files():
    """Найти все Python файлы в корне проекта."""
    python_files = []
    for file in PROJECT_ROOT.glob('*.py'):
        python_files.append(file)
    return python_files

def analyze_file_imports(file_path):
    """Проанализировать импорты в Python файле."""
    imports = []
    try:
        content = file_path.read_text(encoding='utf-8')
        patterns = ['^import\\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\\s*,\\s*[a-zA-Z_][a-zA-Z0-9_]*)*)', '^from\\s+([a-zA-Z_][a-zA-Z0-9_.]*)\\s+import', 'subprocess\\.run\\(\\[.*?["\\\']([a-zA-Z_][a-zA-Z0-9_]*\\.py)["\\\']', 'sys\\.argv\\s*=\\s*\\[.*?["\\\']([a-zA-Z_][a-zA-Z0-9_]*\\.py)["\\\']']
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    module = match.group(1)
                    if '.py' in module or (not module.startswith('src.') and (not module.startswith('plugins.')) and (not module.startswith('.'))):
                        imports.append(module)
                        break
        if 'manage_tools.py' in content:
            subprocess_calls = re.findall('cmd\\s*=\\s*\\[sys\\.executable,\\s*["\\\']([a-zA-Z_][a-zA-Z0-9_]*\\.py)["\\\']', content)
            imports.extend(subprocess_calls)
    except Exception as e:
        print(f'Error при анализе {file_path}: {e}')
    return imports

def analyze_ps1_files():
    """Проанализировать PowerShell скрипты на вызовы других скриптов."""
    ps1_dependencies = defaultdict(list)
    for ps1_file in PROJECT_ROOT.glob('*.ps1'):
        try:
            content = ps1_file.read_text(encoding='utf-8')
            called_scripts = set()
            ps1_calls = re.findall('&\\s*["\\\']?([a-zA-Z_][a-zA-Z0-9_]*\\.ps1)["\\\']?', content)
            called_scripts.update(ps1_calls)
            py_calls = re.findall('python\\s+["\\\']?([a-zA-Z_][a-zA-Z0-9_]*\\.py)["\\\']?', content)
            called_scripts.update(py_calls)
            start_process_calls = re.findall('Start-Process.*["\\\']([a-zA-Z_][a-zA-Z0-9_]*\\.(?:py|ps1|exe))["\\\']', content, re.IGNORECASE)
            called_scripts.update(start_process_calls)
            relative_calls = re.findall('\\.\\\\([a-zA-Z_][a-zA-Z0-9_]*\\.(?:py|ps1|exe))', content)
            called_scripts.update(relative_calls)
            if called_scripts:
                ps1_dependencies[ps1_file.name] = list(called_scripts)
        except Exception as e:
            print(f'Error при анализе {ps1_file}: {e}')
    return ps1_dependencies

def build_dependency_graph():
    """Построить граф зависимостей между скриптами."""
    python_files = find_python_files()
    dependencies = defaultdict(list)
    reverse_deps = defaultdict(list)
    for py_file in python_files:
        file_name = py_file.name
        imports = analyze_file_imports(py_file)
        root_scripts = []
        for imp in imports:
            if '.py' in imp:
                script_name = imp if imp.endswith('.py') else f'{imp}.py'
                if (PROJECT_ROOT / script_name).exists():
                    root_scripts.append(script_name)
            elif (PROJECT_ROOT / f'{imp}.py').exists():
                root_scripts.append(f'{imp}.py')
        if root_scripts:
            dependencies[file_name] = root_scripts
            for dep in root_scripts:
                reverse_deps[dep].append(file_name)
    ps1_deps = analyze_ps1_files()
    for ps1_file, deps in ps1_deps.items():
        dependencies[ps1_file] = deps
        for dep in deps:
            if dep.endswith('.py') or dep.endswith('.ps1'):
                reverse_deps[dep].append(ps1_file)
    return (dependencies, reverse_deps)

def analyze_script_usage():
    """Проанализировать использование скриптов."""
    dependencies, reverse_deps = build_dependency_graph()
    usage_count = Counter()
    for deps in dependencies.values():
        for dep in deps:
            usage_count[dep] += 1
    manage_tools_deps = []
    if 'manage_tools.py' in dependencies:
        manage_tools_deps = dependencies['manage_tools.py']
    scripts_by_usage = {'highly_used': [], 'moderately_used': [], 'unused': [], 'leaf_nodes': []}
    all_scripts = set()
    all_scripts.update(dependencies.keys())
    all_scripts.update(reverse_deps.keys())
    for script in all_scripts:
        if script.endswith('.py'):
            depends_on = dependencies.get(script, [])
            depended_by = reverse_deps.get(script, [])
            if len(depended_by) >= 3:
                scripts_by_usage['highly_used'].append((script, len(depended_by)))
            elif len(depended_by) == 1 or len(depended_by) == 2:
                scripts_by_usage['moderately_used'].append((script, len(depended_by)))
            elif len(depended_by) == 0:
                scripts_by_usage['unused'].append((script, 0))
            if not depends_on:
                scripts_by_usage['leaf_nodes'].append(script)
    return {'dependencies': dict(dependencies), 'reverse_deps': dict(reverse_deps), 'usage_count': dict(usage_count), 'scripts_by_usage': scripts_by_usage, 'manage_tools_deps': manage_tools_deps}

def print_dependency_report(analysis):
    """Напечатать отчет о зависимостях."""
    print('=' * 80)
    print('АНАЛИЗ ЗАВИСИМОСТЕЙ СКРИПТОВ ПРОЕКТА')
    print('=' * 80)
    print('\n1. СКРИПТЫ, ИСПОЛЬЗУЕМЫЕ В manage_tools.py:')
    print('-' * 40)
    if analysis['manage_tools_deps']:
        for dep in sorted(analysis['manage_tools_deps']):
            print(f'  • {dep}')
    else:
        print('  Нет зависимостей')
    print('\n2. САМЫЕ ИСПОЛЬЗУЕМЫЕ СКРИПТЫ:')
    print('-' * 40)
    sorted_usage = sorted(analysis['usage_count'].items(), key=lambda x: x[1], reverse=True)
    for script, count in sorted_usage[:10]:
        print(f'  • {script}: используется {count} скриптом(ами)')
    print('\n3. СКРИПТЫ, КОТОРЫЕ НИКТО НЕ ИСПОЛЬЗУЕТ:')
    print('-' * 40)
    unused = analysis['scripts_by_usage']['unused']
    if unused:
        for script, _ in sorted(unused):
            print(f'  • {script}')
    else:
        print('  Все скрипты используются')
    print('\n4. ГРАФ ЗАВИСИМОСТЕЙ (основные связи):')
    print('-' * 40)
    for script, deps in analysis['dependencies'].items():
        if deps:
            print(f"  {script} -> {', '.join(deps)}")
    print('\n5. РЕКОМЕНДАЦИИ ПО УДАЛЕНИЮ:')
    print('-' * 40)
    candidates = []
    for script, _ in analysis['scripts_by_usage']['unused']:
        if script not in ['main.py', 'bot_runner.py', 'run_media_organizer.py', 'manage_tools.py']:
            candidates.append((script, 'Не используется другими скриптами'))
    for script, count in analysis['scripts_by_usage']['moderately_used']:
        if count == 1 and script not in ['header.py']:
            file_path = PROJECT_ROOT / script
            if file_path.exists() and file_path.stat().st_size < 1000:
                candidates.append((script, f'Мало используется ({count} зависимость), маленький размер'))
    if candidates:
        for script, reason in sorted(candidates):
            print(f'  • {script}: {reason}')
    else:
        print('  Нет явных кандидатов на удаление')
    print('\n' + '=' * 80)

def main():
    """Основная function."""
    print('Анализ зависимостей скриптов...')
    analysis = analyze_script_usage()
    print_dependency_report(analysis)
    report_file = PROJECT_ROOT / 'scripts_dependency_report.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('# Отчет о зависимостях скриптов\n\n')
        f.write('## Скрипты, используемые в manage_tools.py:\n')
        if analysis['manage_tools_deps']:
            for dep in sorted(analysis['manage_tools_deps']):
                f.write(f'- `{dep}`\n')
        else:
            f.write('Нет зависимостей\n')
        f.write('\n## Неиспользуемые скрипты:\n')
        unused = analysis['scripts_by_usage']['unused']
        if unused:
            for script, _ in sorted(unused):
                f.write(f'- `{script}`\n')
        else:
            f.write('Все скрипты используются\n')
        f.write('\n## Кандидаты на удаление:\n')
        candidates = []
        for script, _ in analysis['scripts_by_usage']['unused']:
            if script not in ['main.py', 'bot_runner.py', 'run_media_organizer.py', 'manage_tools.py']:
                candidates.append(script)
        if candidates:
            for script in sorted(candidates):
                f.write(f'- `{script}` - не используется другими скриптами\n')
        else:
            f.write('Нет явных кандидатов на удаление\n')
    print(f'\nОтчет сохранен в {report_file}')
if __name__ == '__main__':
    main()