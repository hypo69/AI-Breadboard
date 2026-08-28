# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тесты конфигурации qBittorrent
# =============================================================================
# Описание:
#   Модуль содержит unit-тесты для проверки загрузки параметров qBittorrent
#   из файла config.json через модуль core.config.
#
# File: tests/test_qbittorrent_config.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""
.. module:: tests.test_qbittorrent_config
    :platform: Windows, Unix
    :synopsis: Тесты чтения конфигурации qBittorrent из config.json
"""

import json
from pathlib import Path
from types import SimpleNamespace
import pytest

from core.config import qbittorrent_cfg, qbt_cfg, CONFIG_FILE
from core.utils.jjson import j_loads_ns


class TestQBittorrentConfig:
    """Тестирование опциональной конфигурации qBittorrent и совместимости."""

    def test_core_config_exports_qbittorrent_cfg(self) -> None:
        """Проверка безопасного экспорта qbittorrent_cfg и qbt_cfg в core.config."""
        assert isinstance(qbittorrent_cfg, SimpleNamespace)
        assert isinstance(qbt_cfg, SimpleNamespace)
        assert qbt_cfg is qbittorrent_cfg

    def test_j_loads_ns_parses_custom_namespace(self, tmp_path: Path) -> None:
        """Проверка корректной десериализации параметров через j_loads_ns."""
        sample_config = tmp_path / "sample_config.json"
        sample_config.write_text(
            json.dumps(
                {
                    "custom_service": {
                        "host": "192.168.1.50",
                        "port": 8080,
                        "user": "custom_user",
                    }
                }
            ),
            encoding="utf-8",
        )

        ns = j_loads_ns(sample_config)
        assert hasattr(ns, "custom_service")
        assert ns.custom_service.host == "192.168.1.50"
        assert ns.custom_service.port == 8080
        assert ns.custom_service.user == "custom_user"
