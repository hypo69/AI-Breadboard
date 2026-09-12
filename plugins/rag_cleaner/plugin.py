# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from header import __root__
from src.logger import logger
from plugins.base import BasePlugin
from .cleaner import RAGDocumentCleanerCore


class RAGCleanerPlugin(BasePlugin):
    name: str = "rag_cleaner"
    title: str = "RAG Document Cleaner & Ingestor"
    version: str = "1.0.0"
    description: str = "Sanitizes and chunks heterogeneous files (PDF, DOCX, ZIP, HTML, CSV, JSON, TXT) for RAG."
    icon: str = "🞩"
    category: str = "tools"
    enabled: bool = True
    is_system: bool = False
    scope: str = "user"

    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(ai_model=ai_model, config=config)
        min_chunk = self.config.get("min_chunk_len", 20)
        max_chunk = self.config.get("max_chunk_len", 1500)
        self.cleaner = RAGDocumentCleanerCore(min_chunk_len=min_chunk, max_chunk_len=max_chunk)

    async def initialize(self) -> bool:
        logger.info("RAG Cleaner plugin initialized successfully.")
        return True

    async def handle(self, message: str, **kwargs: Any) -> AsyncGenerator[Dict[str, Any], None]:
        yield {"status": "started", "text": f"Processing RAG cleaning for: {message}"}
        path = Path(message.strip())
        if path.exists():
            chunks = self.cleaner.process_target(path)
            yield {"status": "complete", "count": len(chunks), "chunks": chunks[:5]}
        else:
            yield {"status": "error", "text": f"Path not found: {message}"}

    def get_manifest(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        manifest = super().get_manifest(*args, **kwargs)
        manifest.update({
            "supported_extensions": [".zip", ".tar", ".gz", ".tgz", ".docx", ".pdf", ".html", ".htm", ".csv", ".json", ".txt", ".md"],
            "actions": [
                {
                    "name": "clean_file",
                    "description": "Clean and chunk a single file or archive into RAG chunks.",
                    "parameters": {"file_path": "string"}
                },
                {
                    "name": "clean_directory",
                    "description": "Clean and chunk all documents in a directory into RAG chunks.",
                    "parameters": {"dir_path": "string", "output_jsonl": "string (optional)"}
                }
            ]
        })
        return manifest

    async def execute_action(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = params or {}
        if action == "clean_file":
            file_path = params.get("file_path")
            if not file_path:
                return {"success": False, "error": "Missing 'file_path' parameter."}
            chunks = list(self.cleaner.process_file(file_path))
            return {"success": True, "count": len(chunks), "chunks": chunks}

        elif action == "clean_directory":
            dir_path = params.get("dir_path")
            if not dir_path:
                return {"success": False, "error": "Missing 'dir_path' parameter."}
            chunks = self.cleaner.process_target(dir_path)
            out_file = params.get("output_jsonl")
            if out_file:
                out_path = Path(out_file)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "w", encoding="utf-8") as f:
                    for c in chunks:
                        f.write(json.dumps(c, ensure_ascii=False) + "\n")
            return {"success": True, "count": len(chunks), "saved_to": out_file, "chunks": chunks[:5]}

        return {"success": False, "error": f"Unknown action: {action}"}

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "clean_and_chunk_documents_for_rag",
                "description": "Cleans, normalizes, and extracts semantic chunks from user uploaded files or archives for RAG embeddings.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target_path": {
                            "type": "string",
                            "description": "Path to file, archive (.zip/.tar), or folder to clean."
                        }
                    },
                    "required": ["target_path"]
                }
            }
        ]
