# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unicode escape sequence decoding utilities
# =============================================================================
# Description:
#   Decodes unicode escape sequences in dictionaries, lists, or strings to readable text.
#   Handles nested structures recursively for comprehensive unicode processing.
#
# File: unicode.py
# Project: ai-breadboard
# Package: core.utils.convertors
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import re
from typing import Dict, Any

def decode_unicode_escape(input_data: Dict[str, Any] | list | str) -> Dict[str, Any] | list | str:
    """Decoding of unicode escape sequences in dictionaries, lists, or strings to readable text.

    Args:
        input_data (dict | list | str): Input data - dictionary, list or string, which may contain unicode escape sequences.

    Returns:
        dict | list | str: Transformed data. For strings escape sequences are decoded. For dictionaries or lists all values are processed recursively.

    Пример использования:
    .. code-block:: python
        input_dict = {
            'product_name': r'\u05de\u05e7\"\u05d8 \u05d9\u05e6\u05e8\u05df\nH510M K V2',
            'category': r'\u05e2\u05e8\u05db\u05ea \u05e9\u05d1\u05d1\u05d9\u05dd',
            'price': 123.45
        }

        input_list = [r'\u05e2\u05e8\u05db\u05ea \u05e9\u05d1\u05d1\u05d9\u05dd', r'H510M K V2']

        input_string = r'\u05de\u05e7\"\u05d8 \u05d9\u05e6\u05e8\u05df\nH510M K V2'

        # Применяем функцию
        decoded_dict = decode_unicode_escape(input_dict)
        decoded_list = decode_unicode_escape(input_list)
        decoded_string = decode_unicode_escape(input_string)

        print(decoded_dict)
        print(decoded_list)
        print(decoded_string)

    """
    
    if isinstance(input_data, dict):
        # Рекурсивная обработка значений словаря
        return {key: decode_unicode_escape(value) for key, value in input_data.items()}
    
    elif isinstance(input_data, list):
        # Рекурсивная обработка элементов списка
        return [decode_unicode_escape(item) for item in input_data]
    
    elif isinstance(input_data, str):
        # Function декодирует строку, если она содержит escape-последовательности
        try:
            # Шаг 1: Decoding строки с escape-последовательностями
            decoded_string = input_data.encode('utf-8').decode('unicode_escape')
        except UnicodeDecodeError:
            decoded_string = input_data
        
        # Шаг 2: Conversion всех найденных последовательностей \uXXXX
        unicode_escape_pattern = r'\\u[0-9a-fA-F]{4}'
        decoded_string = re.sub(unicode_escape_pattern, lambda match: match.group(0).encode('utf-8').decode('unicode_escape'), decoded_string)
        
        return decoded_string
    
    else:
        # Если тип данных не поддерживается, function вернет данные без изменений
        return input_data
