# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows User Folders & Storage Relocation Engine
# =============================================================================
# Description:
#   Движок для анализа размеров пользовательских директорий Windows
#   (Рабочий стол, Документы, Загрузки, Изображения, Музыка, Видео),
#   поиска доступных физических дисков и безопасного переноса папок
#   с обновлением реестра User Shell Folders и библиотек Windows.
#
# Examples:
#   >>> from apps.windows.backup_manager.core.user_folders_manager import UserFoldersManager
#   >>> mgr = UserFoldersManager()
#   >>> overview = mgr.get_overview()
#   >>> res = mgr.relocate_folder("Downloads", "D:")
#
# File: user_folders_manager.py
# Project: ai-breadboard
# Package: apps.windows.backup_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Движок анализа и переноса пользовательских директорий Windows."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil

from logger import logger
from apps.windows.backup_manager.core.libraries_manager import WindowsLibrariesManager
from apps.windows.backup_manager.core.models import (
    RelocateFolderResponse,
    TargetDriveInfo,
    UserFolderInfo,
    UserFoldersOverviewResponse,
)

# Известные GUID и имена в реестре Windows User Shell Folders
FOLDER_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "id": "Personal",
        "guid_keys": ["Personal", "{F42EE2D3-909F-4907-8871-4C22FC0BF756}"],
        "name": "Документы",
        "default_subfolder": "Documents",
        "library_name": "Documents",
    },
    {
        "id": "Downloads",
        "guid_keys": ["{374DE290-123F-4565-9164-39C4925E467B}", "{7D83EE9B-2244-4E70-B1F5-5393042AF1E4}"],
        "name": "Загрузки",
        "default_subfolder": "Downloads",
        "library_name": "Downloads",
    },
    {
        "id": "Desktop",
        "guid_keys": ["Desktop"],
        "name": "Рабочий стол",
        "default_subfolder": "Desktop",
        "library_name": "Desktop",
    },
    {
        "id": "My Pictures",
        "guid_keys": ["My Pictures", "{0DDD015D-B06C-45D5-8C4C-F59713854639}"],
        "name": "Изображения",
        "default_subfolder": "Pictures",
        "library_name": "Pictures",
    },
    {
        "id": "My Music",
        "guid_keys": ["My Music", "{A0C69A99-21C8-4671-8703-7934162FCF1D}"],
        "name": "Музыка",
        "default_subfolder": "Music",
        "library_name": "Music",
    },
    {
        "id": "My Video",
        "guid_keys": ["My Video", "{35286A68-3C57-41A1-BBB1-0EAE73D76C95}"],
        "name": "Видео",
        "default_subfolder": "Videos",
        "library_name": "Videos",
    },
]

REG_USER_SHELL_FOLDERS = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
REG_SHELL_FOLDERS = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"


