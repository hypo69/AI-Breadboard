# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: JSON and CSV file handling utilities
# =============================================================================
# Description:
#   Provides comprehensive functions for handling JSON and CSV files including loading,
#   dumping, merging, and conversion operations. Includes SimpleNamespace conversion,
#   Markdown parsing, data validation, and repair of malformed JSON structures.
#
# File: jjson.py
# Project: ai-breadboard
# Package: core.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from datetime import datetime
import copy
from math import log
from pathlib import Path
from typing import List, Dict, Optional, Any
from types import SimpleNamespace
import json
import os
import re
import pandas as pd
from json_repair import repair_json
import simplejson as simplejson
from typing import Any
from pathlib import Path
import json
import pandas as pd
from types import SimpleNamespace
from collections import OrderedDict

from core.logger.logger import logger
from .convertors.dict import dict2ns

def j_dumps(
    data: Dict | SimpleNamespace | List[Dict] | List[SimpleNamespace],
    file_path: Optional[Path] = None,
    ensure_ascii: bool = True,
    mode: str = "w",
    exc_info: bool = True,
) -> Optional[Dict]:
    """Dumping JSON data to file or returning JSON data as dictionary.

    Args:
        data (Dict | SimpleNamespace | List[Dict] | List[SimpleNamespace]): JSON-compatible data or SimpleNamespace objects to dump.
        file_path (Optional[Path], optional): Path to the output file. If None, returns JSON as a dictionary. Defaults to None.
        ensure_ascii (bool, optional): If True, escapes non-ASCII characters in output. Defaults to True.
        mode (str, optional): File open mode ('w', 'a+', '+a'). Defaults to 'w'.
        exc_info (bool, optional): If True, logs exceptions with traceback. Defaults to True.

    Returns:
        Optional[Dict]: JSON data as a dictionary if successful, or nothing if an error occurs.

    Exceptions:
        ValueError: If the file mode is unsupported.
    """
    
    path = Path(file_path) if isinstance(file_path, (str, Path)) else None

     # If data comes as string - code will attempt to parse it via `repair_json()`
    if isinstance(data, str): 
        try:
            data = repair_json(data)
        except Exception as ex:
            logger.error(f'Error конвертации строки: {pprint(data)}', ex, False)
            ...
            return 

    def _convert(value: Any) -> Any:
        """
        Recursively process values to handle nested SimpleNamespace, dict, or list.

        Args:
            value (Any): Value to process.

        Returns:
            Any: Converted value.
        """
        if isinstance(value, SimpleNamespace):
            return {key: _convert(val) for key, val in vars(value).items()}
        elif isinstance(value, dict):
            return {key: _convert(val) for key, val in value.items()}
        elif isinstance(value, list):
            return [_convert(item) for item in value]
        return value

    # Конвертация входных данных в valid dictionary `dict` 
    data = _convert(data)

    # если указан неверный режим записи в файл - будет установлен 'w',
    if mode not in {"w", "a+", "+a"}:     
        mode = 'w'

    # Чтение существующих данных из файла (если файл существует и режим 'a+' или '+a')
    existing_data = {}
    if path and path.exists() and mode in {"a+", "+a"}:
        try:
            with path.open("r", encoding="utf-8") as f:  # Чтение в режиме 'r'
                existing_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding existing JSON in {path}: {e}", exc_info=exc_info)
            ...
            return
        except Exception as ex:
            logger.error(f"Error reading {path=}: {ex}", exc_info=exc_info)
            ...
            return 

    # Обработка данных в зависимости от режима
    if mode == "a+":
        # Присоединение новых данных в начало существующего словаря
        try:
            if isinstance(data, list) and isinstance(existing_data, list):
                existing_data = data + existing_data  # Добавляем элементы из списка в начало
            else:
                data.update(existing_data)
        except Exception as ex:
            logger.error(ex)
            ...

    elif mode == "+a":
        # Присоединение новых данных в конец существующего словаря
        try:
            if isinstance(existing_data, list):
                existing_data.extend(data)  # Добавляем элементы из списка в конец
            else:
                existing_data.update(data)
            data = existing_data
        except Exception as ex:
            logger.error(ex)
            ...

    # Режим 'w' - перезаписывает файл новыми данными
    if path:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=ensure_ascii, indent=4)
        except Exception as ex:
            logger.error(f"Failed to write to {path}: ",ex, exc_info=exc_info)
            ...
            return
    else:
        return data

    return data

