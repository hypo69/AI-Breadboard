import argparse
import sys
from pathlib import Path
import json
import os
from dotenv import load_dotenv
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.ai.gemini.user_query_rag import search_user_context
from plugins.web_search import WebSearchPlugin
load_dotenv(Path(__file__).resolve().parents[3] / '.env')

async def search_media(query):
    print(f"🔍 Начинаю поиск: '{query}'")
    print('🤖 Проверяю RAG...')
    try:
        user_id = 'default_user'
        api_key = os.getenv('AGY_API_KEY')
        if not api_key:
            print('⚠️ API ключ не найден в .env.')
        else:
            results = search_user_context(user_id, api_key, query, top_k=3, threshold=0.3)
            if results:
                print(f'✅ Найдено в RAG: {json.dumps(results, indent=2, ensure_ascii=False)}')
                return
            else:
                print('ℹ️ В RAG ничего не найдено.')
    except Exception as e:
        print(f'⚠️ Error при поиске в RAG: {e}')
    print('🌐 RAG не дал результатов. Ищу в интернете...')
    try:
        search_plugin = WebSearchPlugin()
        results = await search_plugin.search(query)
        if results:
            print(f'✅ Найдено в интернете: {json.dumps(results, indent=2, ensure_ascii=False)}')
        else:
            print('❌ В интернете ничего не найдено.')
    except Exception as e:
        print(f'⚠️ Error при поиске в интернете: {e}')
if __name__ == '__main__':
    import asyncio
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', required=True, help='Запрос для поиска')
    args = parser.parse_args()
    asyncio.run(search_media(args.query))