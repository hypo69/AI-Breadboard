#!/usr/bin/env python3
"""
Скрипт для валидации структуры документации.

Проверяет:
1. Наличие обязательных файлов и директорий
2. Корректность Markdown-форматирования
3. Правильность расположения заголовков

Exit codes:
  0 - ошибок нет
  1 - найдены ошибки
"""

import sys
import os
import re
from pathlib import Path
from typing import List, Tuple, Union, Optional

class DocumentationValidator:
    """Валидатор структуры документации для тестов и CI/CD."""

    REQUIRED_DIRECTORIES = ['manual', 'guides', 'architecture', 'plugins', 'skills', 'apps', 'mcp', 'cook-book', 'developer', '_templates', '_static']

    def __init__(self, docs_root: Union[str, Path] = 'docs/ru'):
        self.docs_root = Path(docs_root)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.success_messages: List[str] = []

    def validate_file_exists(self, filename: str) -> bool:
        """Проверяет существование файла относительно корня документации."""
        full_path = self.docs_root / filename
        if full_path.exists():
            self.success_messages.append(f"✓ Файл существует: {filename}")
            return True
        self.errors.append(f"❌ Обязательный файл отсутствует: {filename}")
        return False

    def validate_sections(self, filename: str, required_sections: List[str]) -> bool:
        """Проверяет наличие обязательных разделов в файле."""
        full_path = self.docs_root / filename
        if not full_path.exists():
            self.errors.append(f"❌ Файл для проверки разделов не найден: {filename}")
            return False
        try:
            content = full_path.read_text(encoding='utf-8')
        except Exception as ex:
            self.errors.append(f"❌ Ошибка чтения файла {filename}: {ex}")
            return False

        all_found = True
        for section in required_sections:
            if section not in content:
                self.warnings.append(f"⚠️  Раздел '{section}' отсутствует в {filename}")
                all_found = False
        return all_found

    def validate_markdown_syntax(self, file_path: Union[str, Path]) -> bool:
        """Проверяет базовый синтаксис Markdown файла."""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.docs_root / path
        if not path.exists():
            self.errors.append(f"❌ Файл не найден: {path}")
            return False

        try:
            content = path.read_text(encoding='utf-8')
        except Exception as ex:
            self.errors.append(f"❌ Ошибка чтения файла {path}: {ex}")
            return False

        # Проверка сбалансированности блоков кода (```)
        code_block_count = content.count('```')
        if code_block_count % 2 != 0:
            self.errors.append(f"❌ Несбалансированные блоки кода ``` в {path}")
            return False

        # Проверка ссылок на скобки
        for line in content.splitlines():
            if '[' in line and ']' not in line:
                self.warnings.append(f"⚠️  Несбалансированная скобка '[' в строке: {line}")
            elif '](' in line and ')' not in line:
                self.warnings.append(f"⚠️  Несбалансированная скобка ')' в ссылке: {line}")

        return True

    def validate_directory_structure(self, required_dirs: Optional[List[str]] = None) -> bool:
        """Проверяет наличие требуемых директорий."""
        dirs_to_check = required_dirs or self.REQUIRED_DIRECTORIES
        all_present = True
        for dir_name in dirs_to_check:
            dir_path = self.docs_root / dir_name
            if not dir_path.is_dir():
                self.warnings.append(f"⚠️  Директория отсутствует: {dir_name}")
                all_present = False
            else:
                self.success_messages.append(f"✓ Директория существует: {dir_name}")
        return all_present

    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """Запускает полную валидацию структуры и возвращает статус, ошибки и предупреждения."""
        self.errors.clear()
        self.warnings.clear()
        self.success_messages.clear()

        self.validate_directory_structure()
        self.validate_file_exists('index.md')
        self.validate_file_exists('conf.py')
        self.validate_file_exists('manual/index.md')
        self.validate_file_exists('developer/index.md')

        for md_file in self.docs_root.rglob('*.md'):
            self.validate_markdown_syntax(md_file)

        is_success = len(self.errors) == 0
        return is_success, self.errors, self.warnings

    def generate_report(self) -> str:
        """Генерирует форматированный отчёт о результатах валидации."""
        lines = [
            "=" * 60,
            "📋 ОТЧЁТ О ВАЛИДАЦИИ ДОКУМЕНТАЦИИ",
            "=" * 60,
        ]
        if self.errors:
            lines.append(f"❌ СТАТУС: НАЙДЕНО {len(self.errors)} ОШИБОК")
            lines.append("\n❌ ОШИБКИ:")
            for err in self.errors:
                lines.append(f"  {err}")
        else:
            lines.append("✅ СТАТУС: ВАЛИДАЦИЯ УСПЕШНА")

        if self.warnings:
            lines.append("\n⚠️  ПРЕДУПРЕЖДЕНИЯ:")
            for warn in self.warnings:
                lines.append(f"  {warn}")


        if self.success_messages and not self.errors:
            lines.append("\n✓ УСПЕШНЫЕ ПРОВЕРКИ:")
            for msg in self.success_messages:
                lines.append(f"  {msg}")

        lines.append("=" * 60)
        return "\n".join(lines)


