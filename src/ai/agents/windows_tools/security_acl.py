# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Security ACL Tools Module
# =============================================================================
# Description:
#   Инструменты управления правами доступа (ACL), шифрованием BitLocker/EFS
#   и уровнем безопасности UAC (apps.windows.modules.security_acl).
#   Включают:
#     1. Аудит BitLocker, UAC и получение прав доступа ACL файлов/папок (windows_security_acl_audit)
#     2. Модификация прав доступа ACL по протоколу SafeOps/dry_run (windows_security_acl_action)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.security_acl import windows_security_acl_audit
#     res = await windows_security_acl_audit(action="report")
#
# File: security_acl.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 22:10:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов управления ACL и BitLocker для ИИ-агентов."""

import asyncio
import json
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional
from logger import logger

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
    """Вспомогательное преобразование Pydantic моделей и объектов в словарь."""
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
# Блок 1: Аудит безопасности, BitLocker и прав ACL
# =============================================================================

@tool
async def windows_security_acl_audit(
    action: str = "report",
    target_path: Optional[str] = None,
) -> str:
    """Аудит безопасности Windows: статусы шифрования BitLocker, уровня UAC и прав доступа (ACL) к файлам/папкам.

    Args:
        action: Режим аудита:
            - 'report': полный сводный отчёт (BitLocker, EFS, UAC level)
            - 'bitlocker': подробный статус шифрования BitLocker на томах
            - 'acl': проверка прав доступа ACL (DACL) для пути target_path
        target_path: Абсолютный путь к файлу или папке для инспекции прав доступа ACL (при action='acl').

    Returns:
        JSON со статусом BitLocker, UAC или списком записей ACL.
    """
    try:
        from apps.windows.modules.security_acl.core.manager import SecurityAclManager

        sam = SecurityAclManager()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "report":
            report = await loop.run_in_executor(None, sam.generate_report)
            return json.dumps({"status": "ok", "action": act, "report": _to_serializable(report)}, ensure_ascii=False)

        elif act == "bitlocker":
            statuses = await loop.run_in_executor(None, sam.get_bitlocker_status)
            return json.dumps({"status": "ok", "action": act, "bitlocker_volumes": _to_serializable(statuses)}, ensure_ascii=False)

        elif act == "acl":
            if not target_path:
                target_path = "C:\\Windows"
            acls = await loop.run_in_executor(None, sam.get_path_acl, target_path)
            return json.dumps({"status": "ok", "action": act, "target_path": target_path, "acl": _to_serializable(acls)}, ensure_ascii=False)

        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.security_acl] Ошибка аудита безопасности ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Модификация прав доступа ACL (SafeOps)
# =============================================================================

@tool
async def windows_security_acl_action(
    target_path: str,
    principal: str,
    rights: str = "ReadAndExecute",
    action: str = "grant",
    dry_run: bool = True,
    confirmed_by_user: bool = False,
) -> str:
    """Изменение прав доступа ACL на файлы и каталоги Windows (по протоколу SafeOps/dry_run).

    Args:
        target_path: Абсолютный путь к файлу или каталогу.
        principal: Имя пользователя, группы или SID (например, 'BUILTIN\\Users', 'NT AUTHORITY\\SYSTEM').
        rights: Уровень прав ('FullControl', 'Modify', 'ReadAndExecute', 'Read', 'Write').
        action: Тип действия ('grant', 'deny', 'revoke').
        dry_run: Режим симуляции (по умолчанию True для безопасности).
        confirmed_by_user: Подтверждение выполнения изменений администратором.

    Returns:
        JSON с результатом выполнения операции модификации ACL.
    """
    try:
        from apps.windows.modules.security_acl.core.manager import SecurityAclManager
        from apps.windows.modules.security_acl.core.models import AclModifyRequest

        sam = SecurityAclManager()
        req = AclModifyRequest(
            target_path=target_path,
            principal=principal,
            permission=rights,
            action=action,
            dry_run=dry_run,
            confirmed_by_user=confirmed_by_user,
        )

        res = await sam.execute_acl_modification(req)
        return json.dumps({"status": "ok", "target_path": target_path, "result": _to_serializable(res)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.security_acl] Ошибка изменения ACL для '{target_path}': {e}", exc_info=True)
        return json.dumps({"status": "error", "target_path": target_path, "error": str(e)}, ensure_ascii=False)


WINDOWS_SECURITY_ACL_TOOLS = [
    windows_security_acl_audit,
    windows_security_acl_action,
]
