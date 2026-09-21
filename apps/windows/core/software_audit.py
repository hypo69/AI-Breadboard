# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Software & Application Audit Engine
# =============================================================================
# Description:
#   Комплексный движок аудита установленного программного обеспечения Windows:
#   - Сбор сведений об установленных программах (HKLM, HKCU, Wow6432Node)
#   - Аудит истории и даты последнего запуска (UserAssist ROT13, Prefetch)
#   - Определение категории и назначения программ на русском языке
#   - Формирование сводного аналитического отчета
#
# Examples:
#   >>> from apps.windows.core.software_audit import SoftwareAuditEngine
#   >>> engine = SoftwareAuditEngine()
#   >>> report = engine.generate_audit_report()
#   >>> print(f"Всего программ: {report.total_apps}")
#
# File: software_audit.py
# Project: ai-breadboard
# Package: apps.windows.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль аудита установленного ПО Windows, истории запусков и анализа назначения приложений."""

from __future__ import annotations

import codecs
import csv
import os
import re
import struct
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import winreg
except ImportError:
    winreg = None  # type: ignore

from src.logger import logger
from .data_model import AppCategory, AppExecutionInfo, InstalledAppInfo, SoftwareAuditReport


# Эпоха FILETIME Windows (1 января 1601 г. UTC)
_WINDOWS_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)


def _filetime_to_datetime(filetime: int) -> Optional[datetime]:
    """Преобразовать Windows FILETIME (100-нс интервалы с 1601-01-01) в datetime.

    Args:
        filetime: 64-битное целое число FILETIME.

    Returns:
        Optional[datetime]: Объект datetime в локальном времени или None при невалидном значении.
    """
    if not filetime or filetime <= 0:
        return None
    try:
        dt_utc = _WINDOWS_EPOCH + timedelta(microseconds=filetime / 10)
        # Отсекаем нереалистичные даты
        if dt_utc.year < 1990 or dt_utc.year > 2100:
            return None
        return dt_utc.astimezone()
    except (OverflowError, OSError, ValueError):
        return None


def _decode_rot13(text: str) -> str:
    """Декодировать строку из формата ROT13 (используется в UserAssist).

    Args:
        text: Закодированная строка.

    Returns:
        str: Декодированная строка.
    """
    try:
        return codecs.decode(text, "rot_13")
    except Exception:
        return text


