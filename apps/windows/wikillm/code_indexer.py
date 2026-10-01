# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm - Code Indexer
# =============================================================================
# Description:
#   Индексатор исходного кода на базе Python AST. Извлекает функции, классы,
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.code_indexer import CodeKnowledgeIndexer
#
#     service = CodeKnowledgeIndexer()
#
# File: code_indexer.py
# Project: ai-breadboard
# Package: apps.windows.wikillm
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Индексатор исходного кода на базе Python AST. Извлекает функции, классы,"""

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional
from logger import logger
from .models import (
    ArtifactType,
    CodeKnowledge,
    KnowledgeEntity,
    KnowledgeSource,
    utc_now_iso,
)
from .storage import WikiStorage


class CodeKnowledgeIndexer:
    """Индексатор структуры Python файлов для слоя Code Knowledge."""

    def __init__(self, storage: WikiStorage) -> None:
        """Инициализирует индексатор кода.

        Args:
            storage: Экземпляр хранилища WikiStorage.
        """
        self.storage = storage

    def index_file(self, file_path: Path | str, base_dir: Optional[Path | str] = None) -> List[KnowledgeEntity]:
        """Индексирует отдельный Python файл и сохраняет обнаруженные символы в БД.

        Args:
            file_path: Путь к Python файлу.
            base_dir: Базовая директория для вычисления относительного пути модуля.

        Returns:
            Список созданных сущностей KnowledgeEntity.
        """
        p = Path(file_path).resolve()
        if not p.exists() or p.suffix != ".py":
            return []

        try:
            content = p.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(content, filename=str(p))
        except Exception as exc:
            logger.warning(f"Ошибка парсинга AST файла {p}: {exc}")
            return []

        rel_module = p.name
        if base_dir:
            try:
                rel_module = str(p.relative_to(Path(base_dir).resolve())).replace("\\", "/").replace(".py", "")
            except ValueError:
                rel_module = p.stem

        entities: List[KnowledgeEntity] = []
        imports: List[str] = []

        # 1. Сбор импортов
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)

        # 2. Обход функций и классов верхнего уровня
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                ent = self._process_class_node(node, rel_module, imports)
                if ent:
                    entities.append(ent)
                    self.storage.save_entity(ent)

                # Методы класса
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        m_ent = self._process_function_node(
                            item, rel_module, imports, parent_class=node.name
                        )
                        if m_ent:
                            entities.append(m_ent)
                            self.storage.save_entity(m_ent)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                ent = self._process_function_node(node, rel_module, imports)
                if ent:
                    entities.append(ent)
                    self.storage.save_entity(ent)

        return entities

    def _process_class_node(
        self, node: ast.ClassDef, module_path: str, dependencies: List[str]
    ) -> Optional[KnowledgeEntity]:
        """Формирует сущность базы знаний для класса."""
        doc = ast.get_docstring(node) or ""
        canonical_key = f"code:{module_path}:{node.name}"
        summary = doc.split("\n\n")[0].strip() if doc else f"Класс {node.name}"

        code_info = CodeKnowledge(
            module_path=module_path,
            symbol_name=node.name,
            symbol_type="class",
            docstring=doc,
            dependencies=dependencies[:15],
        )

        return KnowledgeEntity(
            canonical_key=canonical_key,
            entity_type=ArtifactType.CODE_SYMBOL,
            name=node.name,
            summary=summary[:250],
            category="code",
            severity="info",
            confidence=1.0,
            provenance_source=KnowledgeSource.DOCUMENTED,
            code_info=code_info,
            tags=["code", "class", module_path.split("/")[-1]],
        )

    def _process_function_node(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        module_path: str,
        dependencies: List[str],
        parent_class: Optional[str] = None,
    ) -> Optional[KnowledgeEntity]:
        """Формирует сущность базы знаний для функции или метода."""
        doc = ast.get_docstring(node) or ""
        full_name = f"{parent_class}.{node.name}" if parent_class else node.name
        canonical_key = f"code:{module_path}:{full_name}"
        summary = doc.split("\n\n")[0].strip() if doc else f"Функция {full_name}"

        params = [arg.arg for arg in node.args.args if arg.arg != "self"]
        ret_type = ast.unparse(node.returns) if node.returns else None

        code_info = CodeKnowledge(
            module_path=module_path,
            symbol_name=full_name,
            symbol_type="method" if parent_class else "function",
            docstring=doc,
            parameters=params,
            return_type=ret_type,
            dependencies=dependencies[:15],
        )

        return KnowledgeEntity(
            canonical_key=canonical_key,
            entity_type=ArtifactType.CODE_SYMBOL,
            name=full_name,
            summary=summary[:250],
            category="code",
            severity="info",
            confidence=1.0,
            provenance_source=KnowledgeSource.DOCUMENTED,
            code_info=code_info,
            tags=["code", "function", module_path.split("/")[-1]],
        )

    def index_directory(self, dir_path: Path | str) -> int:
        """Рекурсивно индексирует все .py файлы в каталоге.

        Args:
            dir_path: Путь к директории исходного кода.

        Returns:
            Общее количество проиндексированных сущностей.
        """
        p = Path(dir_path).resolve()
        if not p.exists() or not p.is_dir():
            return 0

        count = 0
        for py_file in p.glob("**/*.py"):
            if any(part.startswith(".") or part.startswith("~") or part == "__pycache__" for part in py_file.parts):
                continue
            ents = self.index_file(py_file, base_dir=p)
            count += len(ents)

        return count
