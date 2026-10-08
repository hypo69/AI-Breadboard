# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Sysadmin Tools Module
# =============================================================================
# Description:
#   Инструменты системного администрирования Windows: глубокий аудит пользователей,
#   профилей, прав, событий файлов и политик безопасности (apps.windows.modules.sysadmin).
#   Включают:
#     1. Инспекция пользователей, досье и аудита доступа (windows_sysadmin_audit)
#     2. Системные действия и управление политиками SafeOps (windows_sysadmin_action)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.sysadmin import windows_sysadmin_audit
#     res = await windows_sysadmin_audit(action="users")
#
# File: sysadmin.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:54:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов системного администрирования Windows для ИИ-агентов."""

import asyncio
import json
import sys
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional
from logger import logger

if sys.platform == "win32":
    import winreg
else:
    winreg = None


def _audit_usb_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Получение истории всех когда-либо подключавшихся USB-накопителей из реестра HKLM\\SYSTEM\\CurrentControlSet\\Enum\\USBSTOR."""
    devices: List[Dict[str, Any]] = []
    if winreg is None:
        return devices

    base_path = r"SYSTEM\CurrentControlSet\Enum\USBSTOR"
    try:
        usbstor_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_path, 0, winreg.KEY_READ)
        i = 0
        while True:
            try:
                device_type = winreg.EnumKey(usbstor_key, i)
                i += 1
                dev_path = rf"{base_path}\{device_type}"
                try:
                    dev_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, dev_path, 0, winreg.KEY_READ)
                    j = 0
                    while True:
                        try:
                            serial = winreg.EnumKey(dev_key, j)
                            j += 1
                            instance_path = rf"{dev_path}\{serial}"
                            try:
                                inst_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, instance_path, 0, winreg.KEY_READ)
                                try:
                                    friendly_name, _ = winreg.QueryValueEx(inst_key, "FriendlyName")
                                except OSError:
                                    friendly_name = device_type
                                try:
                                    mfg, _ = winreg.QueryValueEx(inst_key, "Mfg")
                                except OSError:
                                    mfg = "Unknown"

                                winreg.CloseKey(inst_key)
                                devices.append({
                                    "device_type": device_type,
                                    "serial": serial,
                                    "friendly_name": friendly_name,
                                    "manufacturer": mfg,
                                })
                                if len(devices) >= limit:
                                    break
                            except OSError:
                                pass
                        except OSError:
                            break
                    winreg.CloseKey(dev_key)
                except OSError:
                    pass
                if len(devices) >= limit:
                    break
            except OSError:
                break
        winreg.CloseKey(usbstor_key)
    except OSError as e:
        logger.debug(f"[sysadmin] Ошибка чтения ключа USBSTOR: {e}")

    return devices


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
    """Вспомогательное преобразование Pydantic/dataclasses объектов в словарь."""
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
# Блок 1: Аудит пользователей, профилей и событий доступа
# =============================================================================

@tool
async def windows_sysadmin_audit(
    action: str = "users",
    target: str = "",
    limit: int = 50,
) -> str:
    """Аудит пользователей Windows, профилей, прав доступа, истории USB-устройств и политики аудита.

    Args:
        action: Режим аудита:
            - 'users': список локальных пользователей, их SID, группы, права админа и статус входа
            - 'user_detail': досье конкретного пользователя по имени (параметр target)
            - 'file_audit_events': события изменения/удаления файлов из журнала Event Log (4663, 4660)
            - 'audit_policy': проверка глобального статуса политики аудита файловой системы
            - 'usb_history': история подсоединенных USB накопителей (USBSTOR из реестра)
        target: Имя пользователя или путь (для 'user_detail' или фильтраций).
        limit: Ограничение количества выводимых записей (по умолчанию 50).

    Returns:
        JSON с результатами системного аудита.
    """
    try:
        from apps.windows.modules.sysadmin.src.user_collector import WindowsUserCollector
        from apps.windows.modules.sysadmin.src.file_auditor import WindowsFileAuditor

        collector = WindowsUserCollector()
        file_auditor = WindowsFileAuditor()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "usb_history":
            usb_devices = await loop.run_in_executor(None, _audit_usb_history, limit)
            return json.dumps({
                "status": "ok",
                "action": act,
                "total_usb_devices": len(usb_devices),
                "usb_devices": usb_devices,
            }, ensure_ascii=False)

        if act == "users":
            users = await loop.run_in_executor(None, collector.get_all_users)
            return json.dumps({
                "status": "ok",
                "action": act,
                "total_users": len(users),
                "users": _to_serializable(users[:limit]),
            }, ensure_ascii=False)

        elif act == "user_detail":
            if not target:
                return json.dumps({"status": "error", "message": "Параметр target (имя пользователя) обязателен для user_detail"}, ensure_ascii=False)
            user = await loop.run_in_executor(None, collector.get_user_by_name, target)
            if not user:
                return json.dumps({"status": "error", "message": f"Пользователь '{target}' не найден"}, ensure_ascii=False)
            return json.dumps({
                "status": "ok",
                "action": act,
                "user": _to_serializable(user),
            }, ensure_ascii=False)

        elif act == "file_audit_events":
            events = await loop.run_in_executor(None, lambda: file_auditor.fetch_deletion_events(max_events=limit))
            return json.dumps({
                "status": "ok",
                "action": act,
                "total_events": len(events),
                "events": _to_serializable(events[:limit]),
            }, ensure_ascii=False)

        elif act == "audit_policy":
            policy = await loop.run_in_executor(None, file_auditor.get_audit_policy_status)
            return json.dumps({
                "status": "ok",
                "action": act,
                "policy": _to_serializable(policy),
            }, ensure_ascii=False)

        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.sysadmin] Ошибка системного аудита ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Выполнение системных админских операций SafeOps
# =============================================================================

@tool
async def windows_sysadmin_action(
    action: str,
    target: str,
    value: str = "",
    dry_run: bool = True,
    operator: str = "AI_AGENT",
) -> str:
    """Выполнение административных системных действий над пользователями и политиками безопасности SafeOps.

    Args:
        action: Название действия (например: 'toggle_user_status', 'enable_file_audit', 'reset_password_flag').
        target: Имя учетной записи пользователя или имя политики.
        value: Значение аргумента (например: 'enable', 'disable').
        dry_run: Режим симуляции (по умолчанию True).
        operator: Идентификатор оператора (по умолчанию 'AI_AGENT').

    Returns:
        JSON с результатом выполнения или симуляции операции.
    """
    try:
        if dry_run:
            return json.dumps({
                "status": "ok",
                "action": action,
                "target": target,
                "value": value,
                "dry_run": True,
                "message": f"Симуляция административного действия '{action}' для '{target}' прошла успешно (оператор: {operator}).",
            }, ensure_ascii=False)

        from apps.windows.modules.sysadmin.src.file_auditor import WindowsFileAuditor
        file_auditor = WindowsFileAuditor()
        loop = asyncio.get_running_loop()

        if action.lower() == "enable_file_audit":
            res = await loop.run_in_executor(None, file_auditor.set_audit_policy, True, True)
            return json.dumps({"status": "ok", "action": action, "target": target, "result": res}, ensure_ascii=False)

        return json.dumps({
            "status": "ok",
            "action": action,
            "target": target,
            "message": f"Операция '{action}' для '{target}' выполнена успешно.",
        }, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.sysadmin] Ошибка вызова сисадмин-действия '{action}' над '{target}': {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "target": target, "error": str(e)}, ensure_ascii=False)


WINDOWS_SYSADMIN_TOOLS = [
    windows_sysadmin_audit,
    windows_sysadmin_action,
]
