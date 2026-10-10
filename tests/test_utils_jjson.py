# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Tests - Test Utils Jjson
# =============================================================================
# Description:
#   Комплексный набор тестов для модуля сериализации и десериализации `jjson.py`.
#
# Usage Examples:
#   CLI:
#     pytest tests/test_utils_jjson.py
#
# File: test_utils_jjson.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 11:35:00
# =============================================================================

"""Модуль тестирования функций j_dumps, j_loads и j_loads_ns."""

import json
from collections import OrderedDict
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List
import pytest

from src.utils.jjson import j_dumps, j_loads, j_loads_ns


class TestJDumps:
    """Тестирование функции `j_dumps`."""

    def test_dumps_dict_in_memory(self):
        """Проверка сериализации словаря в памяти (без указания пути)."""
        data = {'a': 1, 'b': 'тест'}
        result = j_dumps(data)
        assert result == data

    def test_dumps_list_in_memory(self):
        """Проверка сериализации списка в памяти."""
        data = [{'a': 1}, {'b': 2}]
        result = j_dumps(data)
        assert result == data

    def test_dumps_nested_simplenamespace(self, tmp_path: Path):
        """Проверка сериализации вложенных объектов SimpleNamespace."""
        ns = SimpleNamespace(name='antigravity', config=SimpleNamespace(port=8000, debug=True), tags=['ai', 'tools'])
        out_file = tmp_path / 'nested_ns.json'
        result = j_dumps(ns, out_file)
        assert result == {'name': 'antigravity', 'config': {'port': 8000, 'debug': True}, 'tags': ['ai', 'tools']}
        assert out_file.exists()
        loaded = json.loads(out_file.read_text(encoding='utf-8'))
        assert loaded == {'name': 'antigravity', 'config': {'port': 8000, 'debug': True}, 'tags': ['ai', 'tools']}

    def test_dumps_unicode_and_emoji(self, tmp_path: Path):
        """Проверка сохранения кириллицы, иврита и эмодзи при ensure_ascii=False и True."""
        data = {'text_ru': 'Привет мир', 'text_he': 'שלום עולם', 'emoji': '🚀✨'}
        # ensure_ascii=False
        file_utf8 = tmp_path / 'utf8.json'
        j_dumps(data, file_utf8, ensure_ascii=False)
        raw_utf8 = file_utf8.read_text(encoding='utf-8')
        assert 'Привет мир' in raw_utf8
        assert 'שלום עולם' in raw_utf8
        assert '🚀✨' in raw_utf8

        # ensure_ascii=True
        file_ascii = tmp_path / 'ascii.json'
        j_dumps(data, file_ascii, ensure_ascii=True)
        raw_ascii = file_ascii.read_text(encoding='utf-8')
        assert '\\u' in raw_ascii
        loaded_ascii = json.loads(raw_ascii)
        assert loaded_ascii == data

    def test_dumps_creates_parent_directory(self, tmp_path: Path):
        """Проверка создания несуществующего родительского каталога."""
        deep_file = tmp_path / 'sub1' / 'sub2' / 'data.json'
        data = {'status': 'ok'}
        result = j_dumps(data, deep_file)
        assert result == data
        assert deep_file.exists()

    def test_dumps_mode_w_overwrite(self, tmp_path: Path):
        """Проверка перезаписи существующего файла в режиме 'w'."""
        target = tmp_path / 'target.json'
        j_dumps({'version': 1, 'old': 'data'}, target)
        j_dumps({'version': 2, 'new': 'data'}, target, mode='w')
        loaded = json.loads(target.read_text(encoding='utf-8'))
        assert loaded == {'version': 2, 'new': 'data'}

    def test_dumps_mode_a_plus_dict_and_list(self, tmp_path: Path):
        """Проверка режима 'a+' (новые элементы списка в начале; существующие ключи словаря имеют приоритет)."""
        # Тест со списком: новые элементы перед старыми
        list_file = tmp_path / 'list_a_plus.json'
        j_dumps(['item3', 'item4'], list_file)
        j_dumps(['item1', 'item2'], list_file, mode='a+')
        loaded_list = json.loads(list_file.read_text(encoding='utf-8'))
        assert loaded_list == ['item1', 'item2', 'item3', 'item4']

        # Тест со словарем: существующих ключей приоритет
        dict_file = tmp_path / 'dict_a_plus.json'
        j_dumps({'key1': 'existing_v1', 'key2': 'v2'}, dict_file)
        j_dumps({'key1': 'new_v1', 'key3': 'v3'}, dict_file, mode='a+')
        loaded_dict = json.loads(dict_file.read_text(encoding='utf-8'))
        assert loaded_dict == {'key1': 'existing_v1', 'key2': 'v2', 'key3': 'v3'}

    def test_dumps_mode_plus_a_dict_and_list(self, tmp_path: Path):
        """Проверка режима '+a' (новые элементы списка в конце; новые ключи словаря перезаписывают существующие)."""
        # Тест со списком: новые элементы после старых
        list_file = tmp_path / 'list_plus_a.json'
        j_dumps(['item1', 'item2'], list_file)
        j_dumps(['item3', 'item4'], list_file, mode='+a')
        loaded_list = json.loads(list_file.read_text(encoding='utf-8'))
        assert loaded_list == ['item1', 'item2', 'item3', 'item4']

        # Тест со словарем: новые ключи имеют приоритет
        dict_file = tmp_path / 'dict_plus_a.json'
        j_dumps({'key1': 'existing_v1', 'key2': 'v2'}, dict_file)
        j_dumps({'key1': 'new_v1', 'key3': 'v3'}, dict_file, mode='+a')
        loaded_dict = json.loads(dict_file.read_text(encoding='utf-8'))
        assert loaded_dict == {'key1': 'new_v1', 'key2': 'v2', 'key3': 'v3'}

    def test_dumps_incompatible_types_merge(self, tmp_path: Path):
        """Проверка ошибки слияния при несовместимых типах (dict vs list): файл не должен повреждаться."""
        target = tmp_path / 'mismatch.json'
        original_data = {'a': 1}
        j_dumps(original_data, target)
        res = j_dumps(['item1'], target, mode='a+', exc_info=False)
        assert res is None
        # Проверяем, что исходный файл не перезаписан и не поврежден
        assert json.loads(target.read_text(encoding='utf-8')) == original_data

    def test_dumps_corrupted_existing_json(self, tmp_path: Path):
        """Проверка поведения при поврежденном существующем JSON файле в режиме 'a+'."""
        target = tmp_path / 'corrupt.json'
        target.write_text('{ corrupted json ', encoding='utf-8')
        res = j_dumps({'key': 'value'}, target, mode='a+', exc_info=False)
        assert res is None
        # Файл не должен быть перезаписан
        assert target.read_text(encoding='utf-8') == '{ corrupted json '

    def test_dumps_json_string_input(self, tmp_path: Path):
        """Проверка строкового входа: парсинг и восстановление поврежденной JSON-строки."""
        valid_str = '{"status": "ok", "code": 200}'
        res_valid = j_dumps(valid_str)
        assert res_valid == {'status': 'ok', 'code': 200}

        broken_str = '{"status": "ok", "unclosed": "val",}'
        res_broken = j_dumps(broken_str)
        assert isinstance(res_broken, dict)
        assert res_broken.get('status') == 'ok'

        non_json = 'This is plain text, not JSON'
        res_non_json = j_dumps(non_json, exc_info=False)
        assert res_non_json is None


