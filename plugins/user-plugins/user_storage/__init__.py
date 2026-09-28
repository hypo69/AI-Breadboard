from __future__ import annotations
from typing import Any, Optional
from plugins.user_storage.plugin import UserStoragePlugin
__all__ = ['UserStoragePlugin', 'plugin']

def plugin(ai_model: Any=None, config: Optional[dict]=None) -> UserStoragePlugin:
    """Plugin factory function called by plugin loader.

    Args:
        ai_model (Any): Optional AI model instance.
        config (Optional[dict]): Configuration overrides.

    Returns:
        UserStoragePlugin: Configured plugin instance.
    """
    return UserStoragePlugin(ai_model=ai_model, config=config)