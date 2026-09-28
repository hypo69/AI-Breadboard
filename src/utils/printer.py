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
RESET = '\x1b[0m'
TEXT_COLORS = {'red': '\x1b[31m', 'green': '\x1b[32m', 'blue': '\x1b[34m', 'yellow': '\x1b[33m', 'white': '\x1b[37m', 'cyan': '\x1b[36m', 'magenta': '\x1b[35m', 'light_gray': '\x1b[37m', 'dark_gray': '\x1b[90m', 'light_red': '\x1b[91m', 'light_green': '\x1b[92m', 'light_blue': '\x1b[94m', 'light_yellow': '\x1b[93m'}
BG_COLORS = {'bg_red': '\x1b[41m', 'bg_green': '\x1b[42m', 'bg_blue': '\x1b[44m', 'bg_yellow': '\x1b[43m', 'bg_white': '\x1b[47m', 'bg_cyan': '\x1b[46m', 'bg_magenta': '\x1b[45m', 'bg_light_gray': '\x1b[47m', 'bg_dark_gray': '\x1b[100m', 'bg_light_red': '\x1b[101m', 'bg_light_green': '\x1b[102m', 'bg_light_blue': '\x1b[104m', 'bg_light_yellow': '\x1b[103m'}
FONT_STYLES = {'bold': '\x1b[1m', 'underline': '\x1b[4m'}

def _color_text(text: str, text_color: str='', bg_color: str='', font_style: str='') -> str:
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
    return f'{font_style}{text_color}{bg_color}{text}{RESET}'

def _get_default_indent() -> int:
    """Retrieve default JSON indentation from pprint configuration without hardcoding.

    Returns:
        int: Indentation size in spaces (configured in config.json under pprint, default 6).
    """
    try:
        from src.config import pprint_cfg
        indent = getattr(pprint_cfg, 'json_indent', None)
        if indent is not None and isinstance(indent, int) and (indent > 0):
            return indent
    except Exception:
        pass
    return 6

def _format_embedded_json(text: str, indent: Optional[int]=None) -> str:
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
        if text[i] in ('{', '['):
            try:
                obj, end_idx = decoder.raw_decode(text, i)
                if isinstance(obj, (dict, list)):
                    formatted = json.dumps(obj, indent=actual_indent, ensure_ascii=False)
                    if result and (not ''.join(result).endswith('\n')):
                        last_part = result[-1].rstrip(' \t')
                        result[-1] = last_part
                        result.append('\n')
                    result.append(formatted)
                    if end_idx < length and (not text[end_idx:].startswith('\n')):
                        result.append('\n')
                        while end_idx < length and text[end_idx] in (' ', '\t'):
                            end_idx += 1
                    i = end_idx
                    continue
            except json.JSONDecodeError:
                pass
        result.append(text[i])
        i += 1
    return ''.join(result)

def pformat(print_data: Any=None, text_color: str='', bg_color: str='', font_style: str='', indent: Optional[int]=None) -> str:
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
    clr = TEXT_COLORS.get(text_color.lower(), '') if text_color else ''
    bg = BG_COLORS.get(bg_color.lower(), '') if bg_color else ''
    font = FONT_STYLES.get(font_style.lower(), '') if font_style else ''
    actual_indent = indent if indent is not None else _get_default_indent()
    if print_data is None:
        return _color_text('None', clr, bg, font)
    try:
        if isinstance(print_data, (dict, list)):
            formatted = json.dumps(print_data, indent=actual_indent, ensure_ascii=False)
            return _color_text(formatted, clr, bg, font)
        if isinstance(print_data, str):
            try:
                p = Path(print_data)
                if p.is_file():
                    ext = p.suffix.lower()
                    if ext in ['.csv', '.xls']:
                        return _color_text(f'File: {print_data} (supported: .csv, .xls)', clr, bg, font)
                    return _color_text(f'File: {print_data}', clr, bg, font)
            except Exception:
                pass
            formatted = _format_embedded_json(print_data, indent=actual_indent)
            return _color_text(formatted, clr, bg, font)
        formatted = _format_embedded_json(str(print_data), indent=actual_indent)
        return _color_text(formatted, clr, bg, font)
    except Exception as ex:
        err_msg = f'Format Error: {ex}'
        return _color_text(err_msg, TEXT_COLORS.get('red', ''), bg, font)

def pprint(*args: Any, text_color: str='', bg_color: str='', font_style: str='', indent: Optional[int]=None, sep: str=' ', end: str='\n', file: Any=None, flush: bool=False, **kwargs: Any) -> None:
    """Выводит форматированные данные в консоль с поддержкой цветов ANSI и структурированного JSON.

    Может использоваться как прямая замена стандартной функции `print`:
    `from src.utils.printer import pprint as print`

    Args:
        *args (Any): Объекты для вывода.
        text_color (str): Название цвета текста (например, 'green', 'yellow', 'white'). По умолчанию без изменения цвета.
        bg_color (str): Название цвета фона. По умолчанию пустая строка.
        font_style (str): Стиль шрифта ('bold', 'underline'). По умолчанию пустая строка.
        indent (Optional[int]): Уровень отступа JSON. По умолчанию загружается из config.json (json_indent: 6).
        sep (str): Разделитель между аргументами. По умолчанию пробел (' ').
        end (str): Символ окончания строки. По умолчанию перенос строки ('\\n').
        file (Any): Целевой поток вывода. По умолчанию sys.stdout.
        flush (bool): Флаг принудительного сброса буфера. По умолчанию False.
        **kwargs (Any): Дополнительные параметры для обратной совместимости (например, print_data).

    Example:
        >>> pprint({"name": "Alice", "age": 30}, text_color="green")
        >>> from src.utils.printer import pprint as print
        >>> print("Response:", {"status": "ok", "code": 200})
    """
    import sys
    if not args and 'print_data' in kwargs:
        args = (kwargs.pop('print_data'),)
    target_file = file if file is not None else sys.stdout
    if not args:
        target_file.write(end)
        if flush:
            target_file.flush()
        return
    formatted_parts = [pformat(print_data=arg, text_color=text_color, bg_color=bg_color, font_style=font_style, indent=indent) for arg in args]
    output_str = sep.join(formatted_parts)
    target_file.write(f'{output_str}{end}')
    if flush:
        target_file.flush()
if __name__ == '__main__':
    pprint({'name': 'Alice', 'age': 30}, text_color='green')