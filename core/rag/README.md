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
| `rules_rag.py` | `RulesRAG`: Semantic index over prompt guidelines (`prompts/`) for dynamic LLM system instruction assembly. |
| `user_rag.py` | `UserRAG`: Semantic search over historical Q&A and user preference profiles. |

---

## Code Usage Examples

### 1. Request Evaluation & Routing with `RAGEngine`:
```python
from core.rag import get_rag_engine

engine = get_rag_engine()
decision = await engine.evaluate(
    query="How do I configure the AI Foundry endpoint?",
    user_identifier="user_123",
    api_key=api_key
)

if decision.is_direct:
    # Instant response retrieved directly from knowledge base
    print("Direct answer:", decision.direct_text)
else:
    # Forward query to LLM with enriched context (decision.context_text)
    response = await chat_model.ask(decision.query, context=decision.context_text)
```

### 2. Dynamic System Prompt Retrieval with `RulesRAG`:
```python
from core.rag import RulesRAG

rules_rag = RulesRAG()
relevant_rules = rules_rag.search("narrator audio tone instructions", top_k=3)
```
