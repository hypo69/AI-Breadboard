---
name: rag-search-manager
description: Skill for searching media using RAG index as primary source, with fallback to web search when no matches are found.
description_i18n:
  en: Skill for searching media using RAG index as primary source, with fallback to web search when no matches are found.
  ru: Навык для поиска медиа с использованием RAG-индекса в качестве приоритетного источника, с последующим поиском в интернете при отсутствии совпадений.
---

# RAG Search Manager

## 🚀 Приоритет поиска
1. **RAG Search:** Поиск в локальном RAG-индексе медиатеки.
2. **Internet Search:** Поиск в интернете, если в RAG совпадений не найдено.

## 🛠️ Использование
```bash
python .agents/skills/rag-search-manager/scripts/search_media.py --query "название или запрос"
```
