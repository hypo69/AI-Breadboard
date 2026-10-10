# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Personalization Models
# =============================================================================
# Description:
#   Pydantic модели данных для подсистемы персонализации Windows:
#   темы, размер и цвет курсора, обои рабочего стола, экран блокировки,
#   Windows Spotlight и интеллектуальный AI Spotlight с метаданными.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.personalization.models import CursorSettings, WallpaperSettings
#
#     cursor = CursorSettings(size=32, color="white", shadow=True)
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.personalization
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 18:30:00
# =============================================================================

from __future__ import annotations
"""Модели данных подсистемы Personalization & Appearance Control Plane."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WallpaperFitMode(str, Enum):
    """Режим отображения / масштабирования обоев."""
    FILL = "fill"          # Заполнение (10)
    FIT = "fit"            # По размеру (6)
    STRETCH = "stretch"    # Растянуть (2)
    TILE = "tile"          # Замостить (0 + TileWallpaper=1)
    CENTER = "center"      # По центру (0 + TileWallpaper=0)
    SPAN = "span"          # Расширение на все мониторы (22)


class WallpaperSourceMode(str, Enum):
    """Источник фонового изображения рабочего стола."""
    PICTURE = "picture"
    SOLID_COLOR = "solid_color"
    SLIDESHOW = "slideshow"
    SPOTLIGHT = "spotlight"


class CursorColorScheme(str, Enum):
    """Цветовая схема указателя мыши."""
    WHITE = "white"
    BLACK = "black"
    INVERTED = "inverted"
    CUSTOM = "custom"


class WindowsThemeInfo(BaseModel):
    """Информация об установленной теме Windows."""
    name: str = Field(..., description="Название темы")
    display_name: str = Field(..., description="Отображаемое наименование темы")
    theme_path: Optional[str] = Field(None, description="Абсолютный путь к файлу .theme")
    is_current: bool = Field(False, description="Является ли тема текущей активной")
    is_dark_mode: bool = Field(False, description="Включен ли темный режим интерфейса")
    accent_color_hex: str = Field("#0078D7", description="Акцентный системный цвет HEX")
    wallpaper_path: Optional[str] = Field(None, description="Путь к фоновому изображению темы")
    cursor_scheme: Optional[str] = Field(None, description="Имя схемы указателей мыши")
    sound_scheme: Optional[str] = Field(None, description="Звуковая схема темы")


class ThemeApplyRequest(BaseModel):
    """Запрос на применение темы оформления."""
    theme_name_or_path: str = Field(..., description="Имя зарегистрированной темы или путь к .theme файлу")
    force_dark_mode: Optional[bool] = Field(None, description="Принудительно переключить режим темной темы")
    accent_color_hex: Optional[str] = Field(None, description="Пользовательский акцентный цвет")


class CursorSettings(BaseModel):
    """Текущие настройки указателя мыши и доступности."""
    size: int = Field(default=32, ge=1, le=128, description="Размер указателя (1..128 px)")
    color_scheme: CursorColorScheme = Field(default=CursorColorScheme.WHITE, description="Цветовая схема указателя")
    custom_color_hex: Optional[str] = Field(None, description="Пользовательский цвет указателя (HEX)")
    shadow: bool = Field(default=True, description="Тень под указателем мыши")
    trails: bool = Field(default=False, description="Шлейф указателя при движении")
    trail_length: int = Field(default=0, ge=0, le=7, description="Длина шлейфа (0..7)")
    hide_while_typing: bool = Field(default=True, description="Скрывать указатель при вводе текста")
    show_location_on_ctrl: bool = Field(default=False, description="Показывать положение указателя при нажатии Ctrl")
    pointer_speed: int = Field(default=10, ge=1, le=20, description="Скорость перемещения указателя (1..20)")


class CursorUpdateRequest(BaseModel):
    """Запрос на обновление настроек курсора."""
    size: Optional[int] = Field(None, ge=1, le=128, description="Размер указателя в пикселях")
    color_scheme: Optional[CursorColorScheme] = Field(None, description="Цветовая схема")
    custom_color_hex: Optional[str] = Field(None, description="Пользовательский цвет HEX")
    shadow: Optional[bool] = Field(None, description="Тень под курсором")
    trails: Optional[bool] = Field(None, description="Шлейф курсора")
    hide_while_typing: Optional[bool] = Field(None, description="Скрывать при наборе текста")
    show_location_on_ctrl: Optional[bool] = Field(None, description="Индикация при нажатии Ctrl")
    pointer_speed: Optional[int] = Field(None, ge=1, le=20, description="Скорость указателя")


class WallpaperSettings(BaseModel):
    """Настройки фонового рисунка рабочего стола и экрана блокировки."""
    mode: WallpaperSourceMode = Field(default=WallpaperSourceMode.PICTURE, description="Режим источника обоев")
    current_wallpaper_path: Optional[str] = Field(None, description="Путь к текущему файлу обоев рабочего стола")
    fit_mode: WallpaperFitMode = Field(default=WallpaperFitMode.FILL, description="Режим масштабирования изображения")
    background_color_hex: str = Field(default="#000000", description="Сплошной фоновый цвет (HEX)")
    slideshow_folder: Optional[str] = Field(None, description="Папка для слайд-шоу обоев")
    slideshow_interval_sec: int = Field(default=1800, ge=10, description="Интервал смены изображений в секундах")
    slideshow_shuffle: bool = Field(default=True, description="Случайный порядок показа слайд-шоу")
    span_across_monitors: bool = Field(default=False, description="Растягивать одно изображение на все мониторы")
    lock_screen_image_path: Optional[str] = Field(None, description="Путь к обоям экрана блокировки")


class WallpaperUpdateRequest(BaseModel):
    """Запрос на изменение обоев рабочего стола."""
    mode: Optional[WallpaperSourceMode] = Field(None, description="Режим источника обоев")
    image_path: Optional[str] = Field(None, description="Абсолютный путь к файлу изображения")
    fit_mode: Optional[WallpaperFitMode] = Field(None, description="Режим масштабирования")
    background_color_hex: Optional[str] = Field(None, description="Фоновый цвет HEX")
    slideshow_folder: Optional[str] = Field(None, description="Папка со слайд-шоу")
    slideshow_interval_sec: Optional[int] = Field(None, description="Интервал смены")
    slideshow_shuffle: Optional[bool] = Field(None, description="Случайный порядок")
    span_across_monitors: Optional[bool] = Field(None, description="Растягивание на мониторы")
    apply_to_lock_screen: bool = Field(default=False, description="Применить также к экрану блокировки")


class WindowsSpotlightSettings(BaseModel):
    """Настройки службы Windows Spotlight (Интересное от Windows)."""
    enabled_desktop: bool = Field(default=False, description="Включен ли Spotlight для рабочего стола")
    enabled_lock_screen: bool = Field(default=True, description="Включен ли Spotlight для экрана блокировки")
    allow_fun_facts: bool = Field(default=True, description="Отображение интересных фактов и подсказок")
    allow_suggestions: bool = Field(default=False, description="Отображение рекомендаций и подсказок от партнеров")
    allow_third_party_content: bool = Field(default=False, description="Разрешение стороннего контента в Spotlight")
    current_image_title: Optional[str] = Field(None, description="Заголовок текущей фотографии Spotlight")
    current_image_description: Optional[str] = Field(None, description="Описание текущей фотографии Spotlight")
    learn_about_url: Optional[str] = Field(None, description="Ссылка 'Learn about this picture'")


class SpotlightUpdateRequest(BaseModel):
    """Запрос на настройку параметров Windows Spotlight."""
    enabled_desktop: Optional[bool] = Field(None, description="Включить/выключить Spotlight на рабочем столе")
    enabled_lock_screen: Optional[bool] = Field(None, description="Включить/выключить Spotlight на экране блокировки")
    allow_fun_facts: Optional[bool] = Field(None, description="Разрешить интересные факты")
    allow_suggestions: Optional[bool] = Field(None, description="Разрешить рекомендации")


class AISpotlightLocation(BaseModel):
    """Географические координаты и локация изображения."""
    country: Optional[str] = Field(None, description="Страна")
    city_or_region: Optional[str] = Field(None, description="Город или регион")
    landmark: Optional[str] = Field(None, description="Достопримечательность или объект")
    latitude: Optional[float] = Field(None, description="Широта GPS")
    longitude: Optional[float] = Field(None, description="Долгота GPS")


class AISpotlightImageInfo(BaseModel):
    """Карточка медиа-интеллекта фотографии (AI Spotlight / О фотографии)."""
    image_id: str = Field(..., description="Уникальный идентификатор изображения (хэш или UUID)")
    image_path: str = Field(..., description="Абсолютный путь к файлу изображения")
    file_name: str = Field(..., description="Имя файла")
    title: str = Field(..., description="Название или заголовок сюжета")
    description_ru: str = Field(..., description="Развернутое описание и познавательная справка на русском языке")
    location: Optional[AISpotlightLocation] = Field(None, description="Географическая привязка")
    objects_detected: List[str] = Field(default_factory=list, description="Распознанные объекты и ландшафты")
    historical_era: Optional[str] = Field(None, description="Историческая эпоха или период")
    fun_facts: List[str] = Field(default_factory=list, description="Интересные факты о месте или явлении")
    sources: List[str] = Field(default_factory=list, description="Источники информации (Wikipedia, Wikimedia, AI KB)")
    resolution: Optional[str] = Field(None, description="Разрешение изображения (например: 3840x2160)")
    file_size_mb: Optional[float] = Field(None, description="Размер файла в мегабайтах")
    analyzed_at: str = Field(..., description="Дата и время анализа ISO-8601")
    is_current_wallpaper: bool = Field(False, description="Является ли текущими обоями")


class AISpotlightAnalysisRequest(BaseModel):
    """Запрос на проведение AI-анализа изображения."""
    image_path: Optional[str] = Field(None, description="Путь к изображению (если None, берется текущий рабочий стол)")
    prompt_focus: Optional[str] = Field(None, description="Дополнительный фокус анализа (география, история, природа)")
    save_to_catalog: bool = Field(True, description="Сохранить результат в локальную медиа-базу")


class PersonalizationOverviewResponse(BaseModel):
    """Сводный статус подсистемы Personalization Control Plane."""
    current_theme: str
    is_dark_mode: bool
    accent_color_hex: str
    cursor: CursorSettings
    wallpaper: WallpaperSettings
    spotlight: WindowsSpotlightSettings
    ai_spotlight_current: Optional[AISpotlightImageInfo] = None
    available_themes_count: int = 0
    saved_ai_spotlight_count: int = 0
