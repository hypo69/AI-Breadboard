# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Scripts Docs - Test Generate Api
# =============================================================================
# Description:
#   Unit-тесты для скрипта generate_api.py
#
# Usage Examples:
#   CLI:
#     python -m scripts.docs.test_generate_api
#   Python API:
#     from scripts.docs.test_generate_api import TestDocstringParser
#
#     service = TestDocstringParser()
#
# File: test_generate_api.py
# Project: ai-breadboard
# Package: scripts.docs
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:27:07
# =============================================================================

"""Unit-тесты для скрипта generate_api.py

Тестирует:
- Парсинг Google-style docstrings
- Генерацию Markdown из документации
- Обработку функций и классов
- Создание индекса API"""

import unittest
import ast
import tempfile
from pathlib import Path
from generate_api import DocstringParser, MarkdownGenerator, APIDocumentationGenerator

class TestDocstringParser(unittest.TestCase):
    """Тесты для класса DocstringParser."""

    def test_parse_function_basic(self):
        """Тестирует парсинг простой функции."""
        code = '\ndef hello(name: str) -> str:\n    """Грeets a person.\n    \n    Args:\n        name: The person\'s name\n        \n    Returns:\n        A greeting message\n    """\n    return f"Hello, {name}!"\n'
        tree = ast.parse(code)
        func_node = tree.body[0]
        result = DocstringParser.parse_function(func_node)
        self.assertEqual(result['name'], 'hello')
        self.assertEqual(result['type'], 'function')
        self.assertIn('name', result['args'])
        self.assertFalse(result['is_async'])

    def test_parse_class_basic(self):
        """Тестирует парсинг простого класса."""
        code = '\nclass Person:\n    """Represents a person."""\n    \n    class_var = "class_variable"\n    \n    def __init__(self, name: str):\n        """Initialize person."""\n        self.name = name\n    \n    def greet(self):\n        """Greet someone."""\n        return f"Hello, {self.name}!"\n'
        tree = ast.parse(code)
        class_node = tree.body[0]
        result = DocstringParser.parse_class(class_node)
        self.assertEqual(result['name'], 'Person')
        self.assertEqual(result['type'], 'class')
        self.assertTrue(len(result['methods']) > 0)
        self.assertIn('class_var', result['attributes'])

    def test_parse_google_docstring(self):
        """Тестирует парсинг Google-style docstring."""
        docstring = '\n        Функция для обработки данных.\n        \n        Подробное описание функции.\n        \n        Args:\n            param1: Первый параметр\n            param2: Второй параметр\n            \n        Returns:\n            Результат обработки\n            \n        Raises:\n            ValueError: Если параметры невалидны\n        '
        result = DocstringParser.parse_google_docstring(docstring)
        self.assertTrue(result['summary'])
        self.assertIn('param1', result['args'])
        self.assertIn('param2', result['args'])
        self.assertTrue(result['returns'])
        self.assertTrue(len(result['raises']) > 0)

    def test_parse_empty_docstring(self):
        """Тестирует парсинг пустого docstring."""
        result = DocstringParser.parse_google_docstring('')
        self.assertEqual(result['summary'], 'Документация отсутствует')
        self.assertEqual(result['args'], {})
        self.assertEqual(result['returns'], '')
        self.assertEqual(result['raises'], [])

class TestMarkdownGenerator(unittest.TestCase):
    """Тесты для класса MarkdownGenerator."""

    def test_generate_header(self):
        """Тестирует генерацию заголовков."""
        header1 = MarkdownGenerator.generate_header('Test', 1)
        header2 = MarkdownGenerator.generate_header('Test', 2)
        self.assertTrue(header1.startswith('# '))
        self.assertTrue(header2.startswith('## '))
        self.assertTrue(header1.endswith('\n\n'))

    def test_generate_code_block(self):
        """Тестирует генерацию блока кода."""
        code = 'print("Hello")'
        result = MarkdownGenerator.generate_code_block(code)
        self.assertTrue(result.startswith('```python\n'))
        self.assertTrue(result.endswith('\n```\n\n'))
        self.assertIn('print', result)

    def test_generate_function_docs(self):
        """Тестирует генерацию документации функции."""
        func = {'name': 'test_func', 'type': 'function', 'is_async': False, 'args': ['param1', 'param2'], 'defaults': {'param2': 'default_value'}, 'doc_info': {'summary': 'Test function', 'description': 'A test function', 'args': {'param1': 'First parameter', 'param2': 'Second parameter'}, 'returns': 'A string', 'raises': [], 'examples': []}}
        result = MarkdownGenerator.generate_function_docs(func)
        self.assertIn('test_func', result)
        self.assertIn('param1', result)
        self.assertIn('param2', result)
        self.assertIn('Test function', result)

    def test_generate_class_docs(self):
        """Тестирует генерацию документации класса."""
        cls = {'name': 'TestClass', 'type': 'class', 'bases': [], 'attributes': ['attr1', 'attr2'], 'methods': [], 'doc_info': {'summary': 'Test class', 'description': 'A test class', 'args': {}, 'returns': '', 'raises': [], 'examples': []}}
        result = MarkdownGenerator.generate_class_docs(cls)
        self.assertIn('TestClass', result)
        self.assertIn('attr1', result)
        self.assertIn('attr2', result)
        self.assertIn('Test class', result)

