# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: CSV file processing utilities
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: csv.py
# Project: ai-breadboard
# Package: src.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""CSV and JSON file conversion utilities."""

import csv
import json
from pathlib import Path
from types import SimpleNamespace
from typing import List, Dict, Union
import pandas as pd
from src.logger.logger import logger

def save_csv_file(
    data: List[Dict[str, str]],
    file_path: Union[str, Path],
    mode: str = 'a',
    exc_info: bool = True,
) -> bool:
    """Saves a list of dictionaries to a CSV file.

    :param data: List of dictionaries to save.
    :type data: List[Dict[str, str]]
    :param file_path: Path to the CSV file.
    :type file_path: Union[str, Path]
    :param mode: File mode ('a' to append, 'w' to overwrite). Default is 'a'.
    :type mode: str
    :param exc_info: Include traceback information in logs.
    :type exc_info: bool
    :raises TypeError: If input data is not a list of dictionaries.
    :raises ValueError: If input data is empty.
    :returns: True if successful, otherwise False.
    """
    if not isinstance(data, list):
        raise TypeError("Input data must be a list of dictionaries.")
    if not data:
        raise ValueError("Input data cannot be empty.")
    
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with file_path.open(mode, newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=data[0].keys())
            if mode == 'w' or not file_path.exists():
                writer.writeheader()
            writer.writerows(data)
        return True
    except Exception as e:
        logger.error(f"Failed to save CSV to {file_path}", exc_info=exc_info)
        return False

def read_csv_file(file_path: Union[str, Path], exc_info: bool = True) -> List[Dict[str, str]] | None:
    """Reads CSV content as a list of dictionaries.

    :param file_path: Path to the CSV file.
    :type file_path: Union[str, Path]
    :param exc_info: Include traceback information in logs.
    :type exc_info: bool
    :raises FileNotFoundError: If file not found.
    :returns: List of dictionaries or None if failed.
    """
    try:
        with Path(file_path).open('r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            return list(reader)
    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}", exc_info=exc_info)
        return None
    except Exception as e:
        logger.error(f"Failed to read CSV from {file_path}", exc_info=exc_info)
        return None

def read_csv_as_json(csv_file_path: Union[str, Path], json_file_path: Union[str, Path], exc_info: bool = True) -> bool:
    """
    Convert a CSV file to JSON format and save it.

    :param csv_file_path: Path to the CSV file.
    :type csv_file_path: str | Path
    :param json_file_path: Path to save the JSON file.
    :type json_file_path: str | Path
    :param exc_info: Include traceback information in logs. Defaults to True.
    :type exc_info: bool, optional
    :returns: True if conversion is successful, else False.
    :rtype: bool
    """
    try:
        data = read_csv_file(csv_file_path, exc_info=exc_info)
        if data is None:
            return False
        with Path(json_file_path).open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as ex:
        logger.error(f"Failed to convert CSV to JSON at {json_file_path}", exc_info=exc_info)
        return False

def read_csv_as_dict(csv_file: Union[str, Path]) -> dict | None:
    """
    Convert CSV content to a dictionary.

    :param csv_file: Path to the CSV file.
    :type csv_file: str | Path
    :returns: Dictionary representation of CSV content, or None if failed.
    :rtype: dict | None
    """
    try:
        with Path(csv_file).open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return {"data": [row for row in reader]}
    except Exception as ex:
        logger.error("Failed to read CSV as dictionary", exc_info=True)
        return None

def read_csv_as_ns(file_path: Union[str, Path]) -> List[dict]:
    """Load CSV data into a list of dictionaries using Pandas.

    :param file_path: Path to the CSV file.
    :type file_path: Union[str, Path]
    :returns: List of dictionaries representing the CSV content.
    :raises FileNotFoundError: If file not found.
    """
    try:
        df = pd.read_csv(file_path)
        return df.to_dict(orient='records')
    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Failed to load CSV as dictionaries from {file_path}", exc_info=True)
        return []