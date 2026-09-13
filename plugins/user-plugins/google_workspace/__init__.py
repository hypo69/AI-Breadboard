# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Workspace Plugin Package Interface
# =============================================================================
# Description:
#   Package initializer for Google Workspace integration plugin, managing
#   account pool, OAuth2, Service Accounts, Gmail, Docs, Sheets, and Drive.
#
# File: __init__.py
# Project: ai-breadboard
# Package: plugins.google_workspace
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from typing import Any, Optional

from plugins.google_workspace.plugin import GoogleWorkspacePlugin

__all__ = ["GoogleWorkspacePlugin", "plugin"]


def plugin(ai_model: Any = None, config: Optional[dict] = None) -> GoogleWorkspacePlugin:
    """Plugin factory function called by plugin loader.

    Args:
        ai_model (Any): Optional AI model instance.
        config (Optional[dict]): Configuration overrides.

    Returns:
        GoogleWorkspacePlugin: Configured plugin instance.
    """
    return GoogleWorkspacePlugin(ai_model=ai_model, config=config)
