# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Pretty printing and text formatting utilities
# =============================================================================
# Description:
#   Utility functions for pretty printing and text styling with support for
#   color, background, and font styles. Provides human-readable formatted output.
#
# File: printer.py
# Project: ai-breadboard
# Package: src.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Pretty printing and text formatting module.

Functions:
    - `_color_text`: Apply color and style to text
    - `pformat`: Format data into a pretty string with optional styling
    - `pprint`: Pretty print data in human-readable format to console
"""

import json
import csv
from pathlib import Path
from typing import Any, Optional

# ANSI escape codes
RESET = "\033[0m"

TEXT_COLORS = {
    "red": "\033[31m",
    "green": "\033[32m",
    "blue": "\033[34m",
    "yellow": "\033[33m",
    "white": "\033[37m",
    "cyan": "\033[36m",
    "magenta": "\033[35m",
    "light_gray": "\033[37m",
    "dark_gray": "\033[90m",
    "light_red": "\033[91m",
    "light_green": "\033[92m",
    "light_blue": "\033[94m",
    "light_yellow": "\033[93m",
}

# Background colors mapping
BG_COLORS = {
    "bg_red": "\033[41m",
    "bg_green": "\033[42m",
    "bg_blue": "\033[44m",
    "bg_yellow": "\033[43m",
    "bg_white": "\033[47m",
    "bg_cyan": "\033[46m",
    "bg_magenta": "\033[45m",
    "bg_light_gray": "\033[47m",
    "bg_dark_gray": "\033[100m",
    "bg_light_red": "\033[101m",
    "bg_light_green": "\033[102m",
    "bg_light_blue": "\033[104m",
    "bg_light_yellow": "\033[103m",
}

FONT_STYLES = {
    "bold": "\033[1m",
    "underline": "\033[4m",
}


def _color_text(text: str, text_color: str = "", bg_color: str = "", font_style: str = "") -> str:
    """Apply color, background, and font styling to the text.

    Args:
        text (str): The text to be styled.
        text_color (str): The color to apply to the text. Default is empty string.
        bg_color (str): The background color to apply. Default is empty string.
        font_style (str): The font style to apply to the text. Default is empty string.

    Returns:
        str: The styled text as a string with ANSI escape codes applied.

    Example:
        >>> _color_text("Hello, World!", text_color="green", font_style="bold")
        '\\033[1m\\033[32mHello, World!\\033[0m'
    """
    if not (text_color or bg_color or font_style):
        return text
    return f"{font_style}{text_color}{bg_color}{text}{RESET}"


def _get_default_indent() -> int:
    """Retrieve default JSON indentation from pprint configuration without hardcoding.

    Returns:
        int: Indentation size in spaces (configured in config.json under pprint, default 6).
    """
    try:
        from src.config import pprint_cfg
        indent = getattr(pprint_cfg, "json_indent", None)
        if indent is not None and isinstance(indent, int) and indent > 0:
            return indent
    except Exception:
        pass
    return 6


def _format_embedded_json(text: str, indent: Optional[int] = None) -> str:
    """Scan string for valid JSON objects/arrays and format them in-place with indentation.

    Args:
        text (str): Input text possibly containing embedded JSON blocks.
        indent (Optional[int]): Number of indentation spaces. Defaults to config value (6).

    Returns:
        str: Text with all valid JSON structures formatted and indented.
    """
    actual_indent = indent if indent is not None else _get_default_indent()
    decoder = json.JSONDecoder()
    result = []
    i = 0
    length = len(text)

    while i < length:
        if text[i] in ("{", "["):
            try:
                obj, end_idx = decoder.raw_decode(text, i)
                if isinstance(obj, (dict, list)):
                    formatted = json.dumps(obj, indent=actual_indent, ensure_ascii=False)
                    # Natural newline separation before JSON block
                    if result and not "".join(result).endswith("\n"):
                        last_part = result[-1].rstrip(" \t")
                        result[-1] = last_part
                        result.append("\n")
                    result.append(formatted)
                    # Natural newline separation after JSON block
                    if end_idx < length and not text[end_idx:].startswith("\n"):
                        result.append("\n")
                        while end_idx < length and text[end_idx] in (" ", "\t"):
                            end_idx += 1
                    i = end_idx
                    continue
            except json.JSONDecodeError:
                pass
        result.append(text[i])
        i += 1

    return "".join(result)


def pformat(
    print_data: Any = None,
    text_color: str = "",
    bg_color: str = "",
    font_style: str = "",
    indent: Optional[int] = None,
) -> str:
    """Format data into a pretty string with optional color and style.

    Automatically scans and extracts valid JSON objects/arrays embedded anywhere within
    arbitrary strings (<text> <JSON> <text>), python dictionaries, and lists.
    Indentation is loaded from config.json (json_indent: 6).

    Args:
        print_data (Any): The data to be formatted.
        text_color (str): Text color name. Default is empty string.
        bg_color (str): Background color name. Default is empty string.
        font_style (str): Font style name. Default is empty string.
        indent (Optional[int]): Indentation level for JSON. Default loads from config.json (6).

    Returns:
        str: Formatted string representation of the data.

    Example:
        >>> pformat("User info: {'id': 1} - verified", text_color="cyan")
    """
    clr = TEXT_COLORS.get(text_color.lower(), "") if text_color else ""
    bg = BG_COLORS.get(bg_color.lower(), "") if bg_color else ""
    font = FONT_STYLES.get(font_style.lower(), "") if font_style else ""
    actual_indent = indent if indent is not None else _get_default_indent()

    if print_data is None:
        return _color_text("None", clr, bg, font)

    try:
        if isinstance(print_data, (dict, list)):
            formatted = json.dumps(print_data, indent=actual_indent, ensure_ascii=False)
            return _color_text(formatted, clr, bg, font)

        if isinstance(print_data, str):
            # Check for file path
            try:
                p = Path(print_data)
                if p.is_file():
                    ext = p.suffix.lower()
                    if ext in [".csv", ".xls"]:
                        return _color_text(f"File: {print_data} (supported: .csv, .xls)", clr, bg, font)
                    return _color_text(f"File: {print_data}", clr, bg, font)
            except Exception:
                pass

            formatted = _format_embedded_json(print_data, indent=actual_indent)
            return _color_text(formatted, clr, bg, font)

        # Fallback for other objects
        formatted = _format_embedded_json(str(print_data), indent=actual_indent)
        return _color_text(formatted, clr, bg, font)
    except Exception as ex:
        err_msg = f"Format Error: {ex}"
        return _color_text(err_msg, TEXT_COLORS.get("red", ""), bg, font)


def pprint(
    print_data: Any = None,
    text_color: str = "white",
    bg_color: str = "",
    font_style: str = "",
    indent: Optional[int] = None,
) -> None:
    """Pretty print the given data with optional color, background, and font style.

    Args:
        print_data (Any): Data to be printed.
        text_color (str): Text color name. Default is 'white'.
        bg_color (str): Background color name. Default is empty string.
        font_style (str): Font style name. Default is empty string.
        indent (Optional[int]): Indentation level for JSON. Default loads from config.json (6).

    Example:
        >>> pprint({"name": "Alice", "age": 30}, text_color="green")
    """
    formatted = pformat(
        print_data=print_data,
        text_color=text_color,
        bg_color=bg_color,
        font_style=font_style,
        indent=indent,
    )
    print(formatted)


if __name__ == "__main__":
    pprint({"name": "Alice", "age": 30}, text_color="green")

