---
name: rag-search-manager
description: Навык для поиска медиа с использованием RAG-индекса в качестве приоритетного источника, с последующим поиском в интернете при отсутствии совпадений.
---

# RAG Search Manager

## 🚀 Приоритет поиска
1. **RAG Search:** Поиск в локальном RAG-индексе медиатеки.
2. **Internet Search:** Поиск в интернете, если в RAG совпадений не найдено.

## 🛠️ Использование
```bash
python .gemini\skills\rag-search-manager\scripts\search_media.py --query "название или запрос"
```
