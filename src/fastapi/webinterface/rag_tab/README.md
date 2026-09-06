# RAG Tab Web Interface

## Overview
Provides an interactive web interface for managing knowledge base documents, configuring vector indexing settings, triggering embeddings building, and testing semantic similarity search in AI Breadboard.

## Features
- **Drag & Drop Document Upload**: Upload `.txt`, `.md`, `.json`, `.csv`, `.pdf`, and source code files directly to the server.
- **Documents Manager**: View uploaded document list, file sizes, chunk counts, index status, and delete documents.
- **Vector Index Configuration**: Switch between Google Gemini Embeddings and offline Local TF-IDF, customize chunk sizes and overlaps.
- **Semantic Search Playground**: Test semantic search queries with customizable Top-K and similarity thresholds, with direct score inspection and chunk previews.

## Endpoints Used
- `POST /api/rag/upload` — Multi-file upload
- `GET /api/rag/documents` — Catalog of knowledge base files
- `DELETE /api/rag/documents/{filename}` — Remove file from knowledge base
- `POST /api/rag/build` — Trigger vectorization & chunking
- `GET /api/rag/status` — Current index metrics
- `POST /api/rag/search` — Perform similarity search
