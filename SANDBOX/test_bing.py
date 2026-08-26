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
        await page.goto(f"https://www.bing.com/search?q={encoded_query}", timeout=20000)
        await page.wait_for_timeout(3000)
        
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        results = []
        for a in soup.find_all('a'):
            href = a.get('href')
            # typical bing organic result has an h2 inside it
            if href and href.startswith('http') and 'bing.com' not in href and 'microsoft.com' not in href:
                if a.find('h2'):
                    results.append(href)
                    
        print('LINKS FOUND:', len(results))
        if results: print(results[:3])
        
asyncio.run(main())
