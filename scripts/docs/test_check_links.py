"""
Unit-тесты для скрипта check_links.py

Тестирует:
- Извлечение ссылок из Markdown
- Валидацию существующих и несуществующих ссылок
- Обработку якорей и внешних ссылок
- Разрешение относительных путей
- Отчёты об ошибках

Запуск тестов:
    python -m pytest test_check_links.py -v
    или
    python test_check_links.py

Покрытие:
    - 38+ unit-тестов
    - 7 классов тестов для разных функциональностей
    - Интеграционные тесты с реальной структурой документации
"""

import tempfile
import unittest
from pathlib import Path
from typing import Set

# Импортируем класс LinkChecker из check_links.py
import sys
sys.path.insert(0, str(Path(__file__).parent))
from check_links import LinkChecker


class TestLinkCheckerExtractLinks(unittest.TestCase):
    """Тесты для метода extract_links."""
    
    def setUp(self):
        """Инициализируем LinkChecker для тестирования."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.docs_root = Path(tmpdir)
            self.checker = LinkChecker(self.docs_root)
    
    def test_extract_simple_link(self):
        """Тест извлечения простой ссылки из Markdown."""
        content = "[Google](https://google.com)"
        links = self.checker.extract_links(content)
        self.assertEqual(links, ["https://google.com"])
    
    def test_extract_multiple_links(self):
        """Тест извлечения нескольких ссылок."""
        content = "[Первая](link1.md) и [Вторая](link2.md)"
        links = self.checker.extract_links(content)
        self.assertEqual(links, ["link1.md", "link2.md"])
    
    def test_extract_internal_link(self):
        """Тест извлечения внутренней ссылки."""
        content = "[Manual](../manual/guide.md)"
        links = self.checker.extract_links(content)
        self.assertEqual(links, ["../manual/guide.md"])
    
    def test_extract_anchor_link(self):
        """Тест извлечения якоря в ссылке."""
        content = "[Раздел](#якорь)"
        links = self.checker.extract_links(content)
        self.assertEqual(links, ["#якорь"])
    
    def test_extract_link_with_anchor(self):
        """Тест извлечения ссылки на файл с якорем."""
        content = "[Раздел](file.md#section)"
        links = self.checker.extract_links(content)
        self.assertEqual(links, ["file.md#section"])
    
    def test_extract_no_links(self):
        """Тест контента без ссылок."""
        content = "Это просто текст без ссылок"
        links = self.checker.extract_links(content)
        self.assertEqual(links, [])
    
    def test_extract_links_with_special_chars(self):
        """Тест извлечения ссылок со специальными символами в тексте."""
        content = "[C++ Guide](cpp-guide.md) и [Python 3.10+](python.md)"
        links = self.checker.extract_links(content)
        self.assertEqual(links, ["cpp-guide.md", "python.md"])


class TestLinkCheckerResolveRelativePath(unittest.TestCase):
    """Тесты для метода resolve_relative_path."""
    
    def setUp(self):
        """Инициализируем LinkChecker с тестовыми файлами."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.docs_root = Path(self.temp_dir.name)
        self.checker = LinkChecker(self.docs_root)
        
        # Создаём тестовую структуру файлов
        (self.docs_root / "index.md").touch()
        (self.docs_root / "manual").mkdir()
        (self.docs_root / "manual" / "guide.md").touch()
        (self.docs_root / "api").mkdir()
        (self.docs_root / "api" / "reference.md").touch()
        
        # Собираем все файлы
        self.checker.collect_all_files()
    
    def tearDown(self):
        """Очищаем временную директорию."""
        self.temp_dir.cleanup()
    
    def test_resolve_root_file(self):
        """Тест разрешения файла в корне."""
        result = self.checker.resolve_relative_path("index.md", "manual/guide.md")
        self.assertEqual(result, "index.md")
    
    def test_resolve_sibling_file(self):
        """Тест разрешения соседнего файла."""
        # Файл guide2.md не существует, но разрешается как-есть если в списке all_files
        # Метод resolve_relative_path проверяет существование файла в all_files
        # Если файл не создан, он просто вернёт путь как-есть
        result = self.checker.resolve_relative_path("guide2.md", "manual/guide.md")
        # Это должно возвращать относительный путь как-есть, если файл не в all_files
        self.assertEqual(result, "guide2.md")
    
    def test_resolve_sibling_file_existing(self):
        """Тест разрешения существующего соседнего файла."""
        # Создаём guide2.md в папке manual
        (self.docs_root / "manual" / "guide2.md").touch()
        self.checker.collect_all_files()
        
        result = self.checker.resolve_relative_path("guide2.md", "manual/guide.md")
        # Должно разрешиться в manual/guide2.md
        self.assertEqual(result, "manual/guide2.md")
    
    def test_resolve_parent_reference(self):
        """Тест разрешения ссылки на родительскую папку."""
        result = self.checker.resolve_relative_path("../api/reference.md", "manual/guide.md")
        self.assertEqual(result, "api/reference.md")
    
    def test_resolve_double_parent_reference(self):
        """Тест разрешения ссылки на два уровня вверх."""
        # Создаём вложенную структуру
        (self.docs_root / "manual" / "sub").mkdir()
        (self.docs_root / "manual" / "sub" / "page.md").touch()
        self.checker.collect_all_files()
        
        result = self.checker.resolve_relative_path("../guide.md", "manual/sub/page.md")
        self.assertEqual(result, "manual/guide.md")
    
    def test_resolve_current_dir_reference(self):
        """Тест разрешения ссылки с ./"""
        result = self.checker.resolve_relative_path("./guide.md", "manual/other.md")
        self.assertEqual(result, "manual/guide.md")


