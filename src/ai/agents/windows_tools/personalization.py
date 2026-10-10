# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Personalization Tools Module
# =============================================================================
# Description:
#   Инструменты прямого взаимодействия с подсистемой персонализации и оформления Windows
#   (apps.windows.sdk.modules.personalization).
#   Сгруппированы по 3 логическим блокам:
#     1. Обзор оформления и списка тем Windows (windows_personalization_overview)
#     2. Применение тем и переключение темного режима/акцентного цвета (windows_personalization_theme_action)
#     3. Настройка указателя мыши и обоев рабочего стола (windows_personalization_cursor_wallpaper)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.personalization import windows_personalization_overview
#     res = await windows_personalization_overview(action="overview")
#
# File: personalization.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:00:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов Windows Personalization & Appearance Control Plane для ИИ-агентов."""

import asyncio
import json
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional
from logger import logger

try:
    from langchain_core.tools import tool
except ImportError:
    class DummyTool:
        def __init__(self, func):
            self.func = func
            self.__name__ = getattr(func, '__name__', 'DummyTool')
            self.__doc__ = getattr(func, '__doc__', '')

        def invoke(self, input_data=None, **kwargs):
            if isinstance(input_data, dict):
                return self.func(**input_data)
            elif input_data is not None:
                return self.func(input_data, **kwargs)
            return self.func(**kwargs)

        def __call__(self, *args, **kwargs):
            return self.func(*args, **kwargs)

    def tool(func=None, *args, **kwargs):
        if func is not None:
            return DummyTool(func)
        return lambda f: DummyTool(f)


