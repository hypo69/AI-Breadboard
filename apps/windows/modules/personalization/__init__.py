# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Personalization Module
# =============================================================================
# Description:
#   Модуль персонализации, тем оформления, настройки курсора, обоев рабочего
#   стола и интеллектуального Windows Spotlight с метаданными.
#
# Usage Examples:
#   from apps.windows.modules.personalization import PersonalizationManager, personalization_router
#
# Updated: 2026-10-06 18:35:00
# =============================================================================

"""Пакет управления персонализацией и внешним видом Windows."""

from apps.windows.modules.personalization.models import (
    WindowsThemeInfo,
    ThemeApplyRequest,
    CursorSettings,
    CursorUpdateRequest,
    CursorColorScheme,
    WallpaperSettings,
    WallpaperUpdateRequest,
    WallpaperFitMode,
    WallpaperSourceMode,
    WindowsSpotlightSettings,
    SpotlightUpdateRequest,
    AISpotlightLocation,
    AISpotlightImageInfo,
    AISpotlightAnalysisRequest,
    PersonalizationOverviewResponse,
)
from apps.windows.modules.personalization.manager import (
    PersonalizationManager,
    get_personalization_manager,
)
from apps.windows.modules.personalization.ai_spotlight import (
    AISpotlightEngine,
    get_ai_spotlight_engine,
)
from apps.windows.modules.personalization.router import (
    router as personalization_router,
    init_router,
)

__all__ = [
    "WindowsThemeInfo",
    "ThemeApplyRequest",
    "CursorSettings",
    "CursorUpdateRequest",
    "CursorColorScheme",
    "WallpaperSettings",
    "WallpaperUpdateRequest",
    "WallpaperFitMode",
    "WallpaperSourceMode",
    "WindowsSpotlightSettings",
    "SpotlightUpdateRequest",
    "AISpotlightLocation",
    "AISpotlightImageInfo",
    "AISpotlightAnalysisRequest",
    "PersonalizationOverviewResponse",
    "PersonalizationManager",
    "get_personalization_manager",
    "AISpotlightEngine",
    "get_ai_spotlight_engine",
    "personalization_router",
    "init_router",
]