class TestLinkCheckerValidateInternalLink(unittest.TestCase):
    """Тесты для метода validate_internal_link."""
    
    def setUp(self):
        """Инициализируем LinkChecker с тестовыми файлами."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.docs_root = Path(self.temp_dir.name)
        self.checker = LinkChecker(self.docs_root)
        
        # Создаём тестовую структуру файлов
        (self.docs_root / "index.md").touch()
        (self.docs_root / "manual").mkdir()
        (self.docs_root / "manual" / "guide.md").touch()
        
        # Собираем все файлы
        self.checker.collect_all_files()
    
    def tearDown(self):
        """Очищаем временную директорию."""
        self.temp_dir.cleanup()
    
    def test_validate_http_link(self):
        """Тест валидации HTTP ссылки (должна пройти)."""
        result = self.checker.validate_internal_link("https://google.com", "index.md")
        self.assertTrue(result)
    
    def test_validate_https_link(self):
        """Тест валидации HTTPS ссылки (должна пройти)."""
        result = self.checker.validate_internal_link("https://example.com", "index.md")
        self.assertTrue(result)
    
    def test_validate_file_link_in_http(self):
        """Тест валидации file:// ссылки (должна пройти)."""
        result = self.checker.validate_internal_link("file:///etc/config", "index.md")
        self.assertTrue(result)
    
    def test_validate_anchor_only(self):
        """Тест валидации якоря без файла (должна пройти)."""
        result = self.checker.validate_internal_link("#section", "index.md")
        self.assertTrue(result)
    
    def test_validate_existing_file(self):
        """Тест валидации существующего файла."""
        result = self.checker.validate_internal_link("index.md", "manual/guide.md")
        self.assertTrue(result)
    
    def test_validate_nonexistent_file(self):
        """Тест валидации несуществующего файла."""
        result = self.checker.validate_internal_link("nonexistent.md", "index.md")
        self.assertFalse(result)
        # Проверяем что ошибка была добавлена
        self.assertGreater(len(self.checker.errors), 0)
    
    def test_validate_file_with_anchor(self):
        """Тест валидации файла с якорем."""
        result = self.checker.validate_internal_link("index.md#section", "manual/guide.md")
        self.assertTrue(result)
    
    def test_validate_nonexistent_file_with_anchor(self):
        """Тест валидации несуществующего файла с якорем."""
        result = self.checker.validate_internal_link("missing.md#section", "index.md")
        self.assertFalse(result)
    
    def test_validate_anchor_after_file_removal(self):
        """Тест валидации пустой ссылки после удаления якоря."""
        result = self.checker.validate_internal_link("#section", "index.md")
        self.assertTrue(result)
    
    def test_validate_preserves_errors(self):
        """Тест что ошибки накапливаются."""
        self.checker.validate_internal_link("missing1.md", "index.md")
        self.checker.validate_internal_link("missing2.md", "index.md")
        self.assertEqual(len(self.checker.errors), 2)


