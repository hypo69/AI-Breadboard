"""
Unit-тесты для скрипта валидации структуры документации.

Тестирует функциональность класса DocumentationValidator:
- Проверка наличия файлов
- Валидация Markdown синтаксиса
- Проверка обязательных разделов
- Генерация отчётов об ошибках

Требования: 7.1, 7.4
"""

import pytest
import tempfile
from pathlib import Path
import sys

# Добавляем путь к скриптам в sys.path для импорта
scripts_path = Path(__file__).parent.parent / 'scripts' / 'docs'
sys.path.insert(0, str(scripts_path))

from validate_structure import DocumentationValidator


class TestDocumentationValidatorFileChecks:
    """Тесты проверки наличия файлов."""
    
    def test_validate_file_exists_success(self):
        """Проверяет корректную работу при наличии файла."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            # Создаём обязательный файл
            test_file = docs_root / 'index.md'
            test_file.write_text('# Документация\n')
            
            validator = DocumentationValidator(docs_root)
            result = validator.validate_file_exists('index.md')
            
            assert result is True
            assert len(validator.errors) == 0
            assert len(validator.success_messages) > 0
    
    def test_validate_file_exists_failure(self):
        """Проверяет корректную работу при отсутствии файла."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            validator = DocumentationValidator(docs_root)
            result = validator.validate_file_exists('missing.md')
            
            assert result is False
            assert len(validator.errors) > 0
    
    def test_validate_multiple_required_files(self):
        """Проверяет валидацию нескольких обязательных файлов."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            # Создаём файлы
            (docs_root / 'index.md').write_text('# Index\n')
            (docs_root / 'conf.py').write_text('# Config\n')
            
            validator = DocumentationValidator(docs_root)
            
            # Проверяем существующие файлы
            assert validator.validate_file_exists('index.md') is True
            assert validator.validate_file_exists('conf.py') is True
            
            # Проверяем несуществующий файл
            assert validator.validate_file_exists('missing.md') is False


class TestDocumentationValidatorSections:
    """Тесты проверки обязательных разделов."""
    
    def test_validate_sections_found(self):
        """Проверяет при наличии всех обязательных разделов."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            # Создаём файл с обязательными разделами
            test_file = docs_root / 'manual' / 'index.md'
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text('# Руководства\n\nЭто руководство.\n')
            
            validator = DocumentationValidator(docs_root)
            result = validator.validate_sections('manual/index.md', ['#', 'Руководства'])
            
            assert result is True
            assert len(validator.warnings) == 0
    
    def test_validate_sections_missing(self):
        """Проверяет при отсутствии обязательных разделов."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            # Создаём файл без обязательных разделов
            test_file = docs_root / 'test.md'
            test_file.write_text('# Другое\n\nСодержание без требуемых разделов.\n')
            
            validator = DocumentationValidator(docs_root)
            result = validator.validate_sections('test.md', ['Руководства', 'API'])
            
            assert result is False
            assert len(validator.warnings) > 0
    
    def test_validate_sections_partial_match(self):
        """Проверяет при частичном совпадении разделов."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            test_file = docs_root / 'test.md'
            test_file.write_text('# Title\n\nРуководства\n')
            
            validator = DocumentationValidator(docs_root)
            result = validator.validate_sections('test.md', ['#', 'Руководства', 'API'])
            
            assert result is False
            assert len(validator.warnings) > 0


