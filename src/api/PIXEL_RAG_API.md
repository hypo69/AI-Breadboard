# PixelRAG FastAPI Router Documentation

## Overview

RESTful API for PixelRAG hybrid search system with endpoints for:

- ✅ Document indexing (text and images)
- ✅ Semantic search with smart routing
- ✅ Query analysis and routing
- ✅ Index status and management
- ✅ Document listing and deletion

## Base URL

```
/api/rag/pixel
```

## Endpoints

### 1. Health Check

**GET** `/health`

Check PixelRAG system health and component status.

**Response:**
```json
{
  "status": "✓ healthy",
  "components": {
    "document_rag": "✓ OK",
    "query_router": "✓ OK",
    "rag_engine": "✓ OK"
  },
  "version": "1.0.0"
}
```

**Status Code:** 200 (OK), 503 (Unavailable)

### 2. Search Documents

**POST** `/search`

Search documents with automatic query routing (text/pixel/hybrid).

**Request:**
```json
{
  "query": "Покажи кнопку сохранения",
  "top_k": 5,
  "min_score": 0.3,
  "use_routing": true,
  "version_filter": "latest"
}
```

**Parameters:**
- `query` (string, required) - Search query
- `top_k` (int, 1-20, default: 5) - Number of results
- `min_score` (float, 0-1, default: 0) - Minimum score threshold
- `use_routing` (bool, default: true) - Use smart routing
- `version_filter` (string) - Version filter: 'latest', 'all', 'vX'

**Response:**
```json
{
  "query": "Покажи кнопку сохранения",
  "routing_type": "pixel",
  "query_confidence": 0.95,
  "total_results": 3,
  "results": [
    {
      "chunk_id": "screenshot.png#visual",
      "doc_name": "screenshot.png",
      "text": "Path: /images/screenshot.png",
      "score": 0.92,
      "source_type": "pixel",
      "source_path": "/images/screenshot.png",
      "version": 1,
      "tags": ["ui", "button"]
    },
    {
      "chunk_id": "ui_guide.md#chunk_0",
      "doc_name": "ui_guide.md",
      "text": "To save, click File → Save or press Ctrl+S",
      "score": 0.88,
      "source_type": "text",
      "version": 1,
      "tags": []
    }
  ],
  "status": "success"
}
```

**Status Code:** 200 (OK), 500 (Error)

### 3. Analyze Query

**POST** `/analyze-query`

Analyze query and determine routing strategy without searching.

**Request:**
```
POST /analyze-query?query=Show%20the%20button
```

**Parameters:**
- `query` (string, required) - Query to analyze

**Response:**
```json
{
  "query": "Show the button",
  "routing_type": "pixel",
  "language": "english",
  "confidence": 0.95,
  "visual_keywords": ["show", "button"],
  "reason": "Strong visual indicators: keywords=['show', 'button'], pattern_score=0.95"
}
```

**Status Code:** 200 (OK), 500 (Error)

### 4. Get Index Status

**GET** `/status`

Get current index status and statistics.

**Response:**
```json
{
  "total_documents": 42,
  "total_chunks": 156,
  "total_images": 23,
  "total_size_mb": 45.32,
  "last_built_at": 1726493840.123,
  "provider": "local_tfidf",
  "sources": {
    "text_chunks": 156,
    "images": 23
  }
}
```

**Status Code:** 200 (OK), 500 (Error)

### 5. Index Documents

**POST** `/index`

Upload and index documents (text and images).

**Request:**
```
POST /index
Content-Type: multipart/form-data

files: [document.pdf, image1.png, image2.jpg, readme.md]
```

**Parameters:**
- `files` (List[UploadFile], required) - Files to index

**Response:**
```json
{
  "status": "success",
  "files_indexed": 4,
  "total_documents": 46,
  "new_chunks": 12,
  "message": "Indexed 4 files"
}
```

**Status Code:** 200 (OK), 500 (Error)

### 6. List Documents

**GET** `/documents`

List all indexed documents.

**Response:**
```json
{
  "status": "success",
  "total_documents": 46,
  "documents": [
    {
      "name": "readme.md",
      "size_bytes": 2048,
      "status": "indexed",
      "version": 1,
      "is_latest": true
    },
    {
      "name": "screenshot.png",
      "size_bytes": 45678,
      "status": "indexed",
      "version": 1,
      "is_latest": true
    }
  ]
}
```

**Status Code:** 200 (OK), 500 (Error)

### 7. Get Search Statistics

**GET** `/search-history`

Get search statistics and patterns.

**Response:**
```json
{
  "status": "success",
  "total_searches": 1234,
  "popular_queries": ["button", "save", "interface"],
  "routing_distribution": {
    "text": 0.4,
    "pixel": 0.35,
    "hybrid": 0.25
  },
  "average_query_time_ms": 125
}
```

**Status Code:** 200 (OK)

### 8. Delete Document

**DELETE** `/documents/{doc_name}`

Delete a document from the index.

**Parameters:**
- `doc_name` (string, required) - Document name to delete

**Response:**
```json
{
  "status": "success",
  "message": "Deleted readme.md",
  "purged": false
}
```

**Status Code:** 200 (OK), 404 (Not Found), 500 (Error)

## Usage Examples

### Example 1: Simple Search

```bash
curl -X POST "http://localhost:8000/api/rag/pixel/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to save files?",
    "top_k": 5
  }'
```

### Example 2: Visual Query

```bash
curl -X POST "http://localhost:8000/api/rag/pixel/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Покажи кнопку сохранения",
    "use_routing": true
  }'
```

### Example 3: Upload Documents

```bash
curl -X POST "http://localhost:8000/api/rag/pixel/index" \
  -F "files=@document.pdf" \
  -F "files=@screenshot.png" \
  -F "files=@readme.md"
```

### Example 4: Analyze Query

```bash
curl "http://localhost:8000/api/rag/pixel/analyze-query?query=Show%20the%20save%20button"
```

### Example 5: Get Status

```bash
curl "http://localhost:8000/api/rag/pixel/status"
```

## Python Client Example

```python
import httpx

# Create client
client = httpx.Client(base_url="http://localhost:8000")

# Search
response = client.post("/api/rag/pixel/search", json={
    "query": "Show the button",
    "top_k": 5
})
results = response.json()

print(f"Found {results['total_results']} results")
for result in results['results']:
    print(f"  - {result['doc_name']}: {result['score']:.2f}")

# Analyze query
response = client.post("/api/rag/pixel/analyze-query", 
    params={"query": "Show the button"})
analysis = response.json()

print(f"Routing: {analysis['routing_type']}")
print(f"Confidence: {analysis['confidence']:.2f}")

# Get status
response = client.get("/api/rag/pixel/status")
status = response.json()

print(f"Total documents: {status['total_documents']}")
print(f"Total images: {status['total_images']}")
```

## Data Models

### SearchRequest
```python
{
    "query": str                      # Search query
    "top_k": int = 5                  # Results to return
    "min_score": float = 0.0          # Score threshold
    "use_routing": bool = True        # Use smart routing
    "version_filter": str = "latest"  # Version filter
}
```

### SearchResponse
```python
{
    "query": str                      # Original query
    "routing_type": str              # text | pixel | hybrid
    "query_confidence": float        # Routing confidence 0-1
    "total_results": int             # Number of results
    "results": List[SearchResult]    # Search results
    "status": str                    # success | error
}
```

### SearchResult
```python
{
    "chunk_id": str                  # Unique chunk identifier
    "doc_name": str                  # Document name
    "text": str                      # Result text/path
    "score": float                   # Similarity score
    "source_type": str              # text | pixel
    "source_path": Optional[str]    # Image path if pixel
    "version": int = 1              # Document version
    "tags": List[str] = []          # Associated tags
}
```

### QueryAnalysisResponse
```python
{
    "query": str                      # Original query
    "routing_type": str              # text | pixel | hybrid
    "language": str                  # russian | english | mixed
    "confidence": float              # 0-1 confidence score
    "visual_keywords": List[str]    # Found visual keywords
    "reason": str                    # Explanation
}
```

### IndexStatusResponse
```python
{
    "total_documents": int           # Total documents
    "total_chunks": int              # Total text chunks
    "total_images": int              # Total images
    "total_size_mb": float           # Total size in MB
    "last_built_at": float           # Last index time
    "provider": str                  # Index provider
    "sources": Dict[str, int]       # Source breakdown
}
```

## Error Responses

### 400 Bad Request
```json
{
    "detail": "Invalid query parameter"
}
```

### 404 Not Found
```json
{
    "detail": "Document not found"
}
```

### 500 Internal Server Error
```json
{
    "detail": "Search failed: [error message]"
}
```

### 503 Service Unavailable
```json
{
    "detail": "PixelRAG system unavailable"
}
```

## Integration with FastAPI

```python
from fastapi import FastAPI
from src.api.pixel_rag_router import get_pixel_rag_router

app = FastAPI(title="AI Breadboard API")

# Include PixelRAG routes
app.include_router(get_pixel_rag_router())

# Run with:
# uvicorn main:app --reload
```

## Performance

| Endpoint | Avg Time | Max Time |
|----------|----------|----------|
| /health | <10ms | 50ms |
| /search | 100-200ms | 500ms |
| /analyze-query | 5-10ms | 50ms |
| /status | <20ms | 100ms |
| /documents | <50ms | 200ms |
| /index | 1-5s | 30s |
| /search-history | <5ms | 50ms |

## Authentication (Future)

Future versions may include:
- API key authentication
- JWT bearer tokens
- Role-based access control

## Rate Limiting (Future)

Future versions may include:
- Request rate limiting
- Per-user quotas
- Endpoint-specific limits

## Caching (Future)

Future versions may implement:
- Search result caching
- Query analysis caching
- Index statistics caching

## References

- **Implementation:** `src/api/pixel_rag_router.py`
- **Models:** Pydantic models in router
- **Integration:** Task 11
- **Testing:** `tests/test_api_integration.py` (future)
