# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Storage Directory and Data Classifier
# =============================================================================
# Description:
#   Поиск и категоризация каталогов хранения данных приложений:
#   - %APPDATA% (Roaming) -> Настройки пользователя
#   - %LOCALAPPDATA% -> Кэш, локальные данные
#   - %PROGRAMDATA% -> Общие данные системы
#   - Поиск баз данных (.sqlite, .db), логов и кэша
#
# File: storage_analyzer.py
# Project: ai-breadboard
# Package: apps.software_transparency_scanner.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль классификации мест хранения данных программ."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from apps.software_transparency_scanner.core.models import (
    EvidenceStatus,
    SoftwareItem,
    StorageCategory,
    StorageDirectory,
)


class StorageAnalyzer:
    """Анализатор файловых путей и каталогов хранения пользовательских данных."""

    ROOT_ENV_DIRS = [
        ("%APPDATA%", os.getenv("APPDATA"), StorageCategory.CONFIG, "Пользовательские настройки и профили (Roaming)"),
        ("%LOCALAPPDATA%", os.getenv("LOCALAPPDATA"), StorageCategory.CACHE, "Кэш, временные данные и локальное хранилище"),
        ("%PROGRAMDATA%", os.getenv("PROGRAMDATA"), StorageCategory.CONFIG, "Общие конфигурации и данные всех пользователей"),
        ("%USERPROFILE%\\.config", os.path.join(os.getenv("USERPROFILE", ""), ".config"), StorageCategory.CONFIG, "Конфигурационные каталоги Unix-стиля"),
    ]

    def discover_storage_for_app(self, app: SoftwareItem) -> List[StorageDirectory]:
        """Находит каталоги данных, ассоциированные с конкретной программой.

        Args:
            app: Карточка установленного ПО.

        Returns:
            List[StorageDirectory]: Список найденных каталогов с их категоризацией.
        """
        results: List[StorageDirectory] = []
        app_names = self._get_search_aliases(app)

        # 1. Проверяем каталог установки (Binaries)
        if app.install_location and os.path.isdir(app.install_location):
            stats = self._get_dir_stats(app.install_location)
            display = self._to_display_path(app.install_location)
            results.append(
                StorageDirectory(
                    path=app.install_location,
                    display_path=display,
                    category=StorageCategory.BINARIES,
                    description="Исполняемые файлы и библиотеки программы",
                    file_count=stats["file_count"],
                    total_size_bytes=stats["total_size"],
                    status=EvidenceStatus.LOCAL_OBSERVED,
                )
            )

        # 2. Ищем каталоги в AppData, LocalAppData, ProgramData
        for env_label, base_dir, default_cat, base_desc in self.ROOT_ENV_DIRS:
            if not base_dir or not os.path.exists(base_dir):
                continue

            matched_dir = self._find_matching_folder(base_dir, app_names)
            if matched_dir and os.path.isdir(matched_dir):
                stats = self._get_dir_stats(matched_dir)
                category, desc = self._classify_directory(matched_dir, default_cat, base_desc)
                display = self._to_display_path(matched_dir)

                results.append(
                    StorageDirectory(
                        path=matched_dir,
                        display_path=display,
                        category=category,
                        description=desc,
                        file_count=stats["file_count"],
                        total_size_bytes=stats["total_size"],
                        status=EvidenceStatus.LOCAL_OBSERVED,
                    )
                )

        return results

    def _get_search_aliases(self, app: SoftwareItem) -> List[str]:
        """Возвращает список возможных названий папок для программы."""
        aliases = [app.name.lower()]
        # Отсекаем суффиксы версий и разрядности
        clean_name = re_sub_clean(app.name).lower()
        if clean_name and clean_name not in aliases:
            aliases.append(clean_name)

        if app.publisher and app.publisher.lower() not in ("неизвестен", "unknown"):
            pub_clean = re_sub_clean(app.publisher).lower()
            if pub_clean:
                aliases.append(pub_clean)

        # Извлечение из executable_path
        if app.executable_path:
            exe_stem = Path(app.executable_path).stem.lower()
            if exe_stem not in aliases:
                aliases.append(exe_stem)

        return aliases

    def _find_matching_folder(self, base_path: str, aliases: List[str]) -> Optional[str]:
        """Ищет подкаталог, совпадающий с одним из алиасов приложения."""
        try:
            entries = os.listdir(base_path)
        except (OSError, PermissionError):
            return None

        entries_lower = {e.lower(): e for e in entries}

        for alias in aliases:
            if alias in entries_lower:
                return os.path.join(base_path, entries_lower[alias])

            # Частичное совпадение
            for e_low, orig_name in entries_lower.items():
                if alias in e_low or e_low in alias:
                    # Проверяем, что совпадение не тривиальное (длина > 3)
                    if len(alias) >= 4 and len(e_low) >= 4:
                        return os.path.join(base_path, orig_name)

        return None

    def _classify_directory(
        self, folder_path: str, default_cat: StorageCategory, default_desc: str
    ) -> tuple[StorageCategory, str]:
        """Классифицирует назначение каталога на основе его содержимого."""
        f_lower = folder_path.lower()
        if "cache" in f_lower or "gpu_cache" in f_lower or "temp" in f_lower:
            return StorageCategory.CACHE, "Кэш и временные рабочие данные"
        if "log" in f_lower or "crashpad" in f_lower:
            return StorageCategory.LOGS, "Журналы работы и отчеты об ошибках"

        return default_cat, default_desc

    def _get_dir_stats(self, dir_path: str) -> Dict[str, int]:
        """Считает количество файлов и размер в каталоге (не глубже 2 уровней)."""
        file_count = 0
        total_size = 0
        try:
            for root, _, files in os.walk(dir_path):
                # Ограничение глубины
                depth = len(Path(root).relative_to(Path(dir_path)).parts)
                if depth > 2:
                    continue
                for f in files:
                    file_count += 1
                    fp = os.path.join(root, f)
                    try:
                        total_size += os.path.getsize(fp)
                    except OSError:
                        pass
        except (OSError, PermissionError):
            pass
        return {"file_count": file_count, "total_size": total_size}

    def _to_display_path(self, full_path: str) -> str:
        """Заменяет абсолютный префикс на макрос окружения."""
        p = full_path
        for env_var in ("APPDATA", "LOCALAPPDATA", "PROGRAMDATA", "USERPROFILE", "ProgramFiles", "ProgramFiles(x86)"):
            val = os.getenv(env_var)
            if val and p.lower().startswith(val.lower()):
                return f"%{env_var}%{p[len(val):]}"
        return p


def re_sub_clean(text: str) -> str:
    """Очистка текста от спецсимволов и версионных маркеров."""
    import re
    return re.sub(r"(?i)\b(inc|llc|corp|corporation|ltd|gmbh|64-bit|32-bit|x64|x86|v\d+[\.\d]*)\b", "", text).strip()
