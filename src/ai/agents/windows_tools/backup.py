# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI Agents - Windows Backup Tools Module
# =============================================================================
# Description:
#   Инструменты прямого взаимодействия с подсистемой Windows Backup, Libraries
#   & File History (apps.windows.modules.backup_manager).
#   Сгруппированы по 5 логическим блокам:
#     1. Диагностика и отчёт здоровья бэкапов (Health Check)
#     2. Управление службой и поиском в Истории файлов (File History & RAG)
#     3. Теневые копии томов VSS (VSS Snapshots)
#     4. Аудит и перенос папок пользователя (User Folders Relocate)
#     5. Управление версиями файлов (File Version Control)
#
# Usage Examples:
#   Python API:
#     from src.ai.agents.windows_tools.backup import windows_backup_health_check
#     res = await windows_backup_health_check()
#
# File: backup.py
# Project: ai-breadboard
# Package: src.ai.agents.windows_tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 21:06:00
# =============================================================================

from __future__ import annotations

"""Модуль инструментов Windows Backup & Recovery для ИИ-агентов."""

import asyncio
import json
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
    """Вспомогательное преобразование объектов моделей в сериализуемый словарь."""
    if isinstance(obj, (int, float, bool, str)) or obj is None:
        return obj
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
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
# Блок 1: Диагностика и здоровье бэкапов
# =============================================================================

