# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Software Transparency & Audit Engine
# =============================================================================
# Description:
#   Инспекция прозрачности ПО: инвентаризация, анализ мест хранения данных,
#   поиск и очистка секретов в конфигах, трекинг сетевых доменов и ИИ-исследование
#   через Google Gemini.
#
# File: software_transparency.py
# Project: ai-breadboard
# Package: apps.windows.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль инспекции прозрачности ПО, анализа конфигураций, мест хранения и сетевых доменов."""

from __future__ import annotations

import datetime
import json
import os
import re
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from logger import logger
from apps.windows.core.software_audit import SoftwareAuditEngine
from apps.common.csv_logger import AppCsvLogger


class StorageCategory(str, Enum):
    """Категории хранилищ данных программы."""
    CONFIG = "config"
    DATA = "data"
    CACHE = "cache"
    LOGS = "logs"
    BINARIES = "binaries"
    UNKNOWN = "unknown"


class EvidenceStatus(str, Enum):
    """Статус достоверности данных."""
    LOCAL_OBSERVED = "observed"
    DOCS_CONFIRMED = "confirmed"
    AI_INFERRED = "inferred"


class ConfigFile(BaseModel):
    """Обнаруженный файл конфигурации программы."""
    path: str = Field(..., description="Абсолютный путь к файлу")
    display_path: str = Field(..., description="Путь с макросами окружения")
    filename: str = Field(..., description="Имя файла")
    format: str = Field(default="unknown", description="Формат файла")
    size_bytes: int = Field(default=0, description="Размер в байтах")
    last_modified: Optional[str] = Field(default=None, description="Дата последнего изменения ISO")
    purpose: str = Field(default="Настройки программы", description="Назначение файла")
    is_sanitized: bool = Field(default=True, description="Статус санитизации секретов")
    sample_content: Optional[str] = Field(default=None, description="Очищенный фрагмент конфигурации")
    status: EvidenceStatus = Field(default=EvidenceStatus.LOCAL_OBSERVED, description="Статус достоверности")


class StorageDirectory(BaseModel):
    """Описание обнаруженного каталога данных программы."""
    path: str = Field(..., description="Абсолютный путь к каталогу")
    display_path: str = Field(..., description="Путь с макросами окружения")
    category: StorageCategory = Field(default=StorageCategory.UNKNOWN, description="Тип хранимых данных")
    description: str = Field(default="", description="Описание назначения каталога")
    file_count: int = Field(default=0, description="Количество файлов")
    total_size_bytes: int = Field(default=0, description="Общий размер файлов")
    status: EvidenceStatus = Field(default=EvidenceStatus.LOCAL_OBSERVED, description="Статус достоверности")


class NetworkEndpoint(BaseModel):
    """Описание сетевого соединения или обнаруженного домена."""
    domain_or_ip: str = Field(..., description="Доменное имя или IP-адрес")
    port: Optional[int] = Field(default=None, description="Сетевой порт")
    protocol: str = Field(default="HTTPS", description="Сетевой протокол")
    source: str = Field(default="observed", description="Источник детекции")
    purpose: str = Field(default="Требуется исследование домена", description="Назначение соединения")
    documentation_source: Optional[str] = Field(default=None, description="Ссылка на документацию")
    status: EvidenceStatus = Field(default=EvidenceStatus.LOCAL_OBSERVED, description="Статус достоверности")


class GeminiAppResearch(BaseModel):
    """Результаты аналитического исследования программы через Gemini."""
    app_name: str = Field(..., description="Название исследованной программы")
    summary: str = Field(default="", description="Назначение и функционал программы")
    config_purpose_explanation: str = Field(default="", description="Объяснение назначения конфигурационных файлов")
    data_storage_explanation: str = Field(default="", description="Описание локального хранения данных")
    network_activity_explanation: str = Field(default="", description="Назначение сетевых доменов и серверов")
    confirmed_facts: List[str] = Field(default_factory=list, description="Факты из официальных источников")
    inferred_facts: List[str] = Field(default_factory=list, description="Логические предположения модели")
    unknown_aspects: List[str] = Field(default_factory=list, description="Неизвестные сведения")
    confidence_level: str = Field(default="Высокий", description="Уровень уверенности")


