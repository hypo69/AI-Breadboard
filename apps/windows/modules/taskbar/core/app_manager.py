# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Taskbar - App Manager
# =============================================================================
# Description:
#   Управление закрепленными приложениями и запуск через Shell/PowerShell.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.taskbar.core.app_manager import TaskbarAppManager
#
#     mgr = TaskbarAppManager()
#     apps = mgr.list_pinned_apps()
#
# File: app_manager.py
# Project: ai-breadboard
# Package: apps.windows.modules.taskbar.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 17:30:00
# =============================================================================

from __future__ import annotations
"""Менеджер закрепления, открепления и запуска приложений панели задач."""

import ctypes
import os
from pathlib import Path
import subprocess
from typing import Any, Dict, List, Optional

from logger import logger
from apps.windows.modules.taskbar.core.models import (
    AppLaunchRequest,
    AppPinRequest,
    PinnedAppItem,
)


class TaskbarAppManager:
    """Управление закреплением приложений панели задач и их запуском."""

    def __init__(self) -> None:
        """Инициализация менеджера приложений."""
        self.pinned_dir = Path(os.path.expandvars(
            r"%APPDATA%\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar"
        ))

    def _resolve_shortcut_target(self, lnk_path: Path) -> str:
        """Определяет целевой путь .exe для .lnk ярлыка через PowerShell / WScript."""
        try:
            ps_script = (
                f"$sh = New-Object -ComObject WScript.Shell; "
                f"$target = $sh.CreateShortcut('{str(lnk_path)}').TargetPath; "
                f"Write-Output $target"
            )
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception as exc:
            logger.debug(f"[TaskbarAppManager] Не удалось прочитать ярлык {lnk_path.name}: {exc}")
        return ""

    def list_pinned_apps(self) -> List[PinnedAppItem]:
        """Возвращает список закрепленных на панели задач приложений."""
        result: List[PinnedAppItem] = []
        if not self.pinned_dir.exists():
            return result

        try:
            for item in self.pinned_dir.glob("*.lnk"):
                name = item.stem
                target = self._resolve_shortcut_target(item)
                result.append(PinnedAppItem(
                    name=name,
                    target_path=target,
                    link_path=str(item),
                ))
        except Exception as exc:
            logger.error(f"[TaskbarAppManager] Ошибка чтения каталога закрепленных приложений: {exc}")

        return result

    def launch_app(self, req: AppLaunchRequest) -> Dict[str, Any]:
        """Запускает приложение с заданными параметрами или правами администратора."""
        if req.admin:
            try:
                # Запуск через ShellExecuteW с глаголом 'runas'
                op = "runas"
                params = req.arguments or ""
                cwd = req.working_dir or ""
                res = ctypes.windll.shell32.ShellExecuteW(
                    None, op, req.app_path, params, cwd, 1
                )
                if res > 32:
                    return {"status": "SUCCESS", "message": f"Приложение {req.app_path} запущено с правами UAC."}
                else:
                    return {"status": "ERROR", "error_code": res, "message": "Ошибка ShellExecuteW runas"}
            except Exception as exc:
                logger.error(f"[TaskbarAppManager] Ошибка UAC запуска {req.app_path}: {exc}")
                return {"status": "ERROR", "message": str(exc)}

        try:
            cmd = [req.app_path]
            if req.arguments:
                cmd.extend(req.arguments.split())
            proc = subprocess.Popen(
                cmd,
                cwd=req.working_dir if req.working_dir and os.path.isdir(req.working_dir) else None,
                shell=False,
            )
            return {
                "status": "SUCCESS",
                "pid": proc.pid,
                "message": f"Приложение {req.app_path} успешно запущено.",
            }
        except Exception as exc:
            logger.error(f"[TaskbarAppManager] Ошибка стандартного запуска {req.app_path}: {exc}")
            return {"status": "ERROR", "message": str(exc)}

    def pin_app(self, req: AppPinRequest) -> Dict[str, Any]:
        """Закрепляет приложение на панели задач Windows."""
        path = os.path.abspath(os.path.expandvars(req.target_path))
        if not os.path.exists(path):
            return {"status": "ERROR", "message": f"Файл не найден: {path}"}

        # PowerShell Shell.Application verb pin
        ps_script = f"""
        $path = '{path}'
        $folder = Split-Path $path
        $file = Split-Path $path -Leaf
        $sa = New-Object -ComObject Shell.Application
        $item = $sa.NameSpace($folder).ParseName($file)
        $verbs = $item.Verbs()
        $pinned = $false
        foreach ($v in $verbs) {{
            if ($v.Name -match 'taskbar|панел' -or $v.Name.Replace('&','') -match 'Pin to taskbar|Закрепить на панели задач') {{
                $v.DoIt()
                $pinned = $true
                break
            }}
        }}
        if ($pinned) {{ Write-Output "PINNED" }} else {{ Write-Output "FALLBACK_SYS" }}
        """
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=10,
            )
            output = res.stdout.strip()
            return {
                "status": "SUCCESS",
                "message": f"Команда закрепления для {path} отправлена (результат: {output}).",
                "target_path": path,
            }
        except Exception as exc:
            logger.error(f"[TaskbarAppManager] Ошибка закрепления {path}: {exc}")
            return {"status": "ERROR", "message": str(exc)}

    def unpin_app(self, target_name_or_path: str) -> Dict[str, Any]:
        """Открепляет приложение от панели задач Windows."""
        # Проверяем в каталоге ярлыков User Pinned\TaskBar
        removed = False
        target_clean = target_name_or_path.lower().replace(".lnk", "").replace(".exe", "")

        if self.pinned_dir.exists():
            for item in self.pinned_dir.glob("*.lnk"):
                if target_clean in item.stem.lower():
                    try:
                        item.unlink()
                        removed = True
                    except Exception as exc:
                        logger.warning(f"[TaskbarAppManager] Не удалось удалить ярлык {item}: {exc}")

        # Также выполняем попытку через Shell verb
        ps_script = f"""
        $query = '{target_clean}'
        $dir = [Environment]::GetFolderPath('ApplicationData') + '\\Microsoft\\Internet Explorer\\Quick Launch\\User Pinned\\TaskBar'
        if (Test-Path $dir) {{
            Get-ChildItem -Path $dir -Filter "*$query*.lnk" | ForEach-Object {{
                $sa = New-Object -ComObject Shell.Application
                $folder = $sa.Namespace($_.DirectoryName)
                $item = $folder.ParseName($_.Name)
                foreach ($v in $item.Verbs()) {{
                    if ($v.Name.Replace('&','') -match 'Unpin from taskbar|Открепить от панели задач') {{
                        $v.DoIt()
                    }}
                }}
            }}
        }}
        """
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except Exception:
            pass

        return {
            "status": "SUCCESS" if removed else "COMPLETED",
            "message": f"Действие открепления для '{target_name_or_path}' выполнено.",
            "file_removed": removed,
        }
