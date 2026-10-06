# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Focus_Policy - Listener
# =============================================================================
# Description:
#   Обертка над WinRT UserNotificationListener (Windows 10 1607+/11) с корректной
#   деградацией, если пакет winrt или права доступа недоступны.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.focus_policy.listener import WinRtNotificationListener
#
#     status = WinRtNotificationListener().request_access()
#
# File: listener.py
# Project: ai-breadboard
# Package: apps.windows.modules.focus_policy
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 22:05:00
# =============================================================================

from __future__ import annotations
"""Синхронный адаптер UserNotificationListener."""

import asyncio
from typing import Any, List

from logger import logger
from apps.windows.modules.focus_policy.models import ListenerNotification

try:
    from winrt.windows.ui.notifications import NotificationKinds
    from winrt.windows.ui.notifications.management import UserNotificationListener
except ImportError:  # пакет winrt-Windows.UI.Notifications.Management не установлен
    UserNotificationListener = None
    NotificationKinds = None


class WinRtNotificationListener:
    """Перехват и удаление Toast-уведомлений через WinRT."""

    def __init__(self) -> None:
        self._listener: Any = UserNotificationListener.current if UserNotificationListener else None

    def request_access(self) -> str:
        """Запрашивает доступ; возвращает ``Allowed``/``Denied``/``Unspecified``."""
        if self._listener is None:
            logger.warning('[FocusListener] winrt недоступен: режим без архивации уведомлений')
            return 'Unspecified'
        try:
            status = asyncio.run(self._listener.request_access_async())
            return {1: 'Allowed', 2: 'Denied'}.get(int(status), 'Unspecified')
        except Exception as exc:
            logger.warning(f'[FocusListener] Ошибка RequestAccessAsync: {exc}')
            return 'Unspecified'

    def get_toasts(self) -> List[ListenerNotification]:
        """Возвращает текущие Toast-уведомления центра уведомлений."""
        if self._listener is None:
            return []
        result: List[ListenerNotification] = []
        for n in asyncio.run(self._listener.get_notifications_async(NotificationKinds.TOAST)):
            texts: List[str] = []
            try:
                binding = n.notification.visual.get_binding('ToastGeneric')
                texts = [t.text for t in binding.get_text_elements()] if binding else []
            except Exception as exc:
                logger.debug(f'[FocusListener] Не удалось прочитать текст уведомления {n.id}: {exc}')
            info = n.app_info
            result.append(ListenerNotification(
                id=int(n.id),
                app_user_model_id=info.app_user_model_id,
                app_display_name=info.display_info.display_name,
                title=texts[0] if texts else None,
                text='\n'.join(texts[1:]) or None,
            ))
        return result

    def remove(self, notification_id: int) -> None:
        """Удаляет уведомление, чтобы убрать плашку с экрана."""
        if self._listener is not None:
            self._listener.remove_notification(notification_id)