@tool
async def windows_backup_health_check() -> str:
    """Проводит полную диагностику подсистемы резервного копирования и формирует отчёт Health Score (0-100%).

    Returns:
        JSON с уровнем здоровья (health_score), состоянием службы fhsvc, дисков и списком рекомендаций.
    """
    try:
        from apps.windows.modules.backup_manager.core.health_checker import BackupHealthChecker

        checker = BackupHealthChecker()
        loop = asyncio.get_running_loop()

        res = await loop.run_in_executor(None, checker.generate_report)
        return json.dumps({"status": "ok", "health_report": _to_serializable(res)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.backup] Ошибка проверки здоровья бэкапов: {e}", exc_info=True)
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 2: Управление Историей файлов (File History & RAG)
# =============================================================================

@tool
async def windows_backup_file_history(
    action: str,
    query: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> str:
    """Управление службой Истории файлов (File History) и RAG-поиск по сохраненным копиям.

    Args:
        action: Операция с Историей файлов:
            - 'status': проверить состояние службы fhsvc и файл конфигурации Config.xml
            - 'trigger': выполнить принудительный запуск цикла архивации (fhexec -f)
            - 'audit_storage': аудит занимаемого объёма версий в целевом диске бэкапа
            - 'rag_search': поиск файла по имени или шаблону в архиве Истории файлов (параметр query)
        query: Поисковый запрос или путь к файлу для режима 'rag_search'.
        params: Словарь дополнительных параметров (например, limit для RAG-поиска).

    Returns:
        JSON с результатом выполнения операции Истории файлов.
    """
    try:
        from apps.windows.modules.backup_manager.core.file_history_manager import FileHistoryManager
        from apps.windows.modules.backup_manager.core.file_history_rag import get_file_history_rag
        from apps.windows.modules.backup_manager.core.storage_auditor import BackupStorageAuditor

        mgr = FileHistoryManager()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()
        p = params or {}

        if act == "status":
            res = await loop.run_in_executor(None, mgr.get_status)
            return json.dumps({"status": "ok", "action": act, "file_history": _to_serializable(res)}, ensure_ascii=False)
        elif act == "trigger":
            success, msg = await loop.run_in_executor(None, mgr.trigger_backup_now)
            return json.dumps({"status": "ok" if success else "error", "action": act, "triggered": success, "message": msg}, ensure_ascii=False)
        elif act == "audit_storage":
            auditor = BackupStorageAuditor()
            res = await loop.run_in_executor(None, auditor.audit_storage)
            return json.dumps({"status": "ok", "action": act, "storage_audit": _to_serializable(res)}, ensure_ascii=False)
        elif act == "rag_search":
            if not query:
                return json.dumps({"status": "error", "message": "Параметр 'query' обязателен для rag_search"}, ensure_ascii=False)
            rag = get_file_history_rag()
            limit = int(p.get("limit", 20))
            res = await loop.run_in_executor(None, rag.search, query, limit)
            return json.dumps({"status": "ok", "action": act, "query": query, "results": _to_serializable(res)}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.backup] Ошибка выполнения file_history ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 3: Теневые копии томов VSS (VSS Snapshots)
# =============================================================================

@tool
async def windows_backup_vss_snapshots() -> str:
    """Получает список всех имеющихся теневых копий томов Windows (Volume Shadow Copy / VSS).

    Returns:
        JSON со списком моментальных снимков томов (ShadowCopy ID, дата создания, имя тома).
    """
    try:
        from apps.windows.modules.backup_manager.core.vss_manager import VssManager

        vss = VssManager()
        loop = asyncio.get_running_loop()

        res = await loop.run_in_executor(None, vss.list_snapshots)
        return json.dumps({"status": "ok", "vss_snapshots": _to_serializable(res)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.backup] Ошибка получения VSS снимков: {e}", exc_info=True)
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 4: Аудит и перенос папок пользователя (User Folders Relocate)
# =============================================================================

@tool
async def windows_backup_user_folders(
    action: str,
    folder_name: Optional[str] = None,
    target_drive: Optional[str] = None,
) -> str:
    """Аудит объемов пользовательских папок (Документы, Загрузки и т.д.) и их перенос на другие диски.

    Args:
        action: Операция с папками:
            - 'overview': получить сводку объемов папок и доступных целевых накопителей
            - 'relocate': выполнить перенос папки (folder_name) на выбранный диск (target_drive, например 'D:')
        folder_name: Имя папки для переноса ('Desktop', 'Documents', 'Downloads', 'Pictures', 'Music', 'Videos').
        target_drive: Буква целевого накопителя (например, 'D:' или 'E:').

    Returns:
        JSON со сводкой объемов или статусом релокации директории.
    """
    try:
        from apps.windows.modules.backup_manager.core.user_folders_manager import UserFoldersManager

        ufm = UserFoldersManager()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "overview":
            res = await loop.run_in_executor(None, ufm.get_overview)
            return json.dumps({"status": "ok", "action": act, "user_folders": _to_serializable(res)}, ensure_ascii=False)
        elif act == "relocate":
            if not folder_name or not target_drive:
                return json.dumps({"status": "error", "message": "Параметры 'folder_name' и 'target_drive' обязательны для relocate"}, ensure_ascii=False)
            res = await loop.run_in_executor(None, ufm.relocate_folder, folder_name, target_drive)
            return json.dumps({"status": "ok" if getattr(res, 'success', False) else "error", "action": act, "relocate_result": _to_serializable(res)}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.backup] Ошибка управления пользовательскими папками ('{action}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "error": str(e)}, ensure_ascii=False)


# =============================================================================
# Блок 5: Управление версиями файлов (File Version Control)
# =============================================================================

@tool
async def windows_backup_version_control(
    action: str,
    file_path: str,
    version_id: Optional[int] = None,
    description: Optional[str] = None,
) -> str:
    """Управление двухслойными версиями файлов (VSS + SQLite blob хранилище).

    Args:
        action: Действие над версиями:
            - 'list': получить историю версий указанного файла
            - 'save': зафиксировать новую версию файла в хранилище
            - 'restore': восстановить файл из указанной версии (версия задается через version_id)
        file_path: Абсолютный путь к целевому файлу.
        version_id: Опциональный идентификатор версии при откате (для action='restore').
        description: Описание/комментарий к версии файла при фиксации (для action='save').

    Returns:
        JSON с деталями версий или результатом восстановления.
    """
    try:
        from apps.windows.modules.backup_manager.core.version_provider import WindowsVersionProvider

        provider = WindowsVersionProvider()
        loop = asyncio.get_running_loop()
        act = action.strip().lower()

        if act == "list":
            res = await loop.run_in_executor(None, provider.list_versions, file_path)
            return json.dumps({"status": "ok", "action": act, "file_path": file_path, "versions": _to_serializable(res)}, ensure_ascii=False)
        elif act == "save":
            res = await loop.run_in_executor(None, provider.save_version, file_path, description)
            return json.dumps({"status": "ok", "action": act, "file_path": file_path, "version_record": _to_serializable(res)}, ensure_ascii=False)
        elif act == "restore":
            if version_id is None:
                return json.dumps({"status": "error", "message": "Параметр 'version_id' обязателен для restore"}, ensure_ascii=False)
            res = await loop.run_in_executor(None, provider.restore_version, int(version_id))
            return json.dumps({"status": "ok", "action": act, "restore_result": _to_serializable(res)}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Неизвестное действие: '{action}'"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[windows_tools.backup] Ошибка версионирования файла ('{action}', '{file_path}'): {e}", exc_info=True)
        return json.dumps({"status": "error", "action": action, "file_path": file_path, "error": str(e)}, ensure_ascii=False)


WINDOWS_BACKUP_TOOLS = [
    windows_backup_health_check,
    windows_backup_file_history,
    windows_backup_vss_snapshots,
    windows_backup_user_folders,
    windows_backup_version_control,
]
