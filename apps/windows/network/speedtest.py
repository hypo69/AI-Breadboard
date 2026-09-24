# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Windows Internet Speed & Latency Benchmark Engine
# =============================================================================
# Description:
#   Модуль для измерения скорости интернет-соединения:
#   Ping, Jitter, Download Speed (Mbps), Upload Speed (Mbps),
#   задержка к глобальным DNS/CDN серверам, определение внешнего IP и провайдера.
#
# Examples:
#   >>> from apps.windows.network.speedtest import NetworkSpeedTester
#   >>> tester = NetworkSpeedTester()
#   >>> result = await tester.run_full_speedtest()
#
# File: speedtest.py
# Project: ai-breadboard
# Package: apps.windows.network
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Движок анализа и тестирования скорости интернета для Network Terminal."""

from __future__ import annotations

import asyncio
import statistics
import time
from typing import Any, Dict, List, Optional

import httpx

from logger import logger
from apps.common.csv_logger import AppCsvLogger


class NetworkSpeedTester:
    """Измеритель скорости и качества интернет-соединения."""

    PING_TARGETS = [
        {"name": "Cloudflare DNS", "host": "1.1.1.1", "url": "https://1.1.1.1/cdn-cgi/trace"},
        {"name": "Google Public DNS", "host": "8.8.8.8", "url": "https://dns.google/resolve?name=example.com"},
        {"name": "Quad9 DNS", "host": "9.9.9.9", "url": "https://dns.quad9.net/dns-query?name=example.com"},
        {"name": "OpenDNS", "host": "208.67.222.222", "url": "https://doh.opendns.com/dns-query?name=example.com"},
    ]

    DOWNLOAD_URLS = [
        "https://speed.cloudflare.com/__down?bytes=10000000",  # 10 MB
        "https://speed.cloudflare.com/__down?bytes=5000000",   # 5 MB fallback
    ]

    UPLOAD_URL = "https://speed.cloudflare.com/__up"

    def __init__(self) -> None:
        """Инициализация тестера с CSV-логгером."""
        self._csv_logger = AppCsvLogger("network_terminal")

    async def get_meta_info(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Получить информацию о внешнем IP, локации и CDN-узле.

        Args:
            client (httpx.AsyncClient): HTTP клиент.

        Returns:
            Dict[str, Any]: Метаданные соединения.
        """
        try:
            resp = await client.get("https://speed.cloudflare.com/meta", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "ip": data.get("clientIp", "N/A"),
                    "isp": data.get("asOrganization", data.get("isp", "Unknown ISP")),
                    "asn": data.get("asn", "N/A"),
                    "city": data.get("city", ""),
                    "country": data.get("country", ""),
                    "colo": data.get("colo", ""),
                }
        except Exception as ex:
            logger.debug(f"Speedtest meta info probe failed: {ex}")

        # Fallback trace
        try:
            resp = await client.get("https://1.1.1.1/cdn-cgi/trace", timeout=4.0)
            if resp.status_code == 200:
                lines = dict(line.split("=", 1) for line in resp.text.strip().splitlines() if "=" in line)
                return {
                    "ip": lines.get("ip", "N/A"),
                    "isp": "Cloudflare Edge",
                    "asn": "N/A",
                    "city": lines.get("loc", ""),
                    "country": lines.get("loc", ""),
                    "colo": lines.get("colo", ""),
                }
        except Exception:
            pass

        return {"ip": "Local/Private", "isp": "Unknown", "city": "", "country": "", "colo": ""}

    async def measure_ping_servers(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Измерить задержку (Ping) до ключевых глобальных серверов.

        Args:
            client (httpx.AsyncClient): HTTP клиент.

        Returns:
            List[Dict[str, Any]]: Результаты пинга серверов.
        """
        results: List[Dict[str, Any]] = []

        for target in self.PING_TARGETS:
            latencies: List[float] = []
            for _ in range(3):
                try:
                    t0 = time.perf_counter()
                    resp = await client.get(target["url"], timeout=3.5)
                    if resp.status_code in (200, 204, 400):
                        elapsed = (time.perf_counter() - t0) * 1000.0
                        latencies.append(round(elapsed, 1))
                except Exception:
                    pass
                await asyncio.sleep(0.05)

            if latencies:
                avg_lat = round(statistics.mean(latencies), 1)
                min_lat = min(latencies)
                max_lat = max(latencies)
                jitter = round(max_lat - min_lat, 1)
                results.append({
                    "name": target["name"],
                    "host": target["host"],
                    "avg_ms": avg_lat,
                    "min_ms": min_lat,
                    "max_ms": max_lat,
                    "jitter_ms": jitter,
                    "status": "Online",
                })
            else:
                results.append({
                    "name": target["name"],
                    "host": target["host"],
                    "avg_ms": 0.0,
                    "min_ms": 0.0,
                    "max_ms": 0.0,
                    "jitter_ms": 0.0,
                    "status": "Offline / Timeout",
                })

        return results

    async def measure_download(self, client: httpx.AsyncClient, bytes_count: int = 10_000_000) -> Dict[str, Any]:
        """Измерить скорость скачивания (Download Speed).

        Args:
            client (httpx.AsyncClient): HTTP клиент.
            bytes_count (int): Размер тестовой нагрузки в байтах (по умолчанию 10 MB).

        Returns:
            Dict[str, Any]: Результаты теста входящей скорости.
        """
        download_url = f"https://speed.cloudflare.com/__down?bytes={bytes_count}"
        t0 = time.perf_counter()
        
        try:
            resp = await client.get(download_url, timeout=20.0)
            if resp.status_code == 200:
                elapsed = max(time.perf_counter() - t0, 0.001)
                content_len = len(resp.content)
                mbps = round((content_len * 8 / elapsed) / 1_000_000, 2)
                mb_s = round((content_len / elapsed) / 1_000_000, 2)
                return {
                    "speed_mbps": mbps,
                    "speed_mb_s": mb_s,
                    "duration_s": round(elapsed, 2),
                    "bytes_downloaded": content_len,
                    "status": "SUCCESS",
                }
        except Exception as ex:
            logger.warning(f"Download speedtest error: {ex}")

        return {
            "speed_mbps": 0.0,
            "speed_mb_s": 0.0,
            "duration_s": 0.0,
            "bytes_downloaded": 0,
            "status": "ERROR",
        }

    async def measure_upload(self, client: httpx.AsyncClient, bytes_count: int = 3_000_000) -> Dict[str, Any]:
        """Измерить скорость отдачи (Upload Speed).

        Args:
            client (httpx.AsyncClient): HTTP клиент.
            bytes_count (int): Размер тестовой нагрузки в байтах (по умолчанию 3 MB).

        Returns:
            Dict[str, Any]: Результаты теста исходящей скорости.
        """
        payload = b"0" * bytes_count
        t0 = time.perf_counter()

        try:
            resp = await client.post(self.UPLOAD_URL, content=payload, timeout=20.0)
            if resp.status_code in (200, 204):
                elapsed = max(time.perf_counter() - t0, 0.001)
                mbps = round((len(payload) * 8 / elapsed) / 1_000_000, 2)
                mb_s = round((len(payload) / elapsed) / 1_000_000, 2)
                return {
                    "speed_mbps": mbps,
                    "speed_mb_s": mb_s,
                    "duration_s": round(elapsed, 2),
                    "bytes_uploaded": len(payload),
                    "status": "SUCCESS",
                }
        except Exception as ex:
            logger.warning(f"Upload speedtest error: {ex}")

        return {
            "speed_mbps": 0.0,
            "speed_mb_s": 0.0,
            "duration_s": 0.0,
            "bytes_uploaded": 0,
            "status": "ERROR",
        }

    def _evaluate_quality(self, download_mbps: float, upload_mbps: float, ping_ms: float) -> Dict[str, str]:
        """Оценить общее качество интернет-соединения."""
        if download_mbps >= 100.0 and ping_ms <= 40.0:
            return {
                "grade": "Отличное (Ultra Fast)",
                "rating": "A+",
                "color": "#4ade80",
                "summary": "Идеально подходит для 4K-стриминга, онлайн-гейминга, быстрой работы AI-моделей и больших загрузок.",
            }
        elif download_mbps >= 50.0 and ping_ms <= 70.0:
            return {
                "grade": "Хорошее (High Speed)",
                "rating": "A",
                "color": "#38bdf8",
                "summary": "Отличная скорость для многозадачной работы, видеоконференций и передачи медиа.",
            }
        elif download_mbps >= 15.0 and ping_ms <= 120.0:
            return {
                "grade": "Удовлетворительное (Standard)",
                "rating": "B",
                "color": "#fbbf24",
                "summary": "Достаточно для просмотра веб-страниц, работы в облаке и стандартных задач.",
            }
        else:
            return {
                "grade": "Низкая скорость / Высокий пинг",
                "rating": "C",
                "color": "#f87171",
                "summary": "Возможны задержки при передаче больших файлов и видеозвонках.",
            }

    async def run_full_speedtest(self) -> Dict[str, Any]:
        """Запустить полный цикл тестирования интернета (Meta, Ping, Download, Upload).

        Returns:
            Dict[str, Any]: Полный сводный отчет скорости и задержки.
        """
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            # 1. Meta info
            meta = await self.get_meta_info(client)

            # 2. Server latency / Ping
            servers = await self.measure_ping_servers(client)
            valid_pings = [s["avg_ms"] for s in servers if s["avg_ms"] > 0]
            avg_ping = round(statistics.mean(valid_pings), 1) if valid_pings else 0.0
            avg_jitter = round(statistics.mean([s["jitter_ms"] for s in servers if s["avg_ms"] > 0]), 1) if valid_pings else 0.0

            # 3. Download test
            download_result = await self.measure_download(client, bytes_count=10_000_000)

            # 4. Upload test
            upload_result = await self.measure_upload(client, bytes_count=3_000_000)

            # 5. Quality rating
            quality = self._evaluate_quality(
                download_mbps=download_result["speed_mbps"],
                upload_mbps=upload_result["speed_mbps"],
                ping_ms=avg_ping,
            )

            report = {
                "timestamp": time.time(),
                "meta": meta,
                "ping_ms": avg_ping,
                "jitter_ms": avg_jitter,
                "download": download_result,
                "upload": upload_result,
                "servers": servers,
                "quality": quality,
            }

            self._csv_logger.log_poll(
                poll_type="speedtest",
                metric_name="download_mbps",
                value=download_result["speed_mbps"],
                unit="Mbps",
                status=download_result["status"],
                details={
                    "upload_mbps": upload_result["speed_mbps"],
                    "ping_ms": avg_ping,
                    "isp": meta.get("isp"),
                    "ip": meta.get("ip"),
                },
                filename="network_terminal_speedtests.csv",
            )

            return report