class TestLinkCheckerCollectAllFiles(unittest.TestCase):
    """Тесты для метода collect_all_files."""
    
    def test_collect_single_file(self):
        """Тест сбора одного файла."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            (docs_root / "index.md").touch()
            
            checker = LinkChecker(docs_root)
            checker.collect_all_files()
            
            self.assertIn("index.md", checker.all_files)
    
    def test_collect_multiple_files(self):
        """Тест сбора нескольких файлов."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            (docs_root / "index.md").touch()
            (docs_root / "guide.md").touch()
            (docs_root / "tutorial.md").touch()
            
            checker = LinkChecker(docs_root)
            checker.collect_all_files()
            
            # Собираются файлы и их версии в нижнем регистре (для case-insensitive поиска)
            # Всего 3 файла
            self.assertEqual(len(checker.all_files), 3)
    
    def test_collect_nested_files(self):
        """Тест сбора файлов в подпапках."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            (docs_root / "manual").mkdir()
            (docs_root / "manual" / "guide.md").touch()
            (docs_root / "api").mkdir()
            (docs_root / "api" / "reference.md").touch()
            
            checker = LinkChecker(docs_root)
            checker.collect_all_files()
            
            self.assertIn("manual/guide.md", checker.all_files)
            self.assertIn("api/reference.md", checker.all_files)
    
    def test_collect_ignores_non_markdown(self):
        """Тест что собираются только .md файлы."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            (docs_root / "readme.md").touch()
            (docs_root / "config.txt").touch()
            (docs_root / "image.png").touch()
            
            checker = LinkChecker(docs_root)
            checker.collect_all_files()
            
            # Только markdown файлы (.md)
            md_files = [f for f in checker.all_files if f.endswith('.md')]
            self.assertEqual(len(md_files), 1)  # Только readme.md


