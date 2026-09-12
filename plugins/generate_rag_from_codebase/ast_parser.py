# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Python AST Codebase Decomposer
# =============================================================================
# Description:
#   Parses Python source code into contextual AST chunks (modules, classes, methods,
#   and standalone functions) preserving docstrings, signatures, and symbol relations.
#
# File: ast_parser.py
# Project: ai-breadboard
# Package: plugins.generate_rag_from_codebase
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""AST-based Python source code parser and chunker for codebase RAG.

Decomposes Python modules into rich semantic chunks rather than blind character slices,
retaining parent class context, sibling methods, signatures, and docstrings.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class PythonAstParser:
    """Extracts semantic structural chunks from Python files using AST analysis.

    Attributes:
        base_dir (Path): Base directory for computing relative module paths.
    """

    def __init__(self, base_dir: Path) -> None:
        """Initialize the AST parser.

        Args:
            base_dir (Path): Project root directory.
        """
        self.base_dir = Path(base_dir).resolve()

    def _get_module_name(self, file_path: Path) -> str:
        """Derive Python dotted module path from filesystem path.

        Args:
            file_path (Path): Path to the Python file.

        Returns:
            str: Dotted module name (e.g., 'src.ai.langchain_agent').
        """
        try:
            rel = file_path.resolve().relative_to(self.base_dir)
            parts = list(rel.with_suffix("").parts)
            if parts and parts[-1] == "__init__":
                parts.pop()
            return ".".join(parts)
        except Exception:
            return file_path.stem

    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse a Python file into structured RAG chunks.

        Args:
            file_path (Path): Path to the Python source file.

        Returns:
            List[Dict[str, Any]]: List of extracted semantic chunks.
        """
        try:
            code = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        try:
            tree = ast.parse(code, filename=str(file_path))
        except SyntaxError:
            # Fallback to basic file chunk if syntax error occurs
            return [self._create_raw_chunk(file_path, code)]

        lines = code.splitlines(keepends=True)
        module_name = self._get_module_name(file_path)
        rel_path = file_path.resolve().relative_to(self.base_dir).as_posix() if file_path.is_relative_to(self.base_dir) else file_path.as_posix()

        # Extract module-level docstring and imports
        module_doc = ast.get_docstring(tree) or ""
        imports = self._extract_imports(tree)

        chunks: List[Dict[str, Any]] = []

        # Find classes and top-level functions
        classes: List[ast.ClassDef] = []
        top_functions: List[ast.FunctionDef | ast.AsyncFunctionDef] = []

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes.append(node)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                top_functions.append(node)

        # 1. Module Overview Chunk
        class_names = [c.name for c in classes]
        func_names = [f.name for f in top_functions]
        module_overview_text = (
            f"MODULE: {module_name}\n"
            f"PATH: {rel_path}\n"
            f"TYPE: python_module\n"
            f"DOCSTRING: {module_doc}\n"
            f"IMPORTS: {', '.join(imports) if imports else 'None'}\n"
            f"CLASSES: {', '.join(class_names) if class_names else 'None'}\n"
            f"TOP_FUNCTIONS: {', '.join(func_names) if func_names else 'None'}\n"
        )
        chunks.append({
            "id": f"{rel_path}::module",
            "path": rel_path,
            "module": module_name,
            "type": "python_module",
            "symbol": module_name,
            "class_name": None,
            "function_name": None,
            "is_async": False,
            "docstring": module_doc,
            "signature": f"module {module_name}",
            "imports": imports,
            "related_symbols": class_names + func_names,
            "text": module_overview_text,
            "code": ""
        })

        # 2. Process Classes & Methods
        for cls_node in classes:
            cls_doc = ast.get_docstring(cls_node) or ""
            cls_methods: List[ast.FunctionDef | ast.AsyncFunctionDef] = [
                n for n in cls_node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            cls_method_names = [m.name for m in cls_methods]
            bases = [self._ast_to_name(b) for b in cls_node.bases]

            cls_text = (
                f"CLASS: {cls_node.name}\n"
                f"MODULE: {module_name}\n"
                f"PATH: {rel_path}\n"
                f"BASES: {', '.join(bases) if bases else 'object'}\n"
                f"DOCSTRING: {cls_doc}\n"
                f"METHODS: {', '.join(cls_method_names) if cls_method_names else 'None'}\n"
            )

            chunks.append({
                "id": f"{rel_path}::{cls_node.name}",
                "path": rel_path,
                "module": module_name,
                "type": "python_class",
                "symbol": f"{cls_node.name}",
                "class_name": cls_node.name,
                "function_name": None,
                "is_async": False,
                "docstring": cls_doc,
                "signature": f"class {cls_node.name}",
                "imports": imports,
                "related_symbols": cls_method_names,
                "text": cls_text,
                "code": self._get_node_source(lines, cls_node)
            })

            # Process individual methods with class & sibling context
            for method_node in cls_methods:
                method_chunk = self._build_function_chunk(
                    lines=lines,
                    node=method_node,
                    rel_path=rel_path,
                    module_name=module_name,
                    class_name=cls_node.name,
                    imports=imports,
                    sibling_methods=[m for m in cls_method_names if m != method_node.name]
                )
                chunks.append(method_chunk)

        # 3. Process Top-level Functions
        for func_node in top_functions:
            func_chunk = self._build_function_chunk(
                lines=lines,
                node=func_node,
                rel_path=rel_path,
                module_name=module_name,
                class_name=None,
                imports=imports,
                sibling_methods=[f for f in func_names if f != func_node.name]
            )
            chunks.append(func_chunk)

        return chunks

    def _build_function_chunk(
        self,
        lines: List[str],
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        rel_path: str,
        module_name: str,
        class_name: Optional[str],
        imports: List[str],
        sibling_methods: List[str]
    ) -> Dict[str, Any]:
        """Build a contextual chunk for a method or top-level function."""
        is_async = isinstance(node, ast.AsyncFunctionDef)
        doc = ast.get_docstring(node) or ""
        symbol_name = f"{class_name}.{node.name}" if class_name else node.name
        chunk_type = "python_method" if class_name else "python_function"
        signature = self._get_signature(node, is_async)
        code_body = self._get_node_source(lines, node)

        text = (
            f"PATH: {rel_path}\n"
            f"MODULE: {module_name}\n"
            f"{'CLASS: ' + class_name + chr(10) if class_name else ''}"
            f"SYMBOL: {symbol_name}\n"
            f"SIGNATURE: {signature}\n"
            f"DOCSTRING: {doc}\n"
            f"IMPORTS: {', '.join(imports[:15]) if imports else 'None'}\n"
            f"RELATED_SYMBOLS: {', '.join(sibling_methods[:10]) if sibling_methods else 'None'}\n\n"
            f"CODE:\n{code_body}"
        )

        return {
            "id": f"{rel_path}::{symbol_name}",
            "path": rel_path,
            "module": module_name,
            "type": chunk_type,
            "symbol": symbol_name,
            "class_name": class_name,
            "function_name": node.name,
            "is_async": is_async,
            "docstring": doc,
            "signature": signature,
            "imports": imports,
            "related_symbols": sibling_methods,
            "text": text,
            "code": code_body
        }

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract list of imported module and symbol names."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    imports.append(f"{mod}.{alias.name}" if mod else alias.name)
        return imports

    def _get_node_source(self, lines: List[str], node: ast.AST) -> str:
        """Extract raw source code slice corresponding to an AST node."""
        if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
            start = max(0, node.lineno - 1)
            end = node.end_lineno
            return "".join(lines[start:end])
        return ""

    def _get_signature(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool) -> str:
        """Generate human-readable signature string for a function node."""
        prefix = "async def " if is_async else "def "
        args = [arg.arg for arg in node.args.args]
        return f"{prefix}{node.name}({', '.join(args)})"

    def _ast_to_name(self, node: ast.AST) -> str:
        """Convert AST expression node to identifier string."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._ast_to_name(node.value)}.{node.attr}"
        return "Unknown"

    def _create_raw_chunk(self, file_path: Path, code: str) -> Dict[str, Any]:
        """Create fallback raw chunk if parsing fails."""
        rel_path = file_path.as_posix()
        return {
            "id": f"{rel_path}::raw",
            "path": rel_path,
            "module": file_path.stem,
            "type": "source_code",
            "symbol": file_path.stem,
            "class_name": None,
            "function_name": None,
            "is_async": False,
            "docstring": "",
            "signature": file_path.name,
            "imports": [],
            "related_symbols": [],
            "text": f"FILE: {rel_path}\n\n{code}",
            "code": code
        }