class UserFoldersManager:
    """Менеджер пользовательских директорий и их распределения по дискам."""

    def __init__(self, lib_mgr: Optional[WindowsLibrariesManager] = None) -> None:
        """Инициализация менеджера.

        Args:
            lib_mgr: Экземпляр WindowsLibrariesManager для синхронизации библиотек.
        """
        self.lib_mgr = lib_mgr or WindowsLibrariesManager()

    def _read_registry_path(self, reg_key_names: List[str]) -> Optional[str]:
        """Считывает путь папки из реестра Windows User Shell Folders.

        Args:
            reg_key_names: Список возможных имен ключей реестра.

        Returns:
            Optional[str]: Раскрытый абсолютный путь или None.
        """
        if sys.platform != "win32":
            return None

        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_USER_SHELL_FOLDERS) as key:
                for kn in reg_key_names:
                    try:
                        val, _ = winreg.QueryValueEx(key, kn)
                        if val:
                            return os.path.expandvars(str(val))
                    except OSError:
                        continue
        except Exception as ex:
            logger.debug(f"Не удалось прочитать User Shell Folders из реестра: {ex}")

        return None

    def _update_registry_paths(self, reg_key_names: List[str], new_path: str) -> bool:
        """Обновляет пути папки в реестре User Shell Folders и Shell Folders.

        Args:
            reg_key_names: Имена ключей реестра для обновления.
            new_path: Новый абсолютный путь к папке.

        Returns:
            bool: True при успешной записи.
        """
        if sys.platform != "win32":
            return False

        import winreg

        success = False
        # 1. Запись в User Shell Folders (основное место в современных Windows)
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_USER_SHELL_FOLDERS, 0, winreg.KEY_SET_VALUE) as key:
                for kn in reg_key_names:
                    winreg.SetValueEx(key, kn, 0, winreg.REG_EXPAND_SZ, new_path)
            success = True
        except Exception as ex:
            logger.error(f"Ошибка записи в User Shell Folders ({reg_key_names}): {ex}")

        # 2. Запись в классический Shell Folders для совместимости со старыми приложениями
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_SHELL_FOLDERS, 0, winreg.KEY_SET_VALUE) as key:
                for kn in reg_key_names:
                    winreg.SetValueEx(key, kn, 0, winreg.REG_SZ, new_path)
        except Exception as ex:
            logger.debug(f"Запись в Shell Folders (fallback): {ex}")

        # 3. Оповещение оболочки Windows Shell о смене путей
        try:
            import ctypes
            # SHCNE_ASSOCCHANGED = 0x08000000, SHCNF_IDLIST = 0
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)
        except Exception as ex:
            logger.debug(f"SHChangeNotify failed: {ex}")

        return success

    def _calculate_directory_size(self, folder_path: str) -> Tuple[int, int]:
        """Рекурсивно вычисляет размер директории в байтах и число файлов.

        Args:
            folder_path: Путь к директории.

        Returns:
            Tuple[int, int]: (общий размер в байтах, количество файлов).
        """
        p = Path(folder_path)
        if not p.exists() or not p.is_dir():
            return 0, 0

        total_bytes = 0
        file_count = 0

        try:
            for entry in os.scandir(folder_path):
                try:
                    if entry.is_file(follow_symlinks=False):
                        total_bytes += entry.stat(follow_symlinks=False).st_size
                        file_count += 1
                    elif entry.is_dir(follow_symlinks=False):
                        sub_bytes, sub_count = self._calculate_directory_size(entry.path)
                        total_bytes += sub_bytes
                        file_count += sub_count
                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError):
            pass

        return total_bytes, file_count

    def get_user_folders(self) -> List[UserFolderInfo]:
        """Получает текущие пользовательские папки, их размеры и расположение.

        Returns:
            List[UserFolderInfo]: Список описаний пользовательских папок.
        """
        user_home = Path.home()
        result: List[UserFolderInfo] = []

        for fdef in FOLDER_DEFINITIONS:
            fid = fdef["id"]
            name = fdef["name"]
            subfolder = fdef["default_subfolder"]
            reg_keys = fdef["guid_keys"]
            lib_name = fdef["library_name"]

            reg_path = self._read_registry_path(reg_keys)
            actual_path = reg_path if reg_path else str(user_home / subfolder)

            p = Path(actual_path)
            exists = p.exists()
            drive_letter = p.drive if p.drive else (actual_path[:2] if len(actual_path) >= 2 and actual_path[1] == ":" else "C:")

            size_bytes, file_count = self._calculate_directory_size(actual_path) if exists else (0, 0)
            size_mb = round(size_bytes / (1024 ** 2), 2)
            size_gb = round(size_bytes / (1024 ** 3), 2)

            result.append(
                UserFolderInfo(
                    folder_id=fid,
                    name=name,
                    current_path=actual_path,
                    drive_letter=drive_letter.upper(),
                    size_bytes=size_bytes,
                    size_mb=size_mb,
                    size_gb=size_gb,
                    file_count=file_count,
                    exists=exists,
                    library_associated=lib_name,
                )
            )

        return result

    def get_available_drives(self) -> List[TargetDriveInfo]:
        """Возвращает список всех доступных локальных дисков и информацию о свободном месте.

        Returns:
            List[TargetDriveInfo]: Список дисков.
        """
        drives: List[TargetDriveInfo] = []
        try:
            partitions = psutil.disk_partitions(all=False)
            for part in partitions:
                # Фильтруем оптические приводы и пустые устройства
                if "cdrom" in part.opts or part.fstype == "":
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    total_gb = round(usage.total / (1024 ** 3), 2)
                    free_gb = round(usage.free / (1024 ** 3), 2)
                    used_gb = round(usage.used / (1024 ** 3), 2)
                    drive_let = part.device.replace("\\", "").upper()
                    if not drive_let.endswith(":"):
                        drive_let = drive_let + ":"

                    is_sys = drive_let.startswith("C")

                    drives.append(
                        TargetDriveInfo(
                            drive_letter=drive_let,
                            mount_point=part.mountpoint,
                            fstype=part.fstype,
                            total_space_gb=total_gb,
                            free_space_gb=free_gb,
                            used_space_gb=used_gb,
                            is_system_drive=is_sys,
                        )
                    )
                except (PermissionError, OSError):
                    continue
        except Exception as ex:
            logger.error(f"Ошибка получения списка дисков psutil: {ex}")

        return drives

    def get_overview(self) -> UserFoldersOverviewResponse:
        """Формирует полную сводку по пользовательским папкам и дискам для интерфейса.

        Returns:
            UserFoldersOverviewResponse: Объединенные данные о папках и доступных дисках.
        """
        folders = self.get_user_folders()
        drives = self.get_available_drives()

        total_bytes = sum(f.size_bytes for f in folders)
        total_mb = round(total_bytes / (1024 ** 2), 2)
        total_gb = round(total_bytes / (1024 ** 3), 2)

        # Вторичные диски (не системные и имеющие > 1 ГБ свободного места)
        available_targets = [d for d in drives if not d.is_system_drive and d.free_space_gb >= 1.0]

        return UserFoldersOverviewResponse(
            folders=folders,
            total_user_size_mb=total_mb,
            total_user_size_gb=total_gb,
            drives=drives,
            available_target_drives=available_targets,
        )

    def choose_folder_dialog(
        self, initial_path: Optional[str] = None, title: str = "Выберите целевую папку для переноса"
    ) -> Optional[str]:
        """Открывает нативный системный диалог выбора папки Windows.

        Args:
            initial_path: Начальная директория в диалоге.
            title: Заголовок окна диалога.

        Returns:
            Optional[str]: Выбранный абсолютный путь к папке или None при отмене.
        """
        import subprocess

        # 1. Попытка через Tkinter askdirectory в изолированном подпроцессе
        py_script = (
            "import sys, tkinter as tk, tkinter.filedialog as fd\n"
            "root = tk.Tk()\n"
            "root.withdraw()\n"
            "root.attributes('-topmost', True)\n"
            "initial = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None\n"
            "title = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else 'Выберите целевую папку'\n"
            "path = fd.askdirectory(parent=root, initialdir=initial, title=title, mustexist=False)\n"
            "root.destroy()\n"
            "if path:\n"
            "    print(path.replace('/', '\\\\'))\n"
        )
        try:
            res = subprocess.run(
                [sys.executable, "-c", py_script, initial_path or "", title],
                capture_output=True,
                text=True,
                timeout=180,
                encoding="utf-8",
            )
            chosen = res.stdout.strip()
            if chosen:
                return chosen
        except Exception as ex:
            logger.warning(f"Ошибка при вызове диалога выбора папки через Tkinter: {ex}")

        # 2. Fallback через PowerShell FolderBrowserDialog
        try:
            ps_cmd = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "$f = New-Object System.Windows.Forms.FolderBrowserDialog; "
                f"$f.Description = '{title}'; "
                "$f.ShowNewFolderButton = $true; "
            )
            if initial_path and os.path.exists(initial_path):
                ps_cmd += f"$f.SelectedPath = '{initial_path}'; "
            ps_cmd += "if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { [Console]::WriteLine($f.SelectedPath) }"
            res = subprocess.run(
                ["powershell", "-NoProfile", "-STA", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=180,
            )
            chosen = res.stdout.strip()
            if chosen:
                return chosen
        except Exception as ex:
            logger.error(f"Ошибка при вызове диалога выбора папки через PowerShell: {ex}")

        return None

    def relocate_folder(
        self,
        folder_id: str,
        target_drive_letter: Optional[str] = None,
        target_path: Optional[str] = None,
        delete_source_after: bool = False,
    ) -> RelocateFolderResponse:
        """Переносит пользовательскую папку на другой физический диск или в кастомную директорию.

        Args:
            folder_id: Идентификатор папки (Downloads, Personal, etc.).
            target_drive_letter: Буква целевого диска (например, 'D:' или 'D:\\').
            target_path: Пользовательский целевой путь (директория) для переноса.
            delete_source_after: Удалить ли файлы из исходной папки после успешного копирования.

        Returns:
            RelocateFolderResponse: Результат выполнения операции.
        """
        # 1. Поиск определения папки
        fdef = next((f for f in FOLDER_DEFINITIONS if f["id"].lower() == folder_id.lower()), None)
        if not fdef:
            return RelocateFolderResponse(
                success=False,
                folder_id=folder_id,
                old_path="",
                new_path="",
                message=f"Неизвестный идентификатор папки: '{folder_id}'",
            )

        reg_path = self._read_registry_path(fdef["guid_keys"])
        user_home = Path.home()
        current_path = reg_path if reg_path else str(user_home / fdef["default_subfolder"])
        current_path_obj = Path(current_path).resolve()

        if not current_path_obj.exists():
            return RelocateFolderResponse(
                success=False,
                folder_id=folder_id,
                old_path=current_path,
                new_path="",
                message=f"Исходная папка '{current_path}' не существует на диске.",
            )

        # 2. Определение целевого пути
        if target_path and target_path.strip():
            new_path_obj = Path(target_path.strip()).resolve()
            target_drive = new_path_obj.drive.upper()
            if not target_drive:
                return RelocateFolderResponse(
                    success=False,
                    folder_id=folder_id,
                    old_path=current_path,
                    new_path="",
                    message=f"Некорректный целевой путь '{target_path}'. Укажите абсолютный путь с диском.",
                )
        elif target_drive_letter and target_drive_letter.strip():
            target_drive = target_drive_letter.strip().replace("/", "\\").rstrip("\\").upper()
            if not target_drive.endswith(":"):
                target_drive = target_drive + ":"
            username = user_home.name
            new_path_obj = Path(f"{target_drive}\\Users\\{username}\\{fdef['default_subfolder']}").resolve()
        else:
            return RelocateFolderResponse(
                success=False,
                folder_id=folder_id,
                old_path=current_path,
                new_path="",
                message="Не указан целевой диск или целевая папка для переноса.",
            )

        new_path = str(new_path_obj)

        # Проверка, не совпадает ли целевой путь с текущим
        if str(current_path_obj).lower() == str(new_path_obj).lower():
            return RelocateFolderResponse(
                success=False,
                folder_id=folder_id,
                old_path=current_path,
                new_path=new_path,
                message=f"Папка уже находится в указанной директории '{new_path}'.",
            )

        # 3. Проверка свободного места
        try:
            usage = psutil.disk_usage(f"{target_drive}\\")
        except Exception as ex:
            return RelocateFolderResponse(
                success=False,
                folder_id=folder_id,
                old_path=current_path,
                new_path="",
                message=f"Целевой диск {target_drive} недоступен: {ex}",
            )

        folder_size_bytes, total_files = self._calculate_directory_size(current_path)
        required_bytes = folder_size_bytes + int(1 * 1024 * 1024 * 1024)  # + 1 ГБ буфер

        if usage.free < required_bytes:
            free_gb = round(usage.free / (1024 ** 3), 2)
            req_gb = round(required_bytes / (1024 ** 3), 2)
            return RelocateFolderResponse(
                success=False,
                folder_id=folder_id,
                old_path=current_path,
                new_path="",
                message=f"Недостаточно места на диске {target_drive}. Требуется: {req_gb} ГБ (с запасом), свободно: {free_gb} ГБ.",
            )

        # 4. Создание целевой директории
        new_path_obj.mkdir(parents=True, exist_ok=True)

        # 5. Копирование содержимого
        copied_files = 0
        copied_bytes = 0
        try:
            for root, dirs, files in os.walk(current_path):
                rel_dir = os.path.relpath(root, current_path)
                dest_dir = new_path_obj if rel_dir == "." else new_path_obj / rel_dir
                dest_dir.mkdir(parents=True, exist_ok=True)

                for f in files:
                    src_file = Path(root) / f
                    dst_file = dest_dir / f
                    try:
                        shutil.copy2(str(src_file), str(dst_file))
                        copied_files += 1
                        copied_bytes += src_file.stat().st_size
                    except (PermissionError, OSError) as ex:
                        logger.warning(f"Пропуск файла {src_file} при копировании: {ex}")
        except Exception as ex:
            logger.error(f"Ошибка при копировании данных из {current_path} в {new_path}: {ex}")
            return RelocateFolderResponse(
                success=False,
                folder_id=folder_id,
                old_path=current_path,
                new_path=new_path,
                message=f"Ошибка копирования данных: {ex}",
                files_copied=copied_files,
                bytes_copied=copied_bytes,
            )

        # 6. Обновление реестра
        reg_updated = self._update_registry_paths(fdef["guid_keys"], new_path)
        if not reg_updated:
            logger.warning(f"Не удалось обновить реестр для {folder_id}, но файлы скопированы в {new_path}")

        # 7. Обновление системной библиотеки Windows (.library-ms)
        lib_name = fdef["library_name"]
        try:
            self.lib_mgr.add_folder_to_library(library_name=lib_name, folder_path=new_path, is_default_save=True)
            logger.info(f"Библиотека Windows '{lib_name}' обновлена с новым путем {new_path}")
        except Exception as ex:
            logger.debug(f"Не удалось обновить библиотеку {lib_name}: {ex}")

        # 8. Опциональная очистка старой директории
        if delete_source_after:
            try:
                for entry in os.scandir(current_path):
                    try:
                        if entry.is_file() or entry.is_symlink():
                            os.remove(entry.path)
                        elif entry.is_dir():
                            shutil.rmtree(entry.path, ignore_errors=True)
                    except Exception:
                        pass
                logger.info(f"Исходные файлы в {current_path} очищены после переноса")
            except Exception as ex:
                logger.warning(f"Не удалось полностью очистить исходную папку {current_path}: {ex}")

        msg = (
            f"Папка '{fdef['name']}' успешно перенесена в директорию '{new_path}'. "
            f"Скопировано {copied_files} файлов ({round(copied_bytes / (1024**2), 2)} МБ). "
            f"Реестр и библиотеки обновлены."
        )

        return RelocateFolderResponse(
            success=True,
            folder_id=folder_id,
            old_path=current_path,
            new_path=new_path,
            message=msg,
            files_copied=copied_files,
            bytes_copied=copied_bytes,
        )