class SoftwareCategorizer:
    """Классификатор программного обеспечения и генератор описания назначения."""

    # Словарь известных приложений, их категорий и типовых описаний
    KNOWN_APPS: Dict[str, Tuple[AppCategory, str]] = {
        # Браузеры
        "chrome": (AppCategory.BROWSER, "Веб-браузер Google Chrome для навигации в сети Интернет."),
        "msedge": (AppCategory.BROWSER, "Веб-браузер Microsoft Edge на движке Chromium."),
        "firefox": (AppCategory.BROWSER, "Веб-браузер Mozilla Firefox с открытым исходным кодом."),
        "brave": (AppCategory.BROWSER, "Конфиденциальный веб-браузер Brave со встроенной защитой от трекеров."),
        "opera": (AppCategory.BROWSER, "Веб-браузер Opera с поддержкой встроенного VPN и боковой панели."),
        "yandex": (AppCategory.BROWSER, "Яндекс Браузер со встроенными голосовыми и поисковыми сервисами."),
        "vivaldi": (AppCategory.BROWSER, "Настраиваемый веб-браузер Vivaldi для опытных пользователей."),

        # Разработка
        "code": (AppCategory.DEVELOPMENT, "Редактор исходного кода Visual Studio Code от Microsoft."),
        "visual studio": (AppCategory.DEVELOPMENT, "Интегрированная среда разработки (IDE) Microsoft Visual Studio."),
        "pycharm": (AppCategory.DEVELOPMENT, "Интегрированная среда разработки Python (PyCharm) от JetBrains."),
        "intellij": (AppCategory.DEVELOPMENT, "Интегрированная среда разработки Java и Kotlin от JetBrains."),
        "webstorm": (AppCategory.DEVELOPMENT, "Среда разработки JavaScript и TypeScript от JetBrains."),
        "clion": (AppCategory.DEVELOPMENT, "Среда разработки C/C++ от JetBrains."),
        "python": (AppCategory.DEVELOPMENT, "Интерпретатор и стандартная среда языка программирования Python."),
        "git": (AppCategory.DEVELOPMENT, "Распределенная система управления версиями файлов Git."),
        "node": (AppCategory.DEVELOPMENT, "Среда выполнения серверного JavaScript Node.js."),
        "docker": (AppCategory.DEVELOPMENT, "Платформа контейнеризации и управления микросервисами Docker."),
        "dbeaver": (AppCategory.DEVELOPMENT, "Универсальный клиент и инструмент управления базами данных SQL."),
        "postman": (AppCategory.DEVELOPMENT, "Инструмент для тестирования, отладки и документирования REST API."),
        "notepad++": (AppCategory.DEVELOPMENT, "Текстовый редактор с подсветкой синтаксиса для разработчиков."),
        "sublime": (AppCategory.DEVELOPMENT, "Быстрый многофункциональный редактор кода Sublime Text."),
        "tortoisegit": (AppCategory.DEVELOPMENT, "Графический интерфейс Git для проводника Windows."),
        "android studio": (AppCategory.DEVELOPMENT, "Официальная среда разработки приложений для ОС Android."),

        # Связь и коммуникации
        "telegram": (AppCategory.COMMUNICATION, "Мессенджер Telegram для мгновенного обмена сообщениями и файлами."),
        "discord": (AppCategory.COMMUNICATION, "Платформа голосового, текстового и видеообщения Discord."),
        "slack": (AppCategory.COMMUNICATION, "Корпоративный мессенджер Slack для командного взаимодействия."),
        "zoom": (AppCategory.COMMUNICATION, "Клиент видеоконференций и онлайн-встреч Zoom."),
        "skype": (AppCategory.COMMUNICATION, "Программа голосовой связи и видеозвонков Skype."),
        "whatsapp": (AppCategory.COMMUNICATION, "Мессенджер WhatsApp Desktop для обмена сообщениями."),
        "thunderbird": (AppCategory.COMMUNICATION, "Почтовый клиент Mozilla Thunderbird для управления email."),
        "outlook": (AppCategory.COMMUNICATION, "Почтовый клиент и органайзер Microsoft Outlook."),

        # Офис и документы
        "word": (AppCategory.OFFICE, "Текстовый процессор Microsoft Word для создания документов."),
        "excel": (AppCategory.OFFICE, "Табличный процессор Microsoft Excel для анализа данных."),
        "powerpoint": (AppCategory.OFFICE, "Программа создания и показа презентаций Microsoft PowerPoint."),
        "libreoffice": (AppCategory.OFFICE, "Бесплатный офисный пакет LibreOffice с открытым исходным кодом."),
        "acrobat": (AppCategory.OFFICE, "Программа для просмотра и редактирования PDF-файлов Adobe Acrobat."),
        "foxit": (AppCategory.OFFICE, "Быстрый просмотрщик и редактор PDF-документов Foxit PDF Reader."),
        "notion": (AppCategory.OFFICE, "Рабочее пространство Notion для заметок, задач и баз знаний."),
        "obsidian": (AppCategory.OFFICE, "База знаний и приложение для связанных заметок Obsidian."),

        # Мультимедиа
        "vlc": (AppCategory.MULTIMEDIA, "Универсальный медиаплеер VLC для воспроизведения видео и аудио."),
        "spotify": (AppCategory.MULTIMEDIA, "Стриминговый сервис прослушивания музыки и подкастов Spotify."),
        "photoshop": (AppCategory.MULTIMEDIA, "Профессиональный растровый графический редактор Adobe Photoshop."),
        "illustrator": (AppCategory.MULTIMEDIA, "Профессиональный векторный редактор Adobe Illustrator."),
        "premiere": (AppCategory.MULTIMEDIA, "Программа нелинейного видеомонтажа Adobe Premiere Pro."),
        "obs studio": (AppCategory.MULTIMEDIA, "Программа для записи видео с экрана и проведения прямых трансляций."),
        "audacity": (AppCategory.MULTIMEDIA, "Многодорожечный аудиоредактор Audacity с открытым исходным кодом."),
        "blender": (AppCategory.MULTIMEDIA, "Комплекс для 3D-моделирования, анимации и рендеринга Blender."),
        "gimp": (AppCategory.MULTIMEDIA, "Растровый графический редактор GIMP с открытым исходным кодом."),
        "foobar2000": (AppCategory.MULTIMEDIA, "Легковесный аудиопроигрыватель foobar2000 с поддержкой Lossless."),

        # Утилиты и инструменты
        "7-zip": (AppCategory.UTILITIES, "Архиватор файлов 7-Zip с высокой степенью сжатия."),
        "winrar": (AppCategory.UTILITIES, "Архиватор WinRAR для работы с форматами RAR, ZIP и др."),
        "total commander": (AppCategory.UTILITIES, "Двухпанельный файловый менеджер Total Commander."),
        "everything": (AppCategory.UTILITIES, "Мгновенный поисковик файлов и папок Everything по именам."),
        "powertoys": (AppCategory.UTILITIES, "Набор системных утилит Microsoft PowerToys для Windows."),
        "rufus": (AppCategory.UTILITIES, "Утилита для создания загрузочных USB-накопителей Rufus."),
        "cpu-z": (AppCategory.UTILITIES, "Утилита для сбора детальной информации о процессоре и железе."),
        "gpu-z": (AppCategory.UTILITIES, "Утилита мониторинга видеокарты и видеочипа GPU-Z."),
        "putty": (AppCategory.UTILITIES, "SSH и Telnet клиент PuTTY для удаленного администрирования."),
        "anydesk": (AppCategory.UTILITIES, "Программа для удаленного доступа и управления рабочим столом."),
        "teamviewer": (AppCategory.UTILITIES, "Удаленное управление и поддержка компьютеров TeamViewer."),
        "process explorer": (AppCategory.UTILITIES, "Продвинутый диспетчер задач и анализатор процессов Windows."),
        "autoruns": (AppCategory.UTILITIES, "Утилита для анализа автоматически запускаемых программ и служб."),

        # Безопасность
        "kaspersky": (AppCategory.SECURITY, "Антивирусный комплекс защиты информации Kaspersky Security."),
        "eset": (AppCategory.SECURITY, "Антивирусная защита и файрвол ESET NOD32 / Internet Security."),
        "malwarebytes": (AppCategory.SECURITY, "Сканер и защита от вредоносного ПО Malwarebytes."),
        "keepass": (AppCategory.SECURITY, "Менеджер паролей KeePass с локальным шифрованием базы."),
        "bitwarden": (AppCategory.SECURITY, "Кроссплатформенный менеджер паролей Bitwarden."),
        "openvpn": (AppCategory.SECURITY, "Клиент защищенных виртуальных частных сетей OpenVPN."),
        "wireguard": (AppCategory.SECURITY, "Быстрый и современный VPN-клиент WireGuard."),

        # Системное ПО и драйверы
        "directx": (AppCategory.DRIVERS, "Набор API Microsoft DirectX для мультимедиа и 3D-графики."),
        "nvidia": (AppCategory.DRIVERS, "Графические драйверы и сопутствующее ПО NVIDIA."),
        "amd": (AppCategory.DRIVERS, "Драйверы и программное обеспечение для видеокарт и процессоров AMD."),
        "intel": (AppCategory.DRIVERS, "Драйверы и системные компоненты чипсета Intel."),
        "realtek": (AppCategory.DRIVERS, "Драйверы аудиокодека и сетевого адаптера Realtek."),
        "c++ redistributable": (AppCategory.SYSTEM, "Среда выполнения компонентов Microsoft Visual C++ Runtime."),
        ".net": (AppCategory.SYSTEM, "Компоненты платформы Microsoft .NET Runtime."),
    }

    # Ключевые слова для категоризации
    KEYWORD_CATEGORIES: Dict[str, Tuple[AppCategory, str]] = {
        "sdk": (AppCategory.DEVELOPMENT, "Пакет средств разработки программного обеспечения (SDK)."),
        "compiler": (AppCategory.DEVELOPMENT, "Компилятор или инструментарий разработки ПО."),
        "runtime": (AppCategory.SYSTEM, "Системная среда выполнения для прикладных программ."),
        "redistributable": (AppCategory.SYSTEM, "Распространяемый системный пакет компонентов."),
        "driver": (AppCategory.DRIVERS, "Драйвер аппаратного устройства Windows."),
        "antivirus": (AppCategory.SECURITY, "Антивирусная защита и модуль безопасности."),
        "vpn": (AppCategory.SECURITY, "Клиент защищенного сетевого подключения VPN."),
        "messenger": (AppCategory.COMMUNICATION, "Приложение для обмена сообщениями и коммуникаций."),
        "chat": (AppCategory.COMMUNICATION, "Программа для чата и сетевого общения."),
        "player": (AppCategory.MULTIMEDIA, "Медиаплеер для воспроизведения мультимедиа файлов."),
        "codec": (AppCategory.MULTIMEDIA, "Мультимедиа кодек для кодирования/декодирования медиаданных."),
        "browser": (AppCategory.BROWSER, "Веб-браузер для доступа к интернет-ресурсам."),
        "benchmark": (AppCategory.UTILITIES, "Утилита тестирования производительности оборудования."),
        "backup": (AppCategory.UTILITIES, "Утилита резервного копирования и восстановления данных."),
        "archiver": (AppCategory.UTILITIES, "Архиватор для упаковки и распаковки файлов."),
        "game": (AppCategory.GAMES, "Компьютерная игра или игровой лаунчер."),
    }

    @classmethod
    def classify(
        cls,
        name: str,
        display_name: str,
        publisher: str = "",
        comments: str = "",
        install_location: str = "",
    ) -> Tuple[AppCategory, str]:
        """Определить категорию и описание назначения программы по ее метаданным.

        Args:
            name: Имя ключа реестра или исполняемого файла.
            display_name: Отображаемое название программы.
            publisher: Издатель программы.
            comments: Описание или комментарий из реестра.
            install_location: Путь установки.

        Returns:
            Tuple[AppCategory, str]: (Категория ПО, Назначение программы на русском языке).
        """
        search_target = f"{name} {display_name} {publisher} {comments} {install_location}".lower()

        # 1. Поиск точных и подстрочных совпадений в базе известных программ
        for known_key, (category, desc) in cls.KNOWN_APPS.items():
            if known_key in search_target:
                if comments and len(comments.strip()) > 5:
                    return category, f"{desc} ({comments.strip()})"
                return category, desc

        # 2. Поиск по ключевым словам
        for kw, (category, desc) in cls.KEYWORD_CATEGORIES.items():
            if kw in search_target:
                full_desc = f"{desc} {display_name or name}".strip()
                return category, full_desc

        # 3. Эвристика по издателю
        pub_lower = publisher.lower()
        if "microsoft" in pub_lower:
            if "visual c++" in search_target or "framework" in search_target or "redistributable" in search_target:
                return AppCategory.SYSTEM, "Системный компонент и среда выполнения Microsoft Windows."
            return AppCategory.SYSTEM, f"Приложение или служба от Microsoft ({display_name or name})."

        if "nvidia" in pub_lower or "amd" in pub_lower or "intel" in pub_lower or "realtek" in pub_lower:
            return AppCategory.DRIVERS, f"Драйвер или служебная утилита оборудования от {publisher}."

        if "jetbrains" in pub_lower or "github" in pub_lower or "python" in pub_lower:
            return AppCategory.DEVELOPMENT, f"Инструмент для разработки программного обеспечения ({display_name or name})."

        # 4. Если есть встроенные комментарии из реестра
        if comments and len(comments.strip()) > 3:
            return AppCategory.OTHER, f"Прикладное ПО: {comments.strip()}"

        disp = display_name or name or "Неизвестное приложение"
        return AppCategory.OTHER, f"Прикладное программное обеспечение ({disp})."


