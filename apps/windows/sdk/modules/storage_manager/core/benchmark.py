# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Storage_Manager Core - Benchmark
# =============================================================================
# Description:
#   Сервис тестирования производительности дисковой подсистемы с использованием Microsoft DiskSpd.
#   Выполняет последовательное и случайное тестирование чтения/записи (аналог CrystalDiskMark),
#   безопасно управляет тестовыми файлами и сохраняет историю в SQLite.
#
# Usage Examples:
#   Python API:
#     from apps.windows.sdk.modules.storage_manager.core.benchmark import StorageBenchmarkService
#     from apps.windows.sdk.modules.storage_manager.core.models import BenchmarkRequest
#
#     service = StorageBenchmarkService()
#     res = service.run_suite(BenchmarkRequest(target_drive='C:', duration_sec=3))
#
# File: benchmark.py
# Project: ai-breadboard
# Package: apps.windows.sdk.modules.storage_manager.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 08:16:00
# =============================================================================

from __future__ import annotations
"""Сервис тестирования производительности дисковой подсистемы с использованием Microsoft DiskSpd."""

import asyncio
import io
import json
import os
import shutil
import sqlite3
import subprocess
import time
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import psutil

from header import __root__
from logger import logger
from apps.windows.sdk.modules.storage_manager.core.models import (
    BenchmarkHistoryItem,
    BenchmarkProfileResult,
    BenchmarkRequest,
    BenchmarkSuiteResult,
    BenchmarkTargetInfo,
    StorageTaskStatus,
)

# Профили по умолчанию (CrystalDiskMark)
DEFAULT_CDM_PROFILES: Dict[str, Dict[str, Any]] = {
    'seq1m_q8t1': {
        'label': 'SEQ1M Q8T1',
        'block_size': '1M',
        'access_type': 'Sequential',
        'queue_depth': 8,
        'threads': 1,
        'args': ['-b1M', '-o8', '-t1'],
    },
    'seq1m_q1t1': {
        'label': 'SEQ1M Q1T1',
        'block_size': '1M',
        'access_type': 'Sequential',
        'queue_depth': 1,
        'threads': 1,
        'args': ['-b1M', '-o1', '-t1'],
    },
    'rnd4k_q32t16': {
        'label': 'RND4K Q32T16',
        'block_size': '4K',
        'access_type': 'Random',
        'queue_depth': 32,
        'threads': 1,  # В облегченном режиме 1 поток для стабильности I/O
        'args': ['-b4K', '-o32', '-t1', '-r'],
    },
    'rnd4k_q1t1': {
        'label': 'RND4K Q1T1',
        'block_size': '4K',
        'access_type': 'Random',
        'queue_depth': 1,
        'threads': 1,
        'args': ['-b4K', '-o1', '-t1', '-r'],
    },
}

_DISKSPD_DOWNLOAD_URL = (
    'https://github.com/microsoft/diskspd/releases/latest/download/DiskSpd.zip'
)


