# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Codebase RAG Generator Plugin Controller
# =============================================================================
# Description:
#   Main plugin implementation for AST-driven codebase RAG generation,
#   providing dual symbol and vector indexing, custom project directories,
#   named multi-index management, user isolation, and LLM tools.
#
# File: plugin.py
# Project: ai-breadboard
# Package: plugins.generate_rag_from_codebase
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Codebase RAG generator plugin module.

Integrates AST Python code analysis, hierarchical Markdown sectioning, secret filtering,
multi-index naming, user directory isolation, and dual (Symbol + Vector) indexing.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from header import __root__
from src.logger import logger
from plugins.base import BasePlugin
from plugins.generate_rag_from_codebase.ast_parser import PythonAstParser
from plugins.generate_rag_from_codebase.ignore_filter import IgnoreFilter
from plugins.generate_rag_from_codebase.md_parser import MarkdownParser
from plugins.generate_rag_from_codebase.symbol_index import CodeSymbolIndex
from plugins.generate_rag_from_codebase.vector_indexer import CodebaseVectorIndexer


class GenerateRagCodebasePlugin(BasePlugin):
    """Modular plugin for generating and querying codebase RAG indexes.

    Attributes:
        name (str): 'generate_rag_from_codebase'.
        title (str): 'Codebase RAG & Symbol Indexer'.
        version (str): '1.1.0'.
        description (str): Description of the plugin capabilities.
        icon (str): '🧭'.
        category (str): 'tools'.
    """

    name: str = "generate_rag_from_codebase"
    title: str = "Codebase RAG & Symbol Indexer"
    version: str = "1.1.0"
    description: str = "AST-driven Python code, Markdown, and configuration RAG indexer with custom paths, multi-index naming, and user storage."
    icon: str = "🧭"
    category: str = "tools"
    enabled: bool = True
    is_system: bool = True
    scope: str = "system"

    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the codebase RAG plugin.

        Args:
            ai_model (Any): Optional language model instance.
            config (Optional[Dict[str, Any]]): Initial configuration dictionary.
        """
        defaults = self._load_default_config()
        if config:
            defaults.update(config)

        super().__init__(ai_model=ai_model, config=defaults)

        self.project_root: Path = self._resolve_project_root(self.config.get("project_root"))
        self.default_index_name: str = self._sanitize_index_name(self.config.get("index_name", "codebase"))
        
        self.ignore_filter = IgnoreFilter(
            base_dir=self.project_root,
            ignore_patterns=self.config.get("ignore_patterns", [])
        )
        self.ast_parser = PythonAstParser(base_dir=self.project_root)
        self.md_parser = MarkdownParser(base_dir=self.project_root)

        # Active default in-memory indexes
        self.symbol_index = CodeSymbolIndex()
        self.index_dir: Path = self.resolve_index_dir(self.default_index_name)
        self.vector_indexer = CodebaseVectorIndexer(index_dir=self.index_dir)

        # Attempt to load default cached indexes
        self._load_cached_indexes(self.index_dir)

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default config from plugin directory.

        Returns:
            Dict[str, Any]: Default configuration dictionary.
        """
        cfg_file = Path(__file__).parent / "config.json"
        if cfg_file.exists():
            try:
                return json.loads(cfg_file.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.error(f"Error reading plugin config.json: {exc}")
        return {
            "project_root": ".",
            "index_name": "codebase",
            "include_dirs": ["src", "plugins", "integrations", "launchers", "scripts", "install", "docs", "prompts"],
            "include_files": ["README.md", "README.ru.md", "CHANGELOG.md", "pyproject.toml"],
            "ignore_patterns": [".git/**", ".venv/**", "venv/**", "logs/**", "site/**", "SANDBOX/**"],
        }

    def _sanitize_index_name(self, name: str) -> str:
        """Sanitize index name string for safe filesystem usage."""
        clean = "".join(c for c in str(name).strip() if c.isalnum() or c in ("_", "-"))
        return clean or "codebase"

    def _resolve_project_root(self, root_param: Optional[str]) -> Path:
        """Resolve project root directory path from parameter or default."""
        if root_param and str(root_param).strip() not in (".", "", "/"):
            target = Path(str(root_param).strip())
            if not target.is_absolute():
                target = (__root__ / target).resolve()
            if target.exists() and target.is_dir():
                return target
            return target
        return Path(__root__).resolve()

    def resolve_index_dir(self, index_name: str, user_id: Optional[int | str] = None) -> Path:
        """Resolve filesystem path for saving index data.

        Args:
            index_name (str): Identifier name of the index.
            user_id (Optional[int | str]): User ID for user-isolated index storage.

        Returns:
            Path: Absolute directory path.
        """
        clean_name = self._sanitize_index_name(index_name)
        if user_id is not None:
            try:
                from src.user_manager import user_manager
                user_root = user_manager.get_user_directory(int(user_id), create=True)
                target_dir = user_root / "rag" / clean_name
            except Exception:
                target_dir = __root__ / "data" / "users" / str(user_id) / "rag" / clean_name
        else:
            target_dir = __root__ / "data" / "rag_index" / clean_name

        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    def _load_cached_indexes(self, target_dir: Path) -> None:
        """Load symbol table and vector index from target directory."""
        sym_file = target_dir / "symbols.json"
        if sym_file.exists():
            self.symbol_index.load(sym_file)
        self.vector_indexer.index_dir = target_dir
        self.vector_indexer.load()

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return LLM function calling tool definitions for codebase search."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_codebase_rag",
                    "description": "Perform semantic similarity search over codebase (classes, methods, docs, and configurations).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query or natural language question about the codebase.",
                            },
                            "index_name": {
                                "type": "string",
                                "description": "Name of the target codebase index (default: 'codebase').",
                                "default": "codebase",
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of relevant chunks to retrieve (default: 5).",
                                "default": 5,
                            },
                            "type_filter": {
                                "type": "string",
                                "description": "Optional filter: 'python_class', 'python_method', 'python_function', 'documentation', 'project_overview', 'changelog', 'config'.",
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "lookup_symbol",
                    "description": "Lookup a specific class, method, or function by name across the codebase via the AST Symbol Index.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Name of the class, function, or method (e.g., 'MediaSearchAgent', 'search', 'DocumentRAGManager').",
                            },
                            "index_name": {
                                "type": "string",
                                "description": "Name of the target codebase index (default: 'codebase').",
                                "default": "codebase",
                            },
                            "exact": {
                                "type": "boolean",
                                "description": "Whether to require an exact match.",
                                "default": False,
                            },
                        },
                        "required": ["symbol"],
                    },
                },
            },
        ]

    def get_actions(self) -> List[Dict[str, Any]]:
        """Return executable actions for Admin Web UI."""
        return [
            {
                "id": "rebuild_index",
                "label": "Rebuild Codebase Index",
                "color": "primary",
                "description": "Scan codebase directory, parse AST/Markdown, and build Symbol & Vector indexes under specified name.",
            },
            {
                "id": "search_code",
                "label": "Search Code & Docs",
                "color": "info",
                "description": "Query semantic vector index for matching code chunks.",
            },
            {
                "id": "search_symbols",
                "label": "Lookup Symbol",
                "color": "success",
                "description": "Query Code Symbol Index for class or function locations.",
            },
            {
                "id": "list_indexes",
                "label": "List All Indexes",
                "color": "warning",
                "description": "List all saved codebase RAG indexes.",
            },
            {
                "id": "get_stats",
                "label": "Get Index Stats",
                "color": "secondary",
                "description": "View total indexed files, symbols, and chunk statistics for active index.",
            },
        ]

    def get_config_fields(self) -> List[Dict[str, Any]]:
        """Return schema of settings for Admin Web Interface."""
        return [
            {
                "id": "project_root",
                "label": "Project Root Path / Директория проекта",
                "type": "string",
                "default": ".",
                "description": "Absolute or relative path to project root directory to index (e.g., '.' or 'D:/Projects/app').",
            },
            {
                "id": "index_name",
                "label": "Index Name / Имя RAG индекса",
                "type": "string",
                "default": "codebase",
                "description": "Unique identifier for this RAG index (e.g., 'codebase', 'client_app_v1').",
            },
            {
                "id": "include_dirs",
                "label": "Include Subdirectories / Подкаталоги",
                "type": "list_string",
                "default": ["src", "plugins", "integrations", "launchers", "scripts", "install", "docs", "prompts"],
                "description": "Subdirectories relative to project root to scan and index.",
            },
            {
                "id": "include_files",
                "label": "Include Root Files / Файлы в корне",
                "type": "list_string",
                "default": ["README.md", "README.ru.md", "CHANGELOG.md", "pyproject.toml"],
                "description": "Individual files in project root to index.",
            },
        ]

    def list_available_indexes(self, user_id: Optional[int | str] = None) -> List[Dict[str, Any]]:
        """List all saved codebase indexes for the user or system."""
        if user_id is not None:
            try:
                from src.user_manager import user_manager
                base_dir = user_manager.get_user_directory(int(user_id), create=True) / "rag"
            except Exception:
                base_dir = __root__ / "data" / "users" / str(user_id) / "rag"
        else:
            base_dir = __root__ / "data" / "rag_index"

        results = []
        if not base_dir.exists():
            return results

        for child in base_dir.iterdir():
            if child.is_dir() and not child.name.startswith((".", "_")):
                meta_file = child / "meta.json"
                chunks_file = child / "chunks.json"
                sym_file = child / "symbols.json"

                meta: Dict[str, Any] = {}
                if meta_file.exists():
                    try:
                        meta = json.loads(meta_file.read_text(encoding="utf-8"))
                    except Exception:
                        pass

                chunks_count = 0
                if chunks_file.exists():
                    try:
                        chunks_data = json.loads(chunks_file.read_text(encoding="utf-8"))
                        chunks_count = len(chunks_data) if isinstance(chunks_data, list) else 0
                    except Exception:
                        pass

                results.append({
                    "name": child.name,
                    "path": str(child),
                    "total_chunks": meta.get("total_chunks", chunks_count),
                    "total_symbols": meta.get("total_symbols", 0),
                    "total_files": meta.get("total_files", 0),
                    "project_root": meta.get("project_root", ""),
                    "updated_at": meta.get("updated_at", child.stat().st_mtime),
                })
        return results

    def build_codebase_index(
        self,
        project_root: Optional[str | Path] = None,
        index_name: Optional[str] = None,
        user_id: Optional[int | str] = None,
        include_dirs: Optional[List[str]] = None,
        include_files: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Scan codebase, parse AST / Markdown / Config, filter secrets, and save indexes.

        Args:
            project_root (Optional[str | Path]): Target project directory.
            index_name (Optional[str]): Identifier for the index.
            user_id (Optional[int | str]): User identifier for storage isolation.
            include_dirs (Optional[List[str]]): Directories to scan.
            include_files (Optional[List[str]]): Root files to scan.
            ignore_patterns (Optional[List[str]]): Glob patterns to ignore.

        Returns:
            Dict[str, Any]: Indexing summary report.
        """
        start_time = time.time()
        root_path = self._resolve_project_root(str(project_root) if project_root else self.config.get("project_root"))
        idx_name = self._sanitize_index_name(index_name or self.config.get("index_name", "codebase"))
        target_index_dir = self.resolve_index_dir(idx_name, user_id=user_id)

        inc_dirs = include_dirs if include_dirs is not None else self.config.get("include_dirs", [])
        inc_files = include_files if include_files is not None else self.config.get("include_files", [])
        ign_patterns = ignore_patterns if ignore_patterns is not None else self.config.get("ignore_patterns", [])

        custom_filter = IgnoreFilter(base_dir=root_path, ignore_patterns=ign_patterns)
        custom_ast = PythonAstParser(base_dir=root_path)
        custom_md = MarkdownParser(base_dir=root_path)
        sym_index = CodeSymbolIndex()
        vec_indexer = CodebaseVectorIndexer(index_dir=target_index_dir)

        all_chunks: List[Dict[str, Any]] = []
        indexed_files: List[str] = []
        skipped_secrets: int = 0

        # 1. Collect candidate files
        candidate_paths: List[Path] = []

        for inc_file in inc_files:
            file_path = root_path / inc_file
            if file_path.is_file() and not custom_filter.is_ignored(file_path):
                candidate_paths.append(file_path)

        for inc_dir in inc_dirs:
            dir_path = root_path / inc_dir
            if dir_path.is_dir() and not custom_filter.is_ignored(dir_path):
                for p in dir_path.rglob("*"):
                    if p.is_file() and not custom_filter.is_ignored(p):
                        candidate_paths.append(p)

        # Fallback: if inc_dirs and inc_files resulted in 0 candidates, scan root directly
        if not candidate_paths and root_path.is_dir():
            for p in root_path.rglob("*"):
                if p.is_file() and not custom_filter.is_ignored(p):
                    candidate_paths.append(p)

        # 2. Parse files
        for path in candidate_paths:
            suffix = path.suffix.lower()

            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            # Secret check
            if custom_filter.contains_secrets(content):
                content = custom_filter.redact_secrets(content)
                skipped_secrets += 1

            try:
                rel_str = path.resolve().relative_to(root_path).as_posix()
            except ValueError:
                rel_str = path.name

            if suffix == ".py":
                chunks = custom_ast.parse_file(path)
                for c in chunks:
                    sym_index.add_symbol_from_chunk(c)
                all_chunks.extend(chunks)
                indexed_files.append(rel_str)

            elif suffix in {".md", ".rst"}:
                chunks = custom_md.parse_file(path)
                all_chunks.extend(chunks)
                indexed_files.append(rel_str)

            elif suffix in {".toml", ".yaml", ".yml", ".json", ".txt"} or path.name.startswith("requirements"):
                cfg_chunk = {
                    "id": f"{rel_str}::config",
                    "path": rel_str,
                    "type": "config",
                    "symbol": path.name,
                    "docstring": "",
                    "signature": path.name,
                    "text": f"CONFIG_FILE: {rel_str}\n\n{content}",
                    "code": content
                }
                all_chunks.append(cfg_chunk)
                indexed_files.append(rel_str)

        # 3. Build Vector Index
        vec_indexer.build_index(all_chunks)

        # 4. Save Indexes & Metadata
        sym_file = target_index_dir / "symbols.json"
        sym_index.save(sym_file)
        vec_indexer.save()

        elapsed = round(time.time() - start_time, 2)
        meta_info = {
            "index_name": idx_name,
            "project_root": str(root_path),
            "total_files": len(set(indexed_files)),
            "total_chunks": len(all_chunks),
            "total_symbols": sym_index.count(),
            "redacted_secret_files": skipped_secrets,
            "elapsed_seconds": elapsed,
            "updated_at": time.time(),
            "user_id": user_id,
            "index_dir": str(target_index_dir),
        }
        meta_file = target_index_dir / "meta.json"
        meta_file.write_text(json.dumps(meta_info, indent=2, ensure_ascii=False), encoding="utf-8")

        # Update active default in-memory instances if matching
        if idx_name == self.default_index_name and user_id is None:
            self.symbol_index = sym_index
            self.vector_indexer = vec_indexer
            self.index_dir = target_index_dir

        logger.info(f"GenerateRagCodebasePlugin: Index '{idx_name}' built in {elapsed}s. Chunks: {len(all_chunks)}")
        return {
            "success": True,
            **meta_info
        }

    async def execute_action(self, action_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute admin action by ID.

        Args:
            action_id (str): ID of action.
            params (Optional[Dict[str, Any]]): Action arguments.

        Returns:
            Dict[str, Any]: Execution result dictionary.
        """
        params = params or {}
        project_root = params.get("project_root")
        index_name = params.get("index_name") or self.default_index_name
        user_id = params.get("user_id")

        if action_id == "rebuild_index":
            try:
                include_dirs = params.get("include_dirs")
                include_files = params.get("include_files")
                result = self.build_codebase_index(
                    project_root=project_root,
                    index_name=index_name,
                    user_id=user_id,
                    include_dirs=include_dirs,
                    include_files=include_files
                )
                return {"success": True, "data": result}
            except Exception as exc:
                logger.error(f"Error rebuilding codebase index: {exc}")
                return {"success": False, "error": str(exc)}

        if action_id == "list_indexes":
            indexes = self.list_available_indexes(user_id=user_id)
            return {"success": True, "count": len(indexes), "indexes": indexes}

        if action_id == "search_symbols":
            query = params.get("query") or params.get("symbol", "")
            exact = bool(params.get("exact", False))
            limit = int(params.get("limit", 10))

            target_dir = self.resolve_index_dir(index_name, user_id=user_id)
            sym_index = CodeSymbolIndex()
            sym_file = target_dir / "symbols.json"
            if sym_file.exists():
                sym_index.load(sym_file)
            else:
                sym_index = self.symbol_index

            matches = sym_index.search(query=query, exact=exact, limit=limit)
            return {"success": True, "index_name": index_name, "query": query, "count": len(matches), "results": matches}

        if action_id == "search_code":
            query = params.get("query", "")
            top_k = int(params.get("top_k", 5))
            type_filter = params.get("type_filter")
            module_filter = params.get("module_filter")

            target_dir = self.resolve_index_dir(index_name, user_id=user_id)
            vec_indexer = CodebaseVectorIndexer(index_dir=target_dir)
            if not vec_indexer.load():
                vec_indexer = self.vector_indexer

            results = vec_indexer.search(
                query=query,
                top_k=top_k,
                type_filter=type_filter,
                module_filter=module_filter
            )
            return {"success": True, "index_name": index_name, "query": query, "count": len(results), "results": results}

        if action_id == "delete_index":
            target_dir = self.resolve_index_dir(index_name, user_id=user_id)
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
                return {"success": True, "message": f"Index '{index_name}' deleted."}
            return {"success": False, "error": f"Index '{index_name}' not found."}

        if action_id == "get_stats":
            target_dir = self.resolve_index_dir(index_name, user_id=user_id)
            meta_file = target_dir / "meta.json"
            if meta_file.exists():
                try:
                    data = json.loads(meta_file.read_text(encoding="utf-8"))
                    return {"success": True, "data": data}
                except Exception:
                    pass
            return {
                "success": True,
                "data": {
                    "index_name": index_name,
                    "chunks_count": len(self.vector_indexer.chunks),
                    "symbols_count": self.symbol_index.count(),
                    "vocabulary_size": len(self.vector_indexer.vocab),
                    "index_dir": str(target_index_dir if 'target_index_dir' in locals() else target_dir),
                }
            }

        return await super().execute_action(action_id, params)

    async def handle(self, message: str, **kwargs: Any) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle conversational search or status stream.

        Args:
            message (str): Input query or search prompt.
            **kwargs (Any): Additional options.

        Yields:
            Dict[str, Any]: Stream events with matched symbols and code chunks.
        """
        yield {"status": "start", "plugin": self.name}

        index_name = kwargs.get("index_name") or self.default_index_name
        user_id = kwargs.get("user_id")

        target_dir = self.resolve_index_dir(index_name, user_id=user_id)
        sym_index = CodeSymbolIndex()
        sym_file = target_dir / "symbols.json"
        if sym_file.exists():
            sym_index.load(sym_file)
        else:
            sym_index = self.symbol_index

        vec_indexer = CodebaseVectorIndexer(index_dir=target_dir)
        if not vec_indexer.load():
            vec_indexer = self.vector_indexer

        symbols = sym_index.search(query=message, limit=3)
        code_chunks = vec_indexer.search(query=message, top_k=3)

        lines = [f"### Codebase RAG Results (`{index_name}`) for: `{message}`\n"]
        if symbols:
            lines.append("**Matched Symbols (AST Index):**")
            for s in symbols:
                lines.append(f"- `{s['symbol']}` ({s['type']}) in [{s['path']}](file:///{s['path']})")
            lines.append("")

        if code_chunks:
            lines.append("**Semantic Code Chunks (Vector Index):**")
            for chunk in code_chunks:
                score = chunk.get("similarity_score", 0.0)
                lines.append(f"- **{chunk.get('id')}** (Score: {score})")
                if chunk.get("docstring"):
                    lines.append(f"  *Docstring:* {chunk['docstring'][:120]}...")
            lines.append("")

        if not symbols and not code_chunks:
            lines.append("No matching symbols or chunks found. Try running `rebuild_index` action.")

        text_out = "\n".join(lines)
        yield {
            "status": "complete",
            "text": text_out,
            "data": {
                "index_name": index_name,
                "symbols": symbols,
                "chunks": code_chunks
            }
        }