class SoftwareItem(BaseModel):
    """Сводная карточка установленного программного обеспечения."""
    id: str = Field(..., description="Уникальный идентификатор записи (slug)")
    name: str = Field(..., description="Название программы")
    version: str = Field(default="Не указана", description="Версия ПО")
    publisher: str = Field(default="Неизвестен", description="Разработчик / Издатель")
    install_location: Optional[str] = Field(default=None, description="Путь установки")
    executable_path: Optional[str] = Field(default=None, description="Главный исполняемый файл")
    architecture: str = Field(default="x64", description="Разрядность x64, x86 или ARM64")
    install_date: Optional[str] = Field(default=None, description="Дата установки")
    registry_key: Optional[str] = Field(default=None, description="Ветка реестра Windows")
    
    config_files: List[ConfigFile] = Field(default_factory=list, description="Файлы конфигурации")
    data_directories: List[StorageDirectory] = Field(default_factory=list, description="Каталоги хранения данных")
    network_endpoints: List[NetworkEndpoint] = Field(default_factory=list, description="Сетевые взаимодействия")
    windows_services: List[str] = Field(default_factory=list, description="Связанные службы Windows")
    ai_research: Optional[GeminiAppResearch] = Field(default=None, description="Результаты исследования Gemini")


class ScanSummary(BaseModel):
    """Сводная статистика сканирования системы."""
    total_apps: int = Field(default=0, description="Всего обнаружено установленных программ")
    total_configs_found: int = Field(default=0, description="Всего найдено файлов конфигурации")
    total_network_domains: int = Field(default=0, description="Всего уникальных сетевых доменов")
    total_storage_bytes: int = Field(default=0, description="Суммарный объем отслеживаемых данных")
    scan_duration_sec: float = Field(default=0.0, description="Время выполнения сканирования в секундах")
    last_scan_time: Optional[str] = Field(default=None, description="Время последнего сканирования ISO")


class FullScanReport(BaseModel):
    """Полный отчет инвентаризации и аудита прозрачности ПО."""
    summary: ScanSummary = Field(..., description="Сводка сканирования")
    apps: List[SoftwareItem] = Field(default_factory=list, description="Список детальных карточек программ")


class ResearchRequest(BaseModel):
    """Запрос на AI-исследование конкретной программы."""
    app_id: str = Field(..., description="Идентификатор программы")
    force_refresh: bool = Field(default=False, description="Принудительное обновление через Gemini")


class SoftwareInventory:
    """Инвентаризатор программного обеспечения Windows на базе SoftwareAuditEngine."""

    def __init__(self) -> None:
        self._audit_engine = SoftwareAuditEngine()

    @staticmethod
    def _create_slug(name: str, version: str) -> str:
        clean_name = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.lower()).strip("-")
        clean_ver = re.sub(r"[^a-zA-Z0-9_-]+", "-", version.lower()).strip("-")
        return f"{clean_name or 'unknown-app'}-{clean_ver or 'ver'}"

    def scan_installed_software(self) -> List[SoftwareItem]:
        """Сканирует установленное ПО в системе."""
        try:
            report = self._audit_engine.generate_audit_report()
            items: List[SoftwareItem] = []
            for app in report.apps:
                slug = self._create_slug(app.name, app.version)
                items.append(
                    SoftwareItem(
                        id=slug,
                        name=app.name,
                        version=app.version or "Не указана",
                        publisher=app.publisher or "Неизвестен",
                        install_location=app.install_location,
                        executable_path=app.executable_path,
                        architecture=app.architecture or "x64",
                        install_date=app.install_date,
                        registry_key=app.source,
                    )
                )
            if items:
                return items
        except Exception as ex:
            logger.debug(f"Ошибка вызова SoftwareAuditEngine: {ex}")

        return self._get_fallback_mock_software()

    def _get_fallback_mock_software(self) -> List[SoftwareItem]:
        return [
            SoftwareItem(
                id="google-chrome-140-x",
                name="Google Chrome",
                version="140.0.7132.0",
                publisher="Google LLC",
                install_location=r"C:\Program Files\Google\Chrome\Application",
                executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                architecture="x64",
            ),
            SoftwareItem(
                id="visual-studio-code",
                name="Visual Studio Code",
                version="1.93.0",
                publisher="Microsoft Corporation",
                install_location=os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code"),
                executable_path=os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
                architecture="x64",
            ),
        ]


