# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Переиндексация контекста разработчика
# =============================================================================
# Описание:
#   Скрипт запускает перестроение RAG-индекса для технического контекста разработки.
#   Индексирует файлы исходного кода Python и документации Markdown из указанного
#   набора директорий, обеспечивая актуальность поиска по кодовой базе.
#
# File: rebuild_dev_rag.py
# Project: ai-breadboard
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
from core.ai.dev_rag import build_dev_rag
from core.logger import logger

def main():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ Ошибка: Переменная окружения GEMINI_API_KEY не установлена.")
        return

    print("🔄 Запуск переиндексации кодовой базы и документации...")
    try:
        build_dev_rag(api_key)
        print("✅ Индекс разработчика успешно перестроен.")
    except Exception as e:
        print(f"❌ Ошибка при переиндексации: {e}")
        logger.error(f"Ошибка rebuild_dev_rag: {e}", exc_info=True)

if __name__ == "__main__":
    main()
