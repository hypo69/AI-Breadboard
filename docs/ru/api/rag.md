# RAG — база знаний и семантический поиск

## RAGEngine

Координатор RAG-First пайплайна. Сначала ищет готовый ответ в базе знаний, при низкой уверенности — передаёт контекст в LLM.

::: src.rag.engine.RAGEngine
    options:
      members:
        - __init__
        - evaluate

::: src.rag.engine.get_rag_engine

---

## DocumentRAGManager

Управляет версионированным парсингом, чанкованием, инкрементальным сканированием директорий и поиском с фильтрацией по времени и версиям. Подробное руководство: [Версионированный Document RAG](../rag_versioning.md).

::: src.rag.document_rag.DocumentRAGManager
    options:
      members:
        - __init__
        - save_document
        - scan_and_index_directory
        - build_index
        - search
        - get_document_history
        - delete_document
        - list_documents

---

## UserWorkspaceRAGManager

::: src.rag.user_workspace_rag.UserWorkspaceRAGManager
    options:
      members:
        - create_collection
        - build_collection
        - search_collection
        - sync_google_docs
        - list_collections
        - delete_collection
        - add_qa_entry

---

## Модели данных

::: src.rag.models.RAGRouteDecision

::: src.rag.models.RAGSearchResult

::: src.rag.models.RAGDecisionType
