# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Subsystem 05 Authentication & Policy
# =============================================================================
# Description:
#   Подсистема 05: Политики безопасности паролей, блокировки аккаунтов,
#   ограничения часов входа и рабочих станций (Logon Restrictions).
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.accounts_identity.subsystems.subsystem_05_auth import AuthPolicySubsystem
#
#     subsys = AuthPolicySubsystem()
#     policy = subsys.get_password_policy()
#
# File: subsystem_05_auth.py
# Project: ai-breadboard
# Package: apps.windows.modules.accounts_identity.subsystems
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 00:50:00
# =============================================================================

"""Подсистема политик аутентификации, паролей и ограничений входа."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from logger import logger
from apps.windows.modules.accounts_identity.models import PasswordPolicy
from apps.windows.modules.accounts_identity.win32_bridge import Win32IdentityBridge


class AuthPolicySubsystem:
    """Подсистема управления политиками паролей и ограничений входа SAM."""

    def __init__(self, bridge: Optional[Win32IdentityBridge] = None) -> None:
        """
        Инициализация подсистемы аутентификации.

        Args:
            bridge: Мост вызовов Windows API.
        """
        self.bridge = bridge or Win32IdentityBridge()

    def get_password_policy(self) -> PasswordPolicy:
        """38-41, 44, 46. Получает глобальные параметры политики паролей и блокировок."""
        _, out, _ = self.bridge.run_command(["net", "accounts"])
        policy = PasswordPolicy()
        for line in out.splitlines():
            line_str = line.strip()
            # Минимальная длина пароля
            if "minimum password length" in line_str.lower() or "минимальная длина пароля" in line_str.lower():
                m = re.search(r"\d+", line_str)
                if m:
                    policy.min_password_length = int(m.group())
            # Максимальный срок действия пароля
            elif "maximum password age" in line_str.lower() or "максимальный срок действия пароля" in line_str.lower():
                m = re.search(r"\d+", line_str)
                if m:
                    policy.max_password_age_days = int(m.group())
            # Минимальный срок действия пароля
            elif "minimum password age" in line_str.lower() or "минимальный срок действия пароля" in line_str.lower():
                m = re.search(r"\d+", line_str)
                if m:
                    policy.min_password_age_days = int(m.group())
            # Длина истории паролей
            elif "length of password history" in line_str.lower() or "длина истории паролей" in line_str.lower():
                m = re.search(r"\d+", line_str)
                if m:
                    policy.password_history_length = int(m.group())
            # Порог блокировки
            elif "lockout threshold" in line_str.lower() or "порог блокировки" in line_str.lower():
                m = re.search(r"\d+", line_str)
                if m:
                    policy.lockout_threshold = int(m.group())
            # Длительность блокировки
            elif "lockout duration" in line_str.lower() or "продолжительность блокировки" in line_str.lower():
                m = re.search(r"\d+", line_str)
                if m:
                    policy.lockout_duration_minutes = int(m.group())
            # Окно сброса блокировки
            elif "lockout observation window" in line_str.lower() or "окно наблюдения" in line_str.lower():
                m = re.search(r"\d+", line_str)
                if m:
                    policy.lockout_window_minutes = int(m.group())
        return policy

    def set_password_policy(
        self,
        min_length: Optional[int] = None,
        max_age_days: Optional[int] = None,
        history_length: Optional[int] = None,
        lockout_threshold: Optional[int] = None,
    ) -> bool:
        """45. Обновляет параметры политики паролей (NetUserModalsSet)."""
        args = ["net", "accounts"]
        if min_length is not None:
            args.append(f"/minpwlen:{min_length}")
        if max_age_days is not None:
            args.append(f"/maxpwage:{max_age_days}")
        if history_length is not None:
            args.append(f"/uniquepw:{history_length}")
        if lockout_threshold is not None:
            args.append(f"/lockoutthreshold:{lockout_threshold}")

        if len(args) == 2:
            return True
        ret, _, _ = self.bridge.run_command(args)
        return ret == 0

    def reset_user_password(self, username: str, new_password: str) -> bool:
        """43. Административный сброс пароля пользователя."""
        cmd = f"$pwd = ConvertTo-SecureString '{new_password}' -AsPlainText -Force; Set-LocalUser -Name '{username}' -Password $pwd"
        ret, _, _ = self.bridge.run_command(["powershell.exe", "-NoProfile", "-Command", cmd])
        return ret == 0

    def get_logon_hours(self, username: str) -> Optional[str]:
        """47. Возвращает разрешенные часы входа."""
        _, out, _ = self.bridge.run_command(["net", "user", username])
        for line in out.splitlines():
            if "logon hours allowed" in line.lower() or "разрешенные часы входа" in line.lower():
                parts = line.split(":", 1)
                return parts[1].strip() if len(parts) > 1 else ""
        return "All"

    def set_logon_hours(self, username: str, times_str: str) -> bool:
        """48. Устанавливает разрешенные часы входа (например: 'M-F,8am-5pm')."""
        ret, _, _ = self.bridge.run_command(["net", "user", username, f"/times:{times_str}"])
        return ret == 0

    def get_logon_workstations(self, username: str) -> Optional[str]:
        """49. Возвращает разрешенные рабочие станции."""
        _, out, _ = self.bridge.run_command(["net", "user", username])
        for line in out.splitlines():
            if "workstations allowed" in line.lower() or "разрешенные рабочие станции" in line.lower():
                parts = line.split(":", 1)
                return parts[1].strip() if len(parts) > 1 else ""
        return "All"

    def set_logon_workstations(self, username: str, workstations_str: str) -> bool:
        """50. Устанавливает список рабочих станций для входа."""
        ret, _, _ = self.bridge.run_command(["net", "user", username, f"/workstations:{workstations_str}"])
        return ret == 0