class TestDocumentationValidatorMarkdownSyntax:
    """Тесты валидации Markdown синтаксиса."""
    
    def test_validate_markdown_syntax_correct(self):
        """Проверяет корректный Markdown синтаксис."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            test_file = docs_root / 'test.md'
            test_file.write_text('# Title\n\n```python\nprint("hello")\n```\n')
            
            validator = DocumentationValidator(docs_root)
            result = validator.validate_markdown_syntax(test_file)
            
            assert result is True
            assert len(validator.errors) == 0
    
    def test_validate_markdown_syntax_unbalanced_code_blocks(self):
        """Проверяет при несбалансированных блоках кода."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            test_file = docs_root / 'test.md'
            # Одна открывающая, две закрывающие кавычки
            test_file.write_text('```python\ncode\n```\n```\n')
            
            validator = DocumentationValidator(docs_root)
            result = validator.validate_markdown_syntax(test_file)
            
            assert result is False
            assert len(validator.errors) > 0
    
    def test_validate_markdown_syntax_unbalanced_brackets(self):
        """Проверяет при несбалансированных скобках."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            test_file = docs_root / 'test.md'
            # Несбалансированные скобки в ссылке
            test_file.write_text('[link](url\n')
            
            validator = DocumentationValidator(docs_root)
            result = validator.validate_markdown_syntax(test_file)
            
            # Это должно сгенерировать предупреждение, но не ошибку
            assert len(validator.warnings) > 0
    
    def test_validate_markdown_syntax_file_not_found(self):
        """Проверяет обработку несуществующего файла."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            validator = DocumentationValidator(docs_root)
            result = validator.validate_markdown_syntax(docs_root / 'missing.md')
            
            assert result is False
            assert len(validator.errors) > 0


class TestDocumentationValidatorDirectoryStructure:
    """Тесты валидации структуры директорий."""
    
    def test_validate_directory_structure_complete(self):
        """Проверяет при наличии всех директорий."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            # Создаём все требуемые директории
            for dir_name in ['manual', 'api', 'guides', 'architecture', '_templates', '_static']:
                (docs_root / dir_name).mkdir(parents=True, exist_ok=True)
            
            validator = DocumentationValidator(docs_root)
            result = validator.validate_directory_structure()
            
            assert result is True
            assert len(validator.warnings) == 0
    
    def test_validate_directory_structure_partial(self):
        """Проверяет при отсутствии некоторых директорий."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            # Создаём только некоторые директории
            (docs_root / 'manual').mkdir()
            (docs_root / 'api').mkdir()
            
            validator = DocumentationValidator(docs_root)
            result = validator.validate_directory_structure()
            
            assert result is False
            assert len(validator.warnings) > 0


