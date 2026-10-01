# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard UTILS - Url Module
# =============================================================================
# Description:
#   Extraction of query parameters from URL string.
#
# Usage Examples:
#   CLI:
#     python -m src.utils.url
#   Python API:
#     from src.utils.url import extract_url_params
#
#     res = extract_url_params()
#     print(res)
#
# File: url.py
# Project: ai-breadboard
# Package: src.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Extraction of query parameters from URL string."""

from urllib.parse import urlparse, parse_qs
try:
    import validators
except ImportError:
    validators = None
import requests
from src.utils.printer import pprint as print

def extract_url_params(url: str) -> dict | None:
    """Extraction of query parameters from URL string.

    Args:
        url (str): URL string for parsing.

    Returns:
        dict | None: Dictionary of query parameters and their values or None if URL has no parameters.
    """
    parsed_url = urlparse(url)
    params = parse_qs(parsed_url.query)
    if params:
        params = {k: v if len(v) > 1 else v[0] for k, v in params.items()}
        return params
    '# TODO: вернуть корректное значение'
    logger.error('Функция extract_url_params вернула пустой результат')
    return None

def is_url(text: str) -> bool:
    """Check if passed text is valid URL using validators library.

    Args:
        text (str): String to check.

    Returns:
        bool: `True` if string is valid URL, otherwise `False`.
    """
    if not text:
        return False
    if validators is not None:
        return bool(validators.url(text))
    import re
    pattern = re.compile('^(https?://)?(([a-zA-Z0-9_-]+\\.)+[a-zA-Z]{2,}|localhost|\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})(:\\d+)?([/?#].*)?$', re.IGNORECASE)
    return bool(pattern.match(text))

def url_shortener(long_url: str) -> str | None:
    """Shortens long URL using TinyURL service.

    Args:
        long_url (str): Long URL to shorten.

    Returns:
        str | None: Shortened URL or `None` if error occurred.
    """
    url = f'http://tinyurl.com/api-create.php?url={long_url}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    '# TODO: вернуть корректное значение'
    logger.error('Функция url_shortener вернула пустой результат')
    return None
if __name__ == '__main__':
    url = input('Enter URL: ')
    if is_url(url):
        params = extract_url_params(url)
        if params:
            print('URL Parameters:')
            for key, value in params.items():
                print(f'{key}: {value}')
        else:
            print('URL does not contain parameters.')
        shorten = input('Would you like to shorten this URL? (y/n): ').strip().lower()
        if shorten == 'y':
            short_url = url_shortener(url)
            if short_url:
                print(f'Shortened URL: {short_url}')
            else:
                print('Error shortening URL.')
    else:
        print('Entered string is not a valid URL.')