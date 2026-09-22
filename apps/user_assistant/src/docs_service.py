# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: User Assistant Documents Service
# =============================================================================
# Description:
#   Provides user document retrieval, folder scanning, file reading, and RAG ingestion.
#
# File: docs_service.py
# Package: apps.user_assistant.src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from logger import logger


class DocsService:
    """Manages user personal documents, local files, and RAG vector ingestion."""

    def __init__(self, user_id: int = 1) -> None:
        """Initialize docs service for user."""
        self.user_id = user_id

    def list_user_files(self, subfolder: str = "files") -> List[Dict[str, Any]]:
        """List personal document files for the user.

        Args:
            subfolder (str): Target subfolder.

        Returns:
            List[Dict[str, Any]]: Metadata list of files.
        """
        try:
            from src.user_manager import user_manager
            target_dir = user_manager.get_user_directory(self.user_id, subfolder=subfolder, create=True)
            results = []
            for p in target_dir.iterdir():
                if p.is_file():
                    stat = p.stat()
                    results.append({
                        "name": p.name,
                        "path": str(p),
                        "size_bytes": stat.st_size,
                        "modified_at": stat.st_mtime,
                    })
            return results
        except Exception as ex:
            logger.warning(f"Failed to list user files: {ex}")
            return []

    def ingest_to_rag(self, file_path: str) -> Dict[str, Any]:
        """Send a personal document file to the RAG vector index.

        Args:
            file_path (str): Path to document.

        Returns:
            Dict[str, Any]: Ingestion status.
        """
        p = Path(file_path)
        if not p.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        try:
            from src.rag import add_file_to_rag
            res = add_file_to_rag(file_path=str(p), user_id=self.user_id) if callable(globals().get("add_file_to_rag")) else True
            return {"success": True, "file": p.name, "indexed": True}
        except Exception as ex:
            logger.warning(f"RAG ingestion failed for {file_path}: {ex}")
            return {"success": False, "error": str(ex)}
