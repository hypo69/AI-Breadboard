# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Управление и загрузка таблицы сетевых портов
# =============================================================================
# Description:
#   Загрузка централизованной конфигурации портов из ports.json, поддержка
#   статических портов (static_ports), флага dynamic_ports и методов для
#   получения портов микроприложений, основного сервера и внешних сервисов.
#
# File: ports.py
# Project: ai-breadboard
# Package: src.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Модуль централизованного доступа к конфигурации сетевых портов (ports.json)."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Optional

from header import __root__
from logger import logger
from src.utils.jjson import j_loads_ns

PORTS_FILE: Path = __root__ / "ports.json"


def load_ports_config(ports_file: Optional[Path] = None) -> SimpleNamespace:
    """Загрузить конфигурацию портов из ports.json в виде SimpleNamespace.

    Args:
        ports_file: Необязательный путь к файлу конфигурации портов.

    Returns:
        SimpleNamespace: Объект конфигурации с секциями dynamic_ports, server, static_ports.
    """
    target_file = ports_file or PORTS_FILE
    if not target_file.exists():
        logger.warning(f"Файл портов не найден: {target_file}")
        return SimpleNamespace(
            dynamic_ports=False,
            server=SimpleNamespace(main=8000),
            static_ports=SimpleNamespace(apps=SimpleNamespace(), services=SimpleNamespace()),
            apps=SimpleNamespace(),
            services=SimpleNamespace(),
        )

    try:
        return j_loads_ns(target_file)
    except Exception as e:
        logger.error(f"Ошибка загрузки конфигурации портов из {target_file}: {e}")
        return SimpleNamespace(
            dynamic_ports=False,
            server=SimpleNamespace(main=8000),
            static_ports=SimpleNamespace(apps=SimpleNamespace(), services=SimpleNamespace()),
            apps=SimpleNamespace(),
            services=SimpleNamespace(),
        )


def is_dynamic_ports_enabled(ports_file: Optional[Path] = None) -> bool:
    """Проверить, включен ли режим динамических портов (dynamic_ports).

    Args:
        ports_file: Необязательный путь к файлу ports.json.

    Returns:
        bool: True, если динамические порты включены, иначе False.
    """
    cfg = load_ports_config(ports_file=ports_file)
    return bool(getattr(cfg, "dynamic_ports", False))


def get_all_ports(ports_file: Optional[Path] = None) -> Dict[str, int]:
    """Получить плоский словарь со всеми сопоставлениями 'имя -> порт'.

    Сканирует как секции внутри static_ports, так и корневые server/apps/services.

    Args:
        ports_file: Необязательный путь к файлу конфигурации портов.

    Returns:
        Dict[str, int]: Словарь имен сервисов/приложений и назначенных им портов.
    """
    target_file = ports_file or PORTS_FILE
    if not target_file.exists():
        return {"server": 8000, "main": 8000}

    try:
        with open(target_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Не удалось прочитать {target_file}: {e}")
        return {"server": 8000, "main": 8000}

    flat_ports: Dict[str, int] = {}

    def _extract_dict_ports(d: Any) -> None:
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, int):
                    flat_ports[k] = v
                elif isinstance(v, dict):
                    _extract_dict_ports(v)

    # Корневые секции
    for section_key in ("server", "apps", "services"):
        if section_key in data:
            _extract_dict_ports(data[section_key])

    # Секция static_ports
    if "static_ports" in data and isinstance(data["static_ports"], dict):
        _extract_dict_ports(data["static_ports"])

    return flat_ports


def get_port(
    name: str,
    default: Optional[int] = None,
    ports_file: Optional[Path] = None,
    host: str = "127.0.0.1",
    dynamic_fallback: bool = False,
) -> Optional[int]:
    """Получить номер порта для заданного приложения, сервера или сервиса.

    Args:
        name: Название микроприложения (напр. 'windows_sysadmin'), сервера ('server' / 'main') или сервиса ('ollama').
        default: Значение по умолчанию, если порт не найден.
        ports_file: Необязательный путь к файлу ports.json.
        host: Хост для проверки занятости при динамическом выделении.
        dynamic_fallback: Если True или если dynamic_ports=True в ports.json, при занятом статическом порте выделяется свободный.

    Returns:
        Optional[int]: Номер порта или default.
    """
    ports = get_all_ports(ports_file=ports_file)
    assigned_port: Optional[int] = None

    if name in ports:
        assigned_port = ports[name]
    elif name == "server" and "main" in ports:
        assigned_port = ports["main"]
    else:
        assigned_port = default

    if assigned_port is None:
        return None

    # Проверка dynamic_ports
    dynamic_active = dynamic_fallback or is_dynamic_ports_enabled(ports_file=ports_file)
    if dynamic_active:
        from src.utils.get_free_port import _is_port_in_use, get_free_port

        if _is_port_in_use(host, assigned_port):
            try:
                free_port = get_free_port(host)
                logger.info(f"Статический порт {assigned_port} для '{name}' занят. Динамически выделен порт {free_port}")
                return free_port
            except Exception as e:
                logger.warning(f"Не удалось выделить динамический порт для '{name}': {e}")

    return assigned_port
