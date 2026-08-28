# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Определение свободного сетевого порта
# =============================================================================
# Описание:
#   Поиск и выделение свободного TCP-порта в заданном диапазоне для запуска
#   локальных сетевых сервисов и процессов мониторинга.
#
# Примеры:
#   >>> port = get_free_port(host='localhost', port_range='3000-3005')
#   >>> print(f'Свободный порт: {port}')
#
# File: get_free_port.py
# Project: Наш интеллектуальный помощник
# Package: Utils
# Module: Network
# Function: get_free_port
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import socket
from typing import List, Tuple, Union

from core.logger import logger

def _is_port_in_use(host: str, port: int) -> bool:
    """Проверка занятости порта на хосте."""
    target_host = "127.0.0.1" if host in ("localhost", "") else host
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((target_host, port))
            return False  # Порт свободен
        except OSError:
            return True  # Порт занят

def _parse_port_range(port_range_str: str) -> Tuple[int, int]:
    """Парсинг строки диапазона портов 'min-max'."""
    try:
        parts = port_range_str.split('-')
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(f'Некорректный формат диапазона: {port_range_str}')
        
        min_port = int(parts[0])
        max_port = int(parts[1])

        if min_port >= max_port:
            raise ValueError(f'Некорректный диапазон: {port_range_str}')
        return min_port, max_port

    except ValueError as e:
        logger.error(f'Ошибка парсинга диапазона: {port_range_str}')
        raise ValueError(f'Ошибка парсинга диапазона: {port_range_str}') from e

def get_free_port(host: str, port_range: Union[str, List[str]] = '') -> int:
    """
    Поиск и выделение свободного TCP-порта.

    Поиск свободного порта в заданном диапазоне или первого доступного, если диапазон не указан.

    Args:
        host (str): Адрес хоста для проверки доступности порта.
        port_range (Union[str, List[str]]): Диапазон(ы) портов ("min-max" или список строк).
               Значение по умолчанию: '' (поиск первого доступного).

    Returns:
        int: Номер свободного порта.

    Exceptions:
        ValueError: Ошибка, если свободный порт не найден или диапазон задан некорректно.

    Examples:
        >>> port = get_free_port(host='localhost', port_range='3000-3005')
    """
    if port_range:
        if isinstance(port_range, str):
            min_port, max_port = _parse_port_range(port_range)
            for port in range(min_port, max_port + 1):
                if not _is_port_in_use(host, port):
                    return port
            raise ValueError(f'Свободный порт в диапазоне {port_range} не найден')

        elif isinstance(port_range, list):
            for item in port_range:
                if not isinstance(item, str):
                    continue
                try:
                    min_port, max_port = _parse_port_range(item)
                    for port in range(min_port, max_port + 1):
                        if not _is_port_in_use(host, port):
                            return port
                except ValueError:
                    continue  # Пропуск некорректных диапазонов

            raise ValueError(f'Свободный порт в диапазонах {port_range} не найден')
        else:
            raise ValueError(f'Некорректный тип диапазона: {type(port_range)}')
    else:
        # Поиск первого доступного порта начиная с 1024
        port = 1024
        while port <= 65535:
            if not _is_port_in_use(host, port):
                return port
            port += 1
        raise ValueError('Свободный порт не найден')
