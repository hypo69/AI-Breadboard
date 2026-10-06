# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router Focus
# =============================================================================
# Description:
#   API роутер управления сессиями фокусировки внимания (Windows Focus Sessions),
#   режимом «Не беспокоить» (Do Not Disturb / Quiet Hours), поведением бейджей
#   и мигания панели задач, а также вызовом системных протоколов ms-clock / ms-settings.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_focus import init_router
#
#     router = init_router()
#
# File: router_focus.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 19:35:00
# =============================================================================

from __future__ import annotations
"""API роутер управления сессиями фокусировки внимания (Windows Focus) и режимом «Не беспокоить»."""

import asyncio
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from logger import logger

try:
    import winreg
except ImportError:
    winreg = None  # Для сред тестирования не под Windows


class FocusSettingsDTO(BaseModel):
    """Модель настроек режима фокусировки внимания."""
    session_duration_minutes: int = Field(30, ge=5, le=240, description="Длительность сессии в минутах")
    show_timer_in_clock_app: bool = Field(True, description="Отображать таймер в приложении «Часы»")
    hide_badges_on_taskbar: bool = Field(True, description="Скрывать значки уведомлений (бейджи) на панели задач")
    hide_flashing_on_taskbar: bool = Field(True, description="Скрывать мигание приложений на панели задач")
    turn_on_do_not_disturb: bool = Field(True, description="Включать режим «Не беспокоить» (Do Not Disturb)")


class FocusSessionStateDTO(BaseModel):
    """Модель текущего состояния сессии фокусировки."""
    is_active: bool = Field(False, description="Флаг активности сессии фокусировки")
    session_duration_minutes: int = Field(30, description="Продолжительность текущей или запланированной сессии")
    started_at: Optional[str] = Field(None, description="ISO метка времени старта")
    ends_at: Optional[str] = Field(None, description="ISO метка времени завершения")
    remaining_seconds: int = Field(0, description="Оставшееся время сессии в секундах")
    settings: FocusSettingsDTO = Field(default_factory=FocusSettingsDTO, description="Текущие настройки фокусировки")