def _to_serializable(obj: Any) -> Any:
    """Вспомогательное преобразование объектов моделей и dataclass в сериализуемый словарь."""
    if isinstance(obj, (int, float, bool, str)) or obj is None:
        return obj
    if is_dataclass(obj):
        return _to_serializable(asdict(obj))
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "dict"):
        return obj.dict()
    if hasattr(obj, "__dict__"):
        return {k: _to_serializable(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [_to_serializable(item) for item in obj]
    return str(obj)


# =============================================================================
# Блок 1: Обзор оформления и списка тем Windows
# =============================================================================

@tool
async def windows_personalization_overview(
    action: str = "overview",
) -> str:
    """Обзор текущего оформления Windows (активная тема, темный режим, акцентный цвет, курсор, обои).

    Args:
        action: Операция обзора:
            - 'overview': полный сводный отчёт о персонализации и текущем внешнем виде Windows
            - 'themes': список зарегистрированных и установленных тем оформления (.theme)

    Returns:
        JSON с параметрами оформления или списком доступных тем Windows.
    """
    try:
        from apps.windows.sdk.modules.personalization.manager import get_personalization_manager

        pm = get_personalization_manager()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "overview":
            res = await loop.run_in_executor(None, pm.get_overview)
            return json.dumps({"status": "ok", "action": act, "overview": _to_serializable(res)}, ensure_ascii=False)
        elif act == "themes":
            res = await loop.run_in_executor(None, pm.get_theme_list)
            return json.dumps({"status": "ok", "action": act, "themes": _to_serializable(res)}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.personalization] Ошибка выполнения personalization_overview ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Применение тем и переключение режима Dark Mode
# =============================================================================

@tool
async def windows_personalization_theme_action(
    theme_name_or_path: str,
    force_dark_mode: Optional[bool] = None,
    accent_color_hex: Optional[str] = None,
    operator: str = "AI_AGENT",
) -> str:
    """Применение темы оформления Windows, принудительное переключение темного/светлого режима или акцентного цвета.

    Args:
        theme_name_or_path: Имя установленной темы (например, 'Windows Light', 'Windows Dark') или путь к файлу .theme.
        force_dark_mode: Опциональный флаг принудительного включения тёмного режима (True — тёмный, False — светлый).
        accent_color_hex: Акцентный системный цвет в HEX формате (например, '#0078D7', '#FF5733').
        operator: Имя оператора изменений (по умолчанию 'AI_AGENT').

    Returns:
        JSON с результатом применения темы оформления.
    """
    try:
        from apps.windows.sdk.modules.personalization.manager import get_personalization_manager
        from apps.windows.sdk.modules.personalization.models import ThemeApplyRequest

        pm = get_personalization_manager()
        loop = asyncio.get_running_loop()
        req = ThemeApplyRequest(
            theme_name_or_path=theme_name_or_path,
            force_dark_mode=force_dark_mode,
            accent_color_hex=accent_color_hex,
        )

        res = await loop.run_in_executor(None, pm.apply_theme, req, operator)
        return json.dumps({"status": "ok", "theme": theme_name_or_path, "result": _to_serializable(res)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.personalization] Ошибка применения темы '{theme_name_or_path}': {e}", exc_info=True)
        return json.dumps({"status": "error", "theme": theme_name_or_path, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 3: Указатель мыши и обои рабочего стола
# =============================================================================

@tool
async def windows_personalization_cursor_wallpaper(
    action: str,
    cursor_size: Optional[int] = None,
    cursor_color_scheme: Optional[str] = None,
    custom_color_hex: Optional[str] = None,
    pointer_speed: Optional[int] = None,
    wallpaper_path: Optional[str] = None,
    wallpaper_fit_mode: Optional[str] = None,
    operator: str = "AI_AGENT",
) -> str:
    """Настройка указателя мыши (размер, цвет, скорость) и обоев рабочего стола (путь к фону, режим масштабирования).

    Args:
        action: Цель управления:
            - 'cursor': инспекция или обновление настроек указателя мыши (параметры cursor_size, cursor_color_scheme, custom_color_hex, pointer_speed)
            - 'wallpaper': инспекция или изменение фонового изображения рабочего стола (параметры wallpaper_path, wallpaper_fit_mode)
        cursor_size: Размер указателя мыши в пикселях (1..128 px).
        cursor_color_scheme: Цветовая схема указателя ('white', 'black', 'inverted', 'custom').
        custom_color_hex: Пользовательский цвет указателя HEX (например, '#FF0000').
        pointer_speed: Скорость указателя мыши (1..20).
        wallpaper_path: Абсолютный путь к файлу изображения обоев рабочего стола.
        wallpaper_fit_mode: Режим масштабирования обоев ('fill', 'fit', 'stretch', 'tile', 'center', 'span').
        operator: Имя оператора изменений (по умолчанию 'AI_AGENT').

    Returns:
        JSON с обновившимися параметрами курсора или обоев рабочего стола.
    """
    try:
        from apps.windows.sdk.modules.personalization.manager import get_personalization_manager
        from apps.windows.sdk.modules.personalization.models import (
            CursorColorScheme,
            CursorUpdateRequest,
            WallpaperFitMode,
            WallpaperUpdateRequest,
        )

        pm = get_personalization_manager()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "cursor":
            if any(x is not None for x in (cursor_size, cursor_color_scheme, custom_color_hex, pointer_speed)):
                scheme_enum = CursorColorScheme(cursor_color_scheme.lower()) if cursor_color_scheme else None
                req = CursorUpdateRequest(
                    size=cursor_size,
                    color_scheme=scheme_enum,
                    custom_color_hex=custom_color_hex,
                    pointer_speed=pointer_speed,
                )
                res = await loop.run_in_executor(None, pm.update_cursor, req, operator)
            else:
                res = await loop.run_in_executor(None, pm.get_cursor_settings)
            return json.dumps({"status": "ok", "action": act, "cursor": _to_serializable(res)}, ensure_ascii=False)
        elif act == "wallpaper":
            if wallpaper_path or wallpaper_fit_mode:
                fit_enum = WallpaperFitMode(wallpaper_fit_mode.lower()) if wallpaper_fit_mode else None
                req = WallpaperUpdateRequest(
                    wallpaper_path=wallpaper_path,
                    fit_mode=fit_enum,
                )
                res = await loop.run_in_executor(None, pm.update_wallpaper, req, operator)
            else:
                res = await loop.run_in_executor(None, pm.get_wallpaper_settings)
            return json.dumps({"status": "ok", "action": act, "wallpaper": _to_serializable(res)}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.personalization] Ошибка вызова cursor_wallpaper ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


WINDOWS_PERSONALIZATION_TOOLS = [
    windows_personalization_overview,
    windows_personalization_theme_action,
    windows_personalization_cursor_wallpaper,
]