class UserAssistParser:
    """Парсер артефактов запуска приложений из реестра UserAssist (ROT13)."""

    USERASSIST_PATH = r"Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist"

    @classmethod
    def get_execution_history(cls) -> Dict[str, AppExecutionInfo]:
        """Собрать историю запусков программ из веток UserAssist текущего пользователя.

        Returns:
            Dict[str, AppExecutionInfo]: Словарь {имя_или_путь_exe: AppExecutionInfo}.
        """
        history: Dict[str, AppExecutionInfo] = {}
        if not winreg:
            return history

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.USERASSIST_PATH, 0, winreg.KEY_READ) as ua_root:
                num_guids, _, _ = winreg.QueryInfoKey(ua_root)
                for i in range(num_guids):
                    guid_name = winreg.EnumKey(ua_root, i)
                    count_subpath = f"{guid_name}\\Count"
                    try:
                        with winreg.OpenKey(ua_root, count_subpath, 0, winreg.KEY_READ) as count_key:
                            num_values, _, _ = winreg.QueryInfoKey(count_key)
                            for j in range(num_values):
                                raw_name, raw_data, val_type = winreg.EnumValue(count_key, j)
                                decoded_path = _decode_rot13(raw_name)
                                exec_info = cls._parse_userassist_entry(raw_data, decoded_path)
                                if exec_info:
                                    # Нормализуем ключ (базовое имя exe и полный путь)
                                    norm_key = Path(decoded_path).name.lower()
                                    if norm_key:
                                        # Если уже есть запись, берем с наибольшим временем или счетчиком
                                        if norm_key not in history or (
                                            exec_info.last_run_time
                                            and (
                                                not history[norm_key].last_run_time
                                                or exec_info.last_run_time > history[norm_key].last_run_time
                                            )
                                        ):
                                            history[norm_key] = exec_info
                                    # Также сохраняем по полному нормализованному пути
                                    history[decoded_path.lower()] = exec_info
                    except OSError:
                        continue
        except OSError as e:
            logger.debug(f"Ошибка чтения UserAssist реестра: {e}")

        return history

    @staticmethod
    def _parse_userassist_entry(raw_bytes: bytes, raw_path: str) -> Optional[AppExecutionInfo]:
        """Распаковать структуру данных UserAssist (Win7/8/10/11: 72 байта или 16 байт)."""
        if not isinstance(raw_bytes, (bytes, bytearray)):
            return None

        size = len(raw_bytes)
        try:
            # Win7 - Win11 72-байтовая структура
            if size >= 72:
                # offset 4: run_count (DWORD), offset 8: focus_count (DWORD), offset 12: focus_time_ms (DWORD)
                # offset 60: last_run_filetime (QWORD 8 bytes)
                session_id, run_count, focus_count, focus_time_ms = struct.unpack_from("<IIII", raw_bytes, 0)
                filetime = struct.unpack_from("<Q", raw_bytes, 60)[0]
                last_run = _filetime_to_datetime(filetime)
                focus_sec = max(0, focus_time_ms // 1000)
                return AppExecutionInfo(
                    last_run_time=last_run,
                    run_count=max(0, run_count),
                    focus_time_seconds=focus_sec,
                    source_artifact="UserAssist",
                    raw_path=raw_path,
                )
            # Устаревшая 16-байтовая структура (XP/2003/Win2k)
            elif size >= 16:
                session_id, run_count = struct.unpack_from("<II", raw_bytes, 0)
                filetime = struct.unpack_from("<Q", raw_bytes, 8)[0]
                last_run = _filetime_to_datetime(filetime)
                # В XP счетчик смещен на 5
                actual_count = max(0, run_count - 5) if run_count >= 5 else run_count
                return AppExecutionInfo(
                    last_run_time=last_run,
                    run_count=actual_count,
                    focus_time_seconds=0,
                    source_artifact="UserAssist",
                    raw_path=raw_path,
                )
        except struct.error:
            return None
        return None


class PrefetchScanner:
    """Сканер артефактов Prefetch для получения дат последних запусков."""

    PREFETCH_DIR = r"C:\Windows\Prefetch"

    @classmethod
    def get_prefetch_history(cls) -> Dict[str, datetime]:
        """Получить словарь {имя_exe_без_хэша: дата_последней_модификации_pf}.

        Returns:
            Dict[str, datetime]: Словарь последних запусков.
        """
        results: Dict[str, datetime] = {}
        prefetch_path = Path(cls.PREFETCH_DIR)
        if not prefetch_path.exists() or not os.access(str(prefetch_path), os.R_OK):
            return results

        try:
            for entry in prefetch_path.glob("*.pf"):
                try:
                    # Имя prefetch имеет вид: PROGRAM.EXE-12AB34CD.pf
                    file_name = entry.name
                    exe_part = re.split(r"-[0-9A-Fa-f]{8}\.pf$", file_name, flags=re.IGNORECASE)[0].lower()
                    mtime = entry.stat().st_mtime
                    dt = datetime.fromtimestamp(mtime).astimezone()
                    if exe_part not in results or dt > results[exe_part]:
                        results[exe_part] = dt
                except (OSError, ValueError):
                    continue
        except Exception as e:
            logger.debug(f"Ошибка доступа к папке Prefetch: {e}")

        return results


from apps.windows.telemetry.models import HardwareSensor, TelemetryProvider
from apps.windows.core.data_model import AppCategory, AppExecutionInfo, InstalledAppInfo, SoftwareAuditReport

class SoftwareAuditEngine(TelemetryProvider):
    """Главный движок аудита установленного программного обеспечения Windows.

    Это гибридный движок (Hybrid Audit Engine), который собирает данные из:
    - Реестра Windows (ветки Uninstall для инвентаризации).
    - Артефактов ОС (UserAssist, Prefetch для анализа истории запусков).
    """

    UNINSTALL_PATHS = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "x64"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall", "x86"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "user"),
    ] if winreg else []

    def __init__(self) -> None:
        """Инициализировать движок аудита ПО."""
        self._categorizer = SoftwareCategorizer()
        self._last_report: Optional[SoftwareAuditReport] = None

    def get_sensors(self) -> List[HardwareSensor]:
        """Возвращает текущие показатели аудита как сенсоры."""
        sensors: List[HardwareSensor] = []
        if self._last_report:
            sensors.append(HardwareSensor(
                sensor_id="software_total_apps",
                name="Количество установленных приложений",
                category="software",
                value=float(self._last_report.total_apps),
                unit="count"
            ))
            sensors.append(HardwareSensor(
                sensor_id="software_active_apps",
                name="Активных приложений",
                category="software",
                value=float(self._last_report.active_apps_count),
                unit="count"
            ))
        return sensors


    def get_installed_applications(self) -> List[InstalledAppInfo]:
        """Собрать полный список установленных программ с историей запусков и назначением.

        Returns:
            List[InstalledAppInfo]: Список установленных приложений.
        """
        if not winreg:
            logger.warning("Модуль winreg недоступен на данной платформе (не Windows).")
            return self._get_fallback_mock_data()

        execution_history = UserAssistParser.get_execution_history()
        prefetch_history = PrefetchScanner.get_prefetch_history()
        installed_dict: Dict[str, InstalledAppInfo] = {}

        for root_hive, subkey_path, default_arch in self.UNINSTALL_PATHS:
            try:
                with winreg.OpenKey(root_hive, subkey_path, 0, winreg.KEY_READ) as key:
                    num_subkeys, _, _ = winreg.QueryInfoKey(key)
                    for i in range(num_subkeys):
                        app_guid_or_name = winreg.EnumKey(key, i)
                        try:
                            with winreg.OpenKey(key, app_guid_or_name, 0, winreg.KEY_READ) as app_key:
                                app_info = self._extract_app_info(
                                    app_key=app_key,
                                    app_id=app_guid_or_name,
                                    reg_hive_name="HKLM" if root_hive == winreg.HKEY_LOCAL_MACHINE else "HKCU",
                                    default_arch=default_arch,
                                    execution_history=execution_history,
                                    prefetch_history=prefetch_history,
                                )
                                if app_info and app_info.display_name:
                                    # Дедупликация по display_name + version
                                    dedup_key = f"{app_info.display_name}::{app_info.version}".lower()
                                    if dedup_key not in installed_dict:
                                        installed_dict[dedup_key] = app_info
                                    else:
                                        # Объединяем историю запусков при наличии более полной
                                        existing = installed_dict[dedup_key]
                                        if not existing.execution_info and app_info.execution_info:
                                            existing.execution_info = app_info.execution_info
                        except OSError:
                            continue
            except OSError as e:
                logger.debug(f"Не удалось открыть ветку {subkey_path}: {e}")

        app_list = list(installed_dict.values())
        # Сортируем: сначала те, у которых есть дата запуска (по убыванию даты), затем по имени
        app_list.sort(
            key=lambda a: (
                a.execution_info.last_run_time if (a.execution_info and a.execution_info.last_run_time) else datetime.min.replace(tzinfo=timezone.utc),
                a.display_name.lower(),
            ),
            reverse=True,
        )
        return app_list

    def _extract_app_info(
        self,
        app_key: Any,
        app_id: str,
        reg_hive_name: str,
        default_arch: str,
        execution_history: Dict[str, AppExecutionInfo],
        prefetch_history: Dict[str, datetime],
    ) -> Optional[InstalledAppInfo]:
        """Извлечь параметры приложения из ключа реестра Uninstall.

        Args:
            app_key: Дескриптор открытого ключа реестра.
            app_id: Имя подраздела (GUID или название).
            reg_hive_name: HKLM или HKCU.
            default_arch: x64, x86 или user.
            execution_history: Словарь истории запусков UserAssist.
            prefetch_history: Словарь истории запусков Prefetch.

        Returns:
            Optional[InstalledAppInfo]: Объект приложения или None.
        """
        def _get_val(name: str) -> Any:
            try:
                val, _ = winreg.QueryValueEx(app_key, name)
                return val
            except OSError:
                return None

        display_name = _get_val("DisplayName")
        if not display_name or not str(display_name).strip():
            return None

        display_name = str(display_name).strip()
        version = str(_get_val("DisplayVersion") or "").strip()
        publisher = str(_get_val("Publisher") or "").strip()
        raw_install_date = _get_val("InstallDate")
        install_location = str(_get_val("InstallLocation") or "").strip()
        uninstall_string = str(_get_val("UninstallString") or "").strip()
        estimated_size = _get_val("EstimatedSize")  # размер в КБ в реестре
        comments = str(_get_val("Comments") or "").strip()
        system_component = bool(_get_val("SystemComponent") or 0)
        parent_key_name = _get_val("ParentKeyName")

        # Если это скрытый дочерний компонент обновления/патча
        if parent_key_name:
            system_component = True

        # Форматирование даты установки (YYYYMMDD -> YYYY-MM-DD)
        formatted_install_date = self._format_install_date(raw_install_date)

        # Вычисление размера
        size_bytes = (int(estimated_size) * 1024) if isinstance(estimated_size, int) and estimated_size > 0 else 0

        # Определение категории и назначения
        category, purpose_desc = self._categorizer.classify(
            name=app_id,
            display_name=display_name,
            publisher=publisher,
            comments=comments,
            install_location=install_location,
        )

        # Поиск истории запусков программы
        exec_info = self._find_execution_info(
            display_name=display_name,
            app_id=app_id,
            install_location=install_location,
            uninstall_string=uninstall_string,
            execution_history=execution_history,
            prefetch_history=prefetch_history,
        )

        return InstalledAppInfo(
            name=app_id,
            display_name=display_name,
            version=version,
            publisher=publisher,
            install_date=formatted_install_date,
            install_location=install_location,
            uninstall_string=uninstall_string,
            size_bytes=size_bytes,
            architecture=default_arch,
            registry_key=f"{reg_hive_name}\\{app_id}",
            is_system_component=system_component,
            category=category,
            purpose_description=purpose_desc,
            execution_info=exec_info,
        )

    @staticmethod
    def _format_install_date(raw_date: Any) -> Optional[str]:
        """Преобразовать строку даты установки реестра в стандартный формат ISO (YYYY-MM-DD)."""
        if not raw_date:
            return None
        s = str(raw_date).strip()
        # Формат YYYYMMDD
        if len(s) == 8 and s.isdigit():
            return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
        return s

    @staticmethod
    def _find_execution_info(
        display_name: str,
        app_id: str,
        install_location: str,
        uninstall_string: str,
        execution_history: Dict[str, AppExecutionInfo],
        prefetch_history: Dict[str, datetime],
    ) -> Optional[AppExecutionInfo]:
        """Найти связанную историю запусков по исполняемым файлам и путям приложения."""
        # Кандидаты для поиска
        candidates: List[str] = []

        # 1. Извлекаем exe из UninstallString
        if uninstall_string:
            m = re.search(r'["\']?([^"\']+\.exe)["\']?', uninstall_string, re.IGNORECASE)
            if m:
                exe_name = Path(m.group(1)).name.lower()
                candidates.append(exe_name)

        # 2. Имя из InstallLocation
        if install_location and os.path.exists(install_location):
            try:
                for root, _, files in os.walk(install_location):
                    for f in files:
                        if f.lower().endswith(".exe"):
                            candidates.append(f.lower())
                    break  # сканируем только верхний уровень папки
            except OSError:
                pass

        # 3. Нормализованные имена из DisplayName и app_id
        clean_disp = re.sub(r"[^a-zA-Z0-9]", "", display_name).lower()
        candidates.append(f"{clean_disp}.exe")
        candidates.append(f"{display_name.split()[0].lower()}.exe" if display_name else "")

        # Поиск по UserAssist
        for cand in candidates:
            if not cand:
                continue
            if cand in execution_history:
                return execution_history[cand]

        # Поиск по Prefetch
        for cand in candidates:
            if not cand:
                continue
            if cand in prefetch_history:
                return AppExecutionInfo(
                    last_run_time=prefetch_history[cand],
                    run_count=1,
                    focus_time_seconds=0,
                    source_artifact="Prefetch",
                    raw_path=cand,
                )

        return None

    def generate_audit_report(self) -> SoftwareAuditReport:
        """Сформировать аналитический отчет по установленному программному обеспечению.

        Returns:
            SoftwareAuditReport: Сводный аналитический отчет аудита.
        """
        apps = self.get_installed_applications()
        total_apps = len(apps)
        
        categories_breakdown: Dict[str, int] = {}
        active_apps: List[InstalledAppInfo] = []
        top_launched: List[InstalledAppInfo] = []
        never_launched_or_dormant: List[InstalledAppInfo] = []

        # Порог неактивности: 90 дней
        dormant_threshold = datetime.now(timezone.utc) - timedelta(days=90)

        for app in apps:
            cat_name = app.category.value if isinstance(app.category, AppCategory) else str(app.category)
            categories_breakdown[cat_name] = categories_breakdown.get(cat_name, 0) + 1

            if app.was_launched and app.execution_info and app.execution_info.last_run_time:
                active_apps.append(app)
                # Проверяем не является ли программа "заброшенной"
                run_dt = app.execution_info.last_run_time
                if run_dt.tzinfo is None:
                    run_dt = run_dt.replace(tzinfo=timezone.utc)
                if run_dt < dormant_threshold:
                    never_launched_or_dormant.append(app)
            else:
                never_launched_or_dormant.append(app)

        # Сортируем топ запускаемых по количеству запусков
        top_launched = sorted(
            [a for a in active_apps if a.execution_info and a.execution_info.run_count > 0],
            key=lambda a: a.execution_info.run_count if a.execution_info else 0,
            reverse=True,
        )

        # Недавно запускавшиеся (сортировка по времени)
        recently_launched = sorted(
            active_apps,
            key=lambda a: (
                a.execution_info.last_run_time if (a.execution_info and a.execution_info.last_run_time) else datetime.min.replace(tzinfo=timezone.utc)
            ),
            reverse=True,
        )

        report = SoftwareAuditReport(
            timestamp=datetime.now(),
            total_apps=total_apps,
            active_apps_count=len(active_apps),
            unused_apps_count=len(never_launched_or_dormant),
            categories_breakdown=categories_breakdown,
            recently_launched=recently_launched[:15],
            top_launched=top_launched[:15],
            never_launched_or_dormant=never_launched_or_dormant,
            apps=apps,
        )
        self._last_report = report
        self._save_to_csv(report)
        return report


    def _save_to_csv(self, report: SoftwareAuditReport):
        """Сохранить отчет в CSV файл в %APPDATA%/AI-Assistant."""
        appdata = os.environ.get("APPDATA")
        if not appdata:
            logger.warning("Переменная среды APPDATA не найдена, логирование отменено.")
            return

        log_dir = Path(appdata) / "AI-Assistant"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "software_audit.csv"
        
        try:
            with open(log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "Version", "Publisher", "InstallDate"])
                for app in report.apps:
                    writer.writerow([app.display_name, app.version, app.publisher, app.install_date])
            logger.info(f"Отчет аудита автоматически сохранен в: {log_file}")
        except Exception as e:
            logger.error(f"Не удалось сохранить отчет аудита в CSV: {e}")


    def _get_fallback_mock_data(self) -> List[InstalledAppInfo]:
        """Генерация реалистичных демонстрационных данных для не-Windows окружения или тестов."""
        now = datetime.now()
        return [
            InstalledAppInfo(
                name="Google Chrome",
                display_name="Google Chrome",
                version="125.0.6422.142",
                publisher="Google LLC",
                install_date=(now - timedelta(days=120)).strftime("%Y-%m-%d"),
                install_location=r"C:\Program Files\Google\Chrome\Application",
                uninstall_string=r"C:\Program Files\Google\Chrome\Application\installer.exe --uninstall",
                size_bytes=380 * 1024 * 1024,
                architecture="x64",
                category=AppCategory.BROWSER,
                purpose_description="Веб-браузер Google Chrome для навигации в сети Интернет.",
                execution_info=AppExecutionInfo(
                    last_run_time=now - timedelta(minutes=15),
                    run_count=342,
                    focus_time_seconds=18400,
                    source_artifact="UserAssist",
                    raw_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                ),
            ),
            InstalledAppInfo(
                name="Visual Studio Code",
                display_name="Visual Studio Code",
                version="1.89.1",
                publisher="Microsoft Corporation",
                install_date=(now - timedelta(days=95)).strftime("%Y-%m-%d"),
                install_location=r"C:\Users\User\AppData\Local\Programs\Microsoft VS Code",
                uninstall_string=r"C:\Users\User\AppData\Local\Programs\Microsoft VS Code\unins000.exe",
                size_bytes=420 * 1024 * 1024,
                architecture="x64",
                category=AppCategory.DEVELOPMENT,
                purpose_description="Редактор исходного кода Visual Studio Code от Microsoft.",
                execution_info=AppExecutionInfo(
                    last_run_time=now - timedelta(minutes=5),
                    run_count=520,
                    focus_time_seconds=45000,
                    source_artifact="UserAssist",
                    raw_path=r"C:\Users\User\AppData\Local\Programs\Microsoft VS Code\Code.exe",
                ),
            ),
            InstalledAppInfo(
                name="7-Zip",
                display_name="7-Zip 23.01 (x64)",
                version="23.01",
                publisher="Igor Pavlov",
                install_date=(now - timedelta(days=200)).strftime("%Y-%m-%d"),
                install_location=r"C:\Program Files\7-Zip",
                uninstall_string=r"C:\Program Files\7-Zip\Uninstall.exe",
                size_bytes=5 * 1024 * 1024,
                architecture="x64",
                category=AppCategory.UTILITIES,
                purpose_description="Архиватор файлов 7-Zip с высокой степенью сжатия.",
                execution_info=AppExecutionInfo(
                    last_run_time=now - timedelta(days=2),
                    run_count=45,
                    focus_time_seconds=320,
                    source_artifact="UserAssist",
                    raw_path=r"C:\Program Files\7-Zip\7zFM.exe",
                ),
            ),
            InstalledAppInfo(
                name="Telegram Desktop",
                display_name="Telegram Desktop",
                version="4.16.8",
                publisher="Telegram FZ-LLC",
                install_date=(now - timedelta(days=80)).strftime("%Y-%m-%d"),
                install_location=r"C:\Users\User\AppData\Roaming\Telegram Desktop",
                uninstall_string=r"C:\Users\User\AppData\Roaming\Telegram Desktop\unins000.exe",
                size_bytes=110 * 1024 * 1024,
                architecture="x64",
                category=AppCategory.COMMUNICATION,
                purpose_description="Мессенджер Telegram для мгновенного обмена сообщениями и файлами.",
                execution_info=AppExecutionInfo(
                    last_run_time=now - timedelta(minutes=30),
                    run_count=210,
                    focus_time_seconds=12400,
                    source_artifact="UserAssist",
                    raw_path=r"C:\Users\User\AppData\Roaming\Telegram Desktop\Telegram.exe",
                ),
            ),
            InstalledAppInfo(
                name="Legacy Tool Setup",
                display_name="Legacy Tool Setup 2020",
                version="1.0.0",
                publisher="Old Software Corp",
                install_date=(now - timedelta(days=500)).strftime("%Y-%m-%d"),
                install_location=r"C:\Program Files (x86)\LegacyTool",
                uninstall_string=r"C:\Program Files (x86)\LegacyTool\uninstall.exe",
                size_bytes=85 * 1024 * 1024,
                architecture="x86",
                category=AppCategory.OTHER,
                purpose_description="Прикладное программное обеспечение (Legacy Tool Setup 2020).",
                execution_info=None,
            ),
        ]