class FocusSessionManager:
    """Менеджер управления сессиями фокусировки и системными ключами реестра."""

    def __init__(self) -> None:
        """Инициализация менеджера сессий фокусировки."""
        self._is_active: bool = False
        self._session_duration_minutes: int = 30
        self._started_at_ts: float = 0.0
        self._ends_at_ts: float = 0.0
        self._task: Optional[asyncio.Task] = None
        self._backup_state: Dict[str, Any] = {}
        self._settings = FocusSettingsDTO()

    def get_state(self) -> FocusSessionStateDTO:
        """Возвращает текущее состояние сессии фокусировки и системных параметров.

        Returns:
            FocusSessionStateDTO: Объект состояния сессии.
        """
        now = time.time()
        remaining = 0
        if self._is_active:
            if now < self._ends_at_ts:
                remaining = int(self._ends_at_ts - now)
            else:
                self._is_active = False
                remaining = 0

        started_iso = datetime.fromtimestamp(self._started_at_ts, tz=timezone.utc).isoformat() if self._is_active else None
        ends_iso = datetime.fromtimestamp(self._ends_at_ts, tz=timezone.utc).isoformat() if self._is_active else None

        # Читаем реальные системные флаги из реестра (если не в активной сессии)
        live_settings = self._read_system_settings()

        return FocusSessionStateDTO(
            is_active=self._is_active,
            session_duration_minutes=self._session_duration_minutes,
            started_at=started_iso,
            ends_at=ends_iso,
            remaining_seconds=remaining,
            settings=live_settings,
        )

    def _read_system_settings(self) -> FocusSettingsDTO:
        """Считывает текущие системные параметры из реестра Windows.

        Returns:
            FocusSettingsDTO: Настройки, прочитанные из системы.
        """
        hide_badges = self._settings.hide_badges_on_taskbar
        hide_flashing = self._settings.hide_flashing_on_taskbar
        dnd = self._settings.turn_on_do_not_disturb
        show_timer = self._settings.show_timer_in_clock_app

        if winreg:
            try:
                # 1. Проверяем бейджи на панели задач (TaskbarBadges: 0 = скрыты, 1 = показаны)
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", 0, winreg.KEY_READ) as key:
                    try:
                        val, _ = winreg.QueryValueEx(key, "TaskbarBadges")
                        hide_badges = (val == 0)
                    except FileNotFoundError:
                        pass
            except Exception as exc:
                logger.debug(f"[FocusManager] Ошибка чтения TaskbarBadges: {exc}")

            try:
                # 2. Проверяем мигание (TaskbarFlashing: 0 = отключено, 1 = включено)
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", 0, winreg.KEY_READ) as key:
                    try:
                        val, _ = winreg.QueryValueEx(key, "TaskbarFlashing")
                        hide_flashing = (val == 0)
                    except FileNotFoundError:
                        pass
            except Exception as exc:
                logger.debug(f"[FocusManager] Ошибка чтения TaskbarFlashing: {exc}")

            try:
                # 3. Режим уведомлений (NOC_GLOBAL_SETTING_TOASTS_ENABLED: 0 = DND/выключены, 1 = включены)
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings", 0, winreg.KEY_READ) as key:
                    try:
                        val, _ = winreg.QueryValueEx(key, "NOC_GLOBAL_SETTING_TOASTS_ENABLED")
                        dnd = (val == 0)
                    except FileNotFoundError:
                        pass
            except Exception as exc:
                logger.debug(f"[FocusManager] Ошибка чтения уведомлений DND: {exc}")

        return FocusSettingsDTO(
            session_duration_minutes=self._session_duration_minutes,
            show_timer_in_clock_app=show_timer,
            hide_badges_on_taskbar=hide_badges,
            hide_flashing_on_taskbar=hide_flashing,
            turn_on_do_not_disturb=dnd,
        )

    def update_settings(self, new_settings: FocusSettingsDTO) -> FocusSettingsDTO:
        """Сохраняет обновленные параметры фокусировки.

        Args:
            new_settings: Новый набор настроек.

        Returns:
            FocusSettingsDTO: Актуальные настройки.
        """
        self._settings = new_settings
        self._session_duration_minutes = new_settings.session_duration_minutes
        return self._settings

    async def start_session(self, duration_minutes: Optional[int] = None) -> FocusSessionStateDTO:
        """Запускает сессию фокусировки внимания.

        Args:
            duration_minutes: Длительность в минутах (если переопределена).

        Returns:
            FocusSessionStateDTO: Новое состояние сессии.
        """
        if duration_minutes:
            self._session_duration_minutes = max(5, min(240, duration_minutes))

        now = time.time()
        self._is_active = True
        self._started_at_ts = now
        self._ends_at_ts = now + (self._session_duration_minutes * 60)

        # Сохраняем резервную копию системного состояния для восстановления
        self._backup_state = {
            "applied": True,
            "dnd_applied": self._settings.turn_on_do_not_disturb,
            "badges_applied": self._settings.hide_badges_on_taskbar,
            "flashing_applied": self._settings.hide_flashing_on_taskbar,
        }

        # Применяем системные ограничения фокуса
        self._apply_focus_state(
            dnd=self._settings.turn_on_do_not_disturb,
            hide_badges=self._settings.hide_badges_on_taskbar,
            hide_flashing=self._settings.hide_flashing_on_taskbar,
        )

        # Открываем Windows Clock / Focus если запрошено
        if self._settings.show_timer_in_clock_app:
            self.launch_clock_focus_app()

        logger.info(f"[FocusManager] Сессия фокусировки активирована на {self._session_duration_minutes} мин")
        return self.get_state()

    def stop_session(self) -> FocusSessionStateDTO:
        """Останавливает сессию фокусировки и восстанавливает параметры.

        Returns:
            FocusSessionStateDTO: Обновленное состояние сессии.
        """
        if self._is_active:
            self._is_active = False
            # Восстанавливаем обычный режим (выключаем DND, возвращаем бейджи и мигание)
            self._apply_focus_state(dnd=False, hide_badges=False, hide_flashing=False)
            logger.info("[FocusManager] Сессия фокусировки остановлена пользователем")

        return self.get_state()

    def _apply_focus_state(self, dnd: bool, hide_badges: bool, hide_flashing: bool) -> None:
        """Применяет параметры в системный реестр Windows.

        Args:
            dnd: Включить режим «Не беспокоить».
            hide_badges: Скрыть бейджи значков панели задач.
            hide_flashing: Скрыть мигание панели задач.
        """
        if not winreg:
            return

        try:
            # 1. Бейджи панели задач (0 = скрыть, 1 = показать)
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced") as key:
                winreg.SetValueEx(key, "TaskbarBadges", 0, winreg.REG_DWORD, 0 if hide_badges else 1)
                winreg.SetValueEx(key, "TaskbarFlashing", 0, winreg.REG_DWORD, 0 if hide_flashing else 1)
        except Exception as exc:
            logger.warning(f"[FocusManager] Ошибка установки параметров панели задач: {exc}")

        try:
            # 2. Уведомления Do Not Disturb (0 = выключены / DND, 1 = включены)
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings") as key:
                winreg.SetValueEx(key, "NOC_GLOBAL_SETTING_TOASTS_ENABLED", 0, winreg.REG_DWORD, 0 if dnd else 1)
        except Exception as exc:
            logger.warning(f"[FocusManager] Ошибка установки DND в реестре: {exc}")

    @staticmethod
    def launch_clock_focus_app() -> bool:
        """Запускает системное приложение «Часы» в режиме Focus Sessions.

        Returns:
            bool: True если команда успешно отправлена.
        """
        try:
            if sys.platform == "win32":
                os.startfile("ms-clock:focus")
                return True
        except Exception as exc:
            logger.debug(f"[FocusManager] Не удалось открыть ms-clock:focus ({exc}), пробуем ms-settings:quiethours")
            try:
                if sys.platform == "win32":
                    os.startfile("ms-settings:quiethours")
                    return True
            except Exception:
                pass
        return False

    @staticmethod
    def launch_settings_app() -> bool:
        """Открывает системные параметры Windows в разделе Focus / Фокусировка внимания.

        Returns:
            bool: True если окно успешно открыто.
        """
        try:
            if sys.platform == "win32":
                os.startfile("ms-settings:quiethours")
                return True
        except Exception as exc:
            logger.warning(f"[FocusManager] Ошибка открытия ms-settings:quiethours: {exc}")
        return False