def j_loads(
    jjson: dict | SimpleNamespace | str | Path | list,
    ordered: bool = True
) -> dict | list:
    """
    Loading JSON или CSV данных из файла, директории, строки, объекта JSON или SimpleNamespace.
    Перекодирует строки ключей и значений в Unicode.

    Args:
        jjson (dict | SimpleNamespace | str | Path | list): Путь к файлу, директории, string JSON данных,
                                                           объект JSON или SimpleNamespace.
        ordered (bool, optional): Returns OrderedDict для сохранения порядка элементов. Defaults to True.

    Returns:
        dict | list: Обработанные данные (dictionary или list словарей).

    Raises:
        FileNotFoundError: Если указанный файл не найден.
        json.JSONDecodeError: Если данные JSON не удалось разобрать.
    """

    def decode_strings(data: Any) -> Any:
        """Рекурсивно перекодирует строки в структуре данных."""
        if isinstance(data, str):
            try:
                return data.encode().decode('unicode_escape')  # Декодируем escape-последовательности
            except Exception:
                return data  # Если декодировать не получилось, возвращаем как есть
        elif isinstance(data, list):
            return [decode_strings(item) for item in data]  # Обрабатываем каждый элемент списка
        elif isinstance(data, dict):
            return {decode_strings(key): decode_strings(value) for key, value in data.items()}  # Обрабатываем ключи и значения словаря

        # Decoding escape \u0412\u044b\u0441\u043e\u043a\u043e
        decoded_data = json.loads(json.dumps(data))
        return data  # Возвращаем неизменённые значения, если они не string, list или dictionary

    def string2dict(json_string: str) -> dict:
        """Deletes тройные обратные кавычки и 'json' из начала и конца строки."""
        if json_string.startswith(('```', '```json')) and json_string.endswith(('```','```\n')):
            json_string = json_string.strip('`').replace('json', '', 1).strip()
        #json_string = json_string.replace()
        try:
            _j = simplejson.loads(json_string)
        except json.JSONDecodeError:
            logger.error(f'Error парсинга строки JSON:\n {json_string}', ex, False)
            ...
            return {}
        try:
            # Decoding escape \u0412\u044b\u0441\u043e\u043a\u043e
            return json.loads(json.dumps(_j))
        except Exception as ex:
            logger.error(f"Error декодирования JSON", ex, False)
            ...
            return {}

    # Основная обработка данных
    try:
        if isinstance(jjson, SimpleNamespace):  # Если это SimpleNamespace
            jjson = vars(jjson)  # Преобразуем в dictionary

        if isinstance(jjson, Path):
            if jjson.is_dir():  # Если это директория
                files = list(jjson.glob('*.json'))
                return [j_loads(file, ordered=ordered) for file in files]
            if jjson.suffix.lower() == '.csv':  # Если это CSV

                return pd.read_csv(jjson).to_dict(orient='records')
            # Если это JSON-файл
            #return decode_strings(json.loads(jjson.read_text(encoding='utf-8')))
            return json.loads(jjson.read_text(encoding='utf-8'))
        elif isinstance(jjson, str):  # Если это string
            return string2dict(jjson)
        elif isinstance(jjson, list):  # Если это list
            return [decode_strings(item) for item in jjson]
        elif isinstance(jjson, dict):  # Если это dictionary
            return decode_strings(jjson)

    except FileNotFoundError as ex:
        logger.error(f'Файл не найден: {jjson}')
        return {}
    except json.JSONDecodeError as ex:
        logger.error(f'Error парсинга JSON:\n{jjson}\n', ex, False)
        return {}
    except Exception as ex:
        logger.error(f'Error загрузки данных: ',ex, False)
        return {}

    return {}

def j_loads_ns(
    jjson: Path | SimpleNamespace | Dict | str,
    ordered: bool = True
) -> SimpleNamespace:
    """Load JSON or CSV data from a file, directory, or string and convert to SimpleNamespace.

    Args:
        jjson (Path | SimpleNamespace | Dict | str): Path to a file, directory, or JSON data as a string, or JSON object.
        ordered (bool, optional): If  returns OrderedDict instead of a regular dict to preserve element order. Defaults to False.
        exc_info (bool, optional): If  logs exceptions with traceback. Defaults to True.

    Returns:
        Optional[SimpleNamespace | List[SimpleNamespace]]: Returns SimpleNamespace or a list of SimpleNamespace objects if successful. Returns None if jjson is not found or cannot be read.

    Examples:
        >>> j_loads_ns('data.json')
        SimpleNamespace(key='value')

        >>> j_loads_ns(Path('/path/to/directory'))
        [SimpleNamespace(key1='value1'), SimpleNamespace(key2='value2')]

        >>> j_loads_ns('{"key": "value"}')
        SimpleNamespace(key='value')

        >>> j_loads_ns(Path('/path/to/file.csv'))
        [SimpleNamespace(column1='value1', column2='value2')]
    """
    data = j_loads(jjson, ordered=ordered)
    if data:
        if isinstance(data, list):
            return  [dict2ns(item) for item in data]
        return  dict2ns(data)
    return  {} 

