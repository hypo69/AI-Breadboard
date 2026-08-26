#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для автоматического обновления документации по скриптам проекта.
Запускается регулярно для поддержания актуальности SCRIPTS_DOCUMENTATION.md.
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent

# Категории скриптов с описаниями
SCRIPT_CATEGORIES = {
    'launch_scripts': {
        'name': 'Основные Launch-скрипты',
        'description': 'Скрипты запуска и настройки основных компонентов системы',
        'patterns': ['*.ps1', 'main.py', 'bot_runner.py'],
        'priority': '✅ Критически важны'
    },
    'cli_utilities': {
        'name': 'CLI Управление и утилиты', 
        'description': 'Командный интерфейс для управления системой',
        'patterns': ['manage_*.py'],
        'priority': '✅ Важные'
    },
    'media_processing': {
        'name': 'Обработка медиатеки',
        'description': 'Работа с медиатекой, классификация, обновление БД',
        'patterns': ['audit_*.py', 'generate_*.py', 'complete_*.py', 'fill_*.py', 'update_media_*.py'],
        'priority': '✅ Важные'
    },
    'analysis': {
        'name': 'Анализ и отчетность',
        'description': 'Анализ данных, генерация отчетов',
        'patterns': ['analyze_*.py'],
        'priority': '🔶 Полезные'
    },
    'diagnostics': {
        'name': 'Проверки и диагностика',
        'description': 'Проверка состояния системы',
        'patterns': ['check_*.py', 'debug_*.py'],
        'priority': '🔶 Полезные'
    },
    'database': {
        'name': 'Работа с БД',
        'description': 'Обслуживание базы данных',
        'patterns': ['update_db*.py', 'get_schema.py', 'remove_columns.py'],
        'priority': '🔶 Технические'
    },
    'migration': {
        'name': 'Миграции и бэкапы',
        'description': 'Миграция данных, резервное копирование',
        'patterns': ['*migration*.py'],
        'priority': '🔶 Операционные'
    },
    'counting': {
        'name': 'Статистика и подсчет',
        'description': 'Подсчет различных метрик',
        'patterns': ['count_*.py'],
        'priority': '🔶 Утилиты'
    },
    'other': {
        'name': 'Прочие скрипты',
        'description': 'Скрипты, не попавшие в другие категории',
        'patterns': ['*.py'],
        'priority': '🔶 Разные'
    }
}

def get_script_info(script_path):
    """Получить информацию о скрипте из его содержимого."""
    info = {
        'name': script_path.name,
        'size': script_path.stat().st_size,
        'modified': datetime.fromtimestamp(script_path.stat().st_mtime),
        'lines': 0,
        'purpose': 'Не определено',
        'dependencies': [],
        'usage_examples': []
    }
    
    try:
        content = script_path.read_text(encoding='utf-8', errors='ignore')
        info['lines'] = len(content.split('\n'))
        
        # Извлечение назначения из docstring или комментариев
        lines = content.split('\n')
        purpose_found = False
        
        for i, line in enumerate(lines[:20]):  # Проверяем первые 20 строк
            line_lower = line.lower()
            
            # Ищем docstring
            if '"""' in line and not purpose_found and i < 10:
                # Многострочный docstring
                docstring_lines = []
                for j in range(i + 1, min(i + 10, len(lines))):
                    if '"""' in lines[j]:
                        break
                    docstring_lines.append(lines[j].strip())
                if docstring_lines:
                    info['purpose'] = ' '.join(docstring_lines[:3])[:200]
                    purpose_found = True
            
            # Ищем однострочные комментарии с назначением
            elif not purpose_found and line.strip().startswith('#') and any(word in line_lower for word in ['название', 'назначение', 'описание', 'purpose', 'description']):
                info['purpose'] = line.strip('# \t\n\r')[:200]
                purpose_found = True
        
        # Если не нашли назначение, используем первую содержательную строку
        if not purpose_found:
            for line in lines:
                if line.strip() and not line.strip().startswith(('#', '"', "'", 'import', 'from')):
                    info['purpose'] = line.strip()[:150]
                    break
        
        # Поиск зависимостей
        for line in lines:
            if 'import' in line:
                # Простые импорты
                if 'import ' in line and ' as ' not in line:
                    parts = line.split('import')[1].strip().split(',')
                    for part in parts:
                        module = part.strip().split()[0]
                        if module and '.' not in module:  # Только модули верхнего уровня
                            info['dependencies'].append(module)
        
    except Exception as e:
        info['purpose'] = f"Ошибка чтения: {str(e)}"
    
    return info

