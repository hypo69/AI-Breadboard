# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Subsystem 03 Groups
# =============================================================================
# Description:
#   Подсистема 03: Управление группами безопасности Windows (локальные,
#   доменные, вложенные группы, граф членства, путь User -> Administrators).
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.accounts_identity.subsystems.subsystem_03_groups import GroupsSubsystem
#
#     subsys = GroupsSubsystem()
#     groups = subsys.list_groups()
#
# File: subsystem_03_groups.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.accounts_identity.subsystems
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 02:04:00
# =============================================================================

"""Подсистема управления группами безопасности и графом членства."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from collections import deque

from logger import logger
from apps.windows.sdk.modules.accounts_identity.models import GroupDetails, GroupRef
from apps.windows.sdk.modules.accounts_identity.win32_bridge import Win32IdentityBridge


class GroupsSubsystem:
    """Подсистема управления группами безопасности."""

    def __init__(self, bridge: Optional[Win32IdentityBridge] = None) -> None:
        """
        Инициализация подсистемы групп.

        Args:
            bridge: Мост вызовов Windows API.
        """
        self.bridge = bridge or Win32IdentityBridge()

    def list_groups(self) -> List[GroupDetails]:
        """55. Перечисляет все локальные группы безопасности."""
        ps_cmd = """
        Get-LocalGroup | ForEach-Object {
            $g = $_
            $m = @(Get-LocalGroupMember -Group $g.Name -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name)
            [PSCustomObject]@{
                Name = $g.Name
                SID = if ($g.SID) { $g.SID.Value } else { "" }
                Description = $g.Description
                Members = $m
            }
        }
        """
        raw = self.bridge.run_powershell_json(ps_cmd)
        results: List[GroupDetails] = []
        if raw:
            items = [raw] if isinstance(raw, dict) else raw
            for item in items:
                if not isinstance(item, dict):
                    continue
                name = item.get("Name", "")
                sid_val = str(item.get("SID", ""))
                desc = item.get("Description") or ""
                is_adm = name.lower() in ("administrators", "администраторы")
                raw_members = item.get("Members") or []
                if isinstance(raw_members, str):
                    members = [raw_members]
                elif isinstance(raw_members, list):
                    members = [str(x) for x in raw_members if x]
                else:
                    members = []
                results.append(
                    GroupDetails(
                        name=name,
                        sid=sid_val,
                        description=desc,
                        is_admin=is_adm,
                        is_local=True,
                        members=members,
                    )
                )

        if not results:
            _, out, _ = self.bridge.run_command(["net", "localgroup"])
            for line in out.splitlines():
                if line.startswith("*"):
                    g_name = line.lstrip("*").strip()
                    sid_info = self.bridge.lookup_name_to_sid(g_name)
                    sid_val = sid_info[0] if sid_info else ""
                    is_adm = g_name.lower() in ("administrators", "администраторы")
                    results.append(GroupDetails(name=g_name, sid=sid_val, is_admin=is_adm))
        return results

    def get_group(self, name_or_sid: str) -> Optional[GroupDetails]:
        """56. Получает свойства группы."""
        groups = self.list_groups()
        for g in groups:
            if g.name.lower() == name_or_sid.lower() or g.sid == name_or_sid:
                return g
        return None

    def get_group_sid(self, group_name: str) -> Optional[str]:
        """57. Получает строковый SID группы."""
        info = self.bridge.lookup_name_to_sid(group_name)
        return info[0] if info else None

    def get_group_members(self, group_name: str) -> List[str]:
        """58. Возвращает список участников группы."""
        ps_cmd = f"Get-LocalGroupMember -Group '{group_name}' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name"
        res = self.bridge.run_powershell_json(ps_cmd)
        if res:
            if isinstance(res, str):
                return [res]
            if isinstance(res, list):
                return [str(x) for x in res if x]
        return []

    def create_group(self, name: str, description: str = "") -> bool:
        """59. Создает новую локальную группу."""
        cmd = f"New-LocalGroup -Name '{name}' -Description '{description}'"
        ret, _, _ = self.bridge.run_command(["powershell.exe", "-NoProfile", "-Command", cmd])
        return ret == 0

    def update_group(self, name: str, description: str) -> bool:
        """60. Обновляет описание группы."""
        cmd = f"Set-LocalGroup -Name '{name}' -Description '{description}'"
        ret, _, _ = self.bridge.run_command(["powershell.exe", "-NoProfile", "-Command", cmd])
        return ret == 0

    def rename_group(self, old_name: str, new_name: str) -> bool:
        """61. Переименовывает локальную группу."""
        cmd = f"Rename-LocalGroup -Name '{old_name}' -NewName '{new_name}'"
        ret, _, _ = self.bridge.run_command(["powershell.exe", "-NoProfile", "-Command", cmd])
        return ret == 0

    def delete_group(self, name: str) -> bool:
        """62. Удаляет локальную группу."""
        cmd = f"Remove-LocalGroup -Name '{name}'"
        ret, _, _ = self.bridge.run_command(["powershell.exe", "-NoProfile", "-Command", cmd])
        return ret == 0

    def add_member(self, group_name: str, member_name: str) -> bool:
        """63. Добавляет пользователя или группу в состав группы."""
        cmd = f"Add-LocalGroupMember -Group '{group_name}' -Member '{member_name}'"
        ret, _, _ = self.bridge.run_command(["powershell.exe", "-NoProfile", "-Command", cmd])
        return ret == 0

    def remove_member(self, group_name: str, member_name: str) -> bool:
        """64. Удаляет участника из группы."""
        cmd = f"Remove-LocalGroupMember -Group '{group_name}' -Member '{member_name}'"
        ret, _, _ = self.bridge.run_command(["powershell.exe", "-NoProfile", "-Command", cmd])
        return ret == 0

    def check_membership(self, group_name: str, member_name: str) -> bool:
        """65. Проверяет прямое или косвенное членство в группе."""
        members = self.enumerate_nested_membership(group_name)
        m_lower = member_name.lower()
        for m in members:
            if m.lower() == m_lower or m.lower().endswith(f"\\{m_lower}"):
                return True
        return False

    def get_user_groups(self, username: str) -> List[GroupRef]:
        """66. Возвращает список групп, в которые входит пользователь."""
        all_groups = self.list_groups()
        u_lower = username.lower()
        user_groups: List[GroupRef] = []
        for g in all_groups:
            if any(m.lower() == u_lower or m.lower().endswith(f"\\{u_lower}") for m in g.members):
                user_groups.append(
                    GroupRef(
                        name=g.name,
                        sid=g.sid,
                        is_admin=g.is_admin,
                        is_local=g.is_local,
                        description=g.description,
                    )
                )
        return user_groups

    def enumerate_nested_membership(self, group_name: str) -> List[str]:
        """70. Рекурсивно разворачивает дерево всех участников группы."""
        visited: Set[str] = set()
        queue: deque[str] = deque([group_name])
        leaf_members: Set[str] = set()

        while queue:
            current_group = queue.popleft()
            if current_group.lower() in visited:
                continue
            visited.add(current_group.lower())

            direct_members = self.get_group_members(current_group)
            for member in direct_members:
                # Проверяем, является ли участник локальной группой
                g_match = self.get_group(member)
                if g_match and g_match.name.lower() not in visited:
                    queue.append(g_match.name)
                else:
                    leaf_members.add(member)

        return sorted(list(leaf_members))

    def find_path_to_administrators(self, username: str) -> Optional[List[str]]:
        """
        72. Ищет цепочку вложенности групп от пользователя к группе Administrators.

        Returns:
            Список имен звеньев [username, group1, ..., Administrators] или None.
        """
        u_lower = username.lower()
        admin_group_names = {"administrators", "администраторы"}
        user_groups = self.get_user_groups(username)

        # Прямое членство
        for g in user_groups:
            if g.name.lower() in admin_group_names:
                return [username, g.name]

        # BFS поиск через граф всех групп
        all_groups = self.list_groups()
        group_map = {g.name.lower(): g for g in all_groups}
        
        queue: deque[List[str]] = deque([[username, g.name] for g in user_groups])
        visited: Set[str] = {g.name.lower() for g in user_groups}

        while queue:
            path = queue.popleft()
            current_node = path[-1].lower()

            if current_node in admin_group_names:
                return path

            # Ищем родительские группы, содержащие current_node
            for parent_name_lower, parent_group in group_map.items():
                if any(m.lower() == current_node or m.lower().endswith(f"\\{current_node}") for m in parent_group.members):
                    if parent_name_lower not in visited:
                        visited.add(parent_name_lower)
                        queue.append(path + [parent_group.name])

        return None