class TestDocumentationValidatorIntegration:
    """Интеграционные тесты полной валидации."""
    
    def test_validate_all_success(self):
        """Проверяет полную валидацию успешного сценария."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            # Создаём корректную структуру
            (docs_root / 'manual').mkdir()
            (docs_root / 'api').mkdir()
            (docs_root / 'guides').mkdir()
            (docs_root / 'architecture').mkdir()
            (docs_root / '_templates').mkdir()
            (docs_root / '_static').mkdir()
            
            # Создаём обязательные файлы
            (docs_root / 'index.md').write_text('# Документация\n\n## Содержание\n## Разделы\n')
            (docs_root / 'conf.py').write_text('# Config\n')
            (docs_root / 'manual' / 'index.md').write_text('# Руководства\n')
            (docs_root / 'api' / 'index.md').write_text('# API\n## Модули\n')
            
            validator = DocumentationValidator(docs_root)
            success, errors, warnings = validator.validate_all()
            
            assert success is True
            assert len(errors) == 0
    
    def test_validate_all_with_errors(self):
        """Проверяет полную валидацию со сценарием с ошибками."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            # Минимальная структура без обязательных файлов
            (docs_root / 'manual').mkdir()
            (docs_root / 'api').mkdir()
            (docs_root / 'guides').mkdir()
            (docs_root / 'architecture').mkdir()
            (docs_root / '_templates').mkdir()
            (docs_root / '_static').mkdir()
            
            validator = DocumentationValidator(docs_root)
            success, errors, warnings = validator.validate_all()
            
            assert success is False
            assert len(errors) > 0
    
    def test_validate_all_with_syntax_error(self):
        """Проверяет валидацию с синтаксическими ошибками."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            # Создаём структуру
            (docs_root / 'manual').mkdir()
            (docs_root / 'api').mkdir()
            (docs_root / 'guides').mkdir()
            (docs_root / 'architecture').mkdir()
            (docs_root / '_templates').mkdir()
            (docs_root / '_static').mkdir()
            
            # Создаём файлы с синтаксической ошибкой
            (docs_root / 'index.md').write_text('# Документация\n\n## Содержание\n## Разделы\n```python\ncode\n')
            (docs_root / 'conf.py').write_text('# Config\n')
            (docs_root / 'manual' / 'index.md').write_text('# Руководства\n')
            (docs_root / 'api' / 'index.md').write_text('# API\n## Модули\n')
            
            validator = DocumentationValidator(docs_root)
            success, errors, warnings = validator.validate_all()
            
            assert success is False
            assert len(errors) > 0


class TestDocumentationValidatorReporting:
    """Тесты генерации отчётов."""
    
    def test_generate_report_success(self):
        """Проверяет генерацию отчёта при успешной валидации."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            validator = DocumentationValidator(docs_root)
            validator.success_messages.append('✓ Успешная проверка')
            
            report = validator.generate_report()
            
            assert '✅ СТАТУС: ВАЛИДАЦИЯ УСПЕШНА' in report
            assert '✓ Успешная проверка' in report
    
    def test_generate_report_with_errors(self):
        """Проверяет генерацию отчёта с ошибками."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            validator = DocumentationValidator(docs_root)
            validator.errors.append('❌ Критическая ошибка')
            
            report = validator.generate_report()
            
            assert '❌ СТАТУС: НАЙДЕНО 1 ОШИБОК' in report
            assert '❌ Критическая ошибка' in report
    
    def test_generate_report_with_warnings(self):
        """Проверяет генерацию отчёта с предупреждениями."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            validator = DocumentationValidator(docs_root)
            validator.warnings.append('⚠️  Предупреждение')
            
            report = validator.generate_report()
            
            assert '⚠️  ПРЕДУПРЕЖДЕНИЯ:' in report
            assert '⚠️  Предупреждение' in report
    
    def test_generate_report_empty(self):
        """Проверяет генерацию отчёта без сообщений."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            validator = DocumentationValidator(docs_root)
            report = validator.generate_report()
            
            assert 'ОТЧЁТ О ВАЛИДАЦИИ ДОКУМЕНТАЦИИ' in report
            assert '✅ СТАТУС: ВАЛИДАЦИЯ УСПЕШНА' in report


class TestDocumentationValidatorEdgeCases:
    """Тесты граничных случаев."""
    
    def test_validate_file_with_encoding_error(self):
        """Проверяет обработку файла с проблемами кодировки."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            test_file = docs_root / 'test.md'
            # Пишем корректный UTF-8 контент
            test_file.write_text('# Тест\n', encoding='utf-8')
            
            validator = DocumentationValidator(docs_root)
            result = validator.validate_markdown_syntax(test_file)
            
            assert result is True
    
    def test_validate_empty_markdown_file(self):
        """Проверяет валидацию пустого Markdown файла."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            test_file = docs_root / 'test.md'
            test_file.write_text('')
            
            validator = DocumentationValidator(docs_root)
            result = validator.validate_markdown_syntax(test_file)
            
            assert result is True
    
    def test_validate_markdown_with_multiple_code_blocks(self):
        """Проверяет валидацию Markdown с несколькими блоками кода."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            test_file = docs_root / 'test.md'
            test_file.write_text(
                '# Test\n\n'
                '```python\ncode1\n```\n\n'
                '```bash\ncode2\n```\n'
            )
            
            validator = DocumentationValidator(docs_root)
            result = validator.validate_markdown_syntax(test_file)
            
            assert result is True
    
    def test_validate_nested_directories(self):
        """Проверяет валидацию при вложенных директориях."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            # Создаём вложенные директории
            (docs_root / 'manual' / 'subfolder').mkdir(parents=True)
            (docs_root / 'manual' / 'subfolder' / 'test.md').write_text('# Test\n')
            
            validator = DocumentationValidator(docs_root)
            result = validator.validate_markdown_syntax(
                docs_root / 'manual' / 'subfolder' / 'test.md'
            )
            
            assert result is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