def categorize_script(script_name):
    """Определить категорию скрипта."""
    for category_id, category_info in SCRIPT_CATEGORIES.items():
        for pattern in category_info['patterns']:
            # Преобразуем паттерн в регулярное выражение
            regex_pattern = pattern.replace('*', '.*').replace('?', '.')
            if re.match(f'^{regex_pattern}$', script_name):
                return category_id
    return 'other'

def generate_documentation():
    """Сгенерировать документацию по скриптам."""
    print("Генерация документации по скриптам...")
    
    # Сбор всех скриптов
    all_scripts = []
    
    # Python скрипты
    for py_file in PROJECT_ROOT.glob("*.py"):
        if py_file.name not in ['analyze_dependencies.py', 'update_scripts_documentation.py']:
            all_scripts.append(py_file)
    
    # PowerShell скрипты
    for ps1_file in PROJECT_ROOT.glob("*.ps1"):
        all_scripts.append(ps1_file)
    
    # Группировка по категориям
    categorized_scripts = defaultdict(list)
    
    for script_path in all_scripts:
        category = categorize_script(script_path.name)
        script_info = get_script_info(script_path)
        categorized_scripts[category].append(script_info)
    
    # Сортировка внутри категорий
    for category in categorized_scripts:
        categorized_scripts[category].sort(key=lambda x: x['name'].lower())
    
    # Генерация Markdown документации
    md_content = []
    
    # Заголовок
    md_content.append(f"# 📚 Документация по скриптам проекта ai-assistant\n")
    md_content.append(f"**Версия:** 1.0  \n")
    md_content.append(f"**Дата обновления:** {datetime.now().strftime('%d %B %Y')}  \n")
    md_content.append(f"**Статус:** Актуально (автоматически обновляется)\n")
    
    # Статистика
    md_content.append("## 📊 Общая статистика\n")
    md_content.append("| Категория | Количество | Статус |")
    md_content.append("|-----------|------------|--------|")
    
    total_scripts = 0
    for category_id, scripts in categorized_scripts.items():
        if scripts:  # Только непустые категории
            category_info = SCRIPT_CATEGORIES[category_id]
            count = len(scripts)
            total_scripts += count
            md_content.append(f"| {category_info['name']} | {count} | {category_info['priority']} |")
    
    md_content.append(f"| **Итого активных скриптов** | **{total_scripts}** | |\n")
    
    # Подробное описание по категориям
    for category_id, scripts in categorized_scripts.items():
        if not scripts:
            continue
            
        category_info = SCRIPT_CATEGORIES[category_id]
        md_content.append(f"\n## 🚀 {category_info['name']}\n")
        md_content.append(f"**Описание:** {category_info['description']}  \n")
        md_content.append(f"**Статус:** {category_info['priority']}\n")
        
        for script in scripts:
            md_content.append(f"\n### **{script['name']}**")
            
            if script['name'].endswith('.ps1'):
                md_content.append(f"**Тип:** PowerShell скрипт  \n")
            else:
                md_content.append(f"**Тип:** Python скрипт  \n")
            
            md_content.append(f"**Размер:** {script['size']:,} байт  \n")
            md_content.append(f"**Строк кода:** {script['lines']}  \n")
            md_content.append(f"**Изменен:** {script['modified'].strftime('%Y-%m-%d %H:%M')}  \n")
            md_content.append(f"**Назначение:** {script['purpose']}\n")
            
            # Примеры использования для основных скриптов
            if script['name'] in ['run.ps1', 'manage_tools.py']:
                md_content.append(f"**Примеры использования:**\n")
                
                if script['name'] == 'run.ps1':
                    md_content.append(f"```bash\n.\\run.ps1\n```\n")
                elif script['name'] == 'manage_tools.py':
                    md_content.append(f"```bash\npy manage_tools.py rag rebuild       # Перестроение RAG-индекса\npy manage_tools.py knowledge extract # Извлечение знаний\n```\n")
    
    # Принципы обслуживания
    md_content.append("\n## 📋 Принципы обслуживания\n")
    md_content.append("### 1. Регулярное обновление документации\n")
    md_content.append("- Эта документация обновляется автоматически при запуске `update_scripts_documentation.py`\n")
    md_content.append("- Рекомендуется запускать обновление после добавления или удаления скриптов\n")
    
    md_content.append("\n### 2. Автоматическое обновление\n")
    md_content.append("```bash\n# Обновить документацию\npython update_scripts_documentation.py\n```\n")
    
    md_content.append("\n### 3. Анализ зависимостей\n")
    md_content.append("```bash\n# Проанализировать зависимости между скриптами\npython analyze_dependencies.py\n```\n")
    
    # Информация о проекте
    md_content.append("\n## 📞 Контакты и поддержка\n")
    md_content.append(f"**Проект:** ai-assistant  \n")
    md_content.append(f"**Дата последнего обновления:** {datetime.now().strftime('%d %B %Y %H:%M')}  \n")
    md_content.append(f"**Скрипт обновления:** `update_scripts_documentation.py`  \n")
    md_content.append("\n*Документация автоматически обновляется при изменениях в репозитории.*\n")
    
    # Сохранение документации
    doc_file = PROJECT_ROOT / "SCRIPTS_DOCUMENTATION.md"
    doc_file.write_text('\n'.join(md_content), encoding='utf-8')
    
    print(f"✅ Документация сохранена в {doc_file}")
    print(f"📊 Обработано {len(all_scripts)} скриптов")
    
    # Также создаем краткую сводку
    create_summary(categorized_scripts)

