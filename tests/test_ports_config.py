# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Тестирование централизованной конфигурации портов (ports.json)
# =============================================================================
# Description:
#   Модульные тесты для проверки структуры, уникальности и валидности портов
#   в корневом файле ports.json (включая dynamic_ports и static_ports),
#   корректности работы модуля src.utils.ports, а также синхронизации портов
#   во всех приложениях /apps/*/config.json.
#
# File: test_ports_config.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Тесты для проверки централизованного файла ports.json и синхронизации портов."""

import json
from pathlib import Path
import pytest

from src.utils.ports import PORTS_FILE, get_all_ports, get_port, is_dynamic_ports_enabled, load_ports_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APPS_DIR = PROJECT_ROOT / "apps"


class TestPortsJsonStructure:
    """Тестирование структуры и целостности корневого файла ports.json."""

    def test_ports_file_exists(self) -> None:
        """Проверить, что ports.json существует в корне проекта."""
        assert PORTS_FILE.is_file(), f"Файл ports.json отсутствует по пути: {PORTS_FILE}"

    def test_ports_json_valid_and_has_sections(self) -> None:
        """Проверить, что ports.json содержит валидный JSON, dynamic_ports, server и static_ports."""
        with open(PORTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "dynamic_ports" in data, "В ports.json отсутствует флаг 'dynamic_ports'"
        assert isinstance(data["dynamic_ports"], bool), "'dynamic_ports' должен быть boolean"
        assert "server" in data, "В ports.json отсутствует секция 'server'"
        assert "static_ports" in data, "В ports.json отсутствует секция 'static_ports'"
        assert "apps" in data["static_ports"], "В 'static_ports' отсутствует секция 'apps'"
        assert "services" in data["static_ports"], "В 'static_ports' отсутствует секция 'services'"

    def test_ports_are_integers_and_in_valid_range(self) -> None:
        """Проверить, что все порты являются целыми числами в допустимом диапазоне 1..65535."""
        flat_ports = get_all_ports()
        assert len(flat_ports) > 0, "Словарь портов не должен быть пустым"

        for name, port in flat_ports.items():
            assert isinstance(port, int), f"Порт для '{name}' должен быть int, получено: {type(port)}"
            assert 1 <= port <= 65535, f"Порт {port} для '{name}' выходит за допустимый диапазон 1-65535"

    def test_all_ports_are_unique(self) -> None:
        """Проверить отсутствие дубликатов портов между приложениями и сервисами."""
        flat_ports = get_all_ports()
        seen_ports: dict[int, str] = {}

        for name, port in flat_ports.items():
            if name == "main" and "server" in flat_ports and flat_ports["server"] == port:
                continue
            assert port not in seen_ports, (
                f"Обнаружен конфликт портов! Порт {port} назначен сразу двум компонентам: "
                f"'{seen_ports[port]}' и '{name}'"
            )
            seen_ports[port] = name


class TestPortsUtility:
    """Тестирование функций модуля src.utils.ports."""

    def test_load_ports_config(self) -> None:
        """Проверить загрузку конфигурации через load_ports_config."""
        cfg = load_ports_config()
        assert hasattr(cfg, "static_ports"), "Объект конфигурации должен содержать static_ports"
        assert getattr(cfg.static_ports.apps, "windows_sysadmin", None) == 8100
        assert getattr(cfg.static_ports.apps, "network_terminal", None) == 8101
        assert getattr(cfg.static_ports.apps, "gcloud_monitor", None) == 8106

    def test_is_dynamic_ports_enabled(self) -> None:
        """Проверить функцию проверки dynamic_ports."""
        assert isinstance(is_dynamic_ports_enabled(), bool)

    def test_get_port_helper(self) -> None:
        """Проверить работу функции get_port с дефолтными значениями и существующими именами."""
        assert get_port("server") == 8000
        assert get_port("main") == 8000
        assert get_port("windows_sysadmin") == 8100
        assert get_port("gcloud_monitor") == 8106
        assert get_port("website_monitor") == 8107
        assert get_port("ollama") == 11434
        assert get_port("unknown_component_xyz", default=9999) == 9999


class TestAppsConfigSyncWithPortsJson:
    """Проверка полного соответствия портов в apps/*/config.json и ports.json."""

    @pytest.mark.parametrize(
        "app_name, expected_port",
        [
            ("windows_sysadmin", 8100),
            ("network_terminal", 8101),
            ("system_inspector", 8102),
            ("trading_terminal", 8103),
            ("cloudflared_monitor", 8104),
            ("user_assistant", 8105),
            ("gcloud_monitor", 8106),
            ("website_monitor", 8107),
            ("windows", 8108),
            ("system_control_center", 8109),
        ],
    )
    def test_app_config_matches_ports_json(self, app_name: str, expected_port: int) -> None:
        """Порт в config.json приложения должен в точности совпадать с ports.json."""
        assert get_port(app_name) == expected_port, f"В ports.json для {app_name} ожидался {expected_port}"

        app_config_path = APPS_DIR / app_name / "config.json"
        assert app_config_path.is_file(), f"Файл config.json отсутствует для {app_name}"

        with open(app_config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        app_port = None
        if "server" in data and isinstance(data["server"], dict):
            app_port = data["server"].get("port")
        if app_port is None and "port" in data:
            app_port = data.get("port")

        assert app_port == expected_port, (
            f"Несовпадение порта для '{app_name}': в config.json указан {app_port}, а в ports.json — {expected_port}"
        )
