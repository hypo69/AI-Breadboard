# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Process_Manager Core - Classifier
# =============================================================================
# Description:
#   Движок классификации и группировки процессов Windows на категории:
#   1. Apps (Интерактивные оконные приложения и их подпроцессы)
#   2. Background processes (Фоновые службы и вспомогательные процессы)
#   3. Windows processes (Критические системные процессы ОС)
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.process_manager.core.classifier import ProcessClassifier
#
#     classifier = ProcessClassifier()
#     report = classifier.classify_processes()
#
# File: classifier.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.process_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 02:05:00
# =============================================================================

from __future__ import annotations
"""Движок классификации процессов Windows (Apps, Background processes, Windows processes)."""

import ctypes
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
import psutil
from logger import logger
from apps.windows.sdk.modules.process_manager.core.models import (
    CategorizedProcessReport,
    ProcessGroupItem,
    ProcessItem,
)

# Системные процессы Windows (Windows processes)
WINDOWS_SYSTEM_PROCESS_NAMES = {
    'system',
    'system idle process',
    'registry',
    'smss.exe',
    'csrss.exe',
    'wininit.exe',
    'services.exe',
    'lsass.exe',
    'svchost.exe',
    'dwm.exe',
    'fontdrvhost.exe',
    'winlogon.exe',
    'sihost.exe',
    'taskhostw.exe',
    'taskhost.exe',
    'runtimebroker.exe',
    'ctfmon.exe',
    'spoolsv.exe',
    'werfault.exe',
    'lsiso.exe',
    'secure-system',
    'vssvc.exe',
    'conhost.exe',
    'searchindexer.exe',
    'searchhost.exe',
    'startmenuexperiencehost.exe',
    'shellexperiencehost.exe',
    'smartscreen.exe',
    'securityhealthservice.exe',
    'securityhealthsystray.exe',
    'audiodg.exe',
    'wlanext.exe',
    'dashost.exe',
}

# Известные соответствия бинарников читаемым именам приложений (Friendly Names)
KNOWN_APP_FRIENDLY_NAMES = {
    'chrome.exe': 'Google Chrome',
    'msedge.exe': 'Microsoft Edge',
    'code.exe': 'Visual Studio Code',
    'antigravity.exe': 'Antigravity',
    'chatgpt.exe': 'ChatGPT',
    'telegram.exe': 'Telegram Desktop',
    'whatsapp.exe': 'WhatsApp',
    'keepass.exe': 'KeePass',
    'keepassxc.exe': 'KeePassXC',
    'taskmgr.exe': 'Task Manager',
    'windowsterminal.exe': 'Терминал',
    'wt.exe': 'Терминал',
    'explorer.exe': 'Windows Explorer',
    'notepad.exe': 'Блокнот',
    'devenv.exe': 'Microsoft Visual Studio',
    'slack.exe': 'Slack',
    'discord.exe': 'Discord',
    'spotify.exe': 'Spotify',
    'obs64.exe': 'OBS Studio',
    'vlc.exe': 'VLC Media Player',
    'postman.exe': 'Postman',
    'docker desktop.exe': 'Docker Desktop',
    'pycharm64.exe': 'PyCharm',
    'idea64.exe': 'IntelliJ IDEA',
    'rider64.exe': 'JetBrains Rider',
    'cursor.exe': 'Cursor IDE',
    'windsurf.exe': 'Windsurf IDE',
}


