# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Subsystem 09 User Profiles
# =============================================================================
# Description:
#   Подсистема 09: Профили пользователей Windows (User Profiles, NTUSER.DAT,
#   реестровый ProfileList, аудит осиротевших профилей и аккаунтов без папок).
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.accounts_identity.subsystems.subsystem_09_profiles import ProfilesSubsystem
#
#     subsys = ProfilesSubsystem()
#     profiles = subsys.list_profiles()
#
# File: subsystem_09_profiles.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.accounts_identity.subsystems
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 00:50:00
# =============================================================================

"""Подсистема анализа и аудита профилей пользователей Windows."""

from __future__ import annotations

import os
import winreg
from typing import Any, Dict, List, Optional

from logger import logger
from apps.windows.sdk.modules.accounts_identity.models import ProfileDetails, ProfileType
from apps.windows.sdk.modules.accounts_identity.win32_bridge import Win32IdentityBridge


class ProfilesSubsystem:
    """Подсистема работы с профилями пользователей файловой системы и реестра."""

    def __init__(self, bridge: Optional[Win32IdentityBridge] = None) -> None:
        """
        Инициализация подсистемы профилей.

        Args:
            bridge: Мост вызовов Windows API.
        """
        self.bridge = bridge or Win32IdentityBridge()

    def get_profiles_root_dir(self) -> str:
        """142. Возвращает корневую директорию профилей (обычно C:\\Users)."""
        drive = os.environ.get("SystemDrive", "C:")
        return os.path.join(drive, "Users")

    def get_default_profile_dir(self) -> str:
        """143. Возвращает путь к эталонному профилю по умолчанию."""
        return os.path.join(self.get_profiles_root_dir(), "Default")

    def get_all_users_profile_dir(self) -> str:
        """144. Возвращает путь к профилю всех пользователей (ProgramData)."""
        drive = os.environ.get("SystemDrive", "C:")
        return os.path.join(drive, "ProgramData")

    def list_profiles(self) -> List[ProfileDetails]:
        """145-152. Считывает все профили из ветки реестра ProfileList."""
        profiles: List[ProfileDetails] = []
        profile_list_key = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, profile_list_key) as key:
                num_subkeys = winreg.QueryInfoKey(key)[0]
                for i in range(num_subkeys):
                    sid_str = winreg.EnumKey(key, i)
                    try:
                        with winreg.OpenKey(key, sid_str) as subkey:
                            profile_path = ""
                            state = 0
                            try:
                                profile_path = str(winreg.QueryValueEx(subkey, "ProfileImagePath")[0])
                            except OSError:
                                pass
                            try:
                                state = int(winreg.QueryValueEx(subkey, "State")[0])
                            except OSError:
                                pass

                            ntuser_path = os.path.join(profile_path, "NTUSER.DAT") if profile_path else ""
                            is_loaded = os.path.exists(ntuser_path)

                            # Разрешение имени
                            name_info = self.bridge.lookup_sid_to_name(sid_str)
                            username = name_info[0] if name_info else os.path.basename(profile_path)

                            # Проверка на осиротевший профиль
                            is_orphaned = name_info is None and not self.bridge.check_is_valid_sid(sid_str)

                            profiles.append(
                                ProfileDetails(
                                    sid=sid_str,
                                    username=username,
                                    profile_path=profile_path,
                                    profile_type=ProfileType.LOCAL,
                                    is_loaded=is_loaded,
                                    state_flags=state,
                                    registry_hive_path=ntuser_path,
                                    is_orphaned=is_orphaned,
                                )
                            )
                    except Exception as sub_e:
                        logger.debug(f"Ошибка чтения профиля {sid_str}: {sub_e}")
        except Exception as e:
            logger.debug(f"Ошибка открытия ProfileList: {e}")

        return profiles

    def find_orphaned_profiles(self) -> List[ProfileDetails]:
        """153. Находит папки профилей или записи реестра без живых учетных записей."""
        all_profiles = self.list_profiles()
        orphaned: List[ProfileDetails] = []
        for p in all_profiles:
            # Если SID не разрешается в имя или папка профиля отсутствует на диске
            name_info = self.bridge.lookup_sid_to_name(p.sid)
            folder_exists = os.path.exists(p.profile_path) if p.profile_path else False
            if name_info is None or not folder_exists:
                p.is_orphaned = True
                orphaned.append(p)
        return orphaned

    def find_accounts_without_profiles(self, existing_usernames: List[str]) -> List[str]:
        """154. Находит учетные записи, у которых отсутствует зарегистрированный профиль."""
        profile_users = {p.username.lower() for p in self.list_profiles()}
        accounts_without: List[str] = []
        for u in existing_usernames:
            if u.lower() not in profile_users and u.lower() not in ("guest", "гость", "defaultaccount", "wdagutilityaccount"):
                accounts_without.append(u)
        return accounts_without