class TestAPIDocumentationGenerator(unittest.TestCase):
    """Тесты для класса APIDocumentationGenerator."""

    def setUp(self):
        """Подготовка к тестам."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.src_root = self.temp_path / 'src'
        self.docs_root = self.temp_path / 'docs'
        self.src_root.mkdir()
        self.docs_root.mkdir()
        (self.docs_root / 'ru').mkdir()

    def tearDown(self):
        """Очистка после тестов."""
        self.temp_dir.cleanup()

    def test_generator_initialization(self):
        """Тестирует инициализацию генератора."""
        gen = APIDocumentationGenerator(self.src_root, self.docs_root)
        self.assertEqual(gen.src_root, self.src_root)
        self.assertEqual(gen.docs_root, self.docs_root)
        self.assertTrue((self.docs_root / 'ru' / 'api').exists())

    def test_process_python_file(self):
        """Тестирует обработку Python файла."""
        test_file = self.src_root / 'test_module.py'
        test_file.write_text('\ndef test_function():\n    """Test function."""\n    pass\n\nclass TestClass:\n    """Test class."""\n    pass\n')
        gen = APIDocumentationGenerator(self.src_root, self.docs_root)
        result = gen.process_python_file(test_file)
        self.assertEqual(len(result['functions']), 1)
        self.assertEqual(len(result['classes']), 1)
        self.assertEqual(result['functions'][0]['name'], 'test_function')
        self.assertEqual(result['classes'][0]['name'], 'TestClass')

    def test_generate_api_index(self):
        """Тестирует генерацию индекса API."""
        gen = APIDocumentationGenerator(self.src_root, self.docs_root)
        modules = ['test.module1', 'test.module2']
        gen.generated_modules = modules
        gen.generate_api_index(modules)
        index_file = self.docs_root / 'ru' / 'api' / 'index.md'
        self.assertTrue(index_file.exists())
        content = index_file.read_text()
        self.assertIn('API-документация', content)
        self.assertIn('test.module1', content)
        self.assertIn('test.module2', content)

class TestIntegration(unittest.TestCase):
    """Интеграционные тесты."""

    def setUp(self):
        """Подготовка к тестам."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.src_root = self.temp_path / 'src'
        self.docs_root = self.temp_path / 'docs'
        self.src_root.mkdir()
        self.docs_root.mkdir()
        (self.docs_root / 'ru').mkdir()
        module_dir = self.src_root / 'test_module'
        module_dir.mkdir()
        init_file = module_dir / '__init__.py'
        init_file.write_text('\n"""\nTest module with full documentation.\n\nThis is a test module for API documentation generation.\n"""\n\ndef calculate(a: int, b: int) -> int:\n    """\n    Calculate sum of two numbers.\n    \n    Args:\n        a: First number\n        b: Second number\n        \n    Returns:\n        Sum of a and b\n    """\n    return a + b\n\nclass Calculator:\n    """Calculator class for math operations."""\n    \n    def add(self, a: int, b: int) -> int:\n        """Add two numbers."""\n        return a + b\n')

    def tearDown(self):
        """Очистка после тестов."""
        self.temp_dir.cleanup()

    def test_full_generation_flow(self):
        """Тестирует полный flow генерации."""
        gen = APIDocumentationGenerator(self.src_root, self.docs_root)
        modules = ['src.test_module']
        gen.generate(modules)
        api_dir = self.docs_root / 'ru' / 'api'
        self.assertTrue((api_dir / 'test_module.md').exists())
        self.assertTrue((api_dir / 'index.md').exists())
        content = (api_dir / 'test_module.md').read_text()
        self.assertIn('test_module', content)
        self.assertIn('calculate', content)
        self.assertIn('Calculator', content)

def run_tests():
    """Запускает все тесты."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestDocstringParser))
    suite.addTests(loader.loadTestsFromTestCase(TestMarkdownGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIDocumentationGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print('\n' + '=' * 60)
    print('📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ')
    print('=' * 60)
    print(f'Всего тестов: {result.testsRun}')
    print(f'Успешных: {result.testsRun - len(result.failures) - len(result.errors)}')
    print(f'Ошибок: {len(result.failures)}')
    print(f'Исключений: {len(result.errors)}')
    print('=' * 60)
    return result.wasSuccessful()
if __name__ == '__main__':
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)