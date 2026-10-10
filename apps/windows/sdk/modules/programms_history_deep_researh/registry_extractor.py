# -*- coding: utf-8 -*-
# Updated: 2026-10-03 23:55:00
"""registry_extractor.py – извлечение списка установленных программ из реестра.

Функция `get_installed_programs` использует стандартный модуль `winreg` (или
библиотеку `winapps`, если она установлена) для чтения ключей реестра,
содержащих сведения об установленных приложениях.

Возвращаемый список состоит из словарей с полями:
- `name`
- `version`
- `install_location`
- `uninstall_string`
- `publisher`
- `registry_path`
"""

import sys
from typing import List, Dict

def _load_winreg_module():
    """Возвращает модуль `winreg` (или заглушку, если импорт невозможен)."""
    if sys.platform.startswith('win'):
        import winreg
        return winreg
    # На не‑Windows платформах возвращаем минимальную имитацию для тестов.
    class Dummy:
        HKEY_LOCAL_MACHINE = None
        HKEY_CURRENT_USER = None
    return Dummy

def _enumerate_subkeys(root, path, winreg):
    try:
        with winreg.OpenKey(root, path) as key:
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    yield subkey_name
                except OSError:
                    continue
    except OSError:
        return

def _read_program_info(root, subkey_path, winreg):
    info = {}
    try:
        with winreg.OpenKey(root, subkey_path) as subkey:
            for value_name in ["DisplayName", "DisplayVersion", "InstallLocation", "UninstallString", "Publisher"]:
                try:
                    val, _ = winreg.QueryValueEx(subkey, value_name)
                    info[value_name.lower()] = val
                except OSError:
                    continue
    except OSError:
        return None
    if "displayname" not in info:
        return None
    info["registry_path"] = subkey_path
    return info

def get_installed_programs() -> List[Dict]:
    """Собирает информацию об установленных программах из реестра.

    Returns:
        List[Dict]: список программ.
    """
    winreg = _load_winreg_module()
    programs: List[Dict] = []
    # Ключи реестра, где обычно хранятся данные об установленных приложениях.
    locations = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall"),
    ]
    for hive, path in locations:
        for subkey in _enumerate_subkeys(hive, path, winreg):
            full_path = f"{path}\\{subkey}"
            info = _read_program_info(hive, full_path, winreg)
            if info:
                programs.append(info)
    return programs