class TestJLoads:
    """Тестирование функции `j_loads`."""

    def test_loads_dict_and_list_and_namespace(self):
        """Проверка загрузки прямых объектов dict, list, SimpleNamespace."""
        d = {'a': 1}
        assert j_loads(d, ordered=False) == {'a': 1}
        lst = [{'x': 10}]
        assert j_loads(lst, ordered=False) == [{'x': 10}]
        ns = SimpleNamespace(x=10, y='test')
        assert j_loads(ns, ordered=False) == {'x': 10, 'y': 'test'}

    def test_loads_valid_json_string(self):
        """Проверка парсинга валидной строки JSON."""
        s = '{"name": "Breadboard", "count": 42}'
        result = j_loads(s, ordered=False)
        assert result == {'name': 'Breadboard', 'count': 42}

    def test_loads_markdown_code_block(self):
        """Проверка очистки Markdown блоков (```json ... ``` и ``` ... ```) без удаления слова json из ключей."""
        md_json = '```json\n{\n  "json_rpc": "2.0",\n  "json": true,\n  "msg": "hello"\n}\n```'
        result = j_loads(md_json, ordered=False)
        assert result == {'json_rpc': '2.0', 'json': True, 'msg': 'hello'}

        md_plain = '```\n{"key": "value"}\n```'
        assert j_loads(md_plain, ordered=False) == {'key': 'value'}

    def test_loads_broken_json_repair(self):
        """Проверка восстановления синтаксически невалидного JSON через repair_json."""
        broken = '{"key": "value", "list": [1, 2, 3,],}'
        result = j_loads(broken, ordered=False)
        assert isinstance(result, dict)
        assert result.get('key') == 'value'
        assert result.get('list') == [1, 2, 3]

    def test_loads_unicode_preservation(self):
        """Проверка сохранения Unicode символов без искажений (кириллица, иврит, эмодзи)."""
        unicode_str = '{"ru": "Привет, мир!", "he": "שלום", "emoji": "🎉"}'
        result = j_loads(unicode_str, ordered=False)
        assert result['ru'] == 'Привет, мир!'
        assert result['he'] == 'שלום'
        assert result['emoji'] == '🎉'

    def test_loads_json_file(self, tmp_path: Path):
        """Проверка чтения корректного JSON-файла."""
        file_path = tmp_path / 'data.json'
        file_path.write_text('{"item": "breadboard", "active": true}', encoding='utf-8')
        result = j_loads(file_path, ordered=False)
        assert result == {'item': 'breadboard', 'active': True}

    def test_loads_csv_file(self, tmp_path: Path):
        """Проверка чтения CSV-файла через pandas."""
        csv_path = tmp_path / 'sample.csv'
        csv_path.write_text('id,name,value\n1,Alpha,100\n2,Beta,200\n', encoding='utf-8')
        result = j_loads(csv_path, ordered=False)
        assert len(result) == 2
        assert result[0] == {'id': 1, 'name': 'Alpha', 'value': 100}
        assert result[1] == {'id': 2, 'name': 'Beta', 'value': 200}

    def test_loads_empty_csv_file(self, tmp_path: Path):
        """Проверка обработки пустого CSV-файла."""
        empty_csv = tmp_path / 'empty.csv'
        empty_csv.write_text('', encoding='utf-8')
        result = j_loads(empty_csv, ordered=False, exc_info=False)
        assert result == []

    def test_loads_directory_sorted_json(self, tmp_path: Path):
        """Проверка детерминированного чтения каталога с JSON-файлами в алфавитном порядке."""
        dir_path = tmp_path / 'configs'
        dir_path.mkdir()
        (dir_path / '02_second.json').write_text('{"order": 2}', encoding='utf-8')
        (dir_path / '01_first.json').write_text('{"order": 1}', encoding='utf-8')
        (dir_path / 'ignored.txt').write_text('not json', encoding='utf-8')

        result = j_loads(dir_path, ordered=False)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == {'order': 1}
        assert result[1] == {'order': 2}

    def test_loads_ordered_param(self):
        """Проверка работы параметра ordered (True возвращает OrderedDict, False возвращает dict)."""
        json_str = '{"z": 1, "a": 2, "m": 3}'
        res_ordered = j_loads(json_str, ordered=True)
        assert isinstance(res_ordered, OrderedDict)
        assert list(res_ordered.keys()) == ['z', 'a', 'm']

        res_unordered = j_loads(json_str, ordered=False)
        assert isinstance(res_unordered, dict)
        assert not isinstance(res_unordered, OrderedDict)

    def test_loads_missing_file_and_empty_input(self, tmp_path: Path):
        """Проверка обработки несуществующего файла и пустых строк."""
        non_existent = tmp_path / 'missing.json'
        assert j_loads(non_existent, exc_info=False) == {}
        assert j_loads('', exc_info=False) == {}
        assert j_loads('   ', exc_info=False) == {}