_manager = FocusSessionManager()


def init_router() -> APIRouter:
    """Инициализация и получение роутера FastAPI для управления Focus.

    Returns:
        APIRouter: Экземпляр настроенного роутера.
    """
    router = APIRouter(prefix="/api/windows/focus", tags=["Windows Focus Sessions"])

    @router.get("/state", response_model=FocusSessionStateDTO)
    async def get_focus_state() -> FocusSessionStateDTO:
        """Получить текущее состояние сессии фокусировки внимания и системных опций."""
        return _manager.get_state()

    @router.post("/session/start", response_model=FocusSessionStateDTO)
    async def start_focus_session(duration_minutes: Optional[int] = None) -> FocusSessionStateDTO:
        """Запустить новую сессию фокусировки внимания."""
        return await _manager.start_session(duration_minutes)

    @router.post("/session/stop", response_model=FocusSessionStateDTO)
    async def stop_focus_session() -> FocusSessionStateDTO:
        """Остановить текущую сессию фокусировки и восстановить параметры."""
        return _manager.stop_session()

    @router.post("/settings", response_model=FocusSettingsDTO)
    async def update_focus_settings(settings: FocusSettingsDTO) -> FocusSettingsDTO:
        """Обновить постоянные настройки фокусировки внимания."""
        return _manager.update_settings(settings)

    @router.post("/open-settings")
    async def open_windows_focus_settings() -> Dict[str, Any]:
        """Открыть системное окно «Фокусировка внимания» (ms-settings:quiethours) в Windows."""
        opened = _manager.launch_settings_app()
        return {"success": opened, "target": "ms-settings:quiethours"}

    @router.post("/open-clock")
    async def open_windows_clock_app() -> Dict[str, Any]:
        """Открыть приложение «Часы» в разделе сессий фокусировки (ms-clock:focus)."""
        opened = _manager.launch_clock_focus_app()
        return {"success": opened, "target": "ms-clock:focus"}

    return router


__all__ = ["init_router", "FocusSettingsDTO", "FocusSessionStateDTO", "FocusSessionManager"]
