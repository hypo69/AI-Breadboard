# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard UTILS - Jjson Module
# =============================================================================
# Description:
#   Модуль сериализации и десериализации данных JSON/CSV (`jjson`).
#
# Usage Examples:
#   Python API:
#     from src.utils.jjson import j_dumps, j_loads, j_loads_ns
#
#     data = j_loads('{"key": "value"}')
#     ns = j_loads_ns('{"key": "value"}')
#     j_dumps(data, 'config.json')
#
# File: jjson.py
# Project: ai-breadboard
# Package: src.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-10 11:30:00
# =============================================================================

from __future__ import annotations

import copy
import json
import os
import tempfile
from collections import OrderedDict
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from json_repair import repair_json
from logger import logger

from .convertors.dict import dict2ns


def _clean_json_string(json_string: str) -> str:
    """Очищает строку от обрамления Markdown code blocks (```json ... ```).

    Args:
        json_string (str): Исходная строка с JSON или Markdown.

    Returns:
        str: Очищенная JSON-строка.
    """
    s = json_string.strip()
    if s.startswith('```'):
        lines = s.splitlines()
        if lines and lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        s = '\n'.join(lines).strip()
    return s


def _convert_namespaces_to_dict(value: Any) -> Any:
    """Рекурсивно преобразует SimpleNamespace и вложенные структуры в словари/списки.

    Args:
        value (Any): Значение для преобразования.

    Returns:
        Any: Преобразованное значение.
    """
    if isinstance(value, SimpleNamespace):
        return {k: _convert_namespaces_to_dict(v) for k, v in vars(value).items()}
    elif isinstance(value, dict):
        return {k: _convert_namespaces_to_dict(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_convert_namespaces_to_dict(item) for item in value]
    return value


def _ensure_ordered(data: Any, ordered: bool) -> Any:
    """Рекурсивно приводит словари к OrderedDict или обычному dict.

    Args:
        data (Any): Исходные данные.
        ordered (bool): Флаг использования OrderedDict.

    Returns:
        Any: Преобразованные данные.
    """
    if isinstance(data, dict):
        if ordered:
            return OrderedDict((k, _ensure_ordered(v, ordered)) for k, v in data.items())
        return {k: _ensure_ordered(v, ordered) for k, v in data.items()}
    elif isinstance(data, list):
        return [_ensure_ordered(item, ordered) for item in data]
    return data


def j_dumps(
    data: Dict[str, Any] | SimpleNamespace | List[Any] | str | Any,
    file_path: Optional[Path | str] = None,
    ensure_ascii: bool = True,
    mode: str = 'w',
    exc_info: bool = True,
) -> Optional[Dict[str, Any] | List[Any] | Any]:
    """Сериализует данные в JSON-формат, сохраняет в файл или возвращает структуру данных Python.

    Args:
        data (Dict[str, Any] | SimpleNamespace | List[Any] | str | Any): Данные для сериализации
            (словарь, список, SimpleNamespace, JSON-строка).
        file_path (Optional[Path | str], optional): Путь к файлу для сохранения. Если None,
            возвращает данные в виде словаря/списка. Defaults to None.
        ensure_ascii (bool, optional): Если True, экранирует не-ASCII символы в выводе.
            Если False, сохраняет Unicode-символы. Defaults to True.
        mode (str, optional): Режим записи ('w', 'a+', '+a').
            'w' - полная перезапись файла.
            'a+' - объединение данных; для списков новые элементы идут перед старыми,
                   для словарей существующие ключи имеют приоритет над новыми.
            '+a' - объединение данных; для списков новые элементы идут после старых,
                   для словарей новые ключи перезаписывают существующие.
            Defaults to 'w'.
        exc_info (bool, optional): Если True, логирует исключения со стеком вызовов. Defaults to True.

    Returns:
        Optional[Dict[str, Any] | List[Any] | Any]: Результирующая структура данных или None при ошибке.

    Raises:
        ValueError: Если указан неподдерживаемый режим записи (при внутренней валидации).
    """
    path = Path(file_path) if file_path is not None else None

    # Обработка строкового входа
    if isinstance(data, str):
        cleaned_str = _clean_json_string(data)
        try:
            data = json.loads(cleaned_str)
        except json.JSONDecodeError:
            try:
                repaired = repair_json(cleaned_str, return_objects=True)
                if isinstance(repaired, (dict, list)):
                    data = repaired
                else:
                    logger.error(f'Строка не является валидным JSON: {data[:200]}', exc_info=exc_info)
                    return None
            except Exception as ex:
                logger.error(f'Ошибка восстановления JSON-строки: {ex}', ex=ex, exc_info=exc_info)
                return None
        except Exception as ex:
            logger.error(f'Ошибка парсинга строки данных: {ex}', ex=ex, exc_info=exc_info)
            return None

    # Рекурсивное преобразование SimpleNamespace в словари
    data = _convert_namespaces_to_dict(data)

    if mode not in {'w', 'a+', '+a'}:
        mode = 'w'

    # Чтение существующих данных при режимах объединения
    if path and path.exists() and (mode in {'a+', '+a'}):
        try:
            content = path.read_text(encoding='utf-8').strip()
            if not content:
                existing_data: Any = [] if isinstance(data, list) else {}
            else:
                existing_data = json.loads(content)
        except json.JSONDecodeError as ex:
            logger.error(f'Ошибка декодирования существующего JSON в {path}: {ex}', ex=ex, exc_info=exc_info)
            return None
        except Exception as ex:
            logger.error(f'Ошибка чтения файла {path}: {ex}', ex=ex, exc_info=exc_info)
            return None

        # Проверка совместимости типов
        if isinstance(data, list) and not isinstance(existing_data, list):
            logger.error(
                f'Несовместимые типы для объединения в {path}: ожидался list, получен {type(existing_data).__name__}',
                exc_info=exc_info,
            )
            return None
        if isinstance(data, dict) and not isinstance(existing_data, dict):
            logger.error(
                f'Несовместимые типы для объединения в {path}: ожидался dict, получен {type(existing_data).__name__}',
                exc_info=exc_info,
            )
            return None

        if mode == 'a+':
            if isinstance(data, list) and isinstance(existing_data, list):
                data = data + existing_data
            elif isinstance(data, dict) and isinstance(existing_data, dict):
                merged = copy.deepcopy(data)
                merged.update(existing_data)
                data = merged
        elif mode == '+a':
            if isinstance(data, list) and isinstance(existing_data, list):
                existing_data.extend(data)
                data = existing_data
            elif isinstance(data, dict) and isinstance(existing_data, dict):
                existing_data.update(data)
                data = existing_data

    # Сохранение в файл с атомарной заменой
    if path:
        temp_file = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            json_text = json.dumps(data, ensure_ascii=ensure_ascii, indent=4)
            with tempfile.NamedTemporaryFile('w', dir=str(path.parent), delete=False, encoding='utf-8') as tf:
                temp_file = Path(tf.name)
                tf.write(json_text)
            os.replace(temp_file, path)
            return data
        except Exception as ex:
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            logger.error(f'Ошибка записи в файл {path}: {ex}', ex=ex, exc_info=exc_info)
            return None

    return data


def j_loads(
    jjson: dict | SimpleNamespace | str | Path | list | Any,
    ordered: bool = True,
    exc_info: bool = True,
) -> dict | list:
    """Загружает JSON или CSV данные из файла, директории, строки, словаря или SimpleNamespace.

    Args:
        jjson (dict | SimpleNamespace | str | Path | list | Any): Путь к файлу/директории,
            строка JSON, словарь, список или SimpleNamespace.
        ordered (bool, optional): Если True, возвращает OrderedDict для сохранения порядка ключей.
            Если False, возвращает стандартный dict. Defaults to True.
        exc_info (bool, optional): Если True, логирует исключения со стеком вызовов. Defaults to True.

    Returns:
        dict | list: Распарсенные данные (словарь, OrderedDict или список).
            При ошибке или пустом вводе возвращает `{}`.
    """
    try:
        # Обработка SimpleNamespace
        if isinstance(jjson, SimpleNamespace):
            converted = _convert_namespaces_to_dict(jjson)
            return _ensure_ordered(converted, ordered)

        # Обработка словарей
        if isinstance(jjson, dict):
            return _ensure_ordered(jjson, ordered)

        # Обработка списков
        if isinstance(jjson, list):
            return [_ensure_ordered(item, ordered) if isinstance(item, (dict, list)) else item for item in jjson]

        # Обработка Path
        if isinstance(jjson, Path):
            if jjson.is_dir():
                files = sorted(jjson.glob('*.json'), key=lambda p: p.name)
                results: List[Any] = []
                for file_p in files:
                    try:
                        loaded_item = j_loads(file_p, ordered=ordered, exc_info=exc_info)
                        results.append(loaded_item)
                    except Exception as ex:
                        logger.error(f'Ошибка загрузки файла {file_p} из каталога {jjson}: {ex}', ex=ex, exc_info=exc_info)
                return results

            if not jjson.exists():
                logger.error(f'Файл не найден: {jjson}')
                return {}

            if jjson.suffix.lower() == '.csv':
                try:
                    df = pd.read_csv(jjson, encoding='utf-8')
                    records = df.to_dict(orient='records')
                    return [_ensure_ordered(r, ordered) for r in records]
                except pd.errors.EmptyDataError:
                    return []
                except Exception as ex:
                    logger.error(f'Ошибка чтения CSV-файла {jjson}: {ex}', ex=ex, exc_info=exc_info)
                    return []

            content = jjson.read_text(encoding='utf-8').strip()
            if not content:
                return {}
            hook = OrderedDict if ordered else None
            return json.loads(content, object_pairs_hook=hook)

        # Обработка строк
        if isinstance(jjson, str):
            s = jjson.strip()
            if not s:
                return {}

            # Проверка, не является ли строка путем к существующему файлу или каталогу
            if not s.startswith(('{', '[', '`')) and '\n' not in s and len(s) < 1024:
                try:
                    p = Path(s)
                    if p.exists():
                        return j_loads(p, ordered=ordered, exc_info=exc_info)
                except (OSError, ValueError):
                    pass

            cleaned = _clean_json_string(s)
            if not cleaned:
                return {}

            hook = OrderedDict if ordered else None
            try:
                return json.loads(cleaned, object_pairs_hook=hook)
            except json.JSONDecodeError as ex:
                try:
                    repaired = repair_json(cleaned, return_objects=True)
                    if isinstance(repaired, (dict, list)):
                        return _ensure_ordered(repaired, ordered)
                except Exception:
                    pass
                logger.error(f'Ошибка парсинга JSON-строки:\n{jjson}', ex=ex, exc_info=exc_info)
                return {}
            except Exception as ex:
                logger.error(f'Ошибка декодирования JSON: {ex}', ex=ex, exc_info=exc_info)
                return {}

    except FileNotFoundError as ex:
        logger.error(f'Файл не найден: {jjson}', ex=ex, exc_info=exc_info)
        return {}
    except Exception as ex:
        logger.error(f'Ошибка загрузки данных {jjson}: {ex}', ex=ex, exc_info=exc_info)
        return {}

    return {}


def j_loads_ns(
    jjson: Path | SimpleNamespace | Dict[str, Any] | str | List[Any] | Any,
    ordered: bool = True,
    exc_info: bool = True,
) -> SimpleNamespace | List[SimpleNamespace] | List[Any] | Dict[str, Any] | Any:
    """Загружает JSON или CSV данные и преобразует словари в объекты SimpleNamespace.

    Args:
        jjson (Path | SimpleNamespace | Dict[str, Any] | str | List[Any] | Any): Путь к файлу,
            каталогу, строка JSON, словарь или список.
        ordered (bool, optional): Если True, сохраняет порядок ключей при загрузке. Defaults to True.
        exc_info (bool, optional): Если True, логирует исключения со стеком вызовов. Defaults to True.

    Returns:
        SimpleNamespace | List[SimpleNamespace] | List[Any] | Any: Преобразованные данные
            (SimpleNamespace или список SimpleNamespace). При ошибке возвращает `SimpleNamespace()`.

    Examples:
        >>> j_loads_ns('{"key": "value"}')
        namespace(key='value')

        >>> j_loads_ns('[{"key1": "val1"}, {"key2": "val2"}]')
        [namespace(key1='val1'), namespace(key2='val2')]
    """
    data = j_loads(jjson, ordered=ordered, exc_info=exc_info)
    if isinstance(data, list):
        return [dict2ns(item) if isinstance(item, (dict, list)) else item for item in data]
    elif isinstance(data, dict):
        return dict2ns(data)
    elif isinstance(data, SimpleNamespace):
        return data
    return SimpleNamespace()