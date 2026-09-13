# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Optional
from plugins.rag_cleaner.plugin import RAGCleanerPlugin

__all__ = ["RAGCleanerPlugin", "plugin"]

def plugin(ai_model: Any = None, config: Optional[dict] = None) -> RAGCleanerPlugin:
    return RAGCleanerPlugin(ai_model=ai_model, config=config)
