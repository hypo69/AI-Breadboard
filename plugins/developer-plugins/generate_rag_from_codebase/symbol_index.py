# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Code Symbol Index Manager
# =============================================================================
# Description:
#   Maintains an exact and fuzzy symbol table extracted from codebase AST analysis,
#   allowing instantaneous symbol lookups without embedding latency.
#
# File: symbol_index.py
# Project: ai-breadboard
# Package: plugins.generate_rag_from_codebase
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Code symbol table index for fast symbol resolution.

Indexes classes, functions, and methods to support direct lookup of code symbols,
their enclosing modules, signatures, and file locations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class CodeSymbolIndex:
    """In-memory and persistent Code Symbol Index.

    Attributes:
        symbols (Dict[str, List[Dict[str, Any]]]): Symbol mapping keyed by lower-case symbol.
    """

    def __init__(self) -> None:
        """Initialize empty symbol index."""
        self.symbols: Dict[str, List[Dict[str, Any]]] = {}

    def clear(self) -> None:
        """Clear all indexed symbols."""
        self.symbols.clear()

    def add_symbol_from_chunk(self, chunk: Dict[str, Any]) -> None:
        """Index a symbol entry from an AST parsed chunk.

        Args:
            chunk (Dict[str, Any]): AST chunk with symbol metadata.
        """
        symbol_name = chunk.get("symbol")
        if not symbol_name or chunk.get("type") not in {"python_class", "python_method", "python_function", "python_module"}:
            return

        record = {
            "id": chunk.get("id"),
            "symbol": symbol_name,
            "type": chunk.get("type"),
            "path": chunk.get("path"),
            "module": chunk.get("module"),
            "class_name": chunk.get("class_name"),
            "function_name": chunk.get("function_name"),
            "signature": chunk.get("signature"),
            "docstring": chunk.get("docstring"),
            "related_symbols": chunk.get("related_symbols", []),
        }

        # Index by full symbol name (case-insensitive)
        full_key = symbol_name.lower()
        self.symbols.setdefault(full_key, []).append(record)

        # Also index by simple name if method (e.g. 'search' from 'MediaSearchAgent.search')
        if "." in symbol_name:
            simple_name = symbol_name.split(".")[-1].lower()
            if simple_name != full_key:
                self.symbols.setdefault(simple_name, []).append(record)

    def search(self, query: str, exact: bool = False, limit: int = 10) -> List[Dict[str, Any]]:
        """Search symbol index.

        Args:
            query (str): Symbol query string.
            exact (bool): If True, require exact match on symbol key.
            limit (int): Maximum results to return.

        Returns:
            List[Dict[str, Any]]: Matching symbol records.
        """
        q = query.strip().lower()
        if not q:
            return []

        results: List[Dict[str, Any]] = []
        seen_ids = set()

        # 1. Exact match
        if q in self.symbols:
            for item in self.symbols[q]:
                if item["id"] not in seen_ids:
                    results.append(item)
                    seen_ids.add(item["id"])

        if exact or len(results) >= limit:
            return results[:limit]

        # 2. Prefix & Substring match
        for sym_key, items in self.symbols.items():
            if sym_key != q and (q in sym_key or sym_key in q):
                for item in items:
                    if item["id"] not in seen_ids:
                        results.append(item)
                        seen_ids.add(item["id"])
                        if len(results) >= limit:
                            return results

        return results[:limit]

    def save(self, file_path: Path) -> None:
        """Persist symbol index to JSON file.

        Args:
            file_path (Path): Target file path.
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps(self.symbols, indent=2, ensure_ascii=False), encoding="utf-8")

    def load(self, file_path: Path) -> bool:
        """Load symbol index from JSON file.

        Args:
            file_path (Path): Path to JSON file.

        Returns:
            bool: True if loaded successfully, False otherwise.
        """
        if not file_path.exists():
            return False
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self.symbols = data
                return True
        except Exception:
            pass
        return False

    def count(self) -> int:
        """Return total number of unique symbol keys."""
        return sum(len(v) for v in self.symbols.values())
