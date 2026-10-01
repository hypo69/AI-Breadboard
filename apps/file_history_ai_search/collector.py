# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps File_History_Ai_Search - Collector
# =============================================================================
# Description:
#   Коллектор телеметрии и истории файлов Windows OS.
#
# Usage Examples:
#   Python API:
#     from apps.file_history_ai_search.collector import WindowsFileHistoryCollector
#
#     service = WindowsFileHistoryCollector()
#
# File: collector.py
# Project: ai-breadboard
# Package: apps.file_history_ai_search
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

"""Коллектор телеметрии и истории файлов Windows OS."""

import hashlib
import json
import os
import re
import sqlite3
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from logger import logger
from apps.file_history_ai_search.models import FileHistoryItem


class WindowsFileHistoryCollector:
    """Сборщик элементов истории файлов из операционной системы Windows.

    Поддерживает варианты источников:
    - Конфигурации и каталоги Windows File History (Config1.xml, Catalog1.xml).
    - Ярлыки последних открытых файлов (%APPDATA%\\Microsoft\\Windows\\Recent).
    - Базу данных Windows Activity History (ActivitiesCache.db).
    - Сканирование недавно измененных файлов в файловой системе.
    """

    def __init__(self, target_directories: Optional[List[str]] = None) -> None:
        """Инициализация коллектора истории файлов.

        Args:
            target_directories (Optional[List[str]]): Дополнительные пути для сканирования ФС.
        """
        self.user_profile = Path(os.environ.get("USERPROFILE", "C:\\Users\\Default"))
        self.appdata = Path(os.environ.get("APPDATA", self.user_profile / "AppData" / "Roaming"))
        self.localappdata = Path(os.environ.get("LOCALAPPDATA", self.user_profile / "AppData" / "Local"))

        default_dirs = [
            str(self.user_profile / "Documents"),
            str(self.user_profile / "Desktop"),
            str(self.user_profile / "Downloads"),
        ]
        self.target_directories = target_directories or default_dirs

    def generate_item_id(self, source_type: str, file_path: str, timestamp: str) -> str:
        """Генерация уникального ID для элемента истории.

        Args:
            source_type (str): Тип источника.
            file_path (str): Путь к файлу.
            timestamp (str): Метка времени.

        Returns:
            str: Хэш идентификатор записи.
        """
        raw = f"{source_type}:{file_path.lower()}:{timestamp}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def _read_file_preview(self, file_path: Path, max_bytes: int = 2048) -> str:
        """Безопасное чтение превью содержимого файла.

        Args:
            file_path (Path): Путь к файлу.
            max_bytes (int): Максимальное количество байт.

        Returns:
            str: Первые строки файла или описание.
        """
        if not file_path.exists() or not file_path.is_file():
            return ""

        text_extensions = {".txt", ".md", ".py", ".json", ".csv", ".log", ".xml", ".html", ".css", ".js", ".ps1"}
        if file_path.suffix.lower() not in text_extensions:
            return f"Бинарный файл формата {file_path.suffix}"

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(max_bytes)
                return content.strip()[:1000]
        except Exception as e:
            logger.debug(f"Не удалось прочитать превью для {file_path}: {e}")
            return ""

    def collect_file_history_xml(self) -> List[FileHistoryItem]:
        """Сбор данных из конфигурации Windows File History (Config1.xml / Catalog1.xml).

        Returns:
            List[FileHistoryItem]: Элементы из истории файлов Windows.
        """
        items: List[FileHistoryItem] = []
        fh_config_dir = self.localappdata / "Microsoft" / "Windows" / "FileHistory" / "Configuration"
        if not fh_config_dir.exists():
            return items

        for xml_name in ["Config1.xml", "Config2.xml", "Catalog1.xml"]:
            xml_path = fh_config_dir / xml_name
            if not xml_path.exists():
                continue

            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()

                # Извлечение защищенных папок и записей файлов
                for elem in root.iter():
                    path_val = elem.text.strip() if elem.text else ""
                    if path_val and (":" in path_val or "\\" in path_val) and len(path_val) > 3:
                        p = Path(path_val)
                        if p.exists():
                            mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()
                            item_id = self.generate_item_id("file_history_xml", str(p), mtime)
                            items.append(
                                FileHistoryItem(
                                    item_id=item_id,
                                    file_path=str(p),
                                    file_name=p.name,
                                    source_type="file_history_xml",
                                    event_type="backed_up",
                                    timestamp=mtime,
                                    content_preview=self._read_file_preview(p),
                                    file_size=p.stat().st_size if p.is_file() else 0,
                                    metadata={"config_source": xml_name},
                                )
                            )
            except Exception as e:
                logger.error(f"[FileHistoryCollector] Ошибка парсинга {xml_path}: {e}")

        return items

    def collect_recent_shortcuts(self) -> List[FileHistoryItem]:
        """Сбор информации о недавно открытых файлах из %APPDATA%\\Microsoft\\Windows\\Recent.

        Returns:
            List[FileHistoryItem]: Список элементов из ярлыков Recent.
        """
        items: List[FileHistoryItem] = []
        recent_dir = self.appdata / "Microsoft" / "Windows" / "Recent"
        if not recent_dir.exists():
            return items

        try:
            for lnk_file in recent_dir.glob("*.lnk"):
                try:
                    stat = lnk_file.stat()
                    mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                    # Парсинг оригинального имени файла из имени ярлыка
                    target_name = lnk_file.stem
                    
                    # Пытаемся извлечь сырой путь из бинарного ярлыка если возможно
                    target_path_str = str(lnk_file)
                    try:
                        raw_data = lnk_file.read_bytes()
                        # Ищем паттерны виндовых путей в ярлыке C:\...
                        matches = re.findall(br'[A-Za-z]:\\[\w\s\.\-\\\(\)]+', raw_data)
                        if matches:
                            extracted = matches[0].decode('utf-8', errors='ignore').rstrip('\x00')
                            if os.path.exists(extracted):
                                target_path_str = extracted
                    except Exception:
                        pass

                    p = Path(target_path_str)
                    file_size = p.stat().st_size if p.exists() and p.is_file() else 0
                    item_id = self.generate_item_id("recent_lnk", str(p), mtime)

                    items.append(
                        FileHistoryItem(
                            item_id=item_id,
                            file_path=str(p),
                            file_name=p.name if p.exists() else target_name,
                            source_type="recent_lnk",
                            event_type="opened",
                            timestamp=mtime,
                            content_preview=self._read_file_preview(p) if p.exists() else f"Недавно открытый ярлык: {target_name}",
                            file_size=file_size,
                            metadata={"shortcut_file": lnk_file.name},
                        )
                    )
                except Exception as e:
                    logger.debug(f"Ошибка при обработке ярлыка {lnk_file}: {e}")
        except Exception as e:
            logger.error(f"[FileHistoryCollector] Ошибка при сборе Recent LNK: {e}")

        return items

    def collect_activities_db(self) -> List[FileHistoryItem]:
        """Сбор активности с файлами из базы данных Windows Activity History (ActivitiesCache.db).

        Returns:
            List[FileHistoryItem]: Список элементов из базы данных активности Windows.
        """
        items: List[FileHistoryItem] = []
        cdp_dir = self.localappdata / "ConnectedDevicesPlatform"
        if not cdp_dir.exists():
            return items

        db_files = list(cdp_dir.rglob("ActivitiesCache.db"))
        for db_file in db_files:
            try:
                conn = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Проверяем наличие таблицы Activity
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Activity'")
                if not cursor.fetchone():
                    conn.close()
                    continue

                query = "SELECT AppId, Payload, LastModifiedTime FROM Activity ORDER BY LastModifiedTime DESC LIMIT 100"
                for row in cursor.execute(query):
                    payload_raw = row["Payload"]
                    app_id = row["AppId"]
                    last_mod = row["LastModifiedTime"]

                    timestamp = datetime.fromtimestamp(last_mod, tz=timezone.utc).isoformat() if isinstance(last_mod, (int, float)) and last_mod > 0 else datetime.now(timezone.utc).isoformat()

                    file_path = ""
                    display_text = ""
                    if payload_raw:
                        try:
                            payload = json.loads(payload_raw) if isinstance(payload_raw, str) else json.loads(payload_raw.decode("utf-8", errors="ignore"))
                            file_path = payload.get("appDisplayText", "") or payload.get("displayText", "") or payload.get("userTimezone", "")
                            display_text = payload.get("description", "") or payload.get("displayText", "")
                        except Exception:
                            pass

                    if file_path:
                        p = Path(file_path)
                        item_id = self.generate_item_id("activity_db", file_path, timestamp)
                        items.append(
                            FileHistoryItem(
                                item_id=item_id,
                                file_path=file_path,
                                file_name=p.name if "\\" in file_path or "/" in file_path else file_path,
                                source_type="activity_db",
                                event_type="opened",
                                timestamp=timestamp,
                                content_preview=display_text or f"Активность приложения {app_id}",
                                file_size=p.stat().st_size if p.exists() and p.is_file() else 0,
                                metadata={"app_id": str(app_id)},
                            )
                        )

                conn.close()
            except Exception as e:
                logger.debug(f"[FileHistoryCollector] Не удалось запросить {db_file}: {e}")

        return items

    def collect_filesystem_recent(self, max_files: int = 200) -> List[FileHistoryItem]:
        """Сканирование недавно измененных файлов в целевых директориях.

        Args:
            max_files (int): Максимальное количество файлов для включения.

        Returns:
            List[FileHistoryItem]: Найденные элементы файловой системы.
        """
        items: List[FileHistoryItem] = []
        found_files: List[Path] = []

        for target_dir in self.target_directories:
            td_path = Path(target_dir)
            if not td_path.exists():
                continue

            try:
                for root, _, files in os.walk(td_path):
                    for file in files:
                        p = Path(root) / file
                        if not p.is_file():
                            continue
                        found_files.append(p)
                        if len(found_files) >= max_files * 2:
                            break
                    if len(found_files) >= max_files * 2:
                        break
            except Exception as e:
                logger.error(f"[FileHistoryCollector] Ошибка сканирования {target_dir}: {e}")

        # Сортируем по дате изменения (свежие первые)
        found_files.sort(key=lambda x: x.stat().st_mtime if x.exists() else 0, reverse=True)

        for p in found_files[:max_files]:
            try:
                stat = p.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                item_id = self.generate_item_id("fs_scan", str(p), mtime)

                items.append(
                    FileHistoryItem(
                        item_id=item_id,
                        file_path=str(p),
                        file_name=p.name,
                        source_type="fs_scan",
                        event_type="modified",
                        timestamp=mtime,
                        content_preview=self._read_file_preview(p),
                        file_size=stat.st_size,
                        metadata={"extension": p.suffix},
                    )
                )
            except Exception as e:
                logger.debug(f"Ошибка получения метрик файла {p}: {e}")

        return items

    def collect_all(self) -> List[FileHistoryItem]:
        """Агрегация истории файлов из всех доступных источников ОС Windows.

        Returns:
            List[FileHistoryItem]: Общий список уникальных элементов истории файлов.
        """
        all_items: List[FileHistoryItem] = []
        seen_ids: Set[str] = set()

        sources_methods = [
            ("file_history_xml", self.collect_file_history_xml),
            ("recent_lnk", self.collect_recent_shortcuts),
            ("activity_db", self.collect_activities_db),
            ("fs_scan", self.collect_filesystem_recent),
        ]

        for source_name, method in sources_methods:
            try:
                collected = method()
                logger.info(f"[FileHistoryCollector] Источник {source_name}: собрано {len(collected)} элементов")
                for item in collected:
                    if item.item_id not in seen_ids:
                        seen_ids.add(item.item_id)
                        all_items.append(item)
            except Exception as e:
                logger.error(f"[FileHistoryCollector] Сбой сбора из {source_name}: {e}")

        logger.info(f"[FileHistoryCollector] Всего агрегировано {len(all_items)} элементов истории файлов Windows")
        return all_items
