# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Extract text from files for vectorization
# =============================================================================
# Description:
#   Build RAG index for development technical context and codebase.
#
# File: dev_rag.py
# Project: ai-breadboard
# Package: src.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Development RAG index builder for code and documentation.

Indexes Python and Markdown files from specified directories for semantic search."""

import json
import os
from pathlib import Path
from src.ai.gemini.rag import GeminiRAG
from src.logger import logger

# Index file path
DEV_RAG_DB = Path(__file__).parent.parent.parent / ".gemini" / "knowledge" / "dev_rag.db"

def _file_to_text(file_path: Path) -> str:
    """Extract text from file for vectorization.

    Args:
        file_path (Path): Path to file.

    Returns:
        str: File content with metadata.
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        return f"File: {file_path.name}\nPath: {file_path}\nContent:\n{content}"
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return ""

def build_dev_rag(api_key: str) -> GeminiRAG:
    """Build RAG index for code and documentation.

    Indexes .py and .md files from specified directories.

    Args:
        api_key (str): Gemini API key.

    Returns:
        GeminiRAG: Initialized index.
    """
    rag = GeminiRAG(api_key=api_key, db_path=str(DEV_RAG_DB))
    rag.clear()

    # Directories to index
    target_dirs = ["docs", "prompts", "core", "plugins"]
    docs = []

    for dir_name in target_dirs:
        for file_path in Path(dir_name).rglob("*"):
            if file_path.suffix in [".py", ".md"] and "__pycache__" not in str(file_path):
                text = _file_to_text(file_path)
                if text:
                    docs.append({
                        'id': str(file_path),
                        'text': text,
                        'meta': {'path': str(file_path), 'type': file_path.suffix}
                    })

    rag.add_documents(docs)
    logger.info(f"Developer index built. Files indexed: {len(docs)}")
    return rag

def get_dev_rag(api_key: str) -> GeminiRAG:
    """Get developer index.
    
    Args:
        api_key (str): Gemini API key.
        
    Returns:
        GeminiRAG: Index instance.
    """
    return GeminiRAG(api_key=api_key, db_path=DEV_RAG_DB)

def rag_search_tool(query: str, top_k: int = 3, api_key: str = '') -> str:
    """Semantic search across code and documentation via RAG index.

    Args:
        query (str): Search query.
        top_k (int): Number of results to return. Default 3.
        api_key (str): Gemini API key.

    Returns:
        str: JSON string with list of found files.
    """
    rag = get_dev_rag(api_key)
    if rag.count() == 0:
        return json.dumps({'error': 'Developer index empty. Run rebuild_dev_rag'}, ensure_ascii=False)
    
    results = rag.search(query, top_k=top_k, threshold=0.3)
    return json.dumps(results, ensure_ascii=False, indent=2)