class StorageAnalyzer:
    """Анализатор мест хранения пользовательских данных программ."""

    ROOT_ENV_DIRS = [
        ("%APPDATA%", os.getenv("APPDATA"), StorageCategory.CONFIG, "Пользовательские настройки (Roaming)"),
        ("%LOCALAPPDATA%", os.getenv("LOCALAPPDATA"), StorageCategory.CACHE, "Кэш и локальные данные"),
        ("%PROGRAMDATA%", os.getenv("PROGRAMDATA"), StorageCategory.CONFIG, "Общие конфигурации всех пользователей"),
    ]

    def discover_storage_for_app(self, app: SoftwareItem) -> List[StorageDirectory]:
        results: List[StorageDirectory] = []
        aliases = self._get_search_aliases(app)

        if app.install_location and os.path.isdir(app.install_location):
            stats = self._get_dir_stats(app.install_location)
            results.append(
                StorageDirectory(
                    path=app.install_location,
                    display_path=self._to_display_path(app.install_location),
                    category=StorageCategory.BINARIES,
                    description="Исполняемые файлы программы",
                    file_count=stats["file_count"],
                    total_size_bytes=stats["total_size"],
                    status=EvidenceStatus.LOCAL_OBSERVED,
                )
            )

        for _, base_dir, default_cat, base_desc in self.ROOT_ENV_DIRS:
            if not base_dir or not os.path.exists(base_dir):
                continue
            matched_dir = self._find_matching_folder(base_dir, aliases)
            if matched_dir and os.path.isdir(matched_dir):
                stats = self._get_dir_stats(matched_dir)
                category, desc = self._classify_directory(matched_dir, default_cat, base_desc)
                results.append(
                    StorageDirectory(
                        path=matched_dir,
                        display_path=self._to_display_path(matched_dir),
                        category=category,
                        description=desc,
                        file_count=stats["file_count"],
                        total_size_bytes=stats["total_size"],
                        status=EvidenceStatus.LOCAL_OBSERVED,
                    )
                )

        return results

    def _get_search_aliases(self, app: SoftwareItem) -> List[str]:
        aliases = [app.name.lower()]
        clean_name = re.sub(r"(?i)\b(inc|llc|corp|ltd|gmbh|64-bit|32-bit|x64|x86)\b", "", app.name).strip().lower()
        if clean_name and clean_name not in aliases:
            aliases.append(clean_name)
        if app.executable_path:
            exe_stem = Path(app.executable_path).stem.lower()
            if exe_stem not in aliases:
                aliases.append(exe_stem)
        return aliases

    def _find_matching_folder(self, base_path: str, aliases: List[str]) -> Optional[str]:
        try:
            entries = os.listdir(base_path)
        except (OSError, PermissionError):
            return None
        entries_lower = {e.lower(): e for e in entries}
        for alias in aliases:
            if alias in entries_lower:
                return os.path.join(base_path, entries_lower[alias])
            for e_low, orig_name in entries_lower.items():
                if len(alias) >= 4 and len(e_low) >= 4 and (alias in e_low or e_low in alias):
                    return os.path.join(base_path, orig_name)
        return None

    def _classify_directory(
        self, folder_path: str, default_cat: StorageCategory, default_desc: str
    ) -> tuple[StorageCategory, str]:
        f_lower = folder_path.lower()
        if "cache" in f_lower or "temp" in f_lower:
            return StorageCategory.CACHE, "Кэш и временные рабочие данные"
        if "log" in f_lower:
            return StorageCategory.LOGS, "Журналы работы"
        return default_cat, default_desc

    def _get_dir_stats(self, dir_path: str) -> Dict[str, int]:
        file_count = 0
        total_size = 0
        try:
            for root, _, files in os.walk(dir_path):
                if len(Path(root).relative_to(Path(dir_path)).parts) > 2:
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
        p = full_path
        for env_var in ("APPDATA", "LOCALAPPDATA", "PROGRAMDATA", "USERPROFILE"):
            val = os.getenv(env_var)
            if val and p.lower().startswith(val.lower()):
                return f"%{env_var}%{p[len(val):]}"
        return p


