import asyncio
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True, locale='ru-RU')
        page = await context.new_page()
        
        encoded_query = urllib.parse.quote_plus("карточка сериала сваты")
        await page.goto(f"https://duckduckgo.com/html/?q={encoded_query}", timeout=20000)
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        results = []
        for a in soup.find_all('a'):
            href = a.get('href')
            if href and href.startswith('http'):
                results.append(href)
                    
        print('LINKS FOUND:', len(results))
        if results: print(results[:3])
        
        # Save html to examine
        with open('search_test.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
asyncio.run(main())
