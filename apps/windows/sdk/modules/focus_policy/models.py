# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Focus_Policy - Models
# =============================================================================
# Description:
#   Модели данных Focus Policy Engine: профили фокусировки, уведомления, статус, итог сессии.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.focus_policy.models import FocusProfile
#
#     profile = FocusProfile(profile_id='p1', name='Работа')
#
# File: models.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.focus_policy
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 22:05:00
# =============================================================================

from __future__ import annotations
"""Pydantic-модели подсистемы Focus Policy Engine."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class FocusSchedule(BaseModel):
    """Расписание профиля."""
    days: List[str] = Field(default_factory=lambda: ['mon', 'tue', 'wed', 'thu', 'fri'])
    start_time: str = Field('09:00', pattern=r'^\d{2}:\d{2}$')
    end_time: str = Field('18:00', pattern=r'^\d{2}:\d{2}$')
    auto_start: bool = True


class FocusNotifications(BaseModel):
    """Правила обработки уведомлений."""
    mode: str = 'suppress_and_store'
    allow_priority_apps: List[str] = Field(default_factory=list)
    store_suppressed: bool = True
    show_summary_at_end: bool = True


class FocusTaskbar(BaseModel):
    """Параметры панели задач."""
    suppress_flashing: bool = True
    suppress_badges: bool = True


class FocusAudio(BaseModel):
    """Параметры звука."""
    mute_notification_sounds: bool = True


class FocusDisplay(BaseModel):
    """Параметры отображения."""
    suppress_toast_banners: bool = True


class FocusProfile(BaseModel):
    """Декларативный профиль фокусировки (хранится в focus_profiles.profile_json)."""
    profile_id: str = Field(pattern=r'^[A-Za-z0-9_\-]+$')
    name: str
    schedule: FocusSchedule = Field(default_factory=FocusSchedule)
    notifications: FocusNotifications = Field(default_factory=FocusNotifications)
    taskbar: FocusTaskbar = Field(default_factory=FocusTaskbar)
    audio: FocusAudio = Field(default_factory=FocusAudio)
    display: FocusDisplay = Field(default_factory=FocusDisplay)


class ListenerNotification(BaseModel):
    """Toast-уведомление, полученное от UserNotificationListener."""
    id: int
    app_user_model_id: Optional[str] = None
    app_display_name: str = ''
    title: Optional[str] = None
    text: Optional[str] = None


class SuppressedNotification(ListenerNotification):
    """Архивная запись подавленного уведомления."""
    notification_id: int = 0
    session_id: str = ''
    profile_id: str = ''
    received_at: str = ''
    is_read: bool = False


class FocusStatus(BaseModel):
    """Состояние WindowsFocusController."""
    is_focus_active: bool = False
    active_profile_id: Optional[str] = None
    active_profile_name: Optional[str] = None
    session_id: Optional[str] = None
    session_started_at: Optional[str] = None
    scheduled_end_at: Optional[str] = None
    suppressed_notifications_count: int = 0
    listener_access_status: str = 'Unspecified'


class SessionSummary(BaseModel):
    """Итог завершенной сессии (Post-Session Summary)."""
    session_id: str
    profile_id: str
    total_suppressed: int = 0
    by_app: Dict[str, int] = Field(default_factory=dict)
