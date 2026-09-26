# -*- coding: utf-8 -*-
# Compatibility alias for apps.system_inspector.tui
from apps.windows.tui import SystemInspectorState, render_inspector_ui as render_ui, RICH_AVAILABLE

__all__ = ["SystemInspectorState", "render_ui", "RICH_AVAILABLE"]
