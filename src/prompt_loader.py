# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Prompt loader and RAG semantic search integration
# =============================================================================
# Description:
#   Module for loading system prompts for AI agents with FAISS-based semantic search.
#   Provides both RAG-mode (with semantic search) and static fallback mode.
#
# File: prompt_loader.py
# Project: ai-breadboard
# Package: src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import sys
from dataclasses import dataclass
from pathlib import Path

## Base paths
_PROMPTS_ROOT: Path = Path(__file__).resolve().parent.parent / "prompts"
_RAG_DIR: Path = Path(__file__).resolve().parent.parent / "tmp" / "rag"
_INDEX_PATH: Path = _RAG_DIR / "rules.index"
_DOCUMENTS_PATH: Path = _RAG_DIR / "documents.json"

## Embeddings model (same as in build_rules_index.py)
_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

## Modules common to both agents (static mode)
_CORE_MODULES: list[str] = [
    "core/identity.md",
    "core/categories.md",
]

## Modules only for chat agent (static mode)
_CHAT_MODULES: list[str] = [
    "chat/chat_rules.md",
    "narrator/narrator_style.md",
]

## Modules only for narrator agent (static mode)
_NARRATOR_MODULES: list[str] = [
    "narrator/tts_rules.md",
    "narrator/narrator_style.md",
]

## Example (static mode)
_EXAMPLE_MODULE: str = "examples/series_example.json"

## JSON schema (static mode)
_SCHEMA_MODULE: str = "core/output_schema.json"

## Files always included in RAG prompt (regardless of search).
## Only small base modules — schema and examples are fetched via FAISS.
_ALWAYS_INCLUDE: list[str] = [
    "identity.md",
    "categories.md",
]

## ---------------------------------------------------------------------------
## Helper functions
## ---------------------------------------------------------------------------

def _read_file(relative_path: str) -> str:
    """
    Read file from prompts directory.

    Args:
        relative_path (str): Path relative to _PROMPTS_ROOT.

    Returns:
        str: File content.

    Raises:
        FileNotFoundError: If file not found.
    """
    full_path: Path = _PROMPTS_ROOT / relative_path
    if not full_path.exists():
        raise FileNotFoundError(f"Prompt module not found: {full_path}")
    return full_path.read_text(encoding="utf-8")

def _load_modules(module_paths: list[str]) -> str:
    """
    Load and concatenate multiple prompt modules.

    Args:
        module_paths (list[str]): List of relative paths to modules.

    Returns:
        str: Combined content of all modules.
    """
    parts: list[str] = [_read_file(p).strip() for p in module_paths]
    return "\n\n---\n\n".join(parts)

def _load_schema_block() -> str:
    """
    Load JSON schema and wrap in markdown block.

    Returns:
        str: String with JSON schema in markdown wrapper.
    """
    raw: str = _read_file(_SCHEMA_MODULE)
    parsed: dict = json.loads(raw)
    formatted: str = json.dumps(parsed, ensure_ascii=False, indent=2)
    return f"## JSON Response Schema\n\n```json\n{formatted}\n```"

def _load_example_block() -> str:
    """
    Load example JSON and wrap in markdown block.

    Returns:
        str: String with example in markdown wrapper.
    """
    raw: str = _read_file(_EXAMPLE_MODULE)
    parsed: dict = json.loads(raw)
    formatted: str = json.dumps(parsed, ensure_ascii=False, indent=2)
    return f"## Example Filled Response (Series)\n\n```json\n{formatted}\n```"

## ---------------------------------------------------------------------------
## RulesRAG — semantic search class
## ---------------------------------------------------------------------------

from src.rag.rules_rag import RulesRAG, RulesSearchResult

# Alias for backward compatibility
SearchResult = RulesSearchResult

## ---------------------------------------------------------------------------
## Public prompt building functions (RAG mode)
## ---------------------------------------------------------------------------

def load_chat_prompt(query: str = "Create media description for chat") -> str:
    """
    Build system prompt for Chat Agent via FAISS search.

    Args:
        query (str): Query used to select relevant modules.
                     Default: universal query for chat agent.

    Returns:
        str: Ready system prompt for chat agent (~5,000–8,000 characters).
    """
    rag: RulesRAG = RulesRAG()
    context: str = rag.build_context(query, top_k=4)
    return context

def load_narrator_prompt(query: str = "Prepare text for voice narrator TTS") -> str:
    """
    Build system prompt for Narrator Agent via FAISS search.

    Args:
        query (str): Query used to select relevant modules.
                     Default: query for TTS mode.

    Returns:
        str: Ready system prompt for narrator agent (~5,000–8,000 characters).
    """
    rag: RulesRAG = RulesRAG()
    context: str = rag.build_context(query, top_k=4)
    return context

## ---------------------------------------------------------------------------
## Static fallback functions (without FAISS)
## ---------------------------------------------------------------------------

def load_chat_prompt_static() -> str:
    """
    Build complete prompt for Chat Agent from files without FAISS.

    Used as fallback if index not built.

    Returns:
        str: Complete prompt for chat agent (~20,000 characters).
    """
    sections: list[str] = [
        _load_modules(_CORE_MODULES),
        _load_schema_block(),
        _load_modules(_CHAT_MODULES),
        _load_example_block(),
    ]
    return "\n\n---\n\n".join(sections)

def load_narrator_prompt_static() -> str:
    """
    Build complete prompt for Narrator Agent from files without FAISS.

    Used as fallback if index not built.

    Returns:
        str: Complete prompt for narrator agent (~20,000 characters).
    """
    sections: list[str] = [
        _load_modules(_CORE_MODULES),
        _load_schema_block(),
        _load_modules(_NARRATOR_MODULES),
        _load_example_block(),
    ]
    return "\n\n---\n\n".join(sections)

## ---------------------------------------------------------------------------
## Entry point — quick check
## ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    print("=== Static Mode ===")
    chat_s: str = load_chat_prompt_static()
    narrator_s: str = load_narrator_prompt_static()
    print(f"Chat (static):     {len(chat_s):>6} characters  |  {len(chat_s.split()):>5} words")
    print(f"Narrator (static): {len(narrator_s):>6} characters  |  {len(narrator_s.split()):>5} words")

    print()
    if not _INDEX_PATH.exists():
        print("FAISS index not found. Run: python rag/build_rules_index.py")
        sys.exit(0)

    print("=== RAG Mode ===")
    rag: RulesRAG = RulesRAG()

    test_queries: list[str] = [
        "Series description",
        "Rules for TTS narrator",
        "Media categories action spies",
    ]
    for q in test_queries:
        results = rag.search(q, top_k=3)
        files: list[str] = [r.file for r in results]
        print(f"  '{q}' → {files}")

    print()
    chat_r: str = load_chat_prompt("Series description")
    narrator_r: str = load_narrator_prompt("Text for narrator")
    print(f"Chat (RAG):        {len(chat_r):>6} characters  |  {len(chat_r.split()):>5} words")
    print(f"Narrator (RAG):    {len(narrator_r):>6} characters  |  {len(narrator_r.split()):>5} words")

    reduction: float = (1 - len(chat_r) / len(chat_s)) * 100
    print(f"\nPrompt compression: {reduction:.0f}%")
