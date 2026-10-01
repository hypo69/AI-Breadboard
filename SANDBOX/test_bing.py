# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Sandbox - Test Bing
# =============================================================================
# Description:
#   Скрипт/модуль системы AI-Breadboard (`test_bing`).
#
# Usage Examples:
#   CLI:
#     python -m SANDBOX.test_bing
#   Python API:
#     import SANDBOX.test_bing as test_bing
#
# File: test_bing.py
# Project: ai-breadboard
# Package: SANDBOX
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:30:04
# =============================================================================

"""Скрипт/модуль системы AI-Breadboard (`test_bing`)."""

import asyncio
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True, locale='ru-RU')
        page = await context.new_page()
        encoded_query = urllib.parse.quote_plus('карточка сериала сваты')
        await page.goto(f'https://www.bing.com/search?q={encoded_query}', timeout=20000)
        await page.wait_for_timeout(3000)
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        for a in soup.find_all('a'):
            href = a.get('href')
            if href and href.startswith('http') and ('bing.com' not in href) and ('microsoft.com' not in href):
                if a.find('h2'):
                    results.append(href)
        print('LINKS FOUND:', len(results))
        if results:
            print(results[:3])
asyncio.run(main())