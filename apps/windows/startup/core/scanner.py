# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Startup Scanner Engine
# =============================================================================
# Description:
#   Движок сбора и обнаружения всех точек автозапуска и механизмов
#   персистентности в ОС Windows: реестр (Run, RunOnce, Winlogon, IFEO,
#   Policies), папки автозагрузки, планировщик задач и автозапускаемые службы.
#
# Examples:
#   >>> from apps.windows.startup.core.scanner import StartupScanner
#   >>> scanner = StartupScanner()
#   >>> entries = scanner.scan_all()
#
# File: scanner.py
# Project: ai-breadboard
# Package: apps.windows.startup.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Движок сканирования всех точек автозагрузки в Windows."""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from logger import logger
from apps.windows.startup.core.models import (
    LocationInfo,
    StartupEntry,
    StartupLocationType,
)

# Проверка доступности winreg (только для Windows)
try:
    import winreg
    HAS_WINREG = True
except ImportError:
    winreg = None
    HAS_WINREG = False


class StartupScanner:
    """Сканер точек автозапуска и персистентности Windows."""

    def __init__(self) -> None:
        """Инициализация сканера точек автозапуска."""
        self._disabled_cache: Dict[str, bool] = {}

    def get_monitored_locations(self) -> List[LocationInfo]:
        """Возвращает список всех известных точек автозапуска в Windows.

        Returns:
            List[LocationInfo]: Каталог мест автозагрузки с описанием.
        """
        appdata = os.getenv("APPDATA", "C:\\Users\\User\\AppData\\Roaming")
        progdata = os.getenv("PROGRAMDATA", "C:\\ProgramData")

        return [
            LocationInfo(
                location_type=StartupLocationType.REGISTRY_RUN,
                title_ru="Реестр: Run (Пользователь)",
                description_ru="Автозапуск программ при входе текущего пользователя в систему",
                target_path=r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
                is_writable=True,
            ),
            LocationInfo(
                location_type=StartupLocationType.REGISTRY_RUN,
                title_ru="Реестр: Run (Система)",
                description_ru="Автозапуск программ для всех пользователей системы",
                target_path=r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run",
                is_writable=False,
            ),
            LocationInfo(
                location_type=StartupLocationType.REGISTRY_RUNONCE,
                title_ru="Реестр: RunOnce (Пользователь / Система)",
                description_ru="Однократный запуск программ при следующем входе",
                target_path=r"HKCU/HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce",
                is_writable=True,
            ),
            LocationInfo(
                location_type=StartupLocationType.STARTUP_FOLDER_USER,
                title_ru="Папка автозагрузки (Пользователь)",
                description_ru="Ярлыки и исполняемые файлы в каталоге Startup профиля пользователя",
                target_path=str(Path(appdata) / r"Microsoft\Windows\Start Menu\Programs\Startup"),
                is_writable=True,
            ),
            LocationInfo(
                location_type=StartupLocationType.STARTUP_FOLDER_COMMON,
                title_ru="Папка автозагрузки (Общая)",
                description_ru="Ярлыки и исполняемые файлы для всех пользователей",
                target_path=str(Path(progdata) / r"Microsoft\Windows\Start Menu\Programs\Startup"),
                is_writable=False,
            ),
            LocationInfo(
                location_type=StartupLocationType.WINLOGON,
                title_ru="Реестр: Winlogon & Windows NT",
                description_ru="Оболочка (Shell), инициализатор сессии (Userinit) и библиотеки AppInit",
                target_path=r"HKLM\Software\Microsoft\Windows NT\CurrentVersion\Winlogon",
                is_writable=False,
            ),
            LocationInfo(
                location_type=StartupLocationType.IFEO,
                title_ru="Image File Execution Options (IFEO)",
                description_ru="Отладочные перехватчики запуска исполняемых файлов (Debugger hijacking)",
                target_path=r"HKLM\Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options",
                is_writable=False,
            ),
            LocationInfo(
                location_type=StartupLocationType.SCHEDULED_TASK,
                title_ru="Планировщик задач (Logon / Boot Triggers)",
                description_ru="Задачи Windows, настроенные на автоматический старт при входе или загрузке",
                target_path=r"Task Scheduler (Root / Custom tasks)",
                is_writable=False,
            ),
            LocationInfo(
                location_type=StartupLocationType.WINDOWS_SERVICE,
                title_ru="Службы Windows (Автозапуск)",
                description_ru="Службы с типом запуска 'Автоматически' и сторонние сервисы",
                target_path=r"Services.msc (StartType: Auto)",
                is_writable=False,
            ),
        ]

    def scan_all(self) -> List[StartupEntry]:
        """Выполняет полное сканирование всех поддерживаемых точек автозапуска.

        Returns:
            List[StartupEntry]: Список всех обнаруженных записей автозапуска.
        """
        entries: List[StartupEntry] = []
        self._load_startup_approved_cache()

        # 1. Сканирование реестра Run / RunOnce / WOW64
        entries.extend(self._scan_registry_run_keys())

        # 2. Сканирование папок автозагрузки
        entries.extend(self._scan_startup_folders())

        # 3. Сканирование Winlogon и параметров загрузки
        entries.extend(self._scan_winlogon_and_init())

        # 4. Сканирование IFEO перехватов
        entries.extend(self._scan_ifeo_debuggers())

        # 5. Сканирование задач планировщика
        entries.extend(self._scan_scheduled_tasks())

        # 6. Сканирование автозапускаемых служб
        entries.extend(self._scan_services())

        return entries

    def _load_startup_approved_cache(self) -> None:
        """Загрузка состояний отключенных элементов из StartupApproved."""
        self._disabled_cache = {}
        if not HAS_WINREG:
            return

        hives = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"),
        ]

        for root, subkey in hives:
            try:
                with winreg.OpenKey(root, subkey, 0, winreg.KEY_READ) as key:
                    num_values = winreg.QueryInfoKey(key)[1]
                    for i in range(num_values):
                        val_name, val_data, val_type = winreg.EnumValue(key, i)
                        # В Windows первый байт: 02/00 - включено, 03/01/06/другие - отключено
                        if isinstance(val_data, (bytes, bytearray)) and len(val_data) > 0:
                            first_byte = val_data[0]
                            is_disabled = (first_byte % 2 == 1) or (first_byte > 2)
                            self._disabled_cache[val_name.lower()] = is_disabled
            except Exception as e:
                logger.debug(f"Не удалось прочитать {subkey}: {e}")

    def _scan_registry_run_keys(self) -> List[StartupEntry]:
        """Сканирование веток Run, RunOnce, Policies в реестре."""
        entries: List[StartupEntry] = []
        if not HAS_WINREG:
            return entries

        targets = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU Run", StartupLocationType.REGISTRY_RUN),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKCU RunOnce", StartupLocationType.REGISTRY_RUNONCE),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM Run", StartupLocationType.REGISTRY_RUN),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKLM RunOnce", StartupLocationType.REGISTRY_RUNONCE),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", "HKLM WOW6432Node Run", StartupLocationType.REGISTRY_RUN),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run", "HKCU Policies Run", StartupLocationType.REGISTRY_POLICIES),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run", "HKLM Policies Run", StartupLocationType.REGISTRY_POLICIES),
        ]

        for root, subkey, label, loc_type in targets:
            try:
                with winreg.OpenKey(root, subkey, 0, winreg.KEY_READ) as key:
                    num_values = winreg.QueryInfoKey(key)[1]
                    for i in range(num_values):
                        val_name, val_data, _ = winreg.EnumValue(key, i)
                        if not val_name and not val_data:
                            continue
                        
                        raw_cmd = str(val_data)
                        exe_path, args = self._parse_command_line(raw_cmd)
                        is_disabled = self._disabled_cache.get(val_name.lower(), False)
                        file_info = self._get_file_info(exe_path)

                        entry_id = f"reg_{label.lower().replace(' ', '_')}_{i}_{val_name}"
                        entries.append(
                            StartupEntry(
                                id=entry_id,
                                name=val_name or "Unnamed",
                                location_type=loc_type,
                                location_path=f"{label} -> {val_name}",
                                command=raw_cmd,
                                executable_path=exe_path,
                                arguments=args,
                                publisher=file_info.get("publisher", "Неизвестен"),
                                is_signed=file_info.get("is_signed", False),
                                is_enabled=not is_disabled,
                                file_exists=file_info.get("exists", False),
                                file_size_kb=file_info.get("size_kb", 0.0),
                                created_date=file_info.get("created_date"),
                            )
                        )
            except Exception as e:
                logger.debug(f"Ветка реестра не найдена или недоступна {subkey}: {e}")

        return entries

    def _scan_startup_folders(self) -> List[StartupEntry]:
        """Сканирование папок автозагрузки в профиле пользователя и ProgramData."""
        entries: List[StartupEntry] = []
        folders = [
            (
                Path(os.getenv("APPDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\Startup",
                StartupLocationType.STARTUP_FOLDER_USER,
                "Пользовательская папка Startup",
            ),
            (
                Path(os.getenv("PROGRAMDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\Startup",
                StartupLocationType.STARTUP_FOLDER_COMMON,
                "Общая папка Startup",
            ),
        ]

        for folder_path, loc_type, label in folders:
            if not folder_path.exists() or not folder_path.is_dir():
                continue

            try:
                for item in folder_path.iterdir():
                    if item.name.lower() in ("desktop.ini", "thumbs.db"):
                        continue
                    
                    target_exe, target_args = self._resolve_shortcut(item)
                    file_info = self._get_file_info(target_exe or str(item))
                    is_disabled = self._disabled_cache.get(item.name.lower(), False)

                    entry_id = f"startup_folder_{loc_type.value}_{item.stem}"
                    entries.append(
                        StartupEntry(
                            id=entry_id,
                            name=item.name,
                            location_type=loc_type,
                            location_path=str(item),
                            command=f'"{target_exe}" {target_args}'.strip(),
                            executable_path=target_exe or str(item),
                            arguments=target_args,
                            publisher=file_info.get("publisher", "Неизвестен"),
                            is_signed=file_info.get("is_signed", False),
                            is_enabled=not is_disabled,
                            file_exists=file_info.get("exists", False),
                            file_size_kb=file_info.get("size_kb", 0.0),
                            created_date=file_info.get("created_date"),
                        )
                    )
            except Exception as e:
                logger.warning(f"Ошибка при сканировании папки автозагрузки {folder_path}: {e}")

        return entries

    def _scan_winlogon_and_init(self) -> List[StartupEntry]:
        """Сканирование системных параметров Winlogon (Userinit, Shell, AppInit_DLLs)."""
        entries: List[StartupEntry] = []
        if not HAS_WINREG:
            return entries

        winlogon_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon", "Userinit"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon", "Shell"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon", "Taskman"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon", "Shell"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows NT\CurrentVersion\Windows", "AppInit_DLLs"),
        ]

        for root, subkey, val_name in winlogon_keys:
            try:
                with winreg.OpenKey(root, subkey, 0, winreg.KEY_READ) as key:
                    val_data, _ = winreg.QueryValueEx(key, val_name)
                    if val_data and str(val_data).strip():
                        raw_cmd = str(val_data).strip()
                        exe_path, args = self._parse_command_line(raw_cmd)
                        file_info = self._get_file_info(exe_path)

                        entry_id = f"winlogon_{subkey.split(chr(92))[-1]}_{val_name}"
                        entries.append(
                            StartupEntry(
                                id=entry_id,
                                name=f"Winlogon {val_name}",
                                location_type=StartupLocationType.WINLOGON,
                                location_path=rf"{subkey}\{val_name}",
                                command=raw_cmd,
                                executable_path=exe_path,
                                arguments=args,
                                publisher=file_info.get("publisher", "Microsoft Windows"),
                                is_signed=file_info.get("is_signed", True),
                                is_enabled=True,
                                file_exists=file_info.get("exists", True),
                                file_size_kb=file_info.get("size_kb", 0.0),
                                created_date=file_info.get("created_date"),
                            )
                        )
            except Exception:
                pass

        return entries

    def _scan_ifeo_debuggers(self) -> List[StartupEntry]:
        """Сканирование перехватчиков Image File Execution Options (IFEO)."""
        entries: List[StartupEntry] = []
        if not HAS_WINREG:
            return entries

        ifeo_path = r"Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, ifeo_path, 0, winreg.KEY_READ) as key:
                num_subkeys = winreg.QueryInfoKey(key)[0]
                for i in range(num_subkeys):
                    app_name = winreg.EnumKey(key, i)
                    try:
                        with winreg.OpenKey(key, app_name, 0, winreg.KEY_READ) as app_key:
                            debugger_val, _ = winreg.QueryValueEx(app_key, "Debugger")
                            if debugger_val:
                                raw_cmd = str(debugger_val)
                                exe_path, args = self._parse_command_line(raw_cmd)
                                file_info = self._get_file_info(exe_path)

                                entries.append(
                                    StartupEntry(
                                        id=f"ifeo_{app_name}",
                                        name=f"IFEO Перехват: {app_name}",
                                        location_type=StartupLocationType.IFEO,
                                        location_path=rf"HKLM\{ifeo_path}\{app_name}\Debugger",
                                        command=raw_cmd,
                                        executable_path=exe_path,
                                        arguments=args,
                                        publisher=file_info.get("publisher", "Неизвестен"),
                                        is_signed=file_info.get("is_signed", False),
                                        is_enabled=True,
                                        file_exists=file_info.get("exists", False),
                                        file_size_kb=file_info.get("size_kb", 0.0),
                                        created_date=file_info.get("created_date"),
                                    )
                                )
                    except FileNotFoundError:
                        continue
        except Exception as e:
            logger.debug(f"Ошибка чтения IFEO: {e}")

        return entries

    def _scan_scheduled_tasks(self) -> List[StartupEntry]:
        """Сканирование задач планировщика с триггерами при входе или автозагрузке."""
        entries: List[StartupEntry] = []
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-ScheduledTask | Where-Object { $_.Triggers.Enabled -contains $true -and ($_.Triggers.CimClass.CimClassName -match 'Logon|Boot|Startup' -or $_.TaskPath -notmatch '^\\\\Microsoft') } | "
            "Select-Object TaskName, TaskPath, State, @{N='Execute';E={$_.Actions.Execute}}, @{N='Arguments';E={$_.Actions.Arguments}} | "
            "ConvertTo-Json -Compress",
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                items = [data] if isinstance(data, dict) else data

                for task in items:
                    task_name = task.get("TaskName", "UnknownTask")
                    exe_cmd = task.get("Execute") or ""
                    args = task.get("Arguments") or ""
                    state = task.get("State", "Ready")

                    if not exe_cmd:
                        continue

                    exe_path, extra_args = self._parse_command_line(exe_cmd)
                    if extra_args and not args:
                        args = extra_args

                    file_info = self._get_file_info(exe_path)
                    entries.append(
                        StartupEntry(
                            id=f"task_{task_name.replace(' ', '_')}",
                            name=f"Задача: {task_name}",
                            location_type=StartupLocationType.SCHEDULED_TASK,
                            location_path=task.get("TaskPath", "\\") + task_name,
                            command=f"{exe_cmd} {args}".strip(),
                            executable_path=exe_path,
                            arguments=str(args),
                            publisher=file_info.get("publisher", "Неизвестен"),
                            is_signed=file_info.get("is_signed", False),
                            is_enabled=(str(state).lower() in ("ready", "running", "enabled")),
                            file_exists=file_info.get("exists", False),
                            file_size_kb=file_info.get("size_kb", 0.0),
                            created_date=file_info.get("created_date"),
                        )
                    )
        except Exception as e:
            logger.debug(f"Не удалось получить задачи планировщика: {e}")

        return entries

    def _scan_services(self) -> List[StartupEntry]:
        """Сканирование сторонних автозапускаемых служб Windows."""
        entries: List[StartupEntry] = []
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_Service | Where-Object { $_.StartMode -eq 'Auto' -and $_.PathName -ne $null -and $_.PathName -notmatch '(?i)C:\\\\Windows\\\\System32\\\\svchost.exe' } | "
            "Select-Object Name, DisplayName, State, StartMode, PathName | ConvertTo-Json -Compress",
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                items = [data] if isinstance(data, dict) else data

                for svc in items:
                    svc_name = svc.get("Name", "UnknownService")
                    display_name = svc.get("DisplayName", svc_name)
                    path_name = svc.get("PathName", "")
                    state = svc.get("State", "Stopped")

                    exe_path, args = self._parse_command_line(path_name)
                    file_info = self._get_file_info(exe_path)

                    entries.append(
                        StartupEntry(
                            id=f"svc_{svc_name}",
                            name=f"Служба: {display_name}",
                            location_type=StartupLocationType.WINDOWS_SERVICE,
                            location_path=f"HKLM\\SYSTEM\\CurrentControlSet\\Services\\{svc_name}",
                            command=path_name,
                            executable_path=exe_path,
                            arguments=args,
                            publisher=file_info.get("publisher", "Неизвестен"),
                            is_signed=file_info.get("is_signed", False),
                            is_enabled=True,
                            file_exists=file_info.get("exists", False),
                            file_size_kb=file_info.get("size_kb", 0.0),
                            created_date=file_info.get("created_date"),
                        )
                    )
        except Exception as e:
            logger.debug(f"Не удалось получить список служб: {e}")

        return entries

    def _parse_command_line(self, cmd_line: str) -> Tuple[str, str]:
        """Извлечение чистого пути к исполняемому файлу и аргументов из строки команды."""
        if not cmd_line or not cmd_line.strip():
            return "", ""

        cmd_line = os.path.expandvars(cmd_line.strip())

        # Если команда заключена в кавычки: "C:\Path\app.exe" /arg1
        if cmd_line.startswith('"'):
            end_quote = cmd_line.find('"', 1)
            if end_quote != -1:
                exe_part = cmd_line[1:end_quote]
                args_part = cmd_line[end_quote + 1 :].strip()
                return exe_part, args_part

        # Если кавычек нет, ищем первое совпадение .exe/.bat/.cmd/.vbs
        match = re.search(r"^(.*?(\.exe|\.bat|\.cmd|\.vbs|\.ps1|\.dll|\.com))\b(.*)$", cmd_line, re.IGNORECASE)
        if match:
            exe_part = match.group(1).strip()
            args_part = match.group(3).strip()
            return exe_part, args_part

        # Разделение по пробелу
        parts = cmd_line.split(" ", 1)
        return parts[0], parts[1] if len(parts) > 1 else ""

    def _resolve_shortcut(self, file_path: Path) -> Tuple[str, str]:
        """Разрешение пути ярлыка .lnk или возврат прямого пути."""
        if not file_path.suffix.lower() == ".lnk":
            return str(file_path), ""

        # Быстрое извлечение через PowerShell WScript.Shell
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            f"$sh = New-Object -ComObject WScript.Shell; $target = $sh.CreateShortcut('{str(file_path)}'); Write-Output ($target.TargetPath + '|' + $target.Arguments)",
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                out = res.stdout.strip().split("|", 1)
                target = out[0] if len(out) > 0 else ""
                args = out[1] if len(out) > 1 else ""
                if target:
                    return target, args
        except Exception:
            pass

        return str(file_path), ""

    def _get_file_info(self, file_path_str: str) -> Dict[str, Any]:
        """Проверка существования файла, размера и метаданных."""
        result: Dict[str, Any] = {
            "exists": False,
            "size_kb": 0.0,
            "publisher": "Неизвестен",
            "is_signed": False,
            "created_date": None,
        }

        if not file_path_str:
            return result

        try:
            clean_path = os.path.expandvars(file_path_str.strip('"'))
            p = Path(clean_path)

            # Если путь не существует и имя короткое (e.g. explorer.exe), ищем в Windows каталогах
            if not p.exists() or not p.is_file():
                sys_root = os.getenv("SystemRoot", "C:\\Windows")
                candidates = [
                    Path(sys_root) / clean_path,
                    Path(sys_root) / "System32" / clean_path,
                ]
                for cand in candidates:
                    if cand.exists() and cand.is_file():
                        p = cand
                        break

            if p.exists() and p.is_file():
                result["exists"] = True
                stat = p.stat()
                result["size_kb"] = round(stat.st_size / 1024.0, 2)
                
                # Простая эвристика издателя на основе каталога
                path_lower = str(p).lower()
                if "windows\\system32" in path_lower or "windows\\winsxs" in path_lower:
                    result["publisher"] = "Microsoft Corporation"
                    result["is_signed"] = True
                elif "microsoft" in path_lower:
                    result["publisher"] = "Microsoft Corporation"
                    result["is_signed"] = True
                elif "google" in path_lower:
                    result["publisher"] = "Google LLC"
                    result["is_signed"] = True
                elif "nvidia" in path_lower:
                    result["publisher"] = "NVIDIA Corporation"
                    result["is_signed"] = True
                elif "intel" in path_lower:
                    result["publisher"] = "Intel Corporation"
                    result["is_signed"] = True
                elif "amd" in path_lower or "advanced micro devices" in path_lower:
                    result["publisher"] = "Advanced Micro Devices, Inc."
                    result["is_signed"] = True
        except Exception:
            pass

        return result
