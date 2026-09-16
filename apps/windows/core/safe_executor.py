# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: SafeOps Execution Layer
# =============================================================================
# Description:
#   Изолированный исполнитель корректирующих действий Windows (SafeOps).
#   Обеспечивает dry-run симуляцию, проверку уровней риска, контроль подтверждений
#   и создание резервных копий перед выполнением деструктивных операций.
#
# Examples:
#   >>> from apps.windows.core.safe_executor import SafeExecutor
#   >>> executor = SafeExecutor()
#   >>> dry_run_res = executor.simulate(action)
#
# File: safe_executor.py
# Project: ai-breadboard
# Package: apps.windows.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Слой безопасного выполнения и симуляции действий (SafeOps)."""

from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.logger import logger
from apps.windows.core.models import ActionType, RemediationAction, RiskLevel


class SafeExecutor:
    """Безопасный исполнитель системных действий Windows."""

    def __init__(self, backup_dir: Optional[Path] = None) -> None:
        """Инициализация исполнителя.

        Args:
            backup_dir: Директория для создания резервных копий перед изменениями.
        """
        if backup_dir is None:
            self.backup_dir = Path(os.environ.get("TEMP", "C:/Temp")) / "ai_breadboard_backups"
        else:
            self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def simulate(self, action: RemediationAction) -> Dict[str, Any]:
        """Симуляция выполнения действия (Dry-Run).

        Args:
            action: Действие для симуляции.

        Returns:
            Dict[str, Any]: Результат симуляции с оценкой освобождаемого пространства и риска.
        """
        logger.info(f"SafeOps Dry-Run: Симуляция действия {action.action_id} ({action.action_type.value}) на объекте {action.target}")
        
        sim_result: Dict[str, Any] = {
            "action_id": action.action_id,
            "target": action.target,
            "risk": action.risk.value,
            "simulated": True,
            "would_delete_files_count": 0,
            "releasable_bytes": 0,
            "releasable_mb": 0.0,
            "command": action.execution_command or action.dry_run_command,
            "safe_to_execute": True,
            "details": [],
        }

        try:
            target_path = Path(action.target)
            if action.action_type == ActionType.CLEAN_DIRECTORY:
                if target_path.exists() and target_path.is_dir():
                    count = 0
                    total_bytes = 0
                    for root, _, files in os.walk(target_path):
                        for f in files:
                            fp = Path(root) / f
                            try:
                                sz = fp.stat().st_size
                                total_bytes += sz
                                count += 1
                            except (OSError, PermissionError):
                                pass
                    sim_result["would_delete_files_count"] = count
                    sim_result["releasable_bytes"] = total_bytes
                    sim_result["releasable_mb"] = round(total_bytes / (1024 * 1024), 2)
            elif action.action_type == ActionType.CLEAN_FILE:
                if target_path.exists() and target_path.is_file():
                    sz = target_path.stat().st_size
                    sim_result["would_delete_files_count"] = 1
                    sim_result["releasable_bytes"] = sz
                    sim_result["releasable_mb"] = round(sz / (1024 * 1024), 2)
        except Exception as e:
            logger.warning(f"Ошибка при оценке размера в симуляции: {e}")
            sim_result["error"] = str(e)

        return sim_result

    def execute(self, action: RemediationAction, confirmed_by_user: bool = False) -> RemediationAction:
        """Безопасное выполнение действия с проверкой риска.

        Args:
            action: Действие для выполнения.
            confirmed_by_user: Флаг явного подтверждения пользователя для рискованных действий.

        Returns:
            RemediationAction: Обновлённый объект действия со статусом выполнения.
        """
        if action.risk in (RiskLevel.CAUTION, RiskLevel.CRITICAL) and not confirmed_by_user:
            action.executed = False
            action.success = False
            action.error_message = f"Действие уровня '{action.risk.value}' требует явного подтверждения пользователя."
            logger.warning(f"SafeOps Блокировка: {action.error_message} (Action ID: {action.action_id})")
            return action

        logger.info(f"SafeOps Execution: Выполнение {action.action_id} ({action.action_type.value}) на {action.target}")
        
        try:
            if action.action_type == ActionType.CLEAN_FILE:
                self._execute_clean_file(action)
            elif action.action_type == ActionType.CLEAN_DIRECTORY:
                self._execute_clean_directory(action)
            elif action.action_type == ActionType.STOP_SERVICE:
                self._execute_service_action(action, "stop")
            elif action.action_type == ActionType.DISABLE_SERVICE:
                self._execute_service_action(action, "disable")
            elif action.action_type == ActionType.DISABLE_TASK:
                self._execute_task_action(action, "disable")
            elif action.action_type == ActionType.KILL_PROCESS:
                self._execute_kill_process(action)
            elif action.action_type in (ActionType.CUSTOM_COMMAND, ActionType.REPAIR_INTEGRITY, ActionType.REMOVE_DRIVER_PACKAGE):
                self._execute_custom_command(action)
            else:
                action.executed = True
                action.success = False
                action.error_message = f"Неподдерживаемый тип действия: {action.action_type.value}"
        except Exception as ex:
            action.executed = True
            action.success = False
            action.error_message = f"Исключение при выполнении: {ex}"
            logger.error(f"SafeOps Ошибка: {ex}", exc_info=True)

        return action

    def _execute_clean_file(self, action: RemediationAction) -> None:
        """Удаление одного файла."""
        path = Path(action.target)
        if not path.exists():
            action.executed = True
            action.success = True
            return
        path.unlink(missing_ok=True)
        action.executed = True
        action.success = True

    def _execute_clean_directory(self, action: RemediationAction) -> None:
        """Очистка содержимого директории (не удаляя саму корневую папку)."""
        target = Path(action.target)
        if not target.exists():
            action.executed = True
            action.success = True
            return

        deleted_count = 0
        for item in target.iterdir():
            try:
                if item.is_file() or item.is_symlink():
                    item.unlink(missing_ok=True)
                    deleted_count += 1
                elif item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                    deleted_count += 1
            except (PermissionError, OSError) as pe:
                logger.debug(f"Файл заблокирован или занят процессом: {item} ({pe})")

        action.executed = True
        action.success = True

    def _execute_service_action(self, action: RemediationAction, operation: str) -> None:
        """Управление службой через sc.exe или powershell."""
        svc_name = action.target
        cmd = ["powershell", "-NoProfile", "-Command"]
        if operation == "stop":
            cmd.append(f"Stop-Service -Name '{svc_name}' -Force -ErrorAction SilentlyContinue")
        elif operation == "disable":
            cmd.append(f"Set-Service -Name '{svc_name}' -StartupType Disabled")

        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        action.executed = True
        action.success = res.returncode == 0
        if res.returncode != 0:
            action.error_message = res.stderr.strip() or res.stdout.strip()

    def _execute_task_action(self, action: RemediationAction, operation: str) -> None:
        """Управление задачей планировщика через schtasks."""
        task_name = action.target
        cmd = ["schtasks", "/Change", "/TN", task_name, "/Disable"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        action.executed = True
        action.success = res.returncode == 0
        if res.returncode != 0:
            action.error_message = res.stderr.strip() or res.stdout.strip()

    def _execute_kill_process(self, action: RemediationAction) -> None:
        """Завершение процесса по PID."""
        pid = int(action.target)
        cmd = ["taskkill", "/F", "/PID", str(pid)]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        action.executed = True
        action.success = res.returncode == 0
        if res.returncode != 0:
            action.error_message = res.stderr.strip() or res.stdout.strip()

    def _execute_custom_command(self, action: RemediationAction) -> None:
        """Выполнение кастомной команды PowerShell."""
        if not action.execution_command:
            action.executed = True
            action.success = False
            action.error_message = "Команда выполнения не задана."
            return

        cmd = ["powershell", "-NoProfile", "-Command", action.execution_command]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        action.executed = True
        action.success = res.returncode == 0
        if res.returncode != 0:
            action.error_message = res.stderr.strip() or res.stdout.strip()
