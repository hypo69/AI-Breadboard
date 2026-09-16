import os
import re

def convert_readme(readme_path, target_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Simple formatting based on assumed structure
    # This might need refinement but it's a good start
    lines = content.split('\n')
    
    title = lines[0].replace('#', '').strip()
    
    formatted_content = f"# {title}\n\n"
    
    # Heuristic for sections - a very simple regex based approach
    sections = {
        'Назначение': '',
        'Структура': '',
        'Запуск': '',
        'API': ''
    }
    
    # Very basic parsing
    current_section = None
    for line in lines[1:]:
        if line.startswith('## '):
            section_name = line.replace('##', '').strip()
            if 'Назначение' in section_name: current_section = 'Назначение'
            elif 'Структура' in section_name: current_section = 'Структура'
            elif 'Запуск' in section_name: current_section = 'Запуск'
            elif 'API' in section_name: current_section = 'API'
            else: current_section = None
        elif current_section:
            sections[current_section] += line + '\n'
            
    for section, text in sections.items():
        if text:
            formatted_content += f"## {section}\n{text}\n"

    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(formatted_content)

# Apps
apps_dir = 'apps'
docs_apps_dir = 'docs/ru/guides/apps'
for app in os.listdir(apps_dir):
    app_path = os.path.join(apps_dir, app)
    if os.path.isdir(app_path):
        readme = os.path.join(app_path, 'README.md')
        if os.path.exists(readme):
            convert_readme(readme, os.path.join(docs_apps_dir, f"{app}.md"))

# Plugins
# (Similar logic for plugins)
