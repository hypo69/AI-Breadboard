# RAGEngine Integration with QueryRouter

## Overview

RAGEngine has been extended with smart document search capabilities that leverage QueryRouter for intelligent routing:

- ✅ Unified search interface for documents (text and images)
- ✅ Automatic query routing (text/pixel/hybrid) 
- ✅ Direct answer detection from document search
- ✅ Context building for LLM fallback
- ✅ Confidence-based decision making

## Architecture

```
User Query
    ↓
┌──────────────────────────────────┐
│ RAGEngine.search_documents()     │
└──────────────────────────────────┘
    ↓
    ├─→ QueryRouter.analyze()
    │   └─→ Determine routing strategy
    │
    ├─→ DocumentRAGManager.search()
    │   ├─→ Text search (if routing=text/hybrid)
    │   └─→ Image search (if routing=pixel/hybrid)
    │
    ├─→ Filter results (based on routing)
    │
    └─→ Build RAGRouteDecision
        ├─→ Direct answer (if score >= 0.90)
        └─→ LLM context (if score < 0.90)
```

## API

### New Method: `search_documents()`

```python
async def search_documents(
    query: str,
    top_k: int = 5,
    min_score: float = 0.0,
    api_key: str = "",
    use_routing: bool = True
) -> RAGRouteDecision
```

**Parameters:**
- `query` - User query string
- `top_k` - Maximum results per provider (default: 5)
- `min_score` - Minimum similarity threshold (default: 0.0)
- `api_key` - Optional Gemini API key for text embeddings
- `use_routing` - Use QueryRouter for smart routing (default: True)

**Returns:**
- `RAGRouteDecision` with search results and routing metadata

## Routing Strategy

### Text-Only Routing (text)
**When:** Query is clearly text-based
- "Объясни как работает система"
- "What is REST API?"

**Behavior:**
```python
# Only search text documents
results = doc_rag.search(query)
results = [r for r in results if r['source_type'] == 'text']
```

### Image-Only Routing (pixel)
**When:** Query is clearly asking for visual information
- "Покажи кнопку сохранения"
- "Show me the save button"

**Behavior:**
```python
# Only search images
results = doc_rag.search(query)
results = [r for r in results if r['source_type'] == 'pixel']
```

### Hybrid Routing (hybrid)
**When:** Query has mixed intent or is ambiguous
- "Покажи кнопку и объясни как её использовать"
- "Show the button and explain what it does"

**Behavior:**
```python
# Search both text and images
results = doc_rag.search(query)
# No filtering - return all results
```

## Decision Making

### High Confidence Direct Answer
**Condition:** `score >= 0.90 && source_type == 'text'`
**Decision:** `DIRECT_ANSWER`
**Action:** Return answer directly to user

```python
RAGRouteDecision(
    decision_type=RAGDecisionType.DIRECT_ANSWER,
    is_direct=True,
    direct_text="Answer from document",
    confidence_score=0.95,
    status_message="📚 Found in documents"
)
```

### Context for LLM
**Condition:** `score < 0.90 || source_type == 'pixel'`
**Decision:** `LLM_FALLBACK`
**Action:** Build context from search results, let LLM generate answer

```python
RAGRouteDecision(
    decision_type=RAGDecisionType.LLM_FALLBACK,
    is_direct=False,
    context_text="[Query Analysis]\nRouting: pixel\n...\n[Search Results]:\n...",
    confidence_score=0.85,
    status_message="📚 Found 3 document matches"
)
```

### No Results
**Condition:** `len(results) == 0`
**Decision:** `LLM_FALLBACK`
**Action:** Empty context, LLM generates from knowledge only

```python
RAGRouteDecision(
    decision_type=RAGDecisionType.LLM_FALLBACK,
    is_direct=False,
    context_text="[Query Analysis]\nNo matches found",
    confidence_score=0.0,
    status_message="No matches in document search"
)
```

## Usage Examples

### Basic Document Search

```python
from src.rag.engine import get_rag_engine

engine = get_rag_engine()

# Search with smart routing
result = await engine.search_documents(
    query="Покажи кнопку сохранения",
    top_k=5
)

print(f"Decision: {result.decision_type.value}")
print(f"Confidence: {result.confidence_score:.2f}")
print(f"Status: {result.status_message}")

if result.is_direct:
    print(f"Direct answer: {result.direct_text}")
else:
    print(f"Context for LLM:\n{result.context_text}")
```

### Disable Routing

```python
# Search with hybrid routing (always search both)
result = await engine.search_documents(
    query="Find the button",
    use_routing=False  # Force hybrid search
)
```

### With Gemini API Key

```python
# Use Gemini for text embeddings
result = await engine.search_documents(
    query="How to save files?",
    api_key="sk-...",
    top_k=10,
    min_score=0.3
)
```

## Output Format

### RAGRouteDecision Response

