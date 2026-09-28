import os
from src.ai.dev_rag import build_dev_rag
from logger import logger

def main():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print('❌ Error: GEMINI_API_KEY environment variable not set.')
        return
    print('🔄 Starting codebase and documentation reindexing...')
    try:
        build_dev_rag(api_key)
        print('✅ Developer index successfully rebuilt.')
    except Exception as e:
        print(f'❌ Error during reindexing: {e}')
        logger.error(f'Error rebuild_dev_rag: {e}', exc_info=True)
if __name__ == '__main__':
    main()