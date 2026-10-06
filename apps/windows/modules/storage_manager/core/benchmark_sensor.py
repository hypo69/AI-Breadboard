# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Storage_Manager Core - Benchmark Sensor
# =============================================================================
# Description:
#   Сенсор телеметрии производительности дисковой подсистемы.
#   Выполняет экспресс-тестирование скорости чтения/записи всех накопителей (DiskSpd),
#   формирует структурированные метрики и сохраняет их в хранилище телеметрии.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.storage_manager.core.benchmark_sensor import StorageBenchmarkSensor
#
#     sensor = StorageBenchmarkSensor()
#     results = sensor.run_quick_benchmark(file_size_mb=16, duration_sec=1)
#
# File: benchmark_sensor.py
# Project: ai-breadboard
# Package: apps.windows.modules.storage_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 02:20:00
# =============================================================================

from __future__ import annotations
"""Сенсор телеметрии производительности дисковой подсистемы на базе DiskSpd."""

import asyncio
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

from header import __root__
from logger import logger
from apps.windows.modules.storage_manager.core.benchmark import StorageBenchmarkService
from apps.windows.modules.storage_manager.core.models import BenchmarkRequest


class StorageBenchmarkSensor:
    """Сенсор телеметрии для экспресс-замеров производительности дисков."""

    def __init__(
        self,
        benchmark_service: Optional[StorageBenchmarkService] = None,
    ) -> None:
        """Инициализация сенсора бенчмарка дисков.

        Args:
            benchmark_service: Экземпляр сервиса DiskSpd.
        """
        self.benchmark_service = benchmark_service or StorageBenchmarkService()
        self._last_results: Dict[str, Any] = {}
        self._last_poll_time: Optional[str] = None

    def run_quick_benchmark(
        self,
        target_drives: Optional[List[str]] = None,
        file_size_mb: int = 16,
        duration_sec: int = 1,
        test_type: str = 'both',
    ) -> Dict[str, Any]:
        """Выполняет быстрый экспресс-бенчмарк всех доступных накопителей.

        Args:
            target_drives: Список букв дисков (например ['C:', 'D:']). Если None, опрашиваются все.
            file_size_mb: Размер тестового файла в МБ (по умолчанию 16 МБ для максимальной скорости).
            duration_sec: Длительность замера каждого профиля в секундах (по умолчанию 1 сек).
            test_type: Режим тестирования ('both', 'read', 'write').

        Returns:
            Dict[str, Any]: Сводка по всем протестированным накопителям и зафиксированным метрикам.
        """
        t0 = time.perf_counter()
        now_iso = datetime.now(timezone.utc).isoformat()
        self._last_poll_time = now_iso

        # 1. Определение списка накопителей
        available_targets = self.benchmark_service.get_available_targets()
        drives_to_test: List[str] = []

        if target_drives:
            norm_drives = [d.upper().strip().rstrip('\\') for d in target_drives]
            for t in available_targets:
                if t.drive_letter.upper() in norm_drives:
                    drives_to_test.append(t.drive_letter)
        else:
            # Все накопители с достаточным свободным местом (> 200 МБ)
            for t in available_targets:
                if t.free_bytes > 200 * 1024 * 1024:
                    drives_to_test.append(t.drive_letter)

        if not drives_to_test:
            drives_to_test = ['C:']

        logger.info(
            f'[StorageBenchmarkSensor] Старт экспресс-бенчмарка дисков: {drives_to_test} '
            f'({file_size_mb} MB, {duration_sec}s)'
        )

        results_by_drive: Dict[str, Dict[str, Any]] = {}
        sensor_poll_items: List[Dict[str, Any]] = []

        # 2. Выполнение тестирования для каждого накопителя
        for drive in drives_to_test:
            try:
                # Запускаем экспресс-набор: SEQ1M Q8T1 и RND4K Q32T16
                req = BenchmarkRequest(
                    target_drive=drive,
                    file_size_mb=file_size_mb,
                    duration_sec=duration_sec,
                    test_type=test_type,
                    profiles=['seq1m_q8t1', 'rnd4k_q32t16'],
                    disable_cache=True,
                    delete_test_file=True,
                )

                suite = self.benchmark_service.run_suite(req)
                
                seq_res = suite.profiles.get('seq1m_q8t1')
                rnd_res = suite.profiles.get('rnd4k_q32t16')

                read_mb_s = seq_res.read_mb_s if seq_res else 0.0
                write_mb_s = seq_res.write_mb_s if seq_res else 0.0
                rnd_read_iops = rnd_res.read_iops if rnd_res else 0.0
                rnd_write_iops = rnd_res.write_iops if rnd_res else 0.0
                latency_us = seq_res.avg_latency_us if seq_res else (rnd_res.avg_latency_us if rnd_res else 0.0)

                drive_data = {
                    'drive': drive,
                    'status': 'ok',
                    'seq_read_mb_s': read_mb_s,
                    'seq_write_mb_s': write_mb_s,
                    'rnd_read_iops': rnd_read_iops,
                    'rnd_write_iops': rnd_write_iops,
                    'latency_us': latency_us,
                    'duration_sec': suite.total_duration_sec,
                }
                results_by_drive[drive] = drive_data

                clean_letter = drive.replace(':', '').replace('\\', '').upper()

                # Формируем метрики для телеметрии
                sensor_poll_items.extend([
                    {
                        'id': f'disk_speed_seq_read_{clean_letter}',
                        'sensor_name': f'Скорость чтения {drive}',
                        'sensor_category': 'Storage Speed',
                        'hardware_name': f'Диск {clean_letter}:',
                        'hardware_type': 'storage',
                        'value': read_mb_s,
                        'unit': 'MB/s',
                        '_provider': 'WINDOWS_STORAGE',
                    },
                    {
                        'id': f'disk_speed_seq_write_{clean_letter}',
                        'sensor_name': f'Скорость записи {drive}',
                        'sensor_category': 'Storage Speed',
                        'hardware_name': f'Диск {clean_letter}:',
                        'hardware_type': 'storage',
                        'value': write_mb_s,
                        'unit': 'MB/s',
                        '_provider': 'WINDOWS_STORAGE',
                    },
                    {
                        'id': f'disk_speed_rnd_read_iops_{clean_letter}',
                        'sensor_name': f'Случайное чтение IOPS {drive}',
                        'sensor_category': 'Storage IOPS',
                        'hardware_name': f'Диск {clean_letter}:',
                        'hardware_type': 'storage',
                        'value': rnd_read_iops,
                        'unit': 'IOPS',
                        '_provider': 'WINDOWS_STORAGE',
                    },
                    {
                        'id': f'disk_speed_latency_{clean_letter}',
                        'sensor_name': f'Латентность доступа {drive}',
                        'sensor_category': 'Storage Latency',
                        'hardware_name': f'Диск {clean_letter}:',
                        'hardware_type': 'storage',
                        'value': latency_us,
                        'unit': 'µs',
                        '_provider': 'WINDOWS_STORAGE',
                    },
                ])

            except Exception as exc:
                logger.warning(f'[StorageBenchmarkSensor] Ошибка бенчмарка для диска {drive}: {exc}')
                results_by_drive[drive] = {
                    'drive': drive,
                    'status': 'error',
                    'error': str(exc),
                }

        total_elapsed = round(time.perf_counter() - t0, 2)
        summary_lines = []
        for d, res in results_by_drive.items():
            if res.get('status') == 'ok':
                summary_lines.append(
                    f"{d} (Seq: {res['seq_read_mb_s']:.0f} R / {res['seq_write_mb_s']:.0f} W MB/s, "
                    f"Rnd: {res['rnd_read_iops']:.0f} IOPS)"
                )
            else:
                summary_lines.append(f"{d} [Ошибка: {res.get('error')}]")

        summary_text = ' | '.join(summary_lines) if summary_lines else 'Накопители не протестированы'

        final_report = {
            'timestamp': now_iso,
            'drives_count': len(results_by_drive),
            'drives_tested': list(results_by_drive.keys()),
            'results': results_by_drive,
            'metrics': sensor_poll_items,
            'summary': summary_text,
            'total_duration_sec': total_elapsed,
        }

        self._last_results = final_report
        logger.info(f'[StorageBenchmarkSensor] Экспресс-бенчмарк завершен за {total_elapsed}с: {summary_text}')
        return final_report

    def get_last_results(self) -> Dict[str, Any]:
        """Возвращает результаты последнего опроса сенсора."""
        return self._last_results


# Глобальный синглтон сенсора
_global_sensor: Optional[StorageBenchmarkSensor] = None


def get_storage_benchmark_sensor() -> StorageBenchmarkSensor:
    """Возвращает глобальный экземпляр сенсора телеметрии бенчмарка дисков."""
    global _global_sensor
    if _global_sensor is None:
        _global_sensor = StorageBenchmarkSensor()
    return _global_sensor


def run_quick_storage_benchmark(
    target_drives: Optional[List[str]] = None,
    file_size_mb: int = 16,
    duration_sec: int = 1,
) -> Dict[str, Any]:
    """Удобная функция-хелпер для быстрого запуска бенчмарка накопителей."""
    sensor = get_storage_benchmark_sensor()
    return sensor.run_quick_benchmark(
        target_drives=target_drives,
        file_size_mb=file_size_mb,
        duration_sec=duration_sec,
    )


__all__ = [
    'StorageBenchmarkSensor',
    'get_storage_benchmark_sensor',
    'run_quick_storage_benchmark',
]