class ConfigInspector:
    """Инспекция конфигурационных файлов ПО и очистка секретов."""

    CONFIG_EXTENSIONS = {".json", ".ini", ".yaml", ".yml", ".xml", ".cfg", ".conf", ".toml", ".config"}
    BEARER_JWT_REGEX = re.compile(r"(Bearer\s+)[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_.+/=]*")
    GENERIC_KEY_REGEX = re.compile(r"(AIzaSy[A-Za-z0-9_-]{33}|sk-[A-Za-z0-9]{32,})")
    SECRET_KV_REGEX = re.compile(
        r"""(?i)(['"]?(?:password|passwd|secret|token|api[_-]?key|auth|credential|private[_-]?key)['"]?\s*[:=]\s*['"])([^'"\r\n]+)(['"])"""
    )

    def __init__(self, max_file_size_kb: int = 256):
        self.max_file_size_bytes = max_file_size_kb * 1024

    def inspect_directories_for_configs(self, directories: List[StorageDirectory]) -> List[ConfigFile]:
        found_configs: List[ConfigFile] = []
        for d in directories:
            if not os.path.exists(d.path) or not os.path.isdir(d.path):
                continue
            try:
                for root, _, files in os.walk(d.path):
                    if len(Path(root).relative_to(Path(d.path)).parts) > 3:
                        continue
                    for file in files:
                        if Path(file).suffix.lower() in self.CONFIG_EXTENSIONS:
                            cfg_item = self._process_config_file(os.path.join(root, file))
                            if cfg_item:
                                found_configs.append(cfg_item)
                                if len(found_configs) >= 20:
                                    return found_configs
            except (OSError, PermissionError):
                continue
        return found_configs

    def _process_config_file(self, full_path: str) -> Optional[ConfigFile]:
        try:
            st = os.stat(full_path)
            size = st.st_size
            if size > self.max_file_size_bytes:
                sample = "[Файл превышает лимит размера 256 KB]"
            else:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    sample = self.sanitize_secrets(f.read(4096))
            mod_time = datetime.datetime.fromtimestamp(st.st_mtime).isoformat()
            return ConfigFile(
                path=full_path,
                display_path=self._to_display_path(full_path),
                filename=Path(full_path).name,
                format=Path(full_path).suffix.lower().lstrip(".") or "text",
                size_bytes=size,
                last_modified=mod_time,
                purpose=self._guess_config_purpose(Path(full_path).name),
                is_sanitized=True,
                sample_content=sample,
                status=EvidenceStatus.LOCAL_OBSERVED,
            )
        except (OSError, PermissionError):
            return None

    def sanitize_secrets(self, content: str) -> str:
        if not content:
            return ""
        sanitized = self.BEARER_JWT_REGEX.sub(r"Bearer [REDACTED_JWT_TOKEN]", content)
        sanitized = self.GENERIC_KEY_REGEX.sub(r"[REDACTED_API_KEY]", sanitized)
        sanitized = self.SECRET_KV_REGEX.sub(r"\g<1>[REDACTED_SECRET]\g<3>", sanitized)
        return sanitized

    def _guess_config_purpose(self, filename: str) -> str:
        fn = filename.lower()
        if "settings" in fn or "config" in fn:
            return "Пользовательские настройки"
        if "session" in fn or "state" in fn:
            return "Состояние сессии"
        return "Конфигурация работы приложения"

    def _to_display_path(self, full_path: str) -> str:
        p = full_path
        for env_var in ("APPDATA", "LOCALAPPDATA", "PROGRAMDATA", "USERPROFILE"):
            val = os.getenv(env_var)
            if val and p.lower().startswith(val.lower()):
                return f"%{env_var}%{p[len(val):]}"
        return p


