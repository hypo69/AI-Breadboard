"""
Скрипт для автоматической генерации API-документации из Python docstrings.

Использует ast для парсинга Python кода и создаёт структурированные Markdown файлы.
Парсит docstrings в формате Google-style и генерирует полноценную API-документацию
в `docs/ru/api/` для следующих модулей:
- src.skills
- src.ai (core)
- src.ai.agents
- src.utils

Автор: AI-Breadboard Team
Язык: Русский
"""

import os
import ast
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import inspect
import re


class DocstringParser:
    """
    Парсер Python docstrings в Google-формате.
    
    Извлекает из docstrings:
    - Краткое описание (summary)
    - Подробное описание (extended description)
    - Параметры функции/метода
    - Типы возвращаемых значений
    - Исключения (raises)
    - Примеры кода
    """
    
    @staticmethod
    def parse_google_docstring(docstring: str) -> Dict[str, Any]:
        """
        Парсит Google-style docstring в структурированный словарь.
        
        Args:
            docstring: Исходная строка документации
            
        Returns:
            Словарь с ключами: summary, description, args, returns, raises, examples
        """
        if not docstring:
            return {
                'summary': 'Документация отсутствует',
                'description': '',
                'args': {},
                'returns': '',
                'raises': [],
                'examples': [],
            }
        
        lines = docstring.strip().split('\n')
        result = {
            'summary': '',
            'description': '',
            'args': {},
            'returns': '',
            'raises': [],
            'examples': [],
        }
        
        # Извлекаем первую строку как summary
        result['summary'] = lines[0].strip() if lines else 'Документация отсутствует'
        
        # Ищем основные разделы
        current_section = None
        section_content = []
        
        for i, line in enumerate(lines[1:], 1):
            stripped = line.strip()
            
            # Определяем тип раздела
            if stripped.startswith('Args:'):
                if current_section:
                    DocstringParser._process_section(
                        current_section, section_content, result
                    )
                current_section = 'args'
                section_content = []
            elif stripped.startswith('Returns:'):
                if current_section:
                    DocstringParser._process_section(
                        current_section, section_content, result
                    )
                current_section = 'returns'
                section_content = []
            elif stripped.startswith('Raises:'):
                if current_section:
                    DocstringParser._process_section(
                        current_section, section_content, result
                    )
                current_section = 'raises'
                section_content = []
            elif stripped.startswith('Examples:'):
                if current_section:
                    DocstringParser._process_section(
                        current_section, section_content, result
                    )
                current_section = 'examples'
                section_content = []
            elif stripped and not current_section and current_section is None:
                # Это часть описания до первого раздела
                result['description'] += line + '\n'
            elif current_section:
                section_content.append(line)
        
        # Обработаем последний раздел
        if current_section:
            DocstringParser._process_section(current_section, section_content, result)
        
        # Очистим description
        result['description'] = result['description'].strip()
        
        return result
    
    @staticmethod
    def _process_section(section_type: str, content: List[str], result: Dict) -> None:
        """Обрабатывает содержимое определённого раздела."""
        if section_type == 'args':
            for line in content:
                if ':' in line:
                    parts = line.split(':', 1)
                    arg_name = parts[0].strip().replace('(', '').replace(')', '')
                    arg_desc = parts[1].strip() if len(parts) > 1 else ''
                    result['args'][arg_name] = arg_desc
        
        elif section_type == 'returns':
            result['returns'] = '\n'.join(content).strip()
        
        elif section_type == 'raises':
            for line in content:
                line = line.strip()
                if line:
                    result['raises'].append(line)
        
        elif section_type == 'examples':
            result['examples'] = [line for line in content if line.strip()]
    
    @staticmethod
    def parse_function(func_node: ast.FunctionDef) -> Dict[str, Any]:
        """
        Парсит функцию и извлекает информацию из docstring и AST.
        
        Args:
            func_node: AST узел функции
            
        Returns:
            Словарь с информацией о функции
        """
        docstring = ast.get_docstring(func_node) or ''
        doc_info = DocstringParser.parse_google_docstring(docstring)
        
        # Извлекаем параметры из AST
        args = []
        defaults = {}
        
        if func_node.args.args:
            for arg in func_node.args.args:
                if arg.arg != 'self' and arg.arg != 'cls':
                    args.append(arg.arg)
        
        # Значения по умолчанию
        num_defaults = len(func_node.args.defaults)
        if num_defaults > 0:
            default_args = func_node.args.args[-num_defaults:]
            for i, default in enumerate(func_node.args.defaults):
                arg_name = default_args[i].arg
                try:
                    default_value = ast.literal_eval(ast.unparse(default))
                    defaults[arg_name] = default_value
                except (ValueError, AttributeError):
                    defaults[arg_name] = '<значение>'
        
        return {
            'name': func_node.name,
            'type': 'function',
            'docstring': docstring,
            'doc_info': doc_info,
            'args': args,
            'defaults': defaults,
            'lineno': func_node.lineno,
            'is_async': isinstance(func_node, ast.AsyncFunctionDef),
        }
    
    @staticmethod
    def parse_class(class_node: ast.ClassDef) -> Dict[str, Any]:
        """
        Парсит класс и его методы.
        
        Args:
            class_node: AST узел класса
            
        Returns:
            Словарь с информацией о классе и его методах
        """
        docstring = ast.get_docstring(class_node) or ''
        doc_info = DocstringParser.parse_google_docstring(docstring)
        
        methods = []
        attributes = []
        
        for node in class_node.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(DocstringParser.parse_function(node))
            elif isinstance(node, ast.Assign):
                # Переменные класса
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)
        
        # Извлекаем родительские классы
        bases = []
        for base in class_node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.unparse(base))
        
        return {
            'name': class_node.name,
            'type': 'class',
            'docstring': docstring,
            'doc_info': doc_info,
            'methods': methods,
            'attributes': attributes,
            'bases': bases,
            'lineno': class_node.lineno,
        }


