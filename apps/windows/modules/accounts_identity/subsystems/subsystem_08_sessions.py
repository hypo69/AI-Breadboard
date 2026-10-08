# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Subsystem 08 Sessions & Logon
# =============================================================================
# Description:
#   Подсистема 08: Сессии входа WTS (Windows Terminal Services), инспекция
#   консольных и RDP-сеансов, отслеживание времени входа и управление сессиями.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.accounts_identity.subsystems.subsystem_08_sessions import SessionsSubsystem
#
#     subsys = SessionsSubsystem()
#     sessions = subsys.list_sessions()
#
# File: subsystem_08_sessions.py
# Project: ai-breadboard
# Package: apps.windows.modules.accounts_identity.subsystems
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 00:50:00
# =============================================================================

"""Подсистема управления сессиями входа (WTS / Terminal Sessions)."""

from __future__ import annotations

import getpass
import re
from typing import Any, Dict, List, Optional

from logger import logger
from apps.windows.modules.accounts_identity.models import SessionDetails
from apps.windows.modules.accounts_identity.win32_bridge import Win32IdentityBridge


class SessionsSubsystem:
    """Подсистема перечисления и контроля терминальных и локальных сессий."""

    def __init__(self, bridge: Optional[Win32IdentityBridge] = None) -> None:
        """
        Инициализация подсистемы сессий.

        Args:
            bridge: Мост вызовов Windows API.
        """
        self.bridge = bridge or Win32IdentityBridge()

    def list_sessions(self) -> List[SessionDetails]:
        """127-138. Перечисляет все текущие сеансы работы пользователей."""
        sessions: List[SessionDetails] = []
        # Запрос через qwinsta
        _, out, _ = self.bridge.run_command(["qwinsta"])
        current_user = getpass.getuser().lower()

        for line in out.splitlines():
            line_str = line.strip()
            if not line_str or line_str.startswith("SESSIONNAME") or line_str.startswith("СЕАНС"):
                continue

            # Парсинг строки qwinsta: SESSIONNAME USERNAME ID STATE TYPE DEVICE
            # Например: >console           onela                     1  Active
            is_current = line_str.startswith(">")
            cleaned = line_str.lstrip(">").strip()
            parts = cleaned.split()

            if len(parts) >= 3:
                s_name = parts[0]
                # Проверка если username отсутствует в строке (служебная сессия)
                if parts[1].isdigit():
                    s_user = ""
                    s_id = int(parts[1])
                    s_state = parts[2] if len(parts) > 2 else "Active"
                else:
                    s_user = parts[1]
                    s_id = int(parts[2]) if parts[2].isdigit() else 0
                    s_state = parts[3] if len(parts) > 3 else "Active"

                s_type = "Console" if "console" in s_name.lower() else ("RDP" if "rdp" in s_name.lower() else "Terminal")

                sessions.append(
                    SessionDetails(
                        session_id=s_id,
                        user_name=s_user,
                        state=s_state,
                        session_type=s_type,
                        is_current=is_current or (s_user.lower() == current_user),
                    )
                )

        if not sessions:
            # Дефолтная активная консольная сессия
            sessions.append(
                SessionDetails(
                    session_id=1,
                    user_name=getpass.getuser(),
                    state="Active",
                    session_type="Console",
                    is_current=True,
                )
            )

        return sessions

    def get_session(self, session_id: int) -> Optional[SessionDetails]:
        """128. Получает параметры сессии по ее ID."""
        for s in self.list_sessions():
            if s.session_id == session_id:
                return s
        return None

    def disconnect_session(self, session_id: int) -> bool:
        """139. Отключает сессию без завершения процессов (tsdiscon)."""
        ret, _, _ = self.bridge.run_command(["tsdiscon", str(session_id)])
        return ret == 0

    def logoff_session(self, session_id: int) -> bool:
        """140. Завершает сеанс пользователя и все его процессы (logoff)."""
        ret, _, _ = self.bridge.run_command(["logoff", str(session_id)])
        return ret == 0
