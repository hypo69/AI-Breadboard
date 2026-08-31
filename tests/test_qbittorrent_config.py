# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Testing qBittorrent configuration loading
# =============================================================================
# Description:
#   Unit tests for qBittorrent configuration parameters loading from config.json
#
# File: test_qbittorrent_config.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
from pathlib import Path
from types import SimpleNamespace
import pytest

from core.config import qbittorrent_cfg, qbt_cfg, CONFIG_FILE
from core.utils.jjson import j_loads_ns

class TestQBittorrentConfig:
    """Testing optional qBittorrent configuration and compatibility."""

    def test_core_config_exports_qbittorrent_cfg(self) -> None:
        """Test safe export of qbittorrent_cfg and qbt_cfg in core.config.
        
        Check: Both configuration objects should be SimpleNamespace instances
               and qbt_cfg should reference same object as qbittorrent_cfg.
        """
        assert isinstance(qbittorrent_cfg, SimpleNamespace)
        assert isinstance(qbt_cfg, SimpleNamespace)
        assert qbt_cfg is qbittorrent_cfg

    def test_j_loads_ns_parses_custom_namespace(self, tmp_path: Path) -> None:
        """Test correct deserialization of parameters via j_loads_ns.
        
        Check: Custom configuration file correctly parsed into nested
               SimpleNamespace with proper attribute access.
        """
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
