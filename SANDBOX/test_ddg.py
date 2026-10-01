# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Sandbox - Test Ddg
# =============================================================================
# Description:
#   Скрипт/модуль системы AI-Breadboard (`test_ddg`).
#
# Usage Examples:
#   Python API:
#     import SANDBOX.test_ddg as test_ddg
#
# File: test_ddg.py
# Project: ai-breadboard
# Package: SANDBOX
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:04
# =============================================================================

"""Скрипт/модуль системы AI-Breadboard (`test_ddg`)."""

import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
url = 'https://lite.duckduckgo.com/lite/'
data = urllib.parse.urlencode({'q': 'карточка сериала сваты'}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a', class_='result-snippet')
        print('result-snippet:', len(links))
        links2 = soup.find_all('a', class_='result-url')
        print('result-url:', len(links2))
        for td in soup.find_all('td', class_='result-snippet'):
            print('td result-snippet text:', td.text[:50])
        for a in soup.find_all('a'):
            if a.get('href') and a.get('href').startswith('http'):
                print('class:', a.get('class'), 'href:', a.get('href'))
                break
except Exception as e:
    print('ERROR:', e)