class DocsValidator:
    """Валидатор структуры документации."""


    
    # Обязательные файлы в корне документации
    REQUIRED_ROOT_FILES = {
        'docs/ru/index.md': 'Главный файл документации',
        'docs/ru/conf.py': 'Конфигурация Sphinx',
        'docs/ru/requirements-docs.txt': 'Зависимости для документации',
        'docs/ru/contributing.md': 'Руководство по контрибьютингу',
        'docs/ru/changelog.md': 'История изменений',
    }
    
    # Обязательные директории
    REQUIRED_DIRECTORIES = {
        'docs/ru/manual': 'Руководства пользователя',
        'docs/ru/guides': 'Практические руководства',
        'docs/ru/architecture': 'Архитектурная документация',
        'docs/ru/plugins': 'Документация плагинов',
        'docs/ru/skills': 'Документация навыков',
        'docs/ru/apps': 'Документация приложений',
        'docs/ru/mcp': 'Документация MCP-серверов',
        'docs/ru/cook-book': 'Учебное пособие',
        'docs/ru/developer': 'Руководство разработчика',
    }
    
    # Обязательные файлы в поддиректориях
    REQUIRED_SUBDIRS = {
        'docs/ru/manual': [
            'index.md',
            'installation.md',
            'getting-started.md',
            'configuration.md',
            'config.md',
            'RUN.md',
            'troubleshooting.md',
        ],
        'docs/ru/guides': [
            'index.md',
            'quickstart.md',
            'README.md',
        ],
        'docs/ru/architecture': [
            'index.md',
            'overview.md',
            'components.md',
        ],
        'docs/ru/plugins': [
            'index.md',
            'catalog.md',
            'architecture.md',
            'development.md',
        ],
        'docs/ru/skills': [
            'index.md',
            'catalog.md',
            'architecture.md',
            'development.md',
        ],
        'docs/ru/apps': [
            'index.md',
            'catalog.md',
        ],
        'docs/ru/mcp': [
            'index.md',
            'catalog.md',
            'guide.md',
        ],
        'docs/ru/developer': [
            'index.md',
            'README.md',
        ],
        'docs/ru/cook-book': [
            'index.md',
            'README.md',
        ],
    }
    
    def __init__(self, docs_root: str = 'docs/ru'):
        """Инициализация валидатора.
        
        Args:
            docs_root: Корневая директория документации
        """
        self.docs_root = Path(docs_root)
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self) -> bool:
        """Запустить все проверки.
        
        Returns:
            True если ошибок нет, False если найдены ошибки
        """
        print(f"📋 Валидация структуры документации в {self.docs_root}/")
        print("-" * 60)
        
        self._check_root_files()
        self._check_directories()
        self._check_subdirectory_files()
        self._check_markdown_files()
        
        self._print_report()
        
        return len(self.errors) == 0
    
    def _check_root_files(self) -> None:
        """Проверить наличие обязательных файлов в корне."""
        print("🔍 Проверка обязательных файлов...")
        
        for file_path, description in self.REQUIRED_ROOT_FILES.items():
            full_path = Path(file_path)
            if not full_path.exists():
                self.errors.append(
                    f"❌ Обязательный файл отсутствует: {file_path} ({description})"
                )
            else:
                print(f"  ✓ {file_path}")
    
    def _check_directories(self) -> None:
        """Проверить наличие обязательных директорий."""
        print("🔍 Проверка обязательных директорий...")
        
        for dir_path, description in self.REQUIRED_DIRECTORIES.items():
            full_path = Path(dir_path)
            if not full_path.is_dir():
                self.errors.append(
                    f"❌ Обязательная директория отсутствует: {dir_path} ({description})"
                )
            else:
                print(f"  ✓ {dir_path}/")
    
    def _check_subdirectory_files(self) -> None:
        """Проверить обязательные файлы в поддиректориях."""
        print("🔍 Проверка файлов в поддиректориях...")
        
        for subdir, files in self.REQUIRED_SUBDIRS.items():
            subdir_path = Path(subdir)
            
            if not subdir_path.is_dir():
                self.errors.append(f"❌ Директория отсутствует: {subdir}/")
                continue
            
            print(f"  📁 {subdir}/")
            for filename in files:
                file_path = subdir_path / filename
                if not file_path.exists():
                    self.errors.append(
                        f"❌ Обязательный файл отсутствует: {subdir}/{filename}"
                    )
                else:
                    print(f"    ✓ {filename}")
    
    def _check_markdown_files(self) -> None:
        """Проверить Markdown-файлы на корректность."""
        print("🔍 Проверка Markdown-файлов...")
        
        md_files = list(self.docs_root.rglob('*.md'))
        
        if not md_files:
            self.warnings.append("⚠️  Markdown-файлы не найдены")
            return
        
        for md_file in md_files:
            relative_path = md_file.relative_to(self.docs_root)
            self._check_markdown_content(md_file, str(relative_path))
    
    def _check_markdown_content(self, file_path: Path, relative_path: str) -> None:
        """Проверить содержимое Markdown-файла.
        
        Args:
            file_path: Полный путь к файлу
            relative_path: Относительный путь для отчёта
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            self.errors.append(
                f"❌ Ошибка чтения файла {relative_path}: {str(e)}"
            )
            return
        
        # Проверка наличия заголовка
        has_heading = any(line.startswith('#') for line in lines)
        if not has_heading:
            self.errors.append(
                f"❌ Файл {relative_path} не содержит заголовок (# или ##)"
            )
            return
        
        # Проверка на пустые заголовки
        for i, line in enumerate(lines, 1):
            if re.match(r'^#+\s*$', line):
                self.errors.append(
                    f"❌ Файл {relative_path}, строка {i}: пустой заголовок"
                )
        
        # Проверка структуры заголовков
        self._check_heading_hierarchy(lines, relative_path)
        
        print(f"  ✓ {relative_path}")
    
    def _check_heading_hierarchy(
        self, lines: List[str], file_path: str
    ) -> None:
        """Проверить правильность иерархии заголовков.
        
        Args:
            lines: Строки файла
            file_path: Путь файла для отчёта
        """
        heading_levels = []
        
        for i, line in enumerate(lines, 1):
            match = re.match(r'^(#+)', line)
            if not match:
                continue
            
            level = len(match.group(1))
            heading_levels.append((level, i))
        
        if not heading_levels:
            return
        
        # Проверка что первый заголовок - H1
        if heading_levels[0][0] != 1:
            self.warnings.append(
                f"⚠️  Файл {file_path}: первый заголовок не H1 (уровень {heading_levels[0][0]})"
            )
        
        # Проверка что скачки между уровнями не более одного
        for j in range(1, len(heading_levels)):
            prev_level, prev_line = heading_levels[j - 1]
            curr_level, curr_line = heading_levels[j]
            
            if curr_level > prev_level + 1:
                self.warnings.append(
                    f"⚠️  Файл {file_path}, строка {curr_line}: "
                    f"недопустимый скачок заголовка с H{prev_level} на H{curr_level}"
                )
    
    def _print_report(self) -> None:
        """Вывести отчёт о валидации."""
        print("-" * 60)
        print("📊 ОТЧЁТ ВАЛИДАЦИИ")
        print("-" * 60)
        
        if self.errors:
            print(f"\n❌ ОШИБКИ ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")
        else:
            print("\n✅ Ошибок не найдено!")
        
        if self.warnings:
            print(f"\n⚠️  ПРЕДУПРЕЖДЕНИЯ ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
        
        print("-" * 60)
        print(f"Всего: ошибок: {len(self.errors)}, предупреждений: {len(self.warnings)}")
        print("-" * 60)


def main() -> int:
    """Главная функция.
    
    Returns:
        0 если ошибок нет, 1 если найдены ошибки
    """
    # Определить корневую директорию проекта
    script_dir = Path(__file__).parent.parent.parent
    os.chdir(script_dir)
    
    validator = DocsValidator('docs/ru')
    
    has_no_errors = validator.validate_all()
    
    return 0 if has_no_errors else 1


if __name__ == '__main__':
    sys.exit(main())