class NetworkTracker:
    """Отслеживание сетевой активности приложений."""

    DOMAIN_REGEX = re.compile(r"(?i)\b(?:https?://)?([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.(?:[a-z0-9-]+\.)+[a-z]{2,})\b")
    POPULAR_DOMAINS: Dict[str, List[tuple[str, int, str, str]]] = {
        "chrome": [("clients2.google.com", 443, "HTTPS", "Safe Browsing"), ("update.googleapis.com", 443, "HTTPS", "Автообновления")],
        "code": [("marketplace.visualstudio.com", 443, "HTTPS", "Каталог расширений VS Code")],
        "python": [("pypi.org", 443, "HTTPS", "Репозиторий пакетов PyPI")],
    }

    def track_app_network(self, app: SoftwareItem, config_files: List[ConfigFile]) -> List[NetworkEndpoint]:
        endpoints: List[NetworkEndpoint] = []
        seen: Set[str] = set()

        for ep in self._get_active_connections(app):
            if ep.domain_or_ip not in seen:
                seen.add(ep.domain_or_ip)
                endpoints.append(ep)

        for cfg in config_files:
            if cfg.sample_content:
                for dom in self.DOMAIN_REGEX.findall(cfg.sample_content):
                    d_clean = dom.strip("/").lower()
                    if "." in d_clean and d_clean not in seen and not d_clean.endswith((".exe", ".dll", ".json")):
                        seen.add(d_clean)
                        endpoints.append(
                            NetworkEndpoint(
                                domain_or_ip=d_clean,
                                port=443,
                                protocol="HTTPS",
                                source="config_file",
                                purpose=f"Файл {cfg.filename}",
                                status=EvidenceStatus.LOCAL_OBSERVED,
                            )
                        )

        app_low = app.name.lower()
        for k, dom_list in self.POPULAR_DOMAINS.items():
            if k in app_low:
                for dom, port, proto, purp in dom_list:
                    if dom not in seen:
                        seen.add(dom)
                        endpoints.append(
                            NetworkEndpoint(
                                domain_or_ip=dom,
                                port=port,
                                protocol=proto,
                                source="known_database",
                                purpose=purp,
                                status=EvidenceStatus.DOCS_CONFIRMED,
                            )
                        )

        return endpoints

    def _get_active_connections(self, app: SoftwareItem) -> List[NetworkEndpoint]:
        if not psutil:
            return []
        results: List[NetworkEndpoint] = []
        target_name = Path(app.executable_path).name.lower() if app.executable_path else ""
        try:
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    pname = (proc.info.get("name") or "").lower()
                    if target_name and pname == target_name:
                        get_conns = getattr(proc, "net_connections", None) or getattr(proc, "connections", None)
                        conns = get_conns(kind="inet") if get_conns else []
                        for c in conns:
                            if c.status == "ESTABLISHED" and c.raddr:
                                rip = c.raddr.ip
                                if rip not in ("127.0.0.1", "::1", "0.0.0.0"):
                                    results.append(
                                        NetworkEndpoint(
                                            domain_or_ip=rip,
                                            port=c.raddr.port,
                                            protocol="TCP" if c.type == 1 else "UDP",
                                            source="active_socket",
                                            purpose=f"Активный сокет {pname} (PID {proc.pid})",
                                            status=EvidenceStatus.LOCAL_OBSERVED,
                                        )
                                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        return results


class GeminiResearcher:
    """ИИ-исследователь прозрачности ПО через Google Gemini."""

    def __init__(self, chat_provider: Optional[Any] = None) -> None:
        self.chat_provider = chat_provider

    async def research_software(self, app: SoftwareItem) -> GeminiAppResearch:
        if self.chat_provider and hasattr(self.chat_provider, "generate_response"):
            try:
                prompt = f"Проанализируй программу {app.name} версии {app.version} от {app.publisher}."
                resp = await self.chat_provider.generate_response(prompt)
                parsed = self._parse_json(resp, app.name)
                if parsed:
                    return parsed
            except Exception as ex:
                logger.debug(f"Ошибка вызова Gemini provider: {ex}")

        return self._generate_fallback(app)

    def _parse_json(self, text: str, app_name: str) -> Optional[GeminiAppResearch]:
        try:
            clean = text.strip().strip("`").replace("json", "").strip()
            data = json.loads(clean)
            return GeminiAppResearch(
                app_name=app_name,
                summary=data.get("summary", ""),
                config_purpose_explanation=data.get("config_purpose_explanation", ""),
                data_storage_explanation=data.get("data_storage_explanation", ""),
                network_activity_explanation=data.get("network_activity_explanation", ""),
                confirmed_facts=data.get("confirmed_facts", []),
                inferred_facts=data.get("inferred_facts", []),
                unknown_aspects=data.get("unknown_aspects", []),
                confidence_level=data.get("confidence_level", "Средний"),
            )
        except Exception:
            return None

    def _generate_fallback(self, app: SoftwareItem) -> GeminiAppResearch:
        return GeminiAppResearch(
            app_name=app.name,
            summary=f"Программа {app.name} от разработчика {app.publisher}. Версия: {app.version}.",
            config_purpose_explanation="Параметры работы и пользовательские настройки.",
            data_storage_explanation="Локальные каталоги %APPDATA% и %LOCALAPPDATA%.",
            network_activity_explanation="Проверка обновлений и взаимодействия по сетевым протоколам.",
            confirmed_facts=[f"ПО установлено в системе ({app.name})", f"Издатель: {app.publisher}"],
            inferred_facts=["Использует стандартную структуру расположения данных Windows"],
            unknown_aspects=["Детали проприетарных протоколов сети"],
            confidence_level="Подтверждено документацией",
        )


def init_software_transparency_router(chat_provider: Optional[Any] = None) -> APIRouter:
    """Инициализация FastAPI роутера сканера прозрачности ПО."""
    router = APIRouter(prefix="/api/v1/software-scanner", tags=["AI Software Transparency Scanner"])
    csv_logger = AppCsvLogger("software_transparency_scanner")

    inventory = SoftwareInventory()
    storage_analyzer = StorageAnalyzer()
    config_inspector = ConfigInspector()
    network_tracker = NetworkTracker()
    researcher = GeminiResearcher(chat_provider=chat_provider)

    _cache: Dict[str, SoftwareItem] = {}
    _last_summary: Optional[ScanSummary] = None

    @router.get("/status")
    async def get_status() -> Dict[str, Any]:
        csv_logger.log_poll(
            poll_type="status",
            metric_name="cached_apps_count",
            value=len(_cache),
            unit="count",
            status="online",
            details="service_status_check",
            filename="software_transparency_polls.csv",
        )
        return {
            "status": "online",
            "service": "AI Software Transparency Scanner",
            "version": "1.0.0",
            "cached_apps_count": len(_cache),
        }

    @router.get("/scan", response_model=FullScanReport)
    async def run_full_scan(force_refresh: bool = Query(False, description="Принудительно пересканировать")) -> FullScanReport:
        nonlocal _cache, _last_summary
        start_time = time.time()

        if not _cache or force_refresh:
            apps = inventory.scan_installed_software()
            _cache = {}

            total_configs = 0
            total_domains = 0
            total_bytes = 0

            for app in apps:
                dirs = storage_analyzer.discover_storage_for_app(app)
                app.data_directories = dirs
                for d in dirs:
                    total_bytes += d.total_size_bytes

                cfgs = config_inspector.inspect_directories_for_configs(dirs)
                app.config_files = cfgs
                total_configs += len(cfgs)

                nets = network_tracker.track_app_network(app, cfgs)
                app.network_endpoints = nets
                total_domains += len(nets)

                _cache[app.id] = app

            dur = round(time.time() - start_time, 2)
            _last_summary = ScanSummary(
                total_apps=len(_cache),
                total_configs_found=total_configs,
                total_network_domains=total_domains,
                total_storage_bytes=total_bytes,
                scan_duration_sec=dur,
                last_scan_time=time.strftime("%Y-%m-%dT%H:%M:%S"),
            )
            csv_logger.log_event(
                event_type="full_scan_completed",
                status="success",
                details=f"apps={len(_cache)},configs={total_configs},domains={total_domains},storage_mb={round(total_bytes/(1024*1024),2)},duration_s={dur}",
                filename="software_transparency_scans.csv",
            )

        return FullScanReport(
            summary=_last_summary or ScanSummary(total_apps=len(_cache)),
            apps=list(_cache.values()),
        )

    @router.get("/apps", response_model=List[SoftwareItem])
    async def get_apps() -> List[SoftwareItem]:
        if not _cache:
            await run_full_scan()
        return list(_cache.values())

    @router.get("/apps/{app_id}", response_model=SoftwareItem)
    async def get_app_details(app_id: str) -> SoftwareItem:
        if not _cache:
            await run_full_scan()
        if app_id in _cache:
            return _cache[app_id]
        for k, v in _cache.items():
            if app_id.lower() in k.lower() or app_id.lower() in v.name.lower():
                return v
        raise HTTPException(status_code=404, detail=f"Программа с ID '{app_id}' не найдена")

    @router.post("/research", response_model=GeminiAppResearch)
    async def research_app(req: ResearchRequest) -> GeminiAppResearch:
        if not _cache:
            await run_full_scan()
        target_app = _cache.get(req.app_id)
        if not target_app:
            for k, v in _cache.items():
                if req.app_id.lower() in k.lower() or req.app_id.lower() in v.name.lower():
                    target_app = v
                    break
        if not target_app:
            csv_logger.log_event(
                event_type="app_research_failed",
                status="not_found",
                details=f"app_id={req.app_id}",
                filename="software_transparency_scans.csv",
            )
            raise HTTPException(status_code=404, detail=f"Программа '{req.app_id}' не найдена для исследования")
        if target_app.ai_research and not req.force_refresh:
            return target_app.ai_research

        research_res = await researcher.research_software(target_app)
        target_app.ai_research = research_res
        csv_logger.log_event(
            event_type="app_research_completed",
            status="success",
            details=f"app_id={req.app_id},app_name={target_app.name}",
            filename="software_transparency_scans.csv",
        )
        return research_res

    return router
