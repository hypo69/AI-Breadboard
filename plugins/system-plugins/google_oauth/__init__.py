from __future__ import annotations
from typing import Any, Optional
from plugins.google_oauth.plugin import GoogleOAuthPlugin
__all__ = ['GoogleOAuthPlugin', 'plugin']

def plugin(ai_model: Any=None, config: Optional[dict]=None) -> GoogleOAuthPlugin:
    """Plugin factory function called by plugin loader.

    Args:
        ai_model (Any): Optional AI model instance.
        config (Optional[dict]): Configuration overrides.

    Returns:
        GoogleOAuthPlugin: Configured plugin instance.
    """
    return GoogleOAuthPlugin(ai_model=ai_model, config=config)