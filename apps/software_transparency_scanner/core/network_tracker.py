# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Network Activity & Endpoint Tracker
# =============================================================================
# Description:
#   Мониторинг сетевой активности установленных программ:
#   - Обнаружение активных TCP/UDP сокетов через psutil/netstat
#   - Статический анализ известных доменов в конфигах и исполняемых файлах
#   - Извлечение портов и определение протокола
#
# File: network_tracker.py
# Project: ai-breadboard
# Package: apps.software_transparency_scanner.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль мониторинга сетевых соединений и доменов приложений."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore

from apps.software_transparency_scanner.core.models import (
    ConfigFile,
    EvidenceStatus,
    NetworkEndpoint,
    SoftwareItem,
)


class NetworkTracker:
    """Отслеживание сетевой активности и доменов, связанных с ПО."""

    DOMAIN_REGEX = re.compile(
        r"(?i)\b(?:https?://)?([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.(?:[a-z0-9-]+\.)+[a-z]{2,})\b"
    )

    # Словарь известных доменов для популярных приложений
    POPULAR_DOMAINS: Dict[str, List[tuple[str, int, str, str]]] = {
        "chrome": [
            ("clients2.google.com", 443, "HTTPS", "Обновления расширений и проверка защищенного просмотра Safe Browsing"),
            ("update.googleapis.com", 443, "HTTPS", "Служба автообновления компонентов Chromium"),
            ("accounts.google.com", 443, "HTTPS", "Синхронизация профиля и учетной записи Google"),
        ],
        "code": [
            ("update.code.visualstudio.com", 443, "HTTPS", "Сервер проверки обновлений редактора VS Code"),
            ("marketplace.visualstudio.com", 443, "HTTPS", "Каталог расширений Visual Studio Code"),
            ("vortex.data.microsoft.com", 443, "HTTPS", "Служба телеметрии Microsoft (настраивается в настройках)"),
        ],
        "python": [
            ("pypi.org", 443, "HTTPS", "Репозиторий пакетов Python Package Index (pip)"),
            ("files.pythonhosted.org", 443, "HTTPS", "Сервер доставки бинарных колес (wheels) и архивов pip"),
        ],
        "git": [
            ("github.com", 443, "HTTPS", "Хостинг репозиториев GitHub"),
            ("gitlab.com", 443, "HTTPS", "Хостинг репозиториев GitLab"),
        ],
        "telegram": [
            ("api.telegram.org", 443, "HTTPS", "Telegram Bot API и обмен сообщениями"),
        ],
    }

    def track_app_network(self, app: SoftwareItem, config_files: List[ConfigFile]) -> List[NetworkEndpoint]:
        """Определяет активные и потенциальные сетевые узлы для программы.

        Args:
            app: Карточка ПО.
            config_files: Список найденных конфигов программы.

        Returns:
            List[NetworkEndpoint]: Список обнаруженных доменов и соединений.
        """
        endpoints: List[NetworkEndpoint] = []
        seen_domains: Set[str] = set()

        # 1. Поиск активных соединений через psutil
        active_eps = self._get_active_connections_for_app(app)
        for ep in active_eps:
            if ep.domain_or_ip not in seen_domains:
                seen_domains.add(ep.domain_or_ip)
                endpoints.append(ep)

        # 2. Статический поиск доменов в конфигурационных файлах
        for cfg in config_files:
            if cfg.sample_content:
                matches = self.DOMAIN_REGEX.findall(cfg.sample_content)
                for dom in matches:
                    dom_clean = dom.strip("/").lower()
                    if self._is_valid_domain(dom_clean) and dom_clean not in seen_domains:
                        seen_domains.add(dom_clean)
                        endpoints.append(
                            NetworkEndpoint(
                                domain_or_ip=dom_clean,
                                port=443,
                                protocol="HTTPS",
                                source="config_file",
                                purpose=f"Обнаружен в файле настроек {cfg.filename}",
                                status=EvidenceStatus.LOCAL_OBSERVED,
                            )
                        )

        # 3. Добавление базы известных доменов
        app_name_lower = app.name.lower()
        for key, dom_list in self.POPULAR_DOMAINS.items():
            if key in app_name_lower or (app.executable_path and key in app.executable_path.lower()):
                for dom, port, proto, purpose in dom_list:
                    if dom not in seen_domains:
                        seen_domains.add(dom)
                        endpoints.append(
                            NetworkEndpoint(
                                domain_or_ip=dom,
                                port=port,
                                protocol=proto,
                                source="known_database",
                                purpose=purpose,
                                documentation_source="Официальная документация разработчика",
                                status=EvidenceStatus.DOCS_CONFIRMED,
                            )
                        )

        return endpoints

    def _get_active_connections_for_app(self, app: SoftwareItem) -> List[NetworkEndpoint]:
        """Проверяет запущенные процессы и сокеты."""
        if not psutil:
            return []

        results: List[NetworkEndpoint] = []
        target_name = Path(app.executable_path).name.lower() if app.executable_path else ""
        app_name_slug = app.name.lower()

        try:
            for proc in psutil.process_iter(["pid", "name", "exe"]):
                try:
                    p_name = (proc.info.get("name") or "").lower()
                    p_exe = (proc.info.get("exe") or "").lower()

                    matches = False
                    if target_name and p_name == target_name:
                        matches = True
                    elif app.executable_path and p_exe == app.executable_path.lower():
                        matches = True
                    elif app_name_slug in p_name:
                        matches = True

                    if matches:
                        get_conns = getattr(proc, "net_connections", None) or getattr(proc, "connections", None)
                        conns = get_conns(kind="inet") if get_conns else []
                        for c in conns:
                            if c.status == "ESTABLISHED" and c.raddr:
                                rip, rport = c.raddr.ip, c.raddr.port
                                if rip not in ("127.0.0.1", "::1", "0.0.0.0"):
                                    proto = "TCP" if c.type == 1 else "UDP"
                                    results.append(
                                        NetworkEndpoint(
                                            domain_or_ip=rip,
                                            port=rport,
                                            protocol=proto,
                                            source="active_socket",
                                            purpose=f"Активное сетевое соединение процесса {p_name} (PID {proc.pid})",
                                            status=EvidenceStatus.LOCAL_OBSERVED,
                                        )
                                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass

        return results

    def _is_valid_domain(self, domain: str) -> bool:
        """Валидация доменного имени, исключение схем и служебных расширений."""
        d = domain.lower()
        if d.endswith(('.json', '.xml', '.txt', '.png', '.jpg', '.ico', '.dll', '.exe', '.js', '.css', '.html')):
            return False
        if d in ('schemas.microsoft.com', 'www.w3.org', 'localhost', '127.0.0.1'):
            return False
        return '.' in d and len(d) > 4
