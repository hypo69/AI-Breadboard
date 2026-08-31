# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Переиндексация контекста разработчика
# =============================================================================
# Description:
#   Скрипт запускает перестроение RAG-индекса для технического контекста разработки.
#
# File: rebuild_dev_rag.py
# Project: ai-breadboard
# Package: .ai.tools.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
from core.ai.dev_rag import build_dev_rag
from core.logger import logger

def main():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ Error: Переменная окружения GEMINI_API_KEY не установлена.")
        return

    print("🔄 Запуск переиндексации кодовой базы и документации...")
    try:
        build_dev_rag(api_key)
        print("✅ Индекс разработчика successfully перестроен.")
    except Exception as e:
        print(f"❌ Error при переиндексации: {e}")
        logger.error(f"Error rebuild_dev_rag: {e}", exc_info=True)

if __name__ == "__main__":
    main()
