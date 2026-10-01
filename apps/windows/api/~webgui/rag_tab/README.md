# RAG Tab Web Interface

## Overview
Provides an interactive web interface for managing knowledge base documents, workspace Multi-RAG collections, codebase AST indexes, configuring vector indexing settings, triggering embeddings building, and testing semantic similarity search in AI Breadboard.

## Modular Architecture

The frontend logic follows the single-responsibility principle with each module strictly under 300 lines:

```
rag_tab/
├── modules/
│   ├── utils.js        # Formatting (formatBytes, escapeHtml) and file traversal / DnD helpers
│   ├── docRag.js       # Global Document RAG: upload, status, document listing, indexing, search
│   ├── codebaseRag.js  # Codebase AST RAG: AST index retrieval, AST building, code search, symbol lookup
│   └── userRag.js      # User Workspace Multi-RAG: collections CRUD, storage file checklist, pipeline build, search
├── main.js             # Master coordinator, DOM event wiring, and window.initRagTab entry point
├── index.html          # UI Layout
└── README.md           # This documentation
```

### Module Responsibilities

1. **`modules/utils.js`**
   - Human-readable byte formatting (`formatBytes`).
   - XSS sanitization (`escapeHtml`).
   - Recursive directory and file drag-and-drop traversal (`getAllFilesFromDataTransfer`, `traverseEntry`).

2. **`modules/docRag.js`**
   - File/folder upload to global document RAG storage.
   - Global RAG status polling and document catalog management.
   - Vector index generation with selectable embeddings providers (Gemini / TF-IDF).
   - Global similarity query playground.

3. **`modules/codebaseRag.js`**
   - Multi-project codebase AST index loading and selector population.
   - AST-based symbol parsing and code index building.
   - Semantic code search and AST symbol lookup.

4. **`modules/userRag.js`**
   - User workspace Multi-RAG collection management (CRUD).
   - Workspace file selector and checklist integration.
   - RAG pipeline execution (document cleaning with `rag_cleaner` and TF-IDF index building).
   - Workspace collection semantic query testing.

5. **`main.js`**
   - Central coordinator orchestrating submodules.
   - Attaches event listeners for navigation, modals, upload inputs, and action buttons.
   - Exposes global hooks `window.initRagTab` and `window.deleteRagDocument`.

## Endpoints Used
- `GET /api/user/rags` — List user workspace RAG collections
- `POST /api/user/rags` — Create new workspace RAG collection
- `GET /api/user/rags/{id}` — Get workspace RAG collection details
- `DELETE /api/user/rags/{id}` — Delete workspace RAG collection
- `POST /api/user/rags/{id}/build` — Clean documents and build workspace RAG index
- `POST /api/user/rags/{id}/search` — Search in workspace RAG collection
- `GET /api/user/files` — List user workspace storage files
- `POST /api/user/files/upload` — Upload files to user workspace storage
- `POST /api/rag/upload` — Multi-file upload for global documents
- `GET /api/rag/documents` — Catalog of global knowledge base files
- `DELETE /api/rag/documents/{filename}` — Remove file from global knowledge base
- `POST /api/rag/build` — Trigger global vectorization & chunking
- `GET /api/rag/status` — Global index metrics
- `POST /api/rag/search` — Perform global similarity search
- `GET /api/rag/codebase/indexes` — List codebase AST indexes
- `POST /api/rag/codebase/build` — Build codebase AST and semantic index
- `POST /api/rag/codebase/search` — Perform semantic search on codebase
- `POST /api/rag/codebase/symbols` — Search AST symbols table