```python
@dataclass
class RAGRouteDecision:
    decision_type: RAGDecisionType         # DIRECT_ANSWER | LLM_FALLBACK
    is_direct: bool                       # True if direct answer
    direct_text: str                      # Direct answer text
    direct_voice: str                     # Voice-friendly version
    context_text: str                     # Context for LLM
    confidence_score: float               # 0.0-1.0
    raw_results: List[Dict]               # Raw search results (top 3)
    status_message: str                   # Human-readable status
```

### Response Example

```json
{
  "decision_type": "llm_fallback",
  "is_direct": false,
  "confidence_score": 0.85,
  "status_message": "📚 Found 5 document matches",
  "context_text": "[Query Analysis]\nLanguage: russian\nRouting: hybrid\nConfidence: 0.80\nVisual keywords: покажи, кнопку\n\n[Search Results]:\n1. [ui_guide.md] (score=0.92)\nHow to use the save button...\n\n2. [IMAGE: screenshot.png] (score=0.88)\nPath: /docs/screenshots/screenshot.png",
  "raw_results": [
    {
      "chunk_id": "ui_guide.md#chunk_0",
      "doc_name": "ui_guide.md",
      "text": "...",
      "score": 0.92,
      "source_type": "text"
    },
    {
      "chunk_id": "screenshot.png#visual",
      "doc_name": "screenshot.png",
      "source_path": "/docs/screenshots/screenshot.png",
      "score": 0.88,
      "source_type": "pixel"
    }
  ]
}
```

## Logging

RAGEngine logs routing decisions:

```
[RAGEngine] Query routing: hybrid (confidence=0.80) - Moderate visual indicators
[RAGEngine] Search returned 5 results (Hybrid search (no filtering))
[RAGEngine] Using document search results as LLM context
```

For debugging, enable INFO level logging:

```python
import logging
logging.getLogger('src.rag').setLevel(logging.INFO)
```

## Integration with Document Workflow

### 1. Build Index First

```python
from src.rag import DocumentRAGManager

doc_rag = DocumentRAGManager(
    docs_dir="./documents",
    index_dir="./indices"
)

# Index documents (text and images)
result = doc_rag.build_index(provider='auto')
print(f"Indexed {result['total_documents']} documents")
```

### 2. Search with RAGEngine

```python
from src.rag.engine import get_rag_engine

engine = get_rag_engine()

# Search with smart routing
rag_result = await engine.search_documents(
    query="Find the save button",
    top_k=5
)

# Use decision for next action
if rag_result.is_direct:
    send_to_user(rag_result.direct_text)
else:
    llm_response = await llm.generate(
        query=query,
        context=rag_result.context_text
    )
    send_to_user(llm_response)
```

### 3. Full Pipeline Example

```python
from src.rag import DocumentRAGManager
from src.rag.engine import get_rag_engine

async def answer_question(question: str) -> str:
    # 1. Search documents with smart routing
    engine = get_rag_engine()
    result = await engine.search_documents(question, top_k=5)
    
    # 2. Return direct answer if found
    if result.is_direct:
        return result.direct_text
    
    # 3. Otherwise, generate with LLM
    from src.ai.gemini import get_gemini_client
    client = get_gemini_client("api-key")
    
    response = client.generate(
        prompt=question,
        context=result.context_text
    )
    return response
```

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Query analysis (QueryRouter) | 5-10ms | Negligible |
| Document search | 50-200ms | Depends on index size |
| Result filtering | <1ms | Linear in result count |
| Context building | 1-5ms | Text serialization |
| **Total** | **60-220ms** | Fast, suitable for real-time |

## Error Handling

### No Documents Indexed
```python
# Returns empty results, LLM_FALLBACK decision
result = await engine.search_documents("query")
# → decision_type = LLM_FALLBACK
# → confidence_score = 0.0
# → status_message = "No matches in document search"
```

### Invalid Query
```python
result = await engine.search_documents("")
# → Returns early with empty decision
```

### API Errors
```python
# Gracefully handled by DocumentRAGManager
# Falls back to local TF-IDF if Gemini fails
```

## Configuration

### Query Router Configuration
See `src/rag/QUERY_ROUTER.md` for keyword customization

### Search Parameters
```python
result = await engine.search_documents(
    query="...",
    top_k=5,           # Results per provider
    min_score=0.3,     # Minimum similarity
    api_key="",        # Gemini key (optional)
    use_routing=True   # Use smart routing
)
```

## Future Enhancements

1. **Caching** - Cache frequent queries
2. **Multi-turn** - Track conversation context
3. **User preferences** - Personalized routing
4. **Metrics** - Track routing accuracy
5. **Feedback loop** - Learn from corrections

## Testing

Run integration tests:
```bash
pytest tests/test_rag_engine_integration.py -v
```

## References

- **Implementation:** `src/rag/engine.py`
- **QueryRouter:** `src/rag/query_router.py`
- **DocumentRAGManager:** `src/rag/document_rag.py`
- **Models:** `src/rag/models.py`
- **Task 8 Docs:** `jupyter_notebooks/Task8_RAGEngine_Integration.md`
