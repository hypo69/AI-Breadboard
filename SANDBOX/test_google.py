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
        await page.goto(f"https://www.google.com/search?q={encoded_query}&hl=ru", timeout=20000)
        await page.wait_for_timeout(3000)
        
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Google search results usually have links inside div.yuRUbf > a, or just finding 'a' with 'href' that starts with http
        results = []
        for div in soup.find_all('div', class_='yuRUbf'):
            a = div.find('a')
            if a and a.get('href'):
                results.append(a.get('href'))
                
        if not results:
            # Fallback for different google layouts
            for a in soup.find_all('a'):
                href = a.get('href')
                if href and href.startswith('http') and 'google.com' not in href:
                    results.append(href)
                    
        print('LINKS FOUND:', len(results))
        if results: print(results[:3])
        
asyncio.run(main())
