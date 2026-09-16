# Плагин Codebase RAG & Symbol Indexer (generate_rag_from_codebase)

## Назначение
Предоставляет интеллектуальную систему индексации и поиска с учетом контекста кодовой базы для проекта AI Breadboard. Выполняет синтаксическую и семантическую декомпозицию кода (Python), документации (Markdown/RST) и конфигурационных файлов.

## Структура
- `plugins/developer-plugins/generate_rag_from_codebase/`
  - `src/`: Парсеры (AST, Markdown, Config)
  - `data/rag_index/codebase`: Индексы (символьный и векторный)

## Запуск
Используется автоматически при построении RAG-индекса:
```powershell
py manage_tools.py rag build
```

## API
Предоставляет инструменты (tools) для LLM:
- `search_codebase_rag(query: str, top_k: int = 5)`: Семантический поиск.
- `lookup_symbol(symbol: str, exact: bool = False)`: Поиск символов (классы, функции).
