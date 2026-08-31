# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: JSON format conversion utilities
# =============================================================================
# Description:
#   Converts JSON data into various formats: CSV, SimpleNamespace, XML, and XLS.
#   Provides flexible serialization methods for different output formats.
#
# File: json.py
# Project: ai-breadboard
# Package: core.utils.convertors
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
JSON data conversion module.

Functions:
    - `json2csv`: Convert JSON data to CSV format.
    - `json2ns`: Convert JSON data to SimpleNamespace object.
    - `json2xml`: Convert JSON data to XML format.
    - `json2xls`: Convert JSON data to XLS format.
"""

import json
import csv
from types import SimpleNamespace
from pathlib import Path
from typing import List, Dict

from core.utils.csv import save_csv_file
from core.utils.jjson import j_dumps
from core.utils.xls import save_xls_file
from core.utils.convertors.dict import dict2xml
from core.logger.logger import logger

def json2csv(json_data: str | list | dict | Path, csv_file_path: str | Path) -> bool:
    """
    Convert JSON data or JSON file to CSV format with a comma delimiter.

    Args:
        json_data (str | list | dict | Path): JSON data as a string, list of dictionaries, or file path to a JSON file.
        csv_file_path (str | Path): Path to the CSV file to write.

    Returns:
        bool: True if successful, False otherwise.

    Raises:
        ValueError: If unsupported type for json_data.
        Exception: If unable to parse JSON or write CSV.
    """
    try:
        # Load JSON data
        if isinstance(json_data, dict):
            data = [json_data]
        elif isinstance(json_data, str):
            data = json.loads(json_data)
        elif isinstance(json_data, list):
            data = json_data
        elif isinstance(json_data, Path):
            with open(json_data, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
        else:
            raise ValueError("Unsupported type for json_data")

        save_csv_file(data, csv_file_path)
        return True
    except Exception as ex:
        logger.error(f"json2csv failed", ex, True)
        ...

def json2ns(json_data: str | dict | Path) -> SimpleNamespace:
    """
    Convert JSON data or JSON file to SimpleNamespace object.

    Args:
        json_data (str | dict | Path): JSON data as a string, dictionary, or file path to a JSON file.

    Returns:
        SimpleNamespace: Parsed JSON data as a SimpleNamespace object.
    
    Raises:
        ValueError: If unsupported type for json_data.
        Exception: If unable to parse JSON.
    """
    try:
        if isinstance(json_data, dict):
            data = json_data
        elif isinstance(json_data, str):
            data = json.loads(json_data)
        elif isinstance(json_data, Path):
            with open(json_data, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
        else:
            raise ValueError("Unsupported type for json_data")
        
        return SimpleNamespace(**data)
    except Exception as ex:
        logger.error(f"json2ns failed", ex, True)

def json2xml(json_data: str | dict | Path, root_tag: str = "root") -> str:
    """
    Convert JSON data or JSON file to XML format.

    Args:
        json_data (str | dict | Path): JSON data as a string, dictionary, or file path to a JSON file.
        root_tag (str): The root element tag for the XML.

    Returns:
        str: The resulting XML string.

    Raises:
        ValueError: If unsupported type for json_data.
        Exception: If unable to parse JSON or convert to XML.
    """
    return dict2xml(json_data)

def json2xls(json_data: str | list | dict | Path, xls_file_path: str | Path) -> bool:
    """
    Convert JSON data or JSON file to XLS format.

    Args:
        json_data (str | list | dict | Path): JSON data as a string, list of dictionaries, or file path to a JSON file.
        xls_file_path (str | Path): Path to the XLS file to write.

    Returns:
        bool: True if successful, False otherwise.

    Raises:
        ValueError: If unsupported type for json_data.
        Exception: If unable to parse JSON or write XLS.
    """
    return save_xls_file(json_data, xls_file_path)
        