class ProcessClassifier:
    """Классификатор процессов Windows на Apps, Background и Windows процессы."""

    def __init__(self) -> None:
        """Инициализация классификатора процессов."""
        self._user32 = getattr(ctypes.windll, 'user32', None) if os.name == 'nt' else None

    def get_windowed_pids_and_titles(self) -> Tuple[Set[int], Dict[int, List[str]]]:
        """Определяет PID процессов, имеющих открытые видимые окна на рабочем столе.

        Returns:
            Tuple[Set[int], Dict[int, List[str]]]: Множество PID с окнами и словарь {pid: [список заголовков окон]}.
        """
        windowed_pids: Set[int] = set()
        titles_map: Dict[int, List[str]] = {}

        if not self._user32:
            return windowed_pids, titles_map

        try:
            enum_windows_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

            def _enum_window_callback(hwnd: Any, extra: Any) -> bool:
                try:
                    if self._user32.IsWindowVisible(hwnd):
                        length = self._user32.GetWindowTextLengthW(hwnd)
                        if length > 0:
                            buf = ctypes.create_unicode_buffer(length + 1)
                            self._user32.GetWindowTextW(hwnd, buf, length + 1)
                            title = buf.value.strip()
                            if title and title != 'Default IME' and title != 'MSCTFIME UI':
                                pid = ctypes.c_ulong()
                                self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                                if pid.value:
                                    windowed_pids.add(pid.value)
                                    titles_map.setdefault(pid.value, []).append(title)
                except Exception:
                    pass
                return True

            cb = enum_windows_proc(_enum_window_callback)
            self._user32.EnumWindows(cb, 0)
        except Exception as ex:
            logger.debug(f'Ошибка EnumWindows при классификации процессов: {ex}')

        return windowed_pids, titles_map

    def _get_friendly_name(self, binary_name: str, window_titles: Optional[List[str]] = None) -> str:
        """Возвращает дружелюбное человекочитаемое имя приложения.

        Args:
            binary_name: Имя исполняемого файла (например, chrome.exe).
            window_titles: Список заголовков окон (опционально).

        Returns:
            str: Отображаемое имя (например, Google Chrome).
        """
        low = binary_name.lower()
        if low in KNOWN_APP_FRIENDLY_NAMES:
            return KNOWN_APP_FRIENDLY_NAMES[low]

        # Если есть понятный заголовок окна и бинарник неизвестен
        if window_titles and window_titles[0]:
            primary_title = window_titles[0]
            # Убираем дефисы и суффиксы окон
            if ' - ' in primary_title:
                parts = primary_title.split(' - ')
                # Часто в конце идет имя программы: "Документ - Microsoft Word"
                if len(parts) > 1 and len(parts[-1].strip()) > 2:
                    return parts[-1].strip()
            if len(primary_title) <= 30:
                return primary_title

        # Очистка имени исполняемого файла от расширения
        clean_name = binary_name
        if clean_name.lower().endswith('.exe'):
            clean_name = clean_name[:-4]
        # Превращаем camelCase / snake_case в красивый заголовок
        return clean_name.replace('_', ' ').replace('-', ' ').title()

    def classify_processes(self) -> CategorizedProcessReport:
        """Собирает и классифицирует все активные процессы Windows на Apps, Background и Windows.

        Returns:
            CategorizedProcessReport: Структурированный сводный отчет по категориям.
        """
        windowed_pids, titles_map = self.get_windowed_pids_and_titles()

        raw_proc_items: List[ProcessItem] = []
        name_to_windowed: Dict[str, bool] = {}

        for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info', 'num_threads', 'create_time', 'exe']):
            try:
                p_info = p.info
                pid = p_info.get('pid', 0)
                name = p_info.get('name') or 'unknown'
                mem_rss = (p_info.get('memory_info').rss if p_info.get('memory_info') else 0)
                mem_mb = round(mem_rss / (1024 * 1024), 1)
                cpu_p = float(p_info.get('cpu_percent') or 0.0)
                num_t = int(p_info.get('num_threads') or 1)
                c_time = datetime.fromtimestamp(p_info.get('create_time', 0)).strftime('%Y-%m-%d %H:%M:%S') if p_info.get('create_time') else ''

                item = ProcessItem(
                    pid=pid,
                    name=name,
                    username=p_info.get('username'),
                    cpu_percent=cpu_p,
                    memory_mb=mem_mb,
                    num_threads=num_t,
                    create_time=c_time,
                    exe_path=p_info.get('exe')
                )
                raw_proc_items.append(item)

                if pid in windowed_pids:
                    name_to_windowed[name.lower()] = True

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Группировка процессов
        groups_by_category: Dict[str, Dict[str, List[ProcessItem]]] = {
            'app': {},
            'background': {},
            'windows': {},
        }

        for item in raw_proc_items:
            low_name = item.name.lower()
            exe_low = (item.exe_path or '').lower()

            # Определение категории:
            # 1. Apps: PID имеет окно ИЛИ процесс с таким именем имеет окно в системе ИЛИ это известное интерактивное приложение
            is_app = (
                (item.pid in windowed_pids) or
                (low_name in name_to_windowed and low_name not in WINDOWS_SYSTEM_PROCESS_NAMES) or
                (low_name in KNOWN_APP_FRIENDLY_NAMES and low_name not in WINDOWS_SYSTEM_PROCESS_NAMES)
            )

            if is_app:
                category = 'app'
            elif low_name in WINDOWS_SYSTEM_PROCESS_NAMES or ('c:\\windows\\system32' in exe_low and not name_to_windowed.get(low_name)):
                category = 'windows'
            else:
                category = 'background'

            groups_by_category[category].setdefault(item.name, []).append(item)

        # Формирование ProcessGroupItem для каждой категории
        def _build_groups(cat_key: str, cat_name: str) -> List[ProcessGroupItem]:
            result_groups: List[ProcessGroupItem] = []
            for bin_name, items in groups_by_category[cat_key].items():
                total_cpu = round(sum(it.cpu_percent for it in items), 1)
                total_mem = round(sum(it.memory_mb for it in items), 1)
                total_thr = sum(it.num_threads for it in items)
                
                # Поиск PID главного/оконного процесса
                main_pid = items[0].pid
                for it in items:
                    if it.pid in windowed_pids:
                        main_pid = it.pid
                        break

                # Сбор всех заголовков окон группы
                all_titles: List[str] = []
                for it in items:
                    if it.pid in titles_map:
                        all_titles.extend(titles_map[it.pid])

                friendly = self._get_friendly_name(bin_name, all_titles)
                has_win = len(all_titles) > 0 or any(it.pid in windowed_pids for it in items)

                # Сортировка подпроцессов: главный с окном или максимальный по RAM первым
                sorted_subprocs = sorted(items, key=lambda x: (1 if x.pid in windowed_pids else 0, x.memory_mb), reverse=True)

                result_groups.append(
                    ProcessGroupItem(
                        category=cat_key,
                        name=bin_name,
                        friendly_name=friendly,
                        instance_count=len(items),
                        total_cpu_percent=total_cpu,
                        total_memory_mb=total_mem,
                        total_threads=total_thr,
                        main_pid=main_pid,
                        has_visible_window=has_win,
                        window_titles=all_titles,
                        subprocesses=sorted_subprocs
                    )
                )

            # Сортировка групп: по суммарной памяти / CPU
            result_groups.sort(key=lambda g: (g.total_cpu_percent, g.total_memory_mb), reverse=True)
            return result_groups

        app_groups = _build_groups('app', 'Apps')
        bg_groups = _build_groups('background', 'Background processes')
        win_groups = _build_groups('windows', 'Windows processes')

        total_procs = len(raw_proc_items)
        total_mem_all = round(sum(it.memory_mb for it in raw_proc_items), 1)

        return CategorizedProcessReport(
            total_processes=total_procs,
            apps_count=len(app_groups),
            background_count=len(bg_groups),
            windows_count=len(win_groups),
            total_memory_used_mb=total_mem_all,
            apps=app_groups,
            background_processes=bg_groups,
            windows_processes=win_groups,
            timestamp=datetime.now().isoformat()
        )


__all__ = [
    'ProcessClassifier',
    'WINDOWS_SYSTEM_PROCESS_NAMES',
    'KNOWN_APP_FRIENDLY_NAMES',
]
