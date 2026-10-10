# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Network - Speedtest
# =============================================================================
# Description:
#   Движок измерения скорости и качества интернет-соединения для Network Terminal.
#   Провайдер - FAST.com (Netflix CDN).
#   Измеряет download/upload Mbps, unloaded/loaded latency и bufferbloat.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.network.speedtest import NetworkSpeedTester
#
#     service = NetworkSpeedTester()
#     report = await service.run_full_speedtest()
#     print(report['record'])  # плоская запись для time-series / ai-diagnostics
#
# File: speedtest.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.network
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 04:55:00
# =============================================================================

from __future__ import annotations
"""Движок измерения скорости, задержки под нагрузкой и bufferbloat (FAST.com)."""

import asyncio
import re
import statistics
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from logger import logger
from apps.common.csv_logger import AppCsvLogger

_FAST_HOME = 'https://fast.com/'
_FAST_API = 'https://api.fast.com/netflix/speedtest/v2'
_UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Breadboard/NetworkTerminal'}
_CHUNK = b'0' * 65536
_GRADES = [
    {'grade': 'Отличное (Ultra Fast)', 'rating': 'A+', 'color': '#4ade80', 'summary': 'Идеально подходит для 4K-стриминга, онлайн-гейминга, быстрой работы AI-моделей и больших загрузок.'},
    {'grade': 'Хорошее (High Speed)', 'rating': 'A', 'color': '#38bdf8', 'summary': 'Отличная скорость для многозадачной работы, видеоконференций и передачи медиа.'},
    {'grade': 'Удовлетворительное (Standard)', 'rating': 'B', 'color': '#fbbf24', 'summary': 'Достаточно для просмотра веб-страниц, работы в облаке и стандартных задач.'},
    {'grade': 'Низкая скорость / Высокий пинг', 'rating': 'C', 'color': '#f87171', 'summary': 'Возможны задержки при передаче больших файлов и видеозвонках.'},
]


