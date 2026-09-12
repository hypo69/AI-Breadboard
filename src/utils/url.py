# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: URL string parsing and manipulation utilities
# =============================================================================
# Description:
#   Provides utilities for working with URL strings including extraction of query parameters,
#   URL validation, and link shortening functionality with support for various URL formats
#   and parameter parsing from query strings.
#
# File: url.py
# Project: ai-breadboard
# Package: src.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from urllib.parse import urlparse, parse_qs
try:
    import validators
except ImportError:
    validators = None
import requests

def extract_url_params(url: str) -> dict | None:
    """Extraction of query parameters from URL string.

    Args:
        url (str): URL string for parsing.

    Returns:
        dict | None: Dictionary of query parameters and their values or None if URL has no parameters.
    """
    parsed_url = urlparse(url)
    params = parse_qs(parsed_url.query)
    
    # Convert parameter values from list to string if parameter has single value
    if params:
        params = {k: v if len(v) > 1 else v[0] for k, v in params.items()}
        return params
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
    pattern = re.compile(
        r'^(https?://)?'
        r'(([a-zA-Z0-9_-]+\.)+[a-zA-Z]{2,}|localhost|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(:\d+)?'
        r'([/?#].*)?$', re.IGNORECASE)
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
    return None

if __name__ == "__main__":
    # Get URL string from user
    url = input("Enter URL: ")
    
    # Check URL validity
    if is_url(url):
        params = extract_url_params(url)
        
        # Display parameters
        if params:
            print("URL Parameters:")
            for key, value in params.items():
                print(f"{key}: {value}")
        else:
            print("URL does not contain parameters.")
        
        # Offer user to shorten URL
        shorten = input("Would you like to shorten this URL? (y/n): ").strip().lower()
        if shorten == 'y':
            short_url = url_shortener(url)
            if short_url:
                print(f"Shortened URL: {short_url}")
            else:
                print("Error shortening URL.")
    else:
        print("Entered string is not a valid URL.")
