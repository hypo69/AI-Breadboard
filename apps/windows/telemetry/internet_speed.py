# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Internet Speed Sensor Module
# =============================================================================
# Description:
#   Internet speed measurement using Windows native tools and HTTP tests.
#   No external dependencies - uses only standard library and requests.
#
# File: internet_speed.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Internet speed measurement using Windows native tools."""

from __future__ import annotations

import threading
import time
from typing import Dict, List, Optional

import requests

try:
    from src.logger.logger import logger
except ImportError:
    from logger import logger

# Module-level cache: (timestamp, result)
_speed_cache: tuple[float, Dict[str, float]] | None = None
_CACHE_TTL = 300  # seconds between real measurements
_cache_lock = threading.Lock()


class InternetSpeedSensor:
    """Сенсор измерения скорости интернета с поддержкой fallback-серверов."""

    DOWNLOAD_ENDPOINTS: List[str] = [
        "https://speed.cloudflare.com/__down?bytes=10000000",
        "https://cachefly.cachefly.net/10mb.test",
        "https://proof.ovh.net/files/10Mb.dat",
        "https://speed.cloudflare.com/__down?bytes=5000000",
    ]

    UPLOAD_ENDPOINTS: List[str] = [
        "https://speed.cloudflare.com/__up",
        "https://httpbin.org/post",
        "https://postman-echo.com/post",
    ]

    def __init__(self, test_url: Optional[str] = None) -> None:
        """Инициализация сенсора скорости интернета.

        Args:
            test_url: URL для теста скорости загрузки (опционально).
        """
        self.test_url = test_url
        self.timeout = 20

    def measure_ping(self, host: str = "8.8.8.8") -> Optional[float]:
        """Измеряет ping до хоста через системную утилиту ping.

        Args:
            host: IP-адрес или домен хоста.

        Returns:
            Ping в миллисекундах или None при ошибке.
        """
        try:
            import subprocess
            start_time = time.perf_counter()

            process = subprocess.run(
                ["ping", "-n", "1", "-w", "3000", host],
                capture_output=True,
                text=True,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW if __import__("os").name == "nt" else 0,
            )

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            if process.returncode != 0:
                logger.warning(
                    f"InternetSpeed: Сбой проверки ICMP ping к хосту {host} (узел недоступен или отсутствует подключение к сети)."
                )
                return None

            # Try to parse actual RTT from ping output
            output = process.stdout
            if "time" in output.lower():
                for part in output.split():
                    if "time" in part.lower():
                        try:
                            # Extract time value (e.g., "time=12ms")
                            time_str = part.replace("time=", "").replace("ms", "")
                            return float(time_str)
                        except (ValueError, IndexError):
                            pass

            return round(elapsed_ms, 2)

        except Exception as ex:
            logger.warning(f"InternetSpeed: Ошибка при выполнении ping к {host}: {ex}")
            return None

    def measure_download_speed(self, url: Optional[str] = None) -> float:
        """Измеряет скорость скачивания через HTTP с поддержкой fallback-серверов.

        Args:
            url: Целевой URL файла для теста. При None перебираются эндпоинты из DOWNLOAD_ENDPOINTS.

        Returns:
            Скорость загрузки в Мбит/с (Mbps).
        """
        endpoints = [url] if url else ([self.test_url] if self.test_url else self.DOWNLOAD_ENDPOINTS)

        last_exception = None
        for endpoint in endpoints:
            start_time = time.perf_counter()
            try:
                response = requests.get(
                    endpoint,
                    stream=True,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                total_bytes = 0
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    total_bytes += len(chunk)

                elapsed_time = time.perf_counter() - start_time
                if elapsed_time > 0 and total_bytes > 0:
                    speed_mbps = (total_bytes * 8) / elapsed_time / 1_000_000
                    return round(speed_mbps, 2)

            except Exception as ex:
                last_exception = ex
                logger.debug(f"InternetSpeed: Тест скорости через {endpoint} не удался: {ex}. Пробуем следующий узел...")
                continue

        if last_exception:
            logger.warning(
                f"InternetSpeed: Сбой всех узлов теста скорости загрузки ({endpoints}): {last_exception}"
            )
        return 0.0

    def measure_upload_speed(self, url: Optional[str] = None) -> float:
        """Измеряет скорость отдачи через HTTP POST с fallback-серверами.

        Args:
            url: URL эндпоинта для выгрузки.

        Returns:
            Скорость отдачи в Мбит/с (Mbps).
        """
        endpoints = [url] if url else self.UPLOAD_ENDPOINTS
        test_data = b"x" * (1024 * 1024)  # 1MB

        last_exception = None
        for endpoint in endpoints:
            start_time = time.perf_counter()
            try:
                response = requests.post(
                    endpoint,
                    data=test_data,
                    timeout=self.timeout,
                )
                if response.status_code in (200, 201, 204):
                    elapsed_time = time.perf_counter() - start_time
                    if elapsed_time > 0:
                        speed_mbps = (len(test_data) * 8) / elapsed_time / 1_000_000
                        return round(speed_mbps, 2)
            except Exception as ex:
                last_exception = ex
                logger.debug(f"InternetSpeed: Тест отдачи через {endpoint} не удался: {ex}. Пробуем резервный узел...")
                continue

        if last_exception:
            logger.warning(
                f"InternetSpeed: Сбой всех узлов теста отдачи ({endpoints}): {last_exception}"
            )
        return 0.0

    def measure_dns_resolution(self, hostname: str = "google.com") -> Optional[float]:
        """Измеряет время разрешения DNS.

        Args:
            hostname: Доменное имя для проверки.

        Returns:
            Время разрешения DNS в миллисекундах.
        """
        try:
            import socket
            start_time = time.perf_counter()

            socket.gethostbyname(hostname)

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return round(elapsed_ms, 2)

        except Exception as ex:
            logger.warning(
                f"InternetSpeed: Сбой разрешения DNS для '{hostname}': {ex} (отсутствует интернет или сбой DNS-сервера)"
            )
            return None

    def measure_internet_speed(self) -> Dict[str, float]:
        """Измеряет полный профиль сетевого соединения с защитой от частых запросов.

        Returns:
            Словарь с метриками ping, download, upload и DNS.
        """
        global _speed_cache
        with _cache_lock:
            if _speed_cache is not None:
                cached_at, cached_result = _speed_cache
                if time.monotonic() - cached_at < _CACHE_TTL:
                    return cached_result

            result: Dict[str, float] = {}

            ping = self.measure_ping("8.8.8.8")
            result["ping_ms"] = ping if ping is not None else 0.0
            result["download_mbps"] = self.measure_download_speed()
            result["upload_mbps"] = self.measure_upload_speed()
            dns_time = self.measure_dns_resolution()
            result["dns_ms"] = dns_time if dns_time is not None else 0.0

            _speed_cache = (time.monotonic(), result)
            return result


def get_internet_speed_sensors() -> list:
    """Get internet speed metrics as sensor-like data.

    Returns:
        List of internet speed metrics.
    """
    sensor = InternetSpeedSensor()
    metrics = sensor.measure_internet_speed()

    sensors = [
        {
            "sensor_id": "internet_ping",
            "name": "Internet Ping",
            "category": "network",
            "value": metrics.get("ping_ms", 0.0),
            "unit": "ms",
        },
        {
            "sensor_id": "internet_download",
            "name": "Internet Download Speed",
            "category": "network",
            "value": metrics.get("download_mbps", 0.0),
            "unit": "Mbps",
        },
        {
            "sensor_id": "internet_upload",
            "name": "Internet Upload Speed",
            "category": "network",
            "value": metrics.get("upload_mbps", 0.0),
            "unit": "Mbps",
        },
        {
            "sensor_id": "internet_dns",
            "name": "DNS Resolution Time",
            "category": "network",
            "value": metrics.get("dns_ms", 0.0),
            "unit": "ms",
        },
    ]

    return sensors
