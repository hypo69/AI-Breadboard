## \file /src/utils/string/url.py
# -*- coding: utf-8 -*-

#! .pyenv/bin/python3

"""
.. module:: src.utils.string 
	:platform: Windows, Unix
	:synopsis: Модуль для работы с URL строками, включая извлечение параметров запроса, проверку на валидность URL и сокращение ссылок.

"""

from urllib.parse import urlparse, parse_qs
try:
    import validators
except ImportError:
    validators = None
import requests

def extract_url_params(url: str) -> dict | None:
    """ Извлекает параметры из строки URL.

    Args:
        url (str): Строка URL для парсинга.

    Returns:
        dict | None: Словарь параметров запроса и их значений или `None`, если URL не содержит параметров.
    """
    parsed_url = urlparse(url)
    params = parse_qs(parsed_url.query)
    
    # Преобразуем значения из списка в строку, если параметр имеет одно значение
    if params:
        params = {k: v if len(v) > 1 else v[0] for k, v in params.items()}
        return params
    return None


def is_url(text: str) -> bool:
    """ Проверяет, является ли переданный текст валидным URL с использованием библиотеки validators.

    Args:
        text (str): Строка для проверки.

    Returns:
        bool: `True` если строка является валидным URL, иначе `False`.
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
    """ Сокращает длинный URL с использованием сервиса TinyURL.

    Args:
        long_url (str): Длинный URL для сокращения.

    Returns:
        str | None: Сокращённый URL или `None`, если произошла ошибка.
    """
    url = f'http://tinyurl.com/api-create.php?url={long_url}'
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.text
    return None


if __name__ == "__main__":
    # Получаем строку URL от пользователя
    url = input("Введите URL: ")
    
    # Проверяем валидность URL
    if is_url(url):
        params = extract_url_params(url)
        
        # Выводим параметры
        if params:
            print("Параметры URL:")
            for key, value in params.items():
                print(f"{key}: {value}")
        else:
            print("URL не содержит параметров.")
        
        # Предлагаем пользователю сократить URL
        shorten = input("Хотите сократить этот URL? (y/n): ").strip().lower()
        if shorten == 'y':
            short_url = url_shortener(url)
            if short_url:
                print(f"Сокращённый URL: {short_url}")
            else:
                print("Ошибка при сокращении URL.")
    else:
        print("Введенная строка не является валидным URL.")