class StorageBenchmarkService:
    """Сервис выполнения бенчмарков дисков через Microsoft DiskSpd."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Инициализация сервиса бенчмарков и базы данных истории.

        Args:
            db_path: Опциональный путь к SQLite файлу истории бенчмарков.
        """
        self.root_dir = Path(__root__)
        self.db_path = db_path or (self.root_dir / 'data' / 'storage_benchmarks.db')
        self._active_tasks: Dict[str, StorageTaskStatus] = {}
        self._cancel_flags: Dict[str, bool] = {}
        self._running_processes: Dict[str, subprocess.Popen] = {}
        self._init_db()

    def _init_db(self) -> None:
        """Инициализация таблиц базы данных SQLite для истории измерений."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS benchmark_history (
                        id TEXT PRIMARY KEY,
                        target TEXT NOT NULL,
                        target_path TEXT NOT NULL,
                        disk_name TEXT,
                        file_size_mb INTEGER,
                        test_duration_sec INTEGER,
                        test_type TEXT,
                        created_at TEXT NOT NULL,
                        completed_at TEXT,
                        total_duration_sec REAL,
                        seq1m_read_mb_s REAL DEFAULT 0,
                        seq1m_write_mb_s REAL DEFAULT 0,
                        rnd4k_read_mb_s REAL DEFAULT 0,
                        rnd4k_write_mb_s REAL DEFAULT 0,
                        rnd4k_read_iops REAL DEFAULT 0,
                        rnd4k_write_iops REAL DEFAULT 0,
                        profiles_json TEXT,
                        success INTEGER DEFAULT 1,
                        error TEXT
                    )
                    """
                )
                conn.commit()
        except Exception as exc:
            logger.warning(f'[StorageBenchmark] Ошибка инициализации БД SQLite ({self.db_path}): {exc}')

    def find_diskspd_binary(self) -> Optional[Path]:
        """Поиск исполняемого файла diskspd.exe в системе и локальных каталогах.

        Returns:
            Optional[Path]: Путь к diskspd.exe или None, если не найден.
        """
        search_paths = [
            self.root_dir / 'bin' / 'diskspd' / 'diskspd.exe',
            self.root_dir / 'bin' / 'diskspd.exe',
            self.root_dir / 'apps' / 'windows' / 'drivers' / 'diskspd.exe',
            Path(os.environ.get('SYSTEMROOT', 'C:\\Windows')) / 'System32' / 'diskspd.exe',
        ]
        for p in search_paths:
            if p.is_file():
                return p

        # Проверка PATH
        which_path = shutil.which('diskspd.exe') or shutil.which('diskspd')
        if which_path:
            return Path(which_path)

        return None

    def ensure_diskspd_binary(self) -> Path:
        """Гарантирует наличие diskspd.exe, скачивая релиз Microsoft при отсутствии.

        Returns:
            Path: Путь к проверенному исполняемому файлу.

        Raises:
            FileNotFoundError: Если не удалось найти или загрузить утилиту.
        """
        existing = self.find_diskspd_binary()
        if existing:
            return existing

        target_dir = self.root_dir / 'bin' / 'diskspd'
        target_exe = target_dir / 'diskspd.exe'
        target_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f'[StorageBenchmark] diskspd.exe не найден. Загрузка из {_DISKSPD_DOWNLOAD_URL}...')
        try:
            req = urllib.request.Request(_DISKSPD_DOWNLOAD_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()

            import zipfile
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                # Извлекаем 64-битный исполняемый файл
                exe_name = None
                for name in zf.namelist():
                    if name.endswith('amd64/diskspd.exe') or name == 'diskspd.exe':
                        exe_name = name
                        break
                if not exe_name:
                    for name in zf.namelist():
                        if name.endswith('.exe'):
                            exe_name = name
                            break

                if not exe_name:
                    raise FileNotFoundError('В архиве DiskSpd.zip не найден исполняемый файл diskspd.exe')

                exe_bytes = zf.read(exe_name)
                with open(target_exe, 'wb') as f:
                    f.write(exe_bytes)

            logger.info(f'[StorageBenchmark] diskspd.exe успешно загружен и сохранен: {target_exe}')
            return target_exe
        except Exception as exc:
            logger.error(f'[StorageBenchmark] Не удалось загрузить diskspd.exe: {exc}')
            raise FileNotFoundError(f'Утилита diskspd.exe недоступна и не удалось ее скачать: {exc}')

    def get_available_targets(self) -> List[BenchmarkTargetInfo]:
        """Возвращает список доступных накопителей и разделов Windows для бенчмарка.

        Returns:
            List[BenchmarkTargetInfo]: Список объектов с характеристиками дисков.
        """
        targets: List[BenchmarkTargetInfo] = []
        try:
            partitions = psutil.disk_partitions(all=False)
        except Exception as exc:
            logger.warning(f'[StorageBenchmark] Ошибка получения разделов: {exc}')
            partitions = []

        system_drive = os.environ.get('SystemDrive', 'C:').upper()

        for p in partitions:
            mount = p.mountpoint
            if not mount:
                continue
            drive_letter = mount.split('\\')[0].upper()
            if not drive_letter.endswith(':'):
                drive_letter += ':'

            try:
                usage = psutil.disk_usage(mount)
                total_bytes = usage.total
                free_bytes = usage.free
                free_gb = round(free_bytes / (1024**3), 2)
            except Exception:
                total_bytes = 0
                free_bytes = 0
                free_gb = 0.0

            # Рекомендуемый каталог для безопасного бенчмарка
            if drive_letter == system_drive:
                rec_dir = str(self.root_dir / 'data' / 'benchmark')
            else:
                rec_dir = f'{drive_letter}\\AI-Breadboard-benchmark'

            targets.append(
                BenchmarkTargetInfo(
                    drive_letter=drive_letter,
                    label=p.device or mount,
                    fs_type=p.fstype or 'NTFS',
                    total_bytes=total_bytes,
                    free_bytes=free_bytes,
                    free_gb=free_gb,
                    recommended_dir=rec_dir,
                    is_system=(drive_letter == system_drive),
                    is_ssd=True,
                )
            )

        if not targets:
            # Fallback для системы
            rec_dir = str(self.root_dir / 'data' / 'benchmark')
            targets.append(
                BenchmarkTargetInfo(
                    drive_letter='C:',
                    label='C:\\',
                    fs_type='NTFS',
                    total_bytes=100 * 1024**3,
                    free_bytes=20 * 1024**3,
                    free_gb=20.0,
                    recommended_dir=rec_dir,
                    is_system=True,
                    is_ssd=True,
                )
            )

        return targets

    def _resolve_test_file_path(self, req: BenchmarkRequest) -> Path:
        """Определяет и подготавливает безопасный путь к тестовому файлу.

        Args:
            req: Параметры запроса.

        Returns:
            Path: Полный путь к тестовому файлу diskspd-test.dat.

        Raises:
            ValueError: Если на диске недостаточно свободного места.
        """
        if req.target_path and req.target_path.strip():
            p = Path(req.target_path.strip())
            if p.is_dir() or not p.suffix:
                test_dir = p
                test_file = test_dir / 'diskspd-test.dat'
            else:
                test_dir = p.parent
                test_file = p
        else:
            drive = req.target_drive.strip().upper()
            if not drive.endswith(':'):
                drive += ':'
            system_drive = os.environ.get('SystemDrive', 'C:').upper()
            if drive == system_drive:
                test_dir = self.root_dir / 'data' / 'benchmark'
            else:
                test_dir = Path(f'{drive}\\AI-Breadboard-benchmark')
            test_file = test_dir / 'diskspd-test.dat'

        test_dir.mkdir(parents=True, exist_ok=True)

        # Проверка свободного места (требуется как минимум file_size_mb + 100MB)
        try:
            usage = psutil.disk_usage(str(test_dir))
            required_bytes = (req.file_size_mb + 100) * 1024 * 1024
            if usage.free < required_bytes:
                raise ValueError(
                    f'Недостаточно места на накопителе {test_dir.drive}. '
                    f'Свободно {round(usage.free / 1024**2, 1)} МБ, требуется {req.file_size_mb} МБ.'
                )
        except Exception as exc:
            if isinstance(exc, ValueError):
                raise
            logger.debug(f'[StorageBenchmark] Проверка места пропущена: {exc}')

        return test_file

    def _parse_xml_results(
        self,
        xml_text: str,
        profile_key: str,
        profile_meta: Dict[str, Any],
        is_write_test: bool = False,
    ) -> BenchmarkProfileResult:
        """Разбирает XML результат работы DiskSpd.

        Args:
            xml_text: XML вывод от DiskSpd.
            profile_key: Ключ профиля нагрузки.
            profile_meta: Метаданные профиля (блок, очередь, потоки).
            is_write_test: Флаг тестирования записи.

        Returns:
            BenchmarkProfileResult: Заполненный объект метрик.
        """
        root = ET.fromstring(xml_text)
        ts = root.find('TimeSpan')
        if ts is None:
            raise ValueError('В ответе DiskSpd отсутствует секция <TimeSpan>')

        seconds = float(ts.findtext('TestTimeSeconds', '1.0'))
        if seconds <= 0:
            seconds = 1.0

        total_read_bytes = 0
        total_write_bytes = 0
        total_read_io = 0
        total_write_io = 0

        for th in ts.findall('Thread'):
            for tgt in th.findall('Target'):
                total_read_bytes += int(tgt.findtext('ReadBytes', '0'))
                total_write_bytes += int(tgt.findtext('WriteBytes', '0'))
                total_read_io += int(tgt.findtext('ReadCount', '0'))
                total_write_io += int(tgt.findtext('WriteCount', '0'))

        read_mb_s = round((total_read_bytes / (1024 * 1024)) / seconds, 2)
        write_mb_s = round((total_write_bytes / (1024 * 1024)) / seconds, 2)
        read_iops = round(total_read_io / seconds, 1)
        write_iops = round(total_write_io / seconds, 1)

        lat_node = ts.find('Latency')
        avg_read_lat_ms = float(lat_node.findtext('AverageReadMilliseconds', '0')) if lat_node is not None else 0.0
        avg_write_lat_ms = float(lat_node.findtext('AverageWriteMilliseconds', '0')) if lat_node is not None else 0.0
        avg_total_lat_ms = float(lat_node.findtext('AverageTotalMilliseconds', '0')) if lat_node is not None else 0.0

        # Средняя загрузка CPU
        cpu_pct = 0.0
        cpu_node = ts.find('CpuUtilization')
        if cpu_node is not None:
            usages = [float(c.findtext('UsagePercent', '0')) for c in cpu_node.findall('CPU')]
            if usages:
                cpu_pct = round(sum(usages) / len(usages), 1)

        return BenchmarkProfileResult(
            profile_name=profile_key,
            profile_label=profile_meta.get('label', profile_key.upper()),
            block_size=profile_meta.get('block_size', '4K'),
            access_type=profile_meta.get('access_type', 'Sequential'),
            queue_depth=profile_meta.get('queue_depth', 1),
            threads=profile_meta.get('threads', 1),
            read_mb_s=read_mb_s,
            write_mb_s=write_mb_s,
            read_iops=read_iops,
            write_iops=write_iops,
            read_latency_ms=round(avg_read_lat_ms, 4),
            write_latency_ms=round(avg_write_lat_ms, 4),
            read_latency_us=round(avg_read_lat_ms * 1000.0, 1),
            write_latency_us=round(avg_write_lat_ms * 1000.0, 1),
            avg_latency_ms=round(avg_total_lat_ms, 4),
            avg_latency_us=round(avg_total_lat_ms * 1000.0, 1),
            cpu_usage_pct=cpu_pct,
            test_time_sec=round(seconds, 2),
        )

    def _execute_diskspd_phase(
        self,
        diskspd_exe: Path,
        test_file: Path,
        profile_meta: Dict[str, Any],
        duration_sec: int,
        file_size_mb: int,
        is_write: bool,
        disable_cache: bool = True,
        warmup_sec: int = 0,
        task_id: Optional[str] = None,
    ) -> str:
        """Выполняет один запуск DiskSpd и возвращает сырой XML вывод.

        Args:
            diskspd_exe: Путь к diskspd.exe.
            test_file: Путь к тестовому файлу.
            profile_meta: Параметры нагрузки.
            duration_sec: Длительность теста в секундах.
            file_size_mb: Размер тестового файла в МБ.
            is_write: Флаг режима записи (-w100).
            disable_cache: Флаг отключения кэша (-Sh).
            warmup_sec: Длительность прогрева в секундах.
            task_id: Идентификатор задачи для отслеживания отмены.

        Returns:
            str: XML строка вывода.
        """
        cmd = [
            str(diskspd_exe),
            f'-c{file_size_mb}M',
            f'-d{duration_sec}',
            f'-W{warmup_sec}',
            '-C0',
            '-L',
            '-Rxml',
        ]

        if disable_cache:
            cmd.append('-Sh')

        # Добавляем аргументы профиля
        cmd.extend(profile_meta.get('args', ['-b4K', '-o32', '-t1']))

        if is_write:
            cmd.append('-w100')
        else:
            cmd.append('-w0')

        cmd.append(str(test_file))

        logger.debug(f'[StorageBenchmark] Запуск команды DiskSpd: {" ".join(cmd)}')

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )

        if task_id:
            self._running_processes[task_id] = proc

        try:
            stdout, stderr = proc.communicate(timeout=duration_sec + warmup_sec + 30)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            raise TimeoutError(f'Превышено время ожидания DiskSpd ({duration_sec}s)')
        finally:
            if task_id and task_id in self._running_processes:
                self._running_processes.pop(task_id, None)

        if proc.returncode != 0:
            err_msg = stderr.strip() or stdout.strip() or f'DiskSpd завершился с кодом {proc.returncode}'
            raise RuntimeError(f'Ошибка выполнения DiskSpd: {err_msg}')

        return stdout

    def run_suite(
        self,
        req: BenchmarkRequest,
        task_id: Optional[str] = None,
        progress_cb: Optional[Callable[[float, str], None]] = None,
    ) -> BenchmarkSuiteResult:
        """Запускает комплексное измерение производительности (CrystalDiskMark стиль).

        Args:
            req: Параметры запроса бенчмарка.
            task_id: Идентификатор задачи.
            progress_cb: Callback-функция передачи прогресса (процент, сообщение).

        Returns:
            BenchmarkSuiteResult: Полный результат всех профилей.
        """
        bench_id = task_id or f'bench_{int(time.time())}_{uuid.uuid4().hex[:6]}'
        started_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start_mono = time.monotonic()

        diskspd_exe = self.ensure_diskspd_binary()
        test_file = self._resolve_test_file_path(req)

        profiles_to_run = req.profiles or list(DEFAULT_CDM_PROFILES.keys())
        total_steps = len(profiles_to_run) * (2 if req.test_type == 'both' else 1)
        current_step = 0

        suite_result = BenchmarkSuiteResult(
            id=bench_id,
            target=req.target_drive,
            target_path=str(test_file),
            file_size_mb=req.file_size_mb,
            test_duration_sec=req.duration_sec,
            test_type=req.test_type,
            created_at=started_at,
            disk_name=req.target_drive,
            profiles={},
            success=True,
        )

        try:
            for p_key in profiles_to_run:
                # Проверка флага отмены
                if task_id and self._cancel_flags.get(task_id):
                    raise asyncio.CancelledError('Бенчмарк отменен пользователем')

                p_meta = DEFAULT_CDM_PROFILES.get(
                    p_key,
                    {
                        'label': p_key.upper(),
                        'block_size': req.block_size,
                        'access_type': 'Custom',
                        'queue_depth': req.outstanding,
                        'threads': req.threads,
                        'args': [f'-b{req.block_size}', f'-o{req.outstanding}', f'-t{req.threads}'],
                    },
                )

                # Инициализируем результирующий профиль
                p_res = BenchmarkProfileResult(
                    profile_name=p_key,
                    profile_label=p_meta.get('label', p_key),
                    block_size=p_meta.get('block_size', req.block_size),
                    access_type=p_meta.get('access_type', 'Sequential'),
                    queue_depth=p_meta.get('queue_depth', req.outstanding),
                    threads=p_meta.get('threads', req.threads),
                )

                # Фаза Чтения (Read)
                if req.test_type in ('both', 'read'):
                    current_step += 1
                    pct = round((current_step / max(1, total_steps)) * 100, 1)
                    msg = f'Чтение {p_meta.get("label", p_key)} ({current_step}/{total_steps})...'
                    if progress_cb:
                        progress_cb(pct, msg)

                    xml_out = self._execute_diskspd_phase(
                        diskspd_exe=diskspd_exe,
                        test_file=test_file,
                        profile_meta=p_meta,
                        duration_sec=req.duration_sec,
                        file_size_mb=req.file_size_mb,
                        is_write=False,
                        disable_cache=req.disable_cache,
                        warmup_sec=req.warmup_sec,
                        task_id=task_id,
                    )
                    r_parsed = self._parse_xml_results(xml_out, p_key, p_meta, is_write_test=False)
                    p_res.read_mb_s = r_parsed.read_mb_s
                    p_res.read_iops = r_parsed.read_iops
                    p_res.read_latency_ms = r_parsed.read_latency_ms
                    p_res.read_latency_us = r_parsed.read_latency_us
                    p_res.cpu_usage_pct = r_parsed.cpu_usage_pct
                    p_res.test_time_sec += r_parsed.test_time_sec

                # Фаза Записи (Write)
                if req.test_type in ('both', 'write'):
                    current_step += 1
                    pct = round((current_step / max(1, total_steps)) * 100, 1)
                    msg = f'Запись {p_meta.get("label", p_key)} ({current_step}/{total_steps})...'
                    if progress_cb:
                        progress_cb(pct, msg)

                    xml_out = self._execute_diskspd_phase(
                        diskspd_exe=diskspd_exe,
                        test_file=test_file,
                        profile_meta=p_meta,
                        duration_sec=req.duration_sec,
                        file_size_mb=req.file_size_mb,
                        is_write=True,
                        disable_cache=req.disable_cache,
                        warmup_sec=req.warmup_sec,
                        task_id=task_id,
                    )
                    w_parsed = self._parse_xml_results(xml_out, p_key, p_meta, is_write_test=True)
                    p_res.write_mb_s = w_parsed.write_mb_s
                    p_res.write_iops = w_parsed.write_iops
                    p_res.write_latency_ms = w_parsed.write_latency_ms
                    p_res.write_latency_us = w_parsed.write_latency_us
                    p_res.cpu_usage_pct = max(p_res.cpu_usage_pct, w_parsed.cpu_usage_pct)
                    p_res.test_time_sec += w_parsed.test_time_sec

                # Общая латентность
                p_res.avg_latency_ms = round((p_res.read_latency_ms + p_res.write_latency_ms) / (2 if req.test_type == 'both' else 1), 4)
                p_res.avg_latency_us = round((p_res.read_latency_us + p_res.write_latency_us) / (2 if req.test_type == 'both' else 1), 1)

                suite_result.profiles[p_key] = p_res

            suite_result.completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            suite_result.total_duration_sec = round(time.monotonic() - start_mono, 2)
            self._save_to_history(suite_result)

        except Exception as exc:
            suite_result.success = False
            suite_result.error = str(exc)
            logger.error(f'[StorageBenchmark] Ошибка выполнения набора бенчмарка: {exc}')
            raise
        finally:
            if req.delete_test_file and test_file.exists():
                try:
                    test_file.unlink(missing_ok=True)
                    logger.debug(f'[StorageBenchmark] Временный файл теста удален: {test_file}')
                except Exception as del_exc:
                    logger.warning(f'[StorageBenchmark] Не удалось удалить тестовый файл {test_file}: {del_exc}')

        return suite_result

    def _save_to_history(self, res: BenchmarkSuiteResult) -> None:
        """Сохраняет сводные результаты в базу данных SQLite.

        Args:
            res: Завершенный объект результатов бенчмарка.
        """
        try:
            seq_p = res.profiles.get('seq1m_q8t1') or res.profiles.get('seq1m_q1t1')
            rnd_p = res.profiles.get('rnd4k_q32t16') or res.profiles.get('rnd4k_q1t1')

            seq1m_r = seq_p.read_mb_s if seq_p else 0.0
            seq1m_w = seq_p.write_mb_s if seq_p else 0.0
            rnd4k_r = rnd_p.read_mb_s if rnd_p else 0.0
            rnd4k_w = rnd_p.write_mb_s if rnd_p else 0.0
            rnd4k_r_iops = rnd_p.read_iops if rnd_p else 0.0
            rnd4k_w_iops = rnd_p.write_iops if rnd_p else 0.0

            prof_dict = {k: v.model_dump() for k, v in res.profiles.items()}

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO benchmark_history (
                        id, target, target_path, disk_name, file_size_mb, test_duration_sec,
                        test_type, created_at, completed_at, total_duration_sec,
                        seq1m_read_mb_s, seq1m_write_mb_s, rnd4k_read_mb_s, rnd4k_write_mb_s,
                        rnd4k_read_iops, rnd4k_write_iops, profiles_json, success, error
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        res.id,
                        res.target,
                        res.target_path,
                        res.disk_name,
                        res.file_size_mb,
                        res.test_duration_sec,
                        res.test_type,
                        res.created_at,
                        res.completed_at,
                        res.total_duration_sec,
                        seq1m_r,
                        seq1m_w,
                        rnd4k_r,
                        rnd4k_w,
                        rnd4k_r_iops,
                        rnd4k_w_iops,
                        json.dumps(prof_dict, ensure_ascii=False),
                        1 if res.success else 0,
                        res.error,
                    ),
                )
                conn.commit()
        except Exception as exc:
            logger.warning(f'[StorageBenchmark] Не удалось записать историю в SQLite: {exc}')

    def get_history(self, limit: int = 50) -> List[BenchmarkHistoryItem]:
        """Возвращает историю ранее выполненных тестов производительности.

        Args:
            limit: Максимальное количество записей.

        Returns:
            List[BenchmarkHistoryItem]: Список записей истории.
        """
        items: List[BenchmarkHistoryItem] = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, target, created_at, seq1m_read_mb_s, seq1m_write_mb_s,
                           rnd4k_read_mb_s, rnd4k_write_mb_s, rnd4k_read_iops, rnd4k_write_iops
                    FROM benchmark_history
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
                for r in cursor.fetchall():
                    items.append(
                        BenchmarkHistoryItem(
                            id=r['id'],
                            target=r['target'],
                            created_at=r['created_at'],
                            seq1m_read_mb_s=r['seq1m_read_mb_s'] or 0.0,
                            seq1m_write_mb_s=r['seq1m_write_mb_s'] or 0.0,
                            rnd4k_read_mb_s=r['rnd4k_read_mb_s'] or 0.0,
                            rnd4k_write_mb_s=r['rnd4k_write_mb_s'] or 0.0,
                            rnd4k_read_iops=r['rnd4k_read_iops'] or 0.0,
                            rnd4k_write_iops=r['rnd4k_write_iops'] or 0.0,
                            score_summary=f"SEQ {r['seq1m_read_mb_s']:.0f}/{r['seq1m_write_mb_s']:.0f} MB/s | RND {r['rnd4k_read_iops']:.0f} IOPS",
                        )
                    )
        except Exception as exc:
            logger.warning(f'[StorageBenchmark] Ошибка чтения истории: {exc}')
        return items

    def delete_history_item(self, bench_id: str) -> bool:
        """Удаляет запись из истории по ее идентификатору.

        Args:
            bench_id: ID бенчмарка.

        Returns:
            bool: True при успешном удалении.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM benchmark_history WHERE id = ?', (bench_id,))
                conn.commit()
            return True
        except Exception as exc:
            logger.warning(f'[StorageBenchmark] Ошибка удаления записи истории {bench_id}: {exc}')
            return False

    async def start_async_benchmark(self, req: BenchmarkRequest) -> StorageTaskStatus:
        """Запускает бенчмарк в асинхронном фоновом потоке с отслеживанием прогресса.

        Args:
            req: Параметры бенчмарка.

        Returns:
            StorageTaskStatus: Объект отслеживания состояния задачи.
        """
        task_id = f'task_bench_{int(time.time())}_{uuid.uuid4().hex[:6]}'
        task = StorageTaskStatus(
            task_id=task_id,
            task_type='benchmark',
            status='running',
            source=req.target_drive,
            destination=req.target_path or 'diskspd-test.dat',
            started_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            progress_percent=0.0,
        )
        self._active_tasks[task_id] = task
        self._cancel_flags[task_id] = False

        def _progress(pct: float, msg: str) -> None:
            if task_id in self._active_tasks:
                self._active_tasks[task_id].progress_percent = pct
                self._active_tasks[task_id].destination = msg

        async def _runner() -> None:
            try:
                res = await asyncio.to_thread(self.run_suite, req, task_id, _progress)
                task.status = 'completed' if res.success else 'failed'
                task.progress_percent = 100.0
                task.finished_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                task.speed_mb_s = list(res.profiles.values())[0].read_mb_s if res.profiles else 0.0
            except asyncio.CancelledError:
                task.status = 'cancelled'
                task.error_message = 'Тестирование отменено пользователем'
                task.finished_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            except Exception as exc:
                task.status = 'failed'
                task.error_message = str(exc)
                task.finished_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        asyncio.create_task(_runner())
        return task

    def get_task_status(self, task_id: str) -> Optional[StorageTaskStatus]:
        """Возвращает статус фоновой задачи бенчмарка.

        Args:
            task_id: ID задачи.

        Returns:
            Optional[StorageTaskStatus]: Объект задачи или None.
        """
        return self._active_tasks.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """Отменяет выполнение запущенного бенчмарка.

        Args:
            task_id: ID задачи.

        Returns:
            bool: True, если сигнал отмены передан.
        """
        if task_id in self._cancel_flags:
            self._cancel_flags[task_id] = True
            proc = self._running_processes.get(task_id)
            if proc:
                try:
                    proc.terminate()
                except Exception:
                    pass
            return True
        return False


__all__ = ['StorageBenchmarkService', 'DEFAULT_CDM_PROFILES']
