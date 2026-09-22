# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows User Manager Module
# =============================================================================
# Description:
#   Управление пользователями операционной системы Windows (не путать с
#   внутренними пользователями проекта AI-Breadboard).
#   Работает с локальными учетными записями Windows через PowerShell/WMI.
#
# Examples:
#   >>> from apps.ai_breadboard_admin.src.windows_user_manager import WindowsUserManager
#   >>> manager = WindowsUserManager()
#   >>> users = manager.get_windows_users()
#
# File: windows_user_manager.py
# Project: AI-Breadboard
# Package: apps.ai_breadboard_admin.src
# Module: windows_user_manager
# Class: WindowsUserManager
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import subprocess
import json
from typing import Any, Dict, List, Optional


class WindowsUserManager:
    """Менеджер управления пользователями операционной системы Windows.
    
    Отдельный модуль для системных учетных записей Windows.
    НЕ СВЯЗАН с внутренними пользователями проекта AI-Breadboard.
    """

    def __init__(self) -> None:
        """Инициализация менеджера Windows-пользователей."""
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: float = 0

    def get_windows_users(self, refresh: bool = False) -> List[Dict[str, Any]]:
        """Получение списка локальных пользователей Windows.
        
        Args:
            refresh: Обновить кэш данных.
            
        Returns:
            Список пользователей с их свойствами.
        """
        import time
        current_time = time.time()
        
        if not refresh and self._cache and (current_time - self._cache_timestamp) < 60:
            return self._cache.get('users', [])
        
        users = []
        try:
            # Используем PowerShell для получения информации о пользователях
            script = """
            Get-LocalUser | Select-Object Name, Enabled, Description, 
                @{Name='SID';Expression={$_.SID.Value}},
                @{Name='LastLogon';Expression={$_.LastLogon}},
                @{Name='PasswordLastSet';Expression={$_.PasswordLastSet}},
                @{Name='AccountExpires';Expression={$_.AccountExpires}} |
            ConvertTo-Json -Depth 3
            """
            
            result = subprocess.run(
                ['powershell', '-Command', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                if isinstance(data, list):
                    users = data
                elif isinstance(data, dict):
                    users = [data]
                    
        except Exception as ex:
            print(f"Error getting Windows users: {ex}")
        
        self._cache = {'users': users}
        self._cache_timestamp = current_time
        return users

    def get_windows_groups(self) -> List[Dict[str, Any]]:
        """Получение списка локальных групп Windows.
        
        Returns:
            Список групп с их членами.
        """
        groups = []
        try:
            script = """
            Get-LocalGroup | Select-Object Name, SID, Description |
            ConvertTo-Json -Depth 2
            """
            
            result = subprocess.run(
                ['powershell', '-Command', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                if isinstance(data, list):
                    groups = data
                elif isinstance(data, dict):
                    groups = [data]
                    
        except Exception as ex:
            print(f"Error getting Windows groups: {ex}")
        
        return groups

    def get_group_members(self, group_name: str) -> List[str]:
        """Получение членов группы Windows.
        
        Args:
            group_name: Имя группы.
            
        Returns:
            Список имен членов группы.
        """
        members = []
        try:
            script = f"""
            Get-LocalGroupMember -Group "{group_name}" | 
            Select-Object Name, ObjectClass |
            ConvertTo-Json -Depth 2
            """
            
            result = subprocess.run(
                ['powershell', '-Command', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                if isinstance(data, list):
                    members = [item.get('Name', '') for item in data]
                elif isinstance(data, dict):
                    members = [data.get('Name', '')]
                    
        except Exception as ex:
            print(f"Error getting group members: {ex}")
        
        return members

    def create_windows_user(
        self,
        username: str,
        password: str,
        fullname: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Создание нового локального пользователя Windows.
        
        Args:
            username: Имя пользователя.
            password: Пароль.
            fullname: Полное имя (опционально).
            description: Описание (опционально).
            
        Returns:
            Результат операции.
        """
        try:
            # Создаем пользователя
            script = f"""
            $passwordSecure = ConvertTo-SecureString "{password}" -AsPlainText -Force
            New-LocalUser -Name "{username}" -Password $passwordSecure -FullName "{fullname}" -Description "{description}"
            """
            
            result = subprocess.run(
                ['powershell', '-Command', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    'status': 'ok',
                    'message': f'Пользователь {username} успешно создан',
                    'username': username
                }
            else:
                return {
                    'status': 'error',
                    'message': result.stderr or 'Ошибка создания пользователя',
                    'error': result.stderr
                }
                
        except Exception as ex:
            return {
                'status': 'error',
                'message': str(ex),
                'error': str(ex)
            }

    def delete_windows_user(self, username: str) -> Dict[str, Any]:
        """Удаление локального пользователя Windows.
        
        Args:
            username: Имя пользователя.
            
        Returns:
            Результат операции.
        """
        try:
            script = f'Remove-LocalUser -Name "{username}"'
            
            result = subprocess.run(
                ['powershell', '-Command', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    'status': 'ok',
                    'message': f'Пользователь {username} успешно удален',
                    'username': username
                }
            else:
                return {
                    'status': 'error',
                    'message': result.stderr or 'Ошибка удаления пользователя',
                    'error': result.stderr
                }
                
        except Exception as ex:
            return {
                'status': 'error',
                'message': str(ex),
                'error': str(ex)
            }

    def enable_windows_user(self, username: str) -> Dict[str, Any]:
        """Включение пользователя Windows.
        
        Args:
            username: Имя пользователя.
            
        Returns:
            Результат операции.
        """
        try:
            script = f'Enable-LocalUser -Name "{username}"'
            
            result = subprocess.run(
                ['powershell', '-Command', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    'status': 'ok',
                    'message': f'Пользователь {username} успешно включен',
                    'username': username
                }
            else:
                return {
                    'status': 'error',
                    'message': result.stderr or 'Ошибка включения пользователя',
                    'error': result.stderr
                }
                
        except Exception as ex:
            return {
                'status': 'error',
                'message': str(ex),
                'error': str(ex)
            }

    def disable_windows_user(self, username: str) -> Dict[str, Any]:
        """Отключение пользователя Windows.
        
        Args:
            username: Имя пользователя.
            
        Returns:
            Результат операции.
        """
        try:
            script = f'Disable-LocalUser -Name "{username}"'
            
            result = subprocess.run(
                ['powershell', '-Command', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    'status': 'ok',
                    'message': f'Пользователь {username} успешно отключен',
                    'username': username
                }
            else:
                return {
                    'status': 'error',
                    'message': result.stderr or 'Ошибка отключения пользователя',
                    'error': result.stderr
                }
                
        except Exception as ex:
            return {
                'status': 'error',
                'message': str(ex),
                'error': str(ex)
            }

    def add_user_to_group(self, username: str, group_name: str) -> Dict[str, Any]:
        """Добавление пользователя в группу Windows.
        
        Args:
            username: Имя пользователя.
            group_name: Имя группы.
            
        Returns:
            Результат операции.
        """
        try:
            script = f'Add-LocalGroupMember -Group "{group_name}" -Member "{username}"'
            
            result = subprocess.run(
                ['powershell', '-Command', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    'status': 'ok',
                    'message': f'Пользователь {username} добавлен в группу {group_name}',
                    'username': username,
                    'group': group_name
                }
            else:
                return {
                    'status': 'error',
                    'message': result.stderr or 'Ошибка добавления в группу',
                    'error': result.stderr
                }
                
        except Exception as ex:
            return {
                'status': 'error',
                'message': str(ex),
                'error': str(ex)
            }

    def remove_user_from_group(self, username: str, group_name: str) -> Dict[str, Any]:
        """Удаление пользователя из группы Windows.
        
        Args:
            username: Имя пользователя.
            group_name: Имя группы.
            
        Returns:
            Результат операции.
        """
        try:
            script = f'Remove-LocalGroupMember -Group "{group_name}" -Member "{username}"'
            
            result = subprocess.run(
                ['powershell', '-Command', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    'status': 'ok',
                    'message': f'Пользователь {username} удален из группы {group_name}',
                    'username': username,
                    'group': group_name
                }
            else:
                return {
                    'status': 'error',
                    'message': result.stderr or 'Ошибка удаления из группы',
                    'error': result.stderr
                }
                
        except Exception as ex:
            return {
                'status': 'error',
                'message': str(ex),
                'error': str(ex)
            }

    def reset_windows_user_password(self, username: str, new_password: str) -> Dict[str, Any]:
        """Сброс пароля пользователя Windows.
        
        Args:
            username: Имя пользователя.
            new_password: Новый пароль.
            
        Returns:
            Результат операции.
        """
        try:
            script = f"""
            $passwordSecure = ConvertTo-SecureString "{new_password}" -AsPlainText -Force
            Set-LocalUser -Name "{username}" -Password $passwordSecure
            """
            
            result = subprocess.run(
                ['powershell', '-Command', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    'status': 'ok',
                    'message': f'Пароль пользователя {username} успешно сброшен',
                    'username': username
                }
            else:
                return {
                    'status': 'error',
                    'message': result.stderr or 'Ошибка сброса пароля',
                    'error': result.stderr
                }
                
        except Exception as ex:
            return {
                'status': 'error',
                'message': str(ex),
                'error': str(ex)
            }


__all__ = ['WindowsUserManager']
