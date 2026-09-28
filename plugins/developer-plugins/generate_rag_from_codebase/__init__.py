"""Generate RAG from Codebase Plugin Package."""
from __future__ import annotations
from typing import Any, Optional
from plugins.generate_rag_from_codebase.plugin import GenerateRagCodebasePlugin
__all__ = ['GenerateRagCodebasePlugin', 'plugin']

def plugin(ai_model: Any=None, config: Optional[dict]=None) -> GenerateRagCodebasePlugin:
    """Plugin factory function called by plugin loader.

    Args:
        ai_model (Any): Optional AI model instance.
        config (Optional[dict]): Configuration overrides.

    Returns:
        GenerateRagCodebasePlugin: Configured plugin instance.
    """
    return GenerateRagCodebasePlugin(ai_model=ai_model, config=config)