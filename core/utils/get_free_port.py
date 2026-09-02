# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Check port availability on host
# =============================================================================
# Description:
#   Search and allocate free TCP port in specified range for launching services.
#
# File: get_free_port.py
# Project: ai-breadboard
# Package: core.utils
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import socket
from typing import List, Tuple, Union

from core.logger import logger

def _is_port_in_use(host: str, port: int) -> bool:
    """Check port availability on host."""
    target_host = "127.0.0.1" if host in ("localhost", "") else host
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((target_host, port))
            return False  # Port is free
        except OSError:
            return True  # Port is in use

def _parse_port_range(port_range_str: str) -> Tuple[int, int]:
    """Parse port range string 'min-max'."""
    try:
        parts = port_range_str.split('-')
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(f'Incorrect range format: {port_range_str}')
        
        min_port = int(parts[0])
        max_port = int(parts[1])

        if min_port >= max_port:
            raise ValueError(f'Incorrect range: {port_range_str}')
        return min_port, max_port

    except ValueError as e:
        logger.error(f'Error parsing range: {port_range_str}')
        raise ValueError(f'Error parsing range: {port_range_str}') from e

def get_free_port(host: str, port_range: Union[str, List[str]] = '') -> int:
    """
    Search and allocate free TCP port.

    Search for free port in specified range or first available if range not specified.

    Args:
        host (str): Host address for checking port availability.
        port_range (Union[str, List[str]]): Port range(s) ("min-max" or list of strings).
               Default value: '' (search first available).

    Returns:
        int: Number of free port.

    Exceptions:
        ValueError: Error if free port not found or range specified incorrectly.

    Examples:
        >>> port = get_free_port(host='localhost', port_range='8000-8005')
    """
    if port_range:
        if isinstance(port_range, str):
            min_port, max_port = _parse_port_range(port_range)
            for port in range(min_port, max_port + 1):
                if not _is_port_in_use(host, port):
                    return port
            raise ValueError(f'Free port in range {port_range} not found')

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
                    continue  # Skip incorrect ranges

            raise ValueError(f'Free port in ranges {port_range} not found')
        else:
            raise ValueError(f'Incorrect range type: {type(port_range)}')
    else:
        # Search first available port starting from 1024
        port = 1024
        while port <= 65535:
            if not _is_port_in_use(host, port):
                return port
            port += 1
        raise ValueError('Free port not found')