class MarkdownGenerator:
    """
    Генератор Markdown из распарсенной информации о коде.
    
    Создаёт структурированные Markdown файлы с:
    - Заголовками различных уровней
    - Документацией функций и классов
    - Таблицами параметров
    - Примерами кода
    - Перекрёстными ссылками
    """
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """Экранирует специальные символы Markdown."""
        return text.replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
    
    @staticmethod
    def generate_header(title: str, level: int = 1) -> str:
        """
        Генерирует Markdown заголовок.
        
        Args:
            title: Текст заголовка
            level: Уровень заголовка (1-6)
            
        Returns:
            Markdown заголовок
        """
        return f"{'#' * level} {title}\n\n"
    
    @staticmethod
    def generate_code_block(code: str, language: str = 'python') -> str:
        """
        Генерирует блок кода в Markdown.
        
        Args:
            code: Текст кода
            language: Язык программирования
            
        Returns:
            Markdown блок кода
        """
        return f"```{language}\n{code}\n```\n\n"
    
    @staticmethod
    def generate_function_docs(func: Dict[str, Any]) -> str:
        """
        Генерирует документацию функции в Markdown.
        
        Args:
            func: Словарь с информацией о функции
            
        Returns:
            Markdown документация функции
        """
        doc_info = func['doc_info']
        
        # Заголовок функции
        prefix = 'async ' if func.get('is_async') else ''
        args_str = ', '.join(func['args']) if func['args'] else ''
        md = f"### `{prefix}{func['name']}({args_str})`\n\n"
        
        # Сводка
        if doc_info['summary']:
            md += f"{doc_info['summary']}\n\n"
        
        # Подробное описание
        if doc_info['description']:
            md += f"{doc_info['description']}\n\n"
        
        # Параметры
        if func['args'] or doc_info['args']:
            md += "**Параметры:**\n\n"
            md += "| Параметр | Описание |\n"
            md += "|----------|----------|\n"
            
            for arg in func['args']:
                desc = doc_info['args'].get(arg, '')
                if arg in func['defaults']:
                    desc += f" (по умолчанию: `{func['defaults'][arg]}`)"
                md += f"| `{arg}` | {desc} |\n"
            
            md += "\n"
        
        # Возвращаемое значение
        if doc_info['returns']:
            md += "**Возвращает:**\n\n"
            md += f"{doc_info['returns']}\n\n"
        
        # Исключения
        if doc_info['raises']:
            md += "**Исключения:**\n\n"
            for exception in doc_info['raises']:
                md += f"- `{exception}`\n"
            md += "\n"
        
        # Примеры
        if doc_info['examples']:
            md += "**Примеры:**\n\n"
            for example in doc_info['examples']:
                if example.strip():
                    md += f"```python\n{example}\n```\n\n"
        
        return md
    
    @staticmethod
    def generate_class_docs(cls: Dict[str, Any]) -> str:
        """
        Генерирует документацию класса в Markdown.
        
        Args:
            cls: Словарь с информацией о классе
            
        Returns:
            Markdown документация класса
        """
        doc_info = cls['doc_info']
        
        # Заголовок класса
        bases_str = f"({', '.join(cls['bases'])})" if cls['bases'] else ''
        md = f"## `{cls['name']}{bases_str}`\n\n"
        
        # Сводка
        if doc_info['summary']:
            md += f"{doc_info['summary']}\n\n"
        
        # Подробное описание
        if doc_info['description']:
            md += f"{doc_info['description']}\n\n"
        
        # Атрибуты
        if cls['attributes']:
            md += "**Атрибуты:**\n\n"
            for attr in cls['attributes']:
                md += f"- `{attr}`\n"
            md += "\n"
        
        # Методы
        if cls['methods']:
            md += "### Методы\n\n"
            for method in cls['methods']:
                md += MarkdownGenerator.generate_function_docs(method)
        
        return md


