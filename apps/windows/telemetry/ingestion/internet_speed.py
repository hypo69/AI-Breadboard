# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Internet Speed
# =============================================================================
# Description:
#   Сенсор телеметрии скорости интернета и задержки сети на базе FAST.com (Netflix CDN).
#   Выполняет периодический замер (1 раз в час / 3600 сек) и кеширует результаты.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.internet_speed import InternetSpeedSensor
#
#     sensor = InternetSpeedSensor()
#     metrics = sensor.measure_internet_speed()
#     print(metrics['download_mbps'], metrics['bufferbloat_ms'])
#
# File: internet_speed.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 07:35:00
# =============================================================================

from __future__ import annotations
"""Сенсор телеметрии скорости интернета и задержки сети на базе FAST.com."""

import asyncio
import threading
import time
from typing import Any, Dict, List, Optional

from logger import logger
from apps.windows.sdk.modules.network.speedtest import NetworkSpeedTester

_speed_cache: Optional[tuple[float, Dict[str, Any]]] = None
_CACHE_TTL = 3600  # 1 час между замерами скорости для снижения нагрузки на сеть
_cache_lock = threading.Lock()
_bg_test_running = False
_bg_lock = threading.Lock()


class InternetSpeedSensor:
    """Сенсор измерения скорости интернета и характеристик задержки (FAST.com)."""

    def __init__(self, cache_ttl: int = _CACHE_TTL) -> None:
        """Инициализация сенсора скорости интернета.

        Args:
            cache_ttl: Время жизни кеша замера в секундах (по умолчанию 3600 сек = 1 час).
        """
        self.cache_ttl = cache_ttl
        self._speedtester = NetworkSpeedTester()

    @classmethod
    def clear_cache(cls) -> None:
        """Очистить глобальный кеш замеров скорости интернета."""
        global _speed_cache
        with _cache_lock:
            _speed_cache = None

    def _run_speedtest_sync(self) -> Dict[str, Any]:
        """Синхронно выполнить полный цикл теста скорости FAST.com."""
        try:
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # Если вызывается внутри уже работающего цикла событий (например, в async worker)
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(lambda: asyncio.run(self._speedtester.run_full_speedtest()))
                    return future.result(timeout=60.0)
            else:
                return asyncio.run(self._speedtester.run_full_speedtest())
        except Exception as ex:
            logger.error(f'Ошибка выполнения теста скорости FAST.com в сенсоре телеметрии: {ex}')
            return {
                'download': {'speed_mbps': 0.0, 'status': 'ERROR'},
                'upload': {'speed_mbps': 0.0, 'status': 'ERROR'},
                'ping_ms': 0.0,
                'latency_unloaded_ms': 0.0,
                'latency_loaded_ms': 0.0,
                'bufferbloat_ms': 0.0,
                'meta': {'ip': 'N/A', 'isp': 'Unknown'},
                'provider': 'fast.com',
                'server': 'N/A'
            }

    def _perform_measurement_and_cache(self) -> Dict[str, Any]:
        """Выполняет замер скорости и сохраняет его в кэш."""
        global _speed_cache, _bg_test_running
        try:
            report = self._run_speedtest_sync()
            download_mbps = float(report.get('download', {}).get('speed_mbps', 0.0))
            upload_mbps = float(report.get('upload', {}).get('speed_mbps', 0.0))
            ping_ms = float(report.get('ping_ms', report.get('latency_unloaded_ms', 0.0)))
            latency_loaded_ms = float(report.get('latency_loaded_ms', 0.0))
            bufferbloat_ms = float(report.get('bufferbloat_ms', 0.0))
            meta = report.get('meta', {})

            result: Dict[str, Any] = {
                'available': report.get('download', {}).get('status') == 'SUCCESS' or download_mbps > 0.0,
                'download_mbps': download_mbps,
                'upload_mbps': upload_mbps,
                'ping_ms': ping_ms,
                'latency_unloaded_ms': float(report.get('latency_unloaded_ms', ping_ms)),
                'latency_loaded_ms': latency_loaded_ms,
                'bufferbloat_ms': bufferbloat_ms,
                'provider': 'fast.com',
                'server': report.get('server', 'FAST.com CDN'),
                'ip': meta.get('ip', 'N/A'),
                'isp': meta.get('isp', 'Unknown ISP'),
                'measured_at': time.time(),
            }

            with _cache_lock:
                _speed_cache = (time.monotonic(), result)

            logger.info(
                f'🌐 [Телеметрия FAST.com] Скорость: ↓{download_mbps:.1f} Mbps, '
                f'↑{upload_mbps:.1f} Mbps, пинг: {ping_ms:.1f} мс, bufferbloat: {bufferbloat_ms:.1f} мс'
            )
            return dict(result)
        finally:
            with _bg_lock:
                _bg_test_running = False

    def trigger_async_measure(self) -> None:
        """Запускает измерение скорости в фоновом потоке, если оно еще не выполняется."""
        global _bg_test_running
        with _bg_lock:
            if _bg_test_running:
                return
            _bg_test_running = True

        thread = threading.Thread(
            target=self._perform_measurement_and_cache,
            name="InternetSpeedTestWorker",
            daemon=True
        )
        thread.start()

    def measure_internet_speed(self, force_refresh: bool = False, sync: bool = False) -> Dict[str, Any]:
        """Измеряет профиль интернет-соединения через FAST.com с кешированием на 1 час.

        По умолчанию выполняется асинхронно в фоне и не блокирует вызывающий поток.

        Args:
            force_refresh: Принудительно инициировать новый замер.
            sync: Выполнить замер синхронно с блокировкой текущего потока.

        Returns:
            Dict[str, Any]: Словарь метрик (download_mbps, upload_mbps, ping_ms, bufferbloat_ms, etc.).
        """
        global _speed_cache
        with _cache_lock:
            if not force_refresh and _speed_cache is not None:
                cached_at, cached_result = _speed_cache
                if time.monotonic() - cached_at < self.cache_ttl:
                    return dict(cached_result)

        if sync:
            return self._perform_measurement_and_cache()

        # Асинхронный запуск замера в фоне
        self.trigger_async_measure()

        with _cache_lock:
            if _speed_cache is not None:
                _, cached_result = _speed_cache
                return dict(cached_result)

        # Возвращаем заглушку по умолчанию без блокировки потока
        return {
            'available': True,
            'download_mbps': 0.0,
            'upload_mbps': 0.0,
            'ping_ms': 0.0,
            'latency_unloaded_ms': 0.0,
            'latency_loaded_ms': 0.0,
            'bufferbloat_ms': 0.0,
            'provider': 'fast.com',
            'server': 'FAST.com CDN (замер в фоне...)',
            'ip': 'N/A',
            'isp': 'Unknown ISP',
            'measured_at': 0.0,
        }


def get_internet_speed_sensors() -> List[Dict[str, Any]]:
    """Получить показания сетевых метрик скорости в формате списка сенсоров.

    Returns:
        List[Dict[str, Any]]: Список метрик сенсоров интернета.
    """
    sensor = InternetSpeedSensor()
    metrics = sensor.measure_internet_speed()
    sensors = [
        {
            'sensor_id': 'internet_ping',
            'name': 'Internet Ping Latency',
            'category': 'network',
            'value': metrics.get('ping_ms', 0.0),
            'unit': 'ms'
        },
        {
            'sensor_id': 'internet_download',
            'name': 'Internet Download Speed',
            'category': 'network',
            'value': metrics.get('download_mbps', 0.0),
            'unit': 'Mbps'
        },
        {
            'sensor_id': 'internet_upload',
            'name': 'Internet Upload Speed',
            'category': 'network',
            'value': metrics.get('upload_mbps', 0.0),
            'unit': 'Mbps'
        },
        {
            'sensor_id': 'internet_bufferbloat',
            'name': 'Internet Bufferbloat',
            'category': 'network',
            'value': metrics.get('bufferbloat_ms', 0.0),
            'unit': 'ms'
        },
        {
            'sensor_id': 'internet_latency_loaded',
            'name': 'Internet Loaded Latency',
            'category': 'network',
            'value': metrics.get('latency_loaded_ms', 0.0),
            'unit': 'ms'
        },
    ]
    return sensors