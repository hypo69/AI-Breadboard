# `webinterface/search_tab` — RAG & Semantic Search Dashboard

## Purpose
Search console enabling users to perform hybrid search across the local media knowledge base, vector embeddings, and web grounding.

---

## Capabilities
- **Semantic RAG Search**: Natural language queries matched against `media.db` and FAISS vector index.
- **Streaming Reasoning Steps**: Real-time display of retrieval confidence scores and reasoning thoughts.
- **Direct Filter Controls**: Filter by media type, release year, genre, and storage drive.

---

## Files
- `index.html`: Search bar, filter toggles, and results grid.
- `main.js`: Search dispatcher and SSE stream handler.