class APIDocumentationGenerator:
    """
    Главный генератор API-документации.
    
    Обрабатывает Python модули, извлекает документацию из docstrings
    и генерирует структурированные Markdown файлы в docs/ru/api/.
    """
    
    def __init__(self, src_root: Path, docs_root: Path):
        """
        Инициализирует генератор.
        
        Args:
            src_root: Корневая директория исходного кода (src/)
            docs_root: Корневая директория документации (docs/)
        """
        self.src_root = src_root
        self.docs_root = docs_root
        self.api_dir = docs_root / 'ru' / 'api'
        self.api_dir.mkdir(parents=True, exist_ok=True)
        self.generated_modules = []
    
    def process_python_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Обрабатывает Python файл и извлекает документацию.
        
        Args:
            file_path: Путь к Python файлу
            
        Returns:
            Словарь с информацией о модуле
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content)
        except Exception as e:
            print(f"⚠️  Ошибка чтения файла {file_path}: {e}")
            return {
                'file': str(file_path.relative_to(self.src_root)),
                'classes': [],
                'functions': [],
                'error': str(e),
            }
        
        docs = {
            'file': str(file_path.relative_to(self.src_root)),
            'classes': [],
            'functions': [],
        }
        
        # Модульный docstring
        module_docstring = ast.get_docstring(tree)
        if module_docstring:
            docs['module_doc'] = module_docstring
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                docs['classes'].append(DocstringParser.parse_class(node))
            elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                # Только функции верхнего уровня
                docs['functions'].append(DocstringParser.parse_function(node))
        
        return docs
    
    def generate_module_docs(self, module_name: str, module_path: Optional[Path] = None) -> str:
        """
        Генерирует документацию для модуля.
        
        Args:
            module_name: Имя модуля (например, 'breadboard.skills')
            module_path: Опциональный путь к модулю
            
        Returns:
            Markdown документация модуля
        """
        # Определяем путь к модулю
        if module_path is None:
            # Преобразуем имя модуля в путь
            path_parts = module_name.split('.')
            if path_parts[0] == 'src':
                module_path = self.src_root / Path(*path_parts[1:])
            else:
                module_path = self.src_root / Path(*path_parts)
        
        # Проверяем __init__.py
        init_file = module_path / '__init__.py'
        if not init_file.exists():
            # Может быть это просто один файл
            py_file = Path(str(module_path) + '.py')
            if py_file.exists():
                init_file = py_file
            else:
                return f"# Модуль `{module_name}`\n\nМодуль не найден по пути: {module_path}\n"
        
        # Обрабатываем основной файл
        docs = self.process_python_file(init_file)
        
        # Генерируем Markdown
        md = MarkdownGenerator.generate_header(f"Модуль `{module_name}`", 1)
        
        # Модульный docstring
        if 'module_doc' in docs:
            md += f"{docs['module_doc']}\n\n"
        
        # Классы
        if docs['classes']:
            md += "## Классы\n\n"
            for cls in docs['classes']:
                md += MarkdownGenerator.generate_class_docs(cls)
        
        # Функции верхнего уровня
        if docs['functions']:
            md += "## Функции\n\n"
            for func in docs['functions']:
                md += MarkdownGenerator.generate_function_docs(func)
        
        return md
    
    def generate(self, modules: List[str]) -> None:
        """
        Генерирует API-документацию для перечисленных модулей.
        
        Args:
            modules: Список имён модулей для обработки
        """
        print("📚 Начало генерации API-документации...")
        print(f"   Исходный код: {self.src_root}")
        print(f"   Выходная директория: {self.api_dir}\n")
        
        for module in modules:
            try:
                output_file = self.api_dir / f'{module.split(".")[-1]}.md'
                content = self.generate_module_docs(module)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.generated_modules.append(module)
                print(f"✓ Сгенерирована документация для модуля: {module}")
                
                # Используем абсолютный путь для вывода
                try:
                    rel_path = output_file.relative_to(Path.cwd())
                    print(f"  Выходной файл: {rel_path}")
                except ValueError:
                    # Если не можно сделать относительным, используем абсолютный
                    print(f"  Выходной файл: {output_file}")
                
            except Exception as e:
                print(f"✗ Ошибка при генерации документации для {module}: {e}")
        
        print()
        
        # Генерируем индекс API
        self.generate_api_index(modules)
    
    def generate_api_index(self, modules: List[str]) -> None:
        """
        Генерирует индексный файл API-документации.
        
        Args:
            modules: Список обработанных модулей
        """
        index_file = self.api_dir / 'index.md'
        
        md = MarkdownGenerator.generate_header("API-документация", 1)
        md += "Автоматически сгенерированная документация API проекта AI-Breadboard.\n\n"
        
        md += "Документация содержит полное описание:\n"
        md += "- Классов и их методов\n"
        md += "- Функций верхнего уровня\n"
        md += "- Параметров и типов возвращаемых значений\n"
        md += "- Примеров использования\n\n"
        
        md += "## Модули\n\n"
        
        for module in sorted(modules):
            module_short = module.split('.')[-1]
            md += f"- [`{module}`]({module_short}.md)\n"
        
        md += "\n"
        md += "## Информация о генерации\n\n"
        md += f"Документация автоматически генерируется из docstrings в исходном коде.\n"
        md += f"Формат docstrings: Google-style (PEP 257).\n"
        md += f"Сгенерировано {len(self.generated_modules)} модулей.\n\n"
        
        md += "---\n\n"
        md += "*Последнее обновление: автоматическое при обновлении кода*\n"
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(md)
        
        print(f"✓ Сгенерирован индекс API")
        try:
            rel_path = index_file.relative_to(Path.cwd())
            print(f"  Выходной файл: {rel_path}\n")
        except ValueError:
            print(f"  Выходной файл: {index_file}\n")
    
    def print_summary(self) -> None:
        """Выводит сводку по генерации."""
        print("=" * 60)
        print("📊 СВОДКА ПО ГЕНЕРАЦИИ API-ДОКУМЕНТАЦИИ")
        print("=" * 60)
        print(f"\nСгенерировано модулей: {len(self.generated_modules)}")
        
        if self.generated_modules:
            print("\nМодули:")
            for module in sorted(self.generated_modules):
                print(f"  • {module}")
        
        print(f"\nВыходная директория: {self.api_dir}")
        print(f"Файлы:")
        
        if self.api_dir.exists():
            for md_file in sorted(self.api_dir.glob('*.md')):
                size = md_file.stat().st_size
                try:
                    rel_path = md_file.relative_to(Path.cwd())
                    print(f"  • {rel_path} ({size} байт)")
                except ValueError:
                    print(f"  • {md_file.name} ({size} байт)")
        
        print("\n" + "=" * 60 + "\n")


def main():
    """Главная функция скрипта."""
    # Конфигурация путей
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    src_root = project_root / 'src'
    docs_root = project_root / 'docs'
    
    # Проверяем существование директорий
    if not src_root.exists():
        print(f"❌ Ошибка: директория исходного кода не найдена: {src_root}")
        sys.exit(1)
    
    if not docs_root.exists():
        print(f"❌ Ошибка: директория документации не найдена: {docs_root}")
        sys.exit(1)
    
    print(f"\n🔍 Конфигурация генератора:")
    print(f"   Корень проекта: {project_root}")
    print(f"   Исходный код: {src_root}")
    print(f"   Документация: {docs_root}\n")
    
    # Модули для генерации документации
    # Адаптирована структура под реальную структуру проекта
    modules = [
        'src.skills',
        'src.ai.agents',
        'src.ai',
        'src.utils',
    ]
    
    # Создаём генератор и запускаем генерацию
    generator = APIDocumentationGenerator(src_root, docs_root)
    
    try:
        generator.generate(modules)
        generator.print_summary()
        print("✅ API-документация успешно сгенерирована!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Критическая ошибка при генерации: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
