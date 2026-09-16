# `core.rag` Module — Universal RAG Subsystem

## Overview
The `core.rag` module implements a clean, domain-agnostic **"RAG-First"** architecture for processing user requests. Queries are first matched against semantic vector memory and local knowledge bases before invoking expensive LLM generation.

---

## RAG-First Query Pipeline

```
User Query ──► RAGEngine.evaluate() ──► Knowledge Base Semantic Search (RAG)
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
[Exact Match (Score >= threshold)]  [No Direct Match]
        │                           │
        ▼                           ▼
Direct Answer Return (Direct RAG)   LLM Call (with Injected RAG Context)
(Instant response, zero LLM cost)   │
                                    ▼
                          Auto-save Answer to RAG Index
```

---

## Module Structure

| File | Purpose |
|---|---|
| `__init__.py` | Public package API and singleton accessor `get_rag_engine()`. |
| `models.py` | Data models and enums (`RAGDecisionType`, `RAGRouteDecision`, `RAGSearchResult`). |
| `engine.py` | `RAGEngine`: Coordinates knowledge base searches, confidence scoring, and context synthesis. |
| `document_rag.py` | `DocumentRAGManager`: Multi-format document parser, chunking, incremental SHA-256 versioning, directory scanning, and temporal retrieval. |
| `rules_rag.py` | `RulesRAG`: Semantic index over prompt guidelines (`prompts/`) for dynamic LLM system instruction assembly. |
| `user_rag.py` | `UserRAG`: Semantic search over historical Q&A and user preference profiles. |

---

## Versioned Document RAG & Temporal State Tracking

The `DocumentRAGManager` supports non-destructive incremental updates with full historical version tracking:

### Key Features:
- **Chunk Metadata:** Every chunk stores `version`, `version_timestamp`, `is_latest`, and `content_hash` (SHA-256).
- **Non-Destructive Versioning:** When a document changes, older chunks are marked `is_latest = False` and new chunks are indexed with `version = N + 1` and `is_latest = True`.
- **Incremental Directory Scanning:** `scan_and_index_directory(dir_path)` scans any folder (e.g. `G:\My Drive`), detects modifications by SHA-256 digest, and skips unchanged files.
- **Search Filtering:** Search query support for `version_filter="latest"` (default), `"all"`, specific version (`"v1"`, `"v2"`), or point-in-time timestamp.

### Usage Example:
```python
from pathlib import Path
from src.rag.document_rag import get_document_rag_manager

manager = get_document_rag_manager()

# 1. Scan and incrementally index a user folder (e.g., Google Drive)
scan_result = manager.scan_and_index_directory(
    dir_path=Path("G:/My Drive"),
    provider="local_tfidf",
    recursive=True
)
print("Scan summary:", scan_result)

# 2. Search latest active versions
latest_results = manager.search(
    query="annual revenue budget",
    top_k=5,
    version_filter="latest"
)

# 3. Search across all historical versions (e.g. for audit or change diffs)
history_results = manager.search(
    query="annual revenue budget",
    top_k=10,
    version_filter="all"
)

# 4. Inspect complete document version history
history = manager.get_document_history("finance/report_2026.md")
print("Document versions:", history["versions"])
```