def create_summary(categorized_scripts):
    """Создать краткую сводку по скриптам."""
    summary = ["# Краткая сводка по скриптам\n"]
    summary.append(f"*Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
    
    for category_id, scripts in categorized_scripts.items():
        if not scripts:
            continue
            
        category_info = SCRIPT_CATEGORIES[category_id]
        summary.append(f"\n## {category_info['name']} ({len(scripts)})\n")
        
        for script in scripts:
            if script['name'].endswith('.ps1'):
                summary.append(f"- `{script['name']}` - PowerShell ({script['size']:,} байт)")
            else:
                summary.append(f"- `{script['name']}` - Python ({script['lines']} строк)")
    
    summary_file = PROJECT_ROOT / "SCRIPTS_SUMMARY.md"
    summary_file.write_text('\n'.join(summary), encoding='utf-8')
    
    print(f"📋 Краткая сводка сохранена в {summary_file}")

def main():
    """Основная функция."""
    print("=" * 60)
    print("ОБНОВЛЕНИЕ ДОКУМЕНТАЦИИ ПО СКРИПТАМ")
    print("=" * 60)
    
    try:
        generate_documentation()
        
        # Также запускаем анализ за��исимостей для полноты
        print("\n" + "=" * 60)
        print("ДОПОЛНИТЕЛЬНЫЙ АНАЛИЗ ЗАВИСИМОСТЕЙ")
        print("=" * 60)
        
        if (PROJECT_ROOT / "analyze_dependencies.py").exists():
            import subprocess
            result = subprocess.run([sys.executable, "analyze_dependencies.py"], 
                                  capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print(f"Предупреждения: {result.stderr}")
        else:
            print("Скрипт analyze_dependencies.py не найден, пропускаем анализ зависимостей.")
        
        print("\n" + "=" * 60)
        print("✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Ошибка при обновлении документации: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()