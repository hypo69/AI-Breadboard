# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard UTILS - Csv Module
# =============================================================================
# Description:
#   CSV and JSON file conversion utilities.
#
# Usage Examples:
#   Python API:
#     from src.utils.convertors.csv import csv2dict
#
#     res = csv2dict()
#     print(res)
#
# File: csv.py
# Project: ai-breadboard
# Package: src.utils.convertors
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""CSV and JSON file conversion utilities."""

' Functions:\n    - `csv2dict`: Convert CSV data to a dictionary.\n    - `csv2ns`: Convert CSV data to SimpleNamespace objects.\n\n.. code-block:: python\n\n    # Example usage:\n\n    # Using JSON list of dictionaries\n    json_data_list = [{"name": "John", "age": 30, "city": "New York"}, {"name": "Alice", "age": 25, "city": "Los Angeles"}]\n    json_file_path = \'data.json\'\n    csv_file_path = \'data.csv\'\n\n    # Convert JSON to CSV\n    json2csv.json2csv(json_data_list, csv_file_path)\n\n    # Convert CSV back to JSON\n    csv_data = csv2json(csv_file_path, json_file_path)\n    if csv_data:\n        if isinstance(csv_data, list):\n            if isinstance(csv_data[0], dict):\n                print("CSV data (list of dictionaries):")\n            else:\n                print("CSV data (list of values):")\n            print(csv_data)\n        else:\n            print("Failed to read CSV data.")\n'
import json
import csv
from pathlib import Path
from typing import List, Dict
from types import SimpleNamespace
from logger import logger
from src.utils.csv import read_csv_as_dict, read_csv_as_ns, save_csv_file, read_csv_file

def csv2dict(csv_file: str | Path, *args, **kwargs) -> dict | None:
    """
    Convert CSV data to a dictionary.

    Args:
        csv_file (str | Path): Path to the CSV file to read.

    Returns:
        dict | None: Dictionary containing the data from CSV converted to JSON format, or `None` if conversion failed.

    Raises:
        Exception: If unable to read CSV.
    """
    return read_csv_as_dict(csv_file, *args, **kwargs)

def csv2ns(csv_file: str | Path, *args, **kwargs) -> SimpleNamespace | None:
    """
    Convert CSV data to SimpleNamespace objects.

    Args:
        csv_file (str | Path): Path to the CSV file to read.

    Returns:
        SimpleNamespace | None: SimpleNamespace object containing the data from CSV, or `None` if conversion failed.

    Raises:
        Exception: If unable to read CSV.
    """
    return read_csv_as_ns(csv_file, *args, **kwargs)

def csv_to_json(csv_file_path: str | Path, json_file_path: str | Path, exc_info: bool=True) -> List[Dict[str, str]] | None:
    """ Convert a CSV file to JSON format and save it to a JSON file.

    Args:
        csv_file_path (str | Path): The path to the CSV file to read.
        json_file_path (str | Path): The path to the JSON file to save.
        exc_info (bool, optional): If True, includes traceback information in the log. Defaults to True.

    Returns:
        List[Dict[str, str]] | None: The JSON data as a list of dictionaries, or None if conversion failed.

    Example:
        >>> json_data = csv_to_json('dialogue_log.csv', 'dialogue_log.json')
        >>> print(json_data)
        [{'role': 'user', 'content': 'Hello'}, {'role': 'assistant', 'content': 'Hi there!'}]
    """
    try:
        data = read_csv_file(csv_file_path, exc_info=exc_info)
        if data is not None:
            with open(json_file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=4)
            return data
        return
    except Exception as ex:
        logger.error('Failed to convert CSV to JSON', ex, exc_info=exc_info)
        return