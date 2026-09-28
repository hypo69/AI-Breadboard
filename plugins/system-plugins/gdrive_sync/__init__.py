from __future__ import annotations
from typing import Any, Optional
from plugins.gdrive_sync.plugin import GDriveSyncPlugin
__all__ = ['GDriveSyncPlugin', 'plugin']

def plugin(ai_model: Any=None, config: Optional[dict]=None) -> GDriveSyncPlugin:
    """Plugin factory function called by plugin loader.

    Args:
        ai_model (Any): Optional AI model instance.
        config (Optional[dict]): Configuration overrides.

    Returns:
        GDriveSyncPlugin: Configured plugin instance.
    """
    return GDriveSyncPlugin(ai_model=ai_model, config=config)