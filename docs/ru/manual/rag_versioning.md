# Versioned Document RAG & Temporal State Tracking

## 1. Overview & Architecture

The **Versioned Document RAG** subsystem in AI Breadboard provides incremental, temporal, and non-destructive document indexing. It allows the system to ingest documents from local user folders (e.g., `Documents` or Google Drive mounted at `G:\My Drive`), track document changes over time via SHA-256 content hashing, and maintain an immutable historical timeline of chunks and versions in the vector index.

```
User Directory (e.g., G:\My Drive or Documents)
       │
       ▼ (Scan & SHA-256 Hashing)
┌───────────────────────────────────────┐
│     Document Version Registry         │  Tracks mtime, hash, current_version,
│     (document_rag_meta.json)          │  and version history per document.
└───────────────────┬───────────────────┘
                    │
       ┌────────────┴─────────────────────────────┐
       ▼ (File Added or Modified)                 ▼ (File Unchanged)
┌───────────────────────────────────────┐  ┌──────────────────────┐
│ 1. Mark existing chunks as:           │  │ Skip chunking &      │
│    `is_latest = False`                │  │ vectorization        │
│ 2. Create new chunks:                 │  │ (Zero redundant CPU) │
│    `version = N + 1`                  │  └──────────────────────┘
│    `is_latest = True`                 │
│    `version_timestamp = mtime`        │
│ 3. Compute Embeddings & Append Index  │
└───────────────────┬───────────────────┘
                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Unified Vector Store                            │
│  - doc.md#chunk_0#v1  (is_latest: false, ts: 1710000000, version: 1)   │
│  - doc.md#chunk_0#v2  (is_latest: true,  ts: 1712000000, version: 2)   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Models & Metadata

### Chunk Representation (`DocumentChunk`)

```python
@dataclass
class DocumentChunk:
    chunk_id: str             # e.g., "finance/report.md#chunk_0#v2"
    doc_name: str             # e.g., "finance/report.md"
    chunk_index: int          # 0, 1, 2...
    text: str                 # Chunk text content
    start_char: int           # Character start offset in source
    end_char: int             # Character end offset in source
    version: int = 1          # Document version number
    version_timestamp: float  # Epoch timestamp of file modification
    is_latest: bool = True    # True if chunk belongs to latest version
    content_hash: str = ""    # Hex SHA-256 digest of source content
    meta: Dict[str, Any]      # Additional tags and properties
```

### Document Registry Entry (`DocumentInfo`)

```python
@dataclass
class DocumentInfo:
    name: str                 # Relative path or identifier
    size_bytes: int           # File size in bytes
    modified_at: float        # File modification timestamp
    status: str               # 'indexed', 'pending', 'error', 'archived'
    chunks_count: int         # Total chunks in current version
    version: int              # Current latest version number
    is_latest: bool           # Whether document is currently active
    content_hash: str         # Current SHA-256 hash
    versions: List[Dict]      # Full version history timeline
```

---

## 3. Incremental Indexing Algorithm

1. **Hash Calculation**:
   When scanning a folder, `compute_file_hash(path)` calculates the SHA-256 digest of each supported file (`.txt`, `.md`, `.json`, `.csv`, `.pdf`, `.py`, etc.).
2. **Change Detection**:
   - **New Document**: Assigned `version = 1`. Extracted text is split into overlapping chunks, vectorized, and added with `is_latest = True`.
   - **Modified Document**: If the hash differs from the latest indexed version:
     - All previous chunks for this document have their `is_latest` flag toggled to `False`.
     - A new version `version = current_version + 1` is generated.
     - New chunks are embedded and appended to the index with `is_latest = True`.
     - Previous versions remain intact in the index.
   - **Unchanged Document**: Skipped immediately without redundant chunking or embedding computation.
   - **Deleted / Archived Document**: Marked `status = "archived"` and `is_latest = False`. Historical chunks remain queryable if requested.

---

## 4. Multi-Mode Search & Filtering

The search API supports version filtering to prevent obsolete information from polluting ordinary LLM prompts while allowing targeted historical comparisons:

| Mode | Parameter | Description |
|---|---|---|
| **Latest Only** *(Default)* | `version_filter="latest"` | Returns only active, latest version chunks (`is_latest == True`). |
| **All Versions** | `version_filter="all"` | Searches across all versions to compare changes over time or audit history. |
| **Specific Version** | `version_filter="v1"` or `"1"` | Limits search to a specific version number. |
| **Point-in-Time** | `version_filter="<timestamp>"` | Retrieves versions active as of the specified Unix epoch timestamp. |

---

## 5. API Endpoints Reference

### 1. Scan External Directory
`POST /api/rag/scan-directory`
```json
{
  "directory_path": "G:\\My Drive",
  "provider": "local_tfidf",
  "recursive": true,
  "chunk_size": 500,
  "chunk_overlap": 50
}
```

### 2. Search Documents with Version Filter
`POST /api/rag/search`
```json
{
  "query": "financial budget forecast",
  "top_k": 5,
  "version_filter": "latest"
}
```

### 3. Retrieve Document Version History
`GET /api/rag/documents/{filename}/history`

**Sample Response:**
```json
{
  "status": "success",
  "data": {
    "found": true,
    "filename": "finance_report.md",
    "current_version": 2,
    "is_latest": true,
    "total_chunks_stored": 4,
    "versions": [
      {
        "version": 1,
        "modified_at": 1710000000.0,
        "size_bytes": 1240,
        "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "chunks_count": 2
      },
      {
        "version": 2,
        "modified_at": 1712000000.0,
        "size_bytes": 1580,
        "content_hash": "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
        "chunks_count": 2
      }
    ]
  }
}
```

---

## 6. Testing & Verification

Automated test suites:
- `tests/test_document_rag.py`: Unit tests for chunking, hash tracking, CRUD operations, and versioned search.
- `tests/test_versioned_drive_rag.py`: Integration tests for directory lifecycle and Google Drive directory scanning.
- `tests/test_router_rag.py`: REST API endpoint validation.

Run tests:
```powershell
pytest tests/test_document_rag.py tests/test_versioned_drive_rag.py tests/test_router_rag.py -v
```
