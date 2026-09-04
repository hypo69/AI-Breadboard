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
    - `pprint`: Pretty print data in human-readable format
"""

import json
import csv
import pandas as pd
from pathlib import Path
from typing import Any
from pprint import pprint as pretty_print

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

    This helper function applies the provided color and font styles to the given text using ANSI escape codes.

    Args:
        text: The text to be styled.
        text_color: The color to apply to the text. Default is empty string (no color).
        bg_color: The background color to apply. Default is empty string (no background).
        font_style: The font style to apply to the text. Default is empty string (no style).

    Returns:
        The styled text as a string with ANSI escape codes applied.

    Example:
        >>> _color_text("Hello, World!", text_color="green", font_style="bold")
        '\033[1m\033[32mHello, World!\033[0m'
    """
    return f"{font_style}{text_color}{bg_color}{text}{RESET}"

def pprint(print_data: Any = None, text_color: str = "white", bg_color: str = "", font_style: str = "") -> None:
    """Pretty print the given data with optional color, background, and font style.

    This function formats the input data based on its type and prints it to the console. The data is printed with optional 
    text color, background color, and font style based on the specified parameters. The function can handle dictionaries, 
    lists, strings, and file paths.

    Args:
        print_data: The data to be printed. Can be None, dict, list, str, or Path. Default is None.
        text_color: The color to apply to the text. Default is 'white'. See TEXT_COLORS for options.
        bg_color: The background color to apply. Default is empty (no background). See BG_COLORS for options.
        font_style: The font style to apply (bold, underline, etc.). Default is empty (no style).

    Raises:
        Exception: If the data type is unsupported or an error occurs during printing.

    Example:
        >>> pprint({"name": "Alice", "age": 30}, text_color="green")
        Prints colored JSON output.

        >>> pprint(["apple", "banana", "cherry"], text_color="blue", font_style="bold")
        Prints each item in colored bold text.

        >>> pprint("text example", text_color="yellow", bg_color="bg_red", font_style="underline")
        Prints styled underlined text with yellow foreground on red background.
    """
    text_color = TEXT_COLORS.get(text_color.lower(), TEXT_COLORS["white"])
    bg_color = BG_COLORS.get(bg_color.lower(), "")
    font_style = FONT_STYLES.get(font_style.lower(), "")

    if print_data is None:
        print(_color_text("No data to print!", text_color=TEXT_COLORS["red"]))
        return

    try:
        if isinstance(print_data, dict):
            print(_color_text(json.dumps(print_data, indent=4), text_color))
        elif isinstance(print_data, list):
            for item in print_data:
                print(_color_text(str(item), text_color))
        elif isinstance(print_data, (str, Path)) and Path(print_data).is_file():
            ext = Path(print_data).suffix.lower()
            if ext in ['.csv', '.xls']:
                print(_color_text("File reading supported for .csv, .xls only.", text_color))
            else:
                print(_color_text("Unsupported file type.", text_color))
        else:
            print(_color_text(str(print_data), text_color))
    except Exception as ex:
        print(_color_text(f"Error: {ex}", text_color=TEXT_COLORS["red"]))

if __name__ == '__main__':
    pprint({"name": "Alice", "age": 30}, text_color="green")