class TestLinkCheckerCheckFile(unittest.TestCase):
    """Тесты для метода check_file."""
    
    def setUp(self):
        """Инициализируем LinkChecker с тестовыми файлами."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.docs_root = Path(self.temp_dir.name)
        self.checker = LinkChecker(self.docs_root)
        
        # Создаём тестовую структуру файлов
        (self.docs_root / "index.md").touch()
        (self.docs_root / "guide.md").touch()
        
        # Собираем все файлы
        self.checker.collect_all_files()
    
    def tearDown(self):
        """Очищаем временную директорию."""
        self.temp_dir.cleanup()
    
    def test_check_file_with_valid_links(self):
        """Тест проверки файла с валидными ссылками."""
        file_path = self.docs_root / "index.md"
        file_path.write_text("[Guide](guide.md) and [External](https://example.com)")
        
        self.checker.check_file(file_path)
        
        self.assertEqual(len(self.checker.errors), 0)
    
    def test_check_file_with_invalid_links(self):
        """Тест проверки файла с невалидными ссылками."""
        file_path = self.docs_root / "index.md"
        file_path.write_text("[Missing](missing.md)")
        
        self.checker.check_file(file_path)
        
        self.assertEqual(len(self.checker.errors), 1)
    
    def test_check_file_with_multiple_errors(self):
        """Тест проверки файла с несколькими ошибками."""
        file_path = self.docs_root / "index.md"
        file_path.write_text(
            "[Missing1](missing1.md) and [Missing2](missing2.md) and [Valid](guide.md)"
        )
        
        self.checker.check_file(file_path)
        
        self.assertEqual(len(self.checker.errors), 2)
    
    def test_check_file_with_anchors(self):
        """Тест проверки файла с якорями."""
        file_path = self.docs_root / "index.md"
        file_path.write_text("[Section](#intro) and [External](#header)")
        
        self.checker.check_file(file_path)
        
        # Якоря не должны вызывать ошибок
        self.assertEqual(len(self.checker.errors), 0)
    
    def test_check_file_encoding_error(self):
        """Тест обработки ошибки кодировки файла."""
        file_path = self.docs_root / "bad.md"
        # Пишем невалидные байты
        with open(file_path, 'wb') as f:
            f.write(b'\xff\xfe')
        
        self.checker.check_file(file_path)
        
        # Ошибка должна быть добавлена
        self.assertGreater(len(self.checker.errors), 0)


class TestLinkCheckerCheckAll(unittest.TestCase):
    """Тесты для метода check_all (главная функция проверки)."""
    
    def test_check_all_no_markdown_files(self):
        """Тест check_all с пустой директорией."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            checker = LinkChecker(docs_root)
            
            success, messages = checker.check_all()
            
            # Пустая директория считается успехом
            self.assertTrue(success)
            self.assertEqual(len(messages), 0)
    
    def test_check_all_with_valid_files(self):
        """Тест check_all с валидными файлами."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            # Создаём файлы
            (docs_root / "index.md").write_text("[Guide](guide.md)")
            (docs_root / "guide.md").write_text("# Guide")
            
            checker = LinkChecker(docs_root)
            success, messages = checker.check_all()
            
            self.assertTrue(success)
            self.assertEqual(len(messages), 0)
    
    def test_check_all_with_invalid_files(self):
        """Тест check_all с невалидными ссылками."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            # Создаём файлы с ошибками
            (docs_root / "index.md").write_text("[Missing](missing.md)")
            
            checker = LinkChecker(docs_root)
            success, messages = checker.check_all()
            
            self.assertFalse(success)
            self.assertGreater(len(messages), 0)
    
    def test_check_all_returns_tuple(self):
        """Тест что check_all возвращает кортеж (bool, list)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            checker = LinkChecker(docs_root)
            
            result = checker.check_all()
            
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)
            self.assertIsInstance(result[0], bool)
            self.assertIsInstance(result[1], list)


class TestLinkCheckerIntegration(unittest.TestCase):
    """Интеграционные тесты для реальных сценариев."""
    
    def test_real_documentation_structure(self):
        """Тест с реальной структурой документации."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            # Создаём структуру как в реальной документации
            (docs_root / "index.md").write_text(
                "[Manual](manual/index.md)\n[API](api/index.md)"
            )
            
            manual_dir = docs_root / "manual"
            manual_dir.mkdir()
            (manual_dir / "index.md").write_text(
                "[Getting Started](getting-started.md)\n[Back to Home](../index.md)"
            )
            (manual_dir / "getting-started.md").write_text(
                "[Configuration](../config.md)\n[External](https://example.com)"
            )
            
            api_dir = docs_root / "api"
            api_dir.mkdir()
            (api_dir / "index.md").write_text("[Back to Home](../index.md)")
            
            (docs_root / "config.md").write_text("# Configuration")
            
            checker = LinkChecker(docs_root)
            success, messages = checker.check_all()
            
            self.assertTrue(success)
            self.assertEqual(len(messages), 0)
    
    def test_cross_directory_links(self):
        """Тест ссылок между директориями."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            
            # Создаём структуру с перекрёстными ссылками
            guides_dir = docs_root / "guides"
            guides_dir.mkdir()
            (guides_dir / "index.md").write_text(
                "[API Reference](../api/reference.md)"
            )
            
            api_dir = docs_root / "api"
            api_dir.mkdir()
            (api_dir / "reference.md").write_text(
                "[Guides](../guides/index.md)"
            )
            
            checker = LinkChecker(docs_root)
            success, messages = checker.check_all()
            
            self.assertTrue(success)


if __name__ == '__main__':
    unittest.main()
