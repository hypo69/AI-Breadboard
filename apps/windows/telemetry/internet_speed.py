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

import time
from typing import Dict, Optional

import requests

from src.logger import logger


class InternetSpeedSensor:
    """Internet speed measurement sensor using HTTP tests."""

    def __init__(self, test_url: Optional[str] = None) -> None:
        """Initialize internet speed sensor.

        Args:
            test_url: URL for download speed test. Defaults to Cloudflare speed test.
        """
        self.test_url = test_url or "https://speed.cloudflare.com/__down?bytes=10000000"
        self.timeout = 30

    def measure_ping(self, host: str = "8.8.8.8") -> Optional[float]:
        """Measure ping to host using Windows native ping command.

        Args:
            host: IP address or hostname to ping.

        Returns:
            Ping in milliseconds or None if failed.
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
                logger.debug(f"Ping failed: {host}")
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
            logger.debug(f"Ping measurement failed: {ex}")
            return None

    def measure_download_speed(self, url: Optional[str] = None) -> float:
        """Measure download speed via HTTP.

        Args:
            url: URL of test file. Defaults to Cloudflare speed test.

        Returns:
            Download speed in Mbps.
        """
        test_url = url or self.test_url
        start_time = time.perf_counter()

        try:
            response = requests.get(
                test_url,
                stream=True,
                timeout=self.timeout,
            )
            response.raise_for_status()

            total_bytes = 0

            for chunk in response.iter_content(chunk_size=1024 * 1024):
                total_bytes += len(chunk)

            elapsed_time = time.perf_counter() - start_time

            if elapsed_time > 0:
                speed_mbps = (total_bytes * 8) / elapsed_time / 1_000_000
                return round(speed_mbps, 2)

            return 0.0

        except Exception as ex:
            logger.debug(f"Download speed test failed: {ex}")
            return 0.0

    def measure_upload_speed(self, url: Optional[str] = None) -> float:
        """Measure upload speed via HTTP POST.

        Args:
            url: Upload endpoint URL.

        Returns:
            Upload speed in Mbps.
        """
        start_time = time.perf_counter()

        try:
            # Generate test data (1MB)
            test_data = b"x" * (1024 * 1024)

            response = requests.post(
                url or "https://httpbin.org/post",
                data=test_data,
                timeout=self.timeout,
            )
            response.raise_for_status()

            elapsed_time = time.perf_counter() - start_time

            if elapsed_time > 0:
                speed_mbps = (len(test_data) * 8) / elapsed_time / 1_000_000
                return round(speed_mbps, 2)

            return 0.0

        except Exception as ex:
            logger.debug(f"Upload speed test failed: {ex}")
            return 0.0

    def measure_dns_resolution(self, hostname: str = "google.com") -> Optional[float]:
        """Measure DNS resolution time.

        Args:
            hostname: Hostname to resolve.

        Returns:
            DNS resolution time in milliseconds.
        """
        try:
            import socket
            start_time = time.perf_counter()

            socket.gethostbyname(hostname)

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return round(elapsed_ms, 2)

        except Exception as ex:
            logger.debug(f"DNS resolution failed: {ex}")
            return None

    def measure_internet_speed(self) -> Dict[str, float]:
        """Measure complete internet speed profile.

        Returns:
            Dictionary with ping, download, upload, and DNS metrics.
        """
        result: Dict[str, float] = {}

        # Measure ping
        ping = self.measure_ping("8.8.8.8")
        result["ping_ms"] = ping if ping is not None else 0.0

        # Measure download speed
        result["download_mbps"] = self.measure_download_speed()

        # Measure upload speed
        result["upload_mbps"] = self.measure_upload_speed()

        # Measure DNS resolution
        dns_time = self.measure_dns_resolution()
        result["dns_ms"] = dns_time if dns_time is not None else 0.0

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