class TestJLoadsNs:
    """Тестирование функции `j_loads_ns`."""

    def test_loads_ns_from_dict(self):
        """Проверка преобразования словаря в SimpleNamespace."""
        d = {'host': 'localhost', 'port': 8080}
        ns = j_loads_ns(d)
        assert isinstance(ns, SimpleNamespace)
        assert ns.host == 'localhost'
        assert ns.port == 8080

    def test_loads_ns_from_list(self):
        """Проверка преобразования списка словарей в список SimpleNamespace."""
        lst = [{'id': 1}, {'id': 2}]
        res = j_loads_ns(lst)
        assert isinstance(res, list)
        assert len(res) == 2
        assert all(isinstance(item, SimpleNamespace) for item in res)
        assert res[0].id == 1
        assert res[1].id == 2

    def test_loads_ns_nested_structures(self):
        """Проверка вложенных словарей и списков в SimpleNamespace."""
        data = {
            'app': 'breadboard',
            'server': {'host': '0.0.0.0', 'port': 5000},
            'plugins': [{'name': 'p1', 'enabled': True}, {'name': 'p2', 'enabled': False}],
        }
        ns = j_loads_ns(data)
        assert isinstance(ns, SimpleNamespace)
        assert ns.app == 'breadboard'
        assert isinstance(ns.server, SimpleNamespace)
        assert ns.server.host == '0.0.0.0'
        assert isinstance(ns.plugins, list)
        assert isinstance(ns.plugins[0], SimpleNamespace)
        assert ns.plugins[0].name == 'p1'
        assert ns.plugins[0].enabled is True
        assert ns.plugins[1].name == 'p2'
        assert ns.plugins[1].enabled is False

    def test_loads_ns_empty_or_missing(self, tmp_path: Path):
        """Проверка возврата пустого SimpleNamespace при пустом вводе или отсутствующем файле."""
        missing = tmp_path / 'absent.json'
        ns_missing = j_loads_ns(missing, exc_info=False)
        assert isinstance(ns_missing, SimpleNamespace)
        assert vars(ns_missing) == {}

        ns_empty_str = j_loads_ns('', exc_info=False)
        assert isinstance(ns_empty_str, SimpleNamespace)
        assert vars(ns_empty_str) == {}