class NetworkSpeedTester:
    """Измеритель скорости, latency под нагрузкой и bufferbloat через FAST.com (Netflix CDN).

    Args:
        duration_s (float): Длительность фазы download и upload (сек).
        warmup_s (float): Прогрев TCP, исключаемый из расчёта скорости (сек).
        connections (int): Число параллельных соединений нагрузки.
        probe_interval_s (float): Интервал между latency-пробами (сек).
    """
    PING_TARGETS = [
        {'name': 'Cloudflare DNS', 'host': '1.1.1.1', 'url': 'https://1.1.1.1/cdn-cgi/trace'},
        {'name': 'Google Public DNS', 'host': '8.8.8.8', 'url': 'https://dns.google/resolve?name=example.com'},
        {'name': 'Quad9 DNS', 'host': '9.9.9.9', 'url': 'https://dns.quad9.net/dns-query?name=example.com'},
        {'name': 'OpenDNS', 'host': '208.67.222.222', 'url': 'https://doh.opendns.com/dns-query?name=example.com'}
    ]

    def __init__(self, duration_s: float = 8.0, warmup_s: float = 1.5, connections: int = 4, probe_interval_s: float = 0.2) -> None:
        """Инициализация тестера с CSV-логгером."""
        self._duration_s = duration_s
        self._warmup_s = min(warmup_s, duration_s / 2)
        self._connections = connections
        self._probe_interval_s = probe_interval_s
        self._csv_logger = AppCsvLogger('network_terminal')

    # ------------------------------------------------------------------ meta
    async def get_meta_info(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Получить информацию о внешнем IP, провайдере и локации клиента из FAST.com API.

        Args:
            client (httpx.AsyncClient): HTTP клиент.

        Returns:
            Dict[str, Any]: Метаданные соединения.
        """
        fast = await self.resolve_fast_target(client)
        if fast and fast.get('client'):
            loc = fast['client'].get('location') or {}
            return {
                'ip': fast['client'].get('ip', 'Local/Private'),
                'isp': fast['client'].get('isp', 'Unknown ISP'),
                'asn': fast['client'].get('asn', 'N/A'),
                'city': loc.get('city', ''),
                'country': loc.get('country', ''),
                'colo': '',
            }
        return {'ip': 'Local/Private', 'isp': 'Unknown', 'asn': 'N/A', 'city': '', 'country': '', 'colo': ''}

    async def measure_ping_servers(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Измерить задержку до ключевых глобальных серверов.

        Args:
            client (httpx.AsyncClient): HTTP клиент.

        Returns:
            List[Dict[str, Any]]: Результаты пинга серверов.
        """
        results: List[Dict[str, Any]] = []
        for target in self.PING_TARGETS:
            stats = await self._probe_latency(client, target['url'], count=3, interval_s=0.05, ok_codes=(200, 204, 400))
            online = stats['count'] > 0
            results.append({'name': target['name'], 'host': target['host'], 'avg_ms': stats['avg_ms'], 'min_ms': stats['min_ms'], 'max_ms': stats['max_ms'], 'jitter_ms': stats['jitter_ms'], 'status': 'Online' if online else 'Offline / Timeout'})
        return results

    # ------------------------------------------------------------ providers
    async def resolve_fast_target(self, client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
        """Получить токен FAST.com и список CDN-серверов Netflix.

        Args:
            client (httpx.AsyncClient): HTTP клиент.

        Returns:
            Optional[Dict[str, Any]]: Описание цели FAST.com (ключи ``down_url``,
            ``up_url``, ``latency_url``, ``name``, ``location``, ``client``, ``servers``)
            или ``None``, если FAST.com недоступен.
        """
        try:
            home = await client.get(_FAST_HOME, headers=_UA, timeout=8.0)
            script = re.search(r'src="(/app-[^"]+\.js)"', home.text)
            if not script:
                raise ValueError('скрипт fast.com не найден')
            js = await client.get(_FAST_HOME.rstrip('/') + script.group(1), headers=_UA, timeout=8.0)
            token = re.search(r'token:"([^"]+)"', js.text)
            if not token:
                raise ValueError('токен fast.com не найден')
            api = await client.get(_FAST_API, params={'https': 'true', 'token': token.group(1), 'urlCount': 5}, headers=_UA, timeout=8.0)
            api.raise_for_status()
            data = api.json()
            targets = data.get('targets') or []
            if not targets:
                raise ValueError('пустой список серверов FAST.com')
        except Exception as ex:
            logger.warning(f'FAST.com API недоступен: {ex}')
            return None
        servers = [self._fast_server_name(t) for t in targets]
        base = targets[0]['url']
        head, _, query = base.partition('?')
        return {
            'name': servers[0],
            'location': servers[0],
            'down_url': f'{head}/range/0-25000000?{query}',
            'up_url': base,
            'latency_url': f'{head}/range/0-0?{query}',
            'client': data.get('client') or {},
            'servers': servers,
        }

    @staticmethod
    def _fast_server_name(target: Dict[str, Any]) -> str:
        """Сформировать читаемое имя CDN-сервера FAST.com."""
        loc = target.get('location') or {}
        place = ', '.join(p for p in (loc.get('city'), loc.get('country')) if p)
        host = re.sub(r'^https?://([^/]+).*$', r'\1', target.get('url', ''))
        return f'{host} ({place})' if place else host

    # ------------------------------------------------------------- latency
    async def _probe_latency(self, client: httpx.AsyncClient, url: str, count: Optional[int] = None, stop: Optional[asyncio.Event] = None, interval_s: Optional[float] = None, ok_codes: tuple = (200, 204, 206)) -> Dict[str, Any]:
        """Измерить RTT серией коротких запросов по одному keep-alive соединению.

        Args:
            client (httpx.AsyncClient): Клиент (для честного замера - отдельный от нагрузки).
            url (str): URL короткого запроса.
            count (Optional[int]): Число проб; ``None`` - пока не установлен ``stop``.
            stop (Optional[asyncio.Event]): Событие остановки проб.
            interval_s (Optional[float]): Пауза между пробами.
            ok_codes (tuple): Допустимые HTTP-коды.

        Returns:
            Dict[str, Any]: ``count``, ``avg_ms``, ``median_ms``, ``min_ms``, ``max_ms``, ``jitter_ms``.
        """
        pause = self._probe_interval_s if interval_s is None else interval_s
        samples: List[float] = []
        warmed = False
        attempts = 0
        max_attempts = None if count is None else count * 3 + 1
        while (count is None or len(samples) < count) and not (stop and stop.is_set()):
            if max_attempts is not None and attempts >= max_attempts:
                break
            attempts += 1
            try:
                t0 = time.perf_counter()
                resp = await client.get(url, timeout=5.0)
                elapsed = (time.perf_counter() - t0) * 1000.0
                if resp.status_code in ok_codes and warmed:
                    samples.append(elapsed)
                warmed = True  # первый запрос - установка TCP/TLS, не учитывается
            except Exception:
                pass
            await asyncio.sleep(pause)
        return self._latency_stats(samples)

    @staticmethod
    def _latency_stats(samples: List[float]) -> Dict[str, Any]:
        """Посчитать статистику по выборке RTT (мс)."""
        if not samples:
            return {'count': 0, 'avg_ms': 0.0, 'median_ms': 0.0, 'min_ms': 0.0, 'max_ms': 0.0, 'jitter_ms': 0.0}
        diffs = [abs(a - b) for a, b in zip(samples[1:], samples)]
        return {'count': len(samples), 'avg_ms': round(statistics.mean(samples), 1), 'median_ms': round(statistics.median(samples), 1), 'min_ms': round(min(samples), 1), 'max_ms': round(max(samples), 1), 'jitter_ms': round(statistics.mean(diffs), 1) if diffs else 0.0}

    # ---------------------------------------------------------------- load
    async def _run_load(self, target: Dict[str, Any], direction: str) -> Dict[str, Any]:
        """Выполнить фазу нагрузки (download/upload) с параллельным замером latency.

        Args:
            target (Dict[str, Any]): Цель измерения (URL провайдера FAST.com).
            direction (str): ``'download'`` или ``'upload'``.

        Returns:
            Dict[str, Any]: Скорость, объём, длительность и статистика loaded latency.
        """
        counter = [0]
        started = time.perf_counter()
        marks: Dict[str, float] = {}
        stop = asyncio.Event()
        limits = httpx.Limits(max_connections=self._connections + 2)
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, limits=limits, headers=_UA) as load_client, \
                httpx.AsyncClient(timeout=10.0, follow_redirects=True, limits=httpx.Limits(max_connections=1), headers=_UA) as probe_client:
            # Прогрев соединения проб ДО начала нагрузки (чтобы не мерить TCP/TLS handshake)
            await probe_client.get(target['latency_url'], timeout=5.0)
            worker = self._download_worker if direction == 'download' else self._upload_worker
            tasks = [asyncio.create_task(worker(load_client, target, counter)) for _ in range(self._connections)]
            probe = asyncio.create_task(self._probe_latency(probe_client, target['latency_url'], stop=stop))
            await asyncio.sleep(self._warmup_s)
            marks['bytes'], marks['t'] = counter[0], time.perf_counter()
            await asyncio.sleep(self._duration_s - self._warmup_s)
            total, now = counter[0], time.perf_counter()
            stop.set()
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            latency = await probe
        window = max(now - marks['t'], 0.001)
        payload = max(total - marks['bytes'], 0)
        mbps = round(payload * 8 / window / 1e6, 2)
        key = 'bytes_downloaded' if direction == 'download' else 'bytes_uploaded'
        status = 'SUCCESS' if total > 0 else 'ERROR'
        return {'speed_mbps': mbps, 'speed_mb_s': round(mbps / 8, 2), 'duration_s': round(now - started, 2), key: total, 'status': status, 'loaded_latency': latency}

    @staticmethod
    async def _download_worker(client: httpx.AsyncClient, target: Dict[str, Any], counter: List[int]) -> None:
        """Непрерывно скачивать данные, накапливая счётчик байт."""
        while True:
            try:
                async with client.stream('GET', target['down_url']) as resp:
                    if resp.status_code not in (200, 206):
                        await asyncio.sleep(0.5)
                        continue
                    async for chunk in resp.aiter_bytes(65536):
                        counter[0] += len(chunk)
            except asyncio.CancelledError:
                raise
            except Exception as ex:
                logger.debug(f'Ошибка download-воркера FAST.com: {ex}')
                await asyncio.sleep(0.5)

    @staticmethod
    async def _upload_worker(client: httpx.AsyncClient, target: Dict[str, Any], counter: List[int]) -> None:
        """Непрерывно отправлять данные, накапливая счётчик отправленных байт."""
        size = 8 * 1024 * 1024

        async def body():
            for _ in range(size // len(_CHUNK)):
                counter[0] += len(_CHUNK)
                yield _CHUNK

        while True:
            try:
                await client.post(target['up_url'], content=body(), headers={'Content-Length': str(size)})
            except asyncio.CancelledError:
                raise
            except Exception as ex:
                logger.debug(f'Ошибка upload-воркера FAST.com: {ex}')
                await asyncio.sleep(0.5)

    # -------------------------------------------------------------- quality
    def _evaluate_quality(self, download_mbps: float, upload_mbps: float, ping_ms: float, bufferbloat_ms: float = 0.0) -> Dict[str, str]:
        """Оценить качество соединения с учётом bufferbloat.

        Bufferbloat >= 50 мс ограничивает оценку уровнем B, >= 150 мс - уровнем C.
        """
        if download_mbps >= 100.0 and ping_ms <= 40.0:
            idx = 0
        elif download_mbps >= 50.0 and ping_ms <= 70.0:
            idx = 1
        elif download_mbps >= 15.0 and ping_ms <= 120.0:
            idx = 2
        else:
            idx = 3
        if bufferbloat_ms >= 150.0:
            idx = 3
        elif bufferbloat_ms >= 50.0:
            idx = max(idx, 2)
        result = dict(_GRADES[idx])
        if bufferbloat_ms >= 50.0:
            result['summary'] += f' Внимание: bufferbloat {bufferbloat_ms:.0f} мс - задержка резко растёт под нагрузкой (очереди роутера/ISP).'
        return result

    # ----------------------------------------------------------------- main
    async def run_full_speedtest(self) -> Dict[str, Any]:
        """Запустить полный цикл тестирования через FAST.com: meta, ping, latency, download, upload.

        Returns:
            Dict[str, Any]: Сводный отчёт о замере скорости и сетевых задержках.
        """
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            fast = await self.resolve_fast_target(client)
            if not fast:
                logger.warning('Не удалось подключиться к серверам FAST.com (Netflix CDN).')
                report = {
                    'timestamp': time.time(),
                    'provider': 'fast.com',
                    'server': 'N/A',
                    'cdn_servers': [],
                    'meta': {'ip': 'N/A', 'isp': 'Unknown', 'asn': 'N/A', 'city': '', 'country': '', 'colo': ''},
                    'ping_ms': 0.0,
                    'jitter_ms': 0.0,
                    'latency_unloaded_ms': 0.0,
                    'latency_loaded_ms': 0.0,
                    'bufferbloat_ms': 0.0,
                    'latency': {
                        'unloaded': {'count': 0, 'avg_ms': 0.0, 'median_ms': 0.0, 'min_ms': 0.0, 'max_ms': 0.0, 'jitter_ms': 0.0},
                        'loaded_download': {'count': 0, 'avg_ms': 0.0, 'median_ms': 0.0, 'min_ms': 0.0, 'max_ms': 0.0, 'jitter_ms': 0.0},
                        'loaded_upload': {'count': 0, 'avg_ms': 0.0, 'median_ms': 0.0, 'min_ms': 0.0, 'max_ms': 0.0, 'jitter_ms': 0.0},
                        'bufferbloat_download_ms': 0.0,
                        'bufferbloat_upload_ms': 0.0
                    },
                    'download': {'speed_mbps': 0.0, 'speed_mb_s': 0.0, 'duration_s': 0.0, 'bytes_downloaded': 0, 'status': 'ERROR'},
                    'upload': {'speed_mbps': 0.0, 'speed_mb_s': 0.0, 'duration_s': 0.0, 'bytes_uploaded': 0, 'status': 'ERROR'},
                    'servers': [],
                    'quality': {'grade': 'Ошибка тестирования', 'rating': 'F', 'color': '#ef4444', 'summary': 'FAST.com недоступен или отсутствует сетевое подключение.'},
                    'record': {
                        'timestamp': datetime.now().astimezone().isoformat(timespec='seconds'),
                        'provider': 'fast.com',
                        'server': 'N/A',
                        'client_ip': 'N/A',
                        'download_mbps': 0.0,
                        'upload_mbps': 0.0,
                        'latency_unloaded_ms': 0.0,
                        'latency_loaded_ms': 0.0,
                        'bufferbloat_ms': 0.0
                    }
                }
                self._csv_logger.log_poll(
                    poll_type='speedtest',
                    metric_name='download_mbps',
                    value=0.0,
                    unit='Mbps',
                    status='ERROR',
                    details={'provider': 'fast.com', 'error': 'FAST.com unavailable'},
                    filename='network_terminal_speedtests.csv'
                )
                return report

            target = fast
            provider = 'fast.com'
            loc = fast['client'].get('location') or {} if fast.get('client') else {}
            meta = {
                'ip': fast['client'].get('ip', 'N/A') if fast.get('client') else 'N/A',
                'isp': fast['client'].get('isp', 'Unknown ISP') if fast.get('client') else 'Unknown ISP',
                'asn': fast['client'].get('asn', 'N/A') if fast.get('client') else 'N/A',
                'city': loc.get('city', ''),
                'country': loc.get('country', ''),
                'colo': '',
            }
            servers = await self.measure_ping_servers(client)

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, limits=httpx.Limits(max_connections=1), headers=_UA) as probe_client:
            unloaded = await self._probe_latency(probe_client, target['latency_url'], count=11, interval_s=0.1)

        download = await self._run_load(target, 'download')
        upload = await self._run_load(target, 'upload')

        loaded_down = download.pop('loaded_latency')
        loaded_up = upload.pop('loaded_latency')
        loaded_ms = max(loaded_down['median_ms'], loaded_up['median_ms'])
        unloaded_ms = unloaded['median_ms']
        have_latency = unloaded['count'] > 0 and loaded_ms > 0
        bufferbloat_ms = round(max(loaded_ms - unloaded_ms, 0.0), 1) if have_latency else 0.0

        valid = [s for s in servers if s['avg_ms'] > 0]
        ping_ms = unloaded_ms if unloaded['count'] else (round(statistics.mean(s['avg_ms'] for s in valid), 1) if valid else 0.0)
        jitter_ms = unloaded['jitter_ms'] if unloaded['count'] else (round(statistics.mean(s['jitter_ms'] for s in valid), 1) if valid else 0.0)
        quality = self._evaluate_quality(download['speed_mbps'], upload['speed_mbps'], ping_ms, bufferbloat_ms)

        latency = {
            'unloaded': unloaded,
            'loaded_download': loaded_down,
            'loaded_upload': loaded_up,
            'bufferbloat_download_ms': round(max(loaded_down['median_ms'] - unloaded_ms, 0.0), 1) if loaded_down['count'] and unloaded['count'] else 0.0,
            'bufferbloat_upload_ms': round(max(loaded_up['median_ms'] - unloaded_ms, 0.0), 1) if loaded_up['count'] and unloaded['count'] else 0.0
        }
        record = {
            'timestamp': datetime.now().astimezone().isoformat(timespec='seconds'),
            'provider': provider,
            'server': target['name'],
            'client_ip': meta.get('ip'),
            'download_mbps': download['speed_mbps'],
            'upload_mbps': upload['speed_mbps'],
            'latency_unloaded_ms': unloaded_ms,
            'latency_loaded_ms': loaded_ms,
            'bufferbloat_ms': bufferbloat_ms
        }
        report = {
            'timestamp': time.time(),
            'provider': provider,
            'server': target['name'],
            'cdn_servers': target.get('servers', []),
            'meta': meta,
            'ping_ms': ping_ms,
            'jitter_ms': jitter_ms,
            'latency_unloaded_ms': unloaded_ms,
            'latency_loaded_ms': loaded_ms,
            'bufferbloat_ms': bufferbloat_ms,
            'latency': latency,
            'download': download,
            'upload': upload,
            'servers': servers,
            'quality': quality,
            'record': record
        }
        self._csv_logger.log_poll(
            poll_type='speedtest',
            metric_name='download_mbps',
            value=download['speed_mbps'],
            unit='Mbps',
            status=download['status'],
            details={
                'provider': provider,
                'server': target['name'],
                'upload_mbps': upload['speed_mbps'],
                'latency_unloaded_ms': unloaded_ms,
                'latency_loaded_ms': loaded_ms,
                'bufferbloat_ms': bufferbloat_ms,
                'isp': meta.get('isp'),
                'ip': meta.get('ip')
            },
            filename='network_terminal_speedtests.csv'
        )
        return report