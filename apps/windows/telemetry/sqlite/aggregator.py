# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Sqlite - Aggregator
# =============================================================================
# Description:
#   Многоуровневый SQL-агрегатор временных рядов телеметрии (raw -> hourly ->
#   daily -> weekly -> monthly -> yearly) и планировщик агрегации.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.sqlite.aggregator import TelemetrySqlAggregator
#
#     agg = TelemetrySqlAggregator(connection_manager)
#     agg.run_pipeline()
#
# File: aggregator.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.sqlite
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 05:32:00
# =============================================================================

from __future__ import annotations

"""Многоуровневый SQL-агрегатор временных рядов телеметрии и планировщик агрегации."""

import sqlite3
import threading
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .connection import TelemetryConnectionManager

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class AggregationLevel(str, Enum):
    """Уровни иерархической агрегации временных рядов телеметрии."""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


def sensors_aggregate(
    conn: sqlite3.Connection,
    level: Union[AggregationLevel, str],
    start_epoch: Optional[float] = None,
    end_epoch: Optional[float] = None,
    detect_spikes: bool = True,
) -> Dict[str, int]:
    """Выполняет единую SQL-агрегацию сенсоров для указанного уровня иерархии.

    Args:
        conn: Активное подключение к базе данных SQLite.
        level: Уровень агрегации ('hourly', 'daily', 'weekly', 'monthly', 'yearly').
        start_epoch: Начальная граница выборки в секундах epoch (опционально).
        end_epoch: Конечная граница выборки в секундах epoch (опционально).
        detect_spikes: Флаг сохранения статистических всплесков/аномалий в telemetry_spikes.

    Returns:
        Dict[str, int]: Словарь с количеством обработанных бакетов и сохраненных аномалий.
    """
    lvl_str = str(level.value if isinstance(level, AggregationLevel) else level).lower()
    cursor = conn.cursor()
    now_epoch = time.time()
    res = {"level": lvl_str, "buckets_aggregated": 0, "spikes_recorded": 0}

    if lvl_str == AggregationLevel.HOURLY.value:
        s_epoch = float(start_epoch) if start_epoch is not None else 0.0
        e_epoch = float(end_epoch) if end_epoch is not None else (int(now_epoch // 3600) * 3600.0)

        # 1. SQL агрегация сырых измерений в часовые бакеты
        cursor.execute("""
            INSERT INTO telemetry_hourly (
                sensor_id,
                bucket_start,
                bucket_end,
                sample_count,
                value_min,
                value_max,
                value_avg,
                value_sum,
                value_sum_sq,
                value_stddev,
                value_first,
                value_last
            )
            WITH raw_window AS (
                SELECT
                    sensor_id,
                    CAST(created_at / 3600 AS INTEGER) * 3600 AS b_start,
                    created_at,
                    value,
                    FIRST_VALUE(value) OVER (
                        PARTITION BY sensor_id, CAST(created_at / 3600 AS INTEGER) * 3600
                        ORDER BY created_at ASC
                    ) AS f_val,
                    FIRST_VALUE(value) OVER (
                        PARTITION BY sensor_id, CAST(created_at / 3600 AS INTEGER) * 3600
                        ORDER BY created_at DESC
                    ) AS l_val
                FROM sensor_polls
                WHERE created_at >= ? AND created_at < ? AND value IS NOT NULL
            )
            SELECT
                sensor_id,
                b_start AS bucket_start,
                b_start + 3600 AS bucket_end,
                COUNT(*) AS sample_count,
                MIN(value) AS value_min,
                MAX(value) AS value_max,
                AVG(value) AS value_avg,
                SUM(value) AS value_sum,
                SUM(value * value) AS value_sum_sq,
                SQRT(MAX(0.0, (SUM(value * value) - (SUM(value) * SUM(value)) / COUNT(*)) / COUNT(*))) AS value_stddev,
                MIN(f_val) AS value_first,
                MAX(l_val) AS value_last
            FROM raw_window
            GROUP BY sensor_id, b_start
            ON CONFLICT(sensor_id, bucket_start) DO UPDATE SET
                bucket_end = excluded.bucket_end,
                sample_count = excluded.sample_count,
                value_min = excluded.value_min,
                value_max = excluded.value_max,
                value_avg = excluded.value_avg,
                value_sum = excluded.value_sum,
                value_sum_sq = excluded.value_sum_sq,
                value_stddev = excluded.value_stddev,
                value_first = excluded.value_first,
                value_last = excluded.value_last;
        """, (s_epoch, e_epoch))
        res["buckets_aggregated"] = cursor.rowcount if cursor.rowcount > 0 else 0

        # 2. Выявление и сохранение аномальных всплесков
        if detect_spikes:
            cursor.execute("""
                INSERT INTO telemetry_spikes (
                    sensor_id, timestamp, created_at, value, spike_type,
                    baseline_avg, baseline_stddev, details
                )
                SELECT
                    p.sensor_id,
                    p.timestamp,
                    p.created_at,
                    p.value,
                    CASE WHEN p.value >= h.value_avg THEN 'high' ELSE 'low' END,
                    h.value_avg,
                    h.value_stddev,
                    'Всплеск: знач=' || ROUND(p.value, 2) || ', avg=' || ROUND(h.value_avg, 2) || ', std=' || ROUND(h.value_stddev, 2)
                FROM sensor_polls p
                JOIN telemetry_hourly h
                  ON p.sensor_id = h.sensor_id
                 AND (CAST(p.created_at / 3600 AS INTEGER) * 3600) = h.bucket_start
                WHERE h.value_stddev > 0.01
                  AND ABS(p.value - h.value_avg) >= 2.5 * h.value_stddev
                  AND p.created_at >= ? AND p.created_at < ?
                  AND NOT EXISTS (
                      SELECT 1 FROM telemetry_spikes s
                      WHERE s.sensor_id = p.sensor_id AND s.created_at = p.created_at
                  );
            """, (s_epoch, e_epoch))
            res["spikes_recorded"] = cursor.rowcount if cursor.rowcount > 0 else 0

    elif lvl_str == AggregationLevel.DAILY.value:
        s_epoch = float(start_epoch) if start_epoch is not None else 0.0
        e_epoch = float(end_epoch) if end_epoch is not None else (int(now_epoch // 86400) * 86400.0)

        cursor.execute("""
            INSERT INTO telemetry_daily (
                sensor_id,
                bucket_start,
                bucket_end,
                sample_count,
                value_min,
                value_max,
                value_avg,
                value_sum,
                value_sum_sq,
                value_stddev,
                value_first,
                value_last
            )
            WITH hourly_window AS (
                SELECT
                    sensor_id,
                    CAST(bucket_start / 86400 AS INTEGER) * 86400 AS b_start,
                    bucket_start,
                    sample_count,
                    value_min,
                    value_max,
                    value_sum,
                    value_sum_sq,
                    value_first,
                    value_last,
                    FIRST_VALUE(value_first) OVER (
                        PARTITION BY sensor_id, CAST(bucket_start / 86400 AS INTEGER) * 86400
                        ORDER BY bucket_start ASC
                    ) AS f_val,
                    FIRST_VALUE(value_last) OVER (
                        PARTITION BY sensor_id, CAST(bucket_start / 86400 AS INTEGER) * 86400
                        ORDER BY bucket_start DESC
                    ) AS l_val
                FROM telemetry_hourly
                WHERE bucket_start >= ? AND bucket_start < ?
            )
            SELECT
                sensor_id,
                b_start AS bucket_start,
                b_start + 86400 AS bucket_end,
                SUM(sample_count) AS sample_count,
                MIN(value_min) AS value_min,
                MAX(value_max) AS value_max,
                SUM(value_sum) / SUM(sample_count) AS value_avg,
                SUM(value_sum) AS value_sum,
                SUM(value_sum_sq) AS value_sum_sq,
                SQRT(MAX(0.0, (SUM(value_sum_sq) - (SUM(value_sum) * SUM(value_sum)) / SUM(sample_count)) / SUM(sample_count))) AS value_stddev,
                MIN(f_val) AS value_first,
                MAX(l_val) AS value_last
            FROM hourly_window
            GROUP BY sensor_id, b_start
            ON CONFLICT(sensor_id, bucket_start) DO UPDATE SET
                bucket_end = excluded.bucket_end,
                sample_count = excluded.sample_count,
                value_min = excluded.value_min,
                value_max = excluded.value_max,
                value_avg = excluded.value_avg,
                value_sum = excluded.value_sum,
                value_sum_sq = excluded.value_sum_sq,
                value_stddev = excluded.value_stddev,
                value_first = excluded.value_first,
                value_last = excluded.value_last;
        """, (s_epoch, e_epoch))
        res["buckets_aggregated"] = cursor.rowcount if cursor.rowcount > 0 else 0

    elif lvl_str == AggregationLevel.WEEKLY.value:
        s_epoch = float(start_epoch) if start_epoch is not None else 0.0
        e_epoch = float(end_epoch) if end_epoch is not None else (int(now_epoch // 604800) * 604800.0)

        cursor.execute("""
            INSERT INTO telemetry_weekly (
                sensor_id,
                bucket_start,
                bucket_end,
                sample_count,
                value_min,
                value_max,
                value_avg,
                value_sum,
                value_sum_sq,
                value_stddev,
                value_first,
                value_last
            )
            WITH daily_window AS (
                SELECT
                    sensor_id,
                    CAST(bucket_start / 604800 AS INTEGER) * 604800 AS b_start,
                    bucket_start,
                    sample_count,
                    value_min,
                    value_max,
                    value_sum,
                    value_sum_sq,
                    value_first,
                    value_last,
                    FIRST_VALUE(value_first) OVER (
                        PARTITION BY sensor_id, CAST(bucket_start / 604800 AS INTEGER) * 604800
                        ORDER BY bucket_start ASC
                    ) AS f_val,
                    FIRST_VALUE(value_last) OVER (
                        PARTITION BY sensor_id, CAST(bucket_start / 604800 AS INTEGER) * 604800
                        ORDER BY bucket_start DESC
                    ) AS l_val
                FROM telemetry_daily
                WHERE bucket_start >= ? AND bucket_start < ?
            )
            SELECT
                sensor_id,
                b_start AS bucket_start,
                b_start + 604800 AS bucket_end,
                SUM(sample_count) AS sample_count,
                MIN(value_min) AS value_min,
                MAX(value_max) AS value_max,
                SUM(value_sum) / SUM(sample_count) AS value_avg,
                SUM(value_sum) AS value_sum,
                SUM(value_sum_sq) AS value_sum_sq,
                SQRT(MAX(0.0, (SUM(value_sum_sq) - (SUM(value_sum) * SUM(value_sum)) / SUM(sample_count)) / SUM(sample_count))) AS value_stddev,
                MIN(f_val) AS value_first,
                MAX(l_val) AS value_last
            FROM daily_window
            GROUP BY sensor_id, b_start
            ON CONFLICT(sensor_id, bucket_start) DO UPDATE SET
                bucket_end = excluded.bucket_end,
                sample_count = excluded.sample_count,
                value_min = excluded.value_min,
                value_max = excluded.value_max,
                value_avg = excluded.value_avg,
                value_sum = excluded.value_sum,
                value_sum_sq = excluded.value_sum_sq,
                value_stddev = excluded.value_stddev,
                value_first = excluded.value_first,
                value_last = excluded.value_last;
        """, (s_epoch, e_epoch))
        res["buckets_aggregated"] = cursor.rowcount if cursor.rowcount > 0 else 0

    elif lvl_str == AggregationLevel.MONTHLY.value:
        s_epoch = float(start_epoch) if start_epoch is not None else 0.0
        e_epoch = float(end_epoch) if end_epoch is not None else now_epoch

        cursor.execute("""
            INSERT INTO telemetry_monthly (
                sensor_id,
                bucket_start,
                bucket_end,
                sample_count,
                value_min,
                value_max,
                value_avg,
                value_sum,
                value_sum_sq,
                value_stddev,
                value_first,
                value_last
            )
            WITH daily_window AS (
                SELECT
                    sensor_id,
                    CAST(strftime('%s', datetime(bucket_start, 'unixepoch', 'start of month')) AS INTEGER) AS b_start,
                    CAST(strftime('%s', datetime(bucket_start, 'unixepoch', 'start of month', '+1 month')) AS INTEGER) AS b_end,
                    bucket_start,
                    sample_count,
                    value_min,
                    value_max,
                    value_sum,
                    value_sum_sq,
                    value_first,
                    value_last,
                    FIRST_VALUE(value_first) OVER (
                        PARTITION BY sensor_id, strftime('%Y-%m', datetime(bucket_start, 'unixepoch'))
                        ORDER BY bucket_start ASC
                    ) AS f_val,
                    FIRST_VALUE(value_last) OVER (
                        PARTITION BY sensor_id, strftime('%Y-%m', datetime(bucket_start, 'unixepoch'))
                        ORDER BY bucket_start DESC
                    ) AS l_val
                FROM telemetry_daily
                WHERE bucket_start >= ? AND bucket_start < ?
            )
            SELECT
                sensor_id,
                b_start AS bucket_start,
                MAX(b_end) AS bucket_end,
                SUM(sample_count) AS sample_count,
                MIN(value_min) AS value_min,
                MAX(value_max) AS value_max,
                SUM(value_sum) / SUM(sample_count) AS value_avg,
                SUM(value_sum) AS value_sum,
                SUM(value_sum_sq) AS value_sum_sq,
                SQRT(MAX(0.0, (SUM(value_sum_sq) - (SUM(value_sum) * SUM(value_sum)) / SUM(sample_count)) / SUM(sample_count))) AS value_stddev,
                MIN(f_val) AS value_first,
                MAX(l_val) AS value_last
            FROM daily_window
            GROUP BY sensor_id, b_start
            ON CONFLICT(sensor_id, bucket_start) DO UPDATE SET
                bucket_end = excluded.bucket_end,
                sample_count = excluded.sample_count,
                value_min = excluded.value_min,
                value_max = excluded.value_max,
                value_avg = excluded.value_avg,
                value_sum = excluded.value_sum,
                value_sum_sq = excluded.value_sum_sq,
                value_stddev = excluded.value_stddev,
                value_first = excluded.value_first,
                value_last = excluded.value_last;
        """, (s_epoch, e_epoch))
        res["buckets_aggregated"] = cursor.rowcount if cursor.rowcount > 0 else 0

    elif lvl_str == AggregationLevel.YEARLY.value:
        s_epoch = float(start_epoch) if start_epoch is not None else 0.0
        e_epoch = float(end_epoch) if end_epoch is not None else now_epoch

        cursor.execute("""
            INSERT INTO telemetry_yearly (
                sensor_id,
                bucket_start,
                bucket_end,
                sample_count,
                value_min,
                value_max,
                value_avg,
                value_sum,
                value_sum_sq,
                value_stddev,
                value_first,
                value_last
            )
            WITH monthly_window AS (
                SELECT
                    sensor_id,
                    CAST(strftime('%s', datetime(bucket_start, 'unixepoch', 'start of year')) AS INTEGER) AS b_start,
                    CAST(strftime('%s', datetime(bucket_start, 'unixepoch', 'start of year', '+1 year')) AS INTEGER) AS b_end,
                    bucket_start,
                    sample_count,
                    value_min,
                    value_max,
                    value_sum,
                    value_sum_sq,
                    value_first,
                    value_last,
                    FIRST_VALUE(value_first) OVER (
                        PARTITION BY sensor_id, strftime('%Y', datetime(bucket_start, 'unixepoch'))
                        ORDER BY bucket_start ASC
                    ) AS f_val,
                    FIRST_VALUE(value_last) OVER (
                        PARTITION BY sensor_id, strftime('%Y', datetime(bucket_start, 'unixepoch'))
                        ORDER BY bucket_start DESC
                    ) AS l_val
                FROM telemetry_monthly
                WHERE bucket_start >= ? AND bucket_start < ?
            )
            SELECT
                sensor_id,
                b_start AS bucket_start,
                MAX(b_end) AS bucket_end,
                SUM(sample_count) AS sample_count,
                MIN(value_min) AS value_min,
                MAX(value_max) AS value_max,
                SUM(value_sum) / SUM(sample_count) AS value_avg,
                SUM(value_sum) AS value_sum,
                SUM(value_sum_sq) AS value_sum_sq,
                SQRT(MAX(0.0, (SUM(value_sum_sq) - (SUM(value_sum) * SUM(value_sum)) / SUM(sample_count)) / SUM(sample_count))) AS value_stddev,
                MIN(f_val) AS value_first,
                MAX(l_val) AS value_last
            FROM monthly_window
            GROUP BY sensor_id, b_start
            ON CONFLICT(sensor_id, bucket_start) DO UPDATE SET
                bucket_end = excluded.bucket_end,
                sample_count = excluded.sample_count,
                value_min = excluded.value_min,
                value_max = excluded.value_max,
                value_avg = excluded.value_avg,
                value_sum = excluded.value_sum,
                value_sum_sq = excluded.value_sum_sq,
                value_stddev = excluded.value_stddev,
                value_first = excluded.value_first,
                value_last = excluded.value_last;
        """, (s_epoch, e_epoch))
        res["buckets_aggregated"] = cursor.rowcount if cursor.rowcount > 0 else 0

    else:
        raise ValueError(f"Неизвестный уровень агрегации: {lvl_str}")

    return res


class TelemetrySqlAggregator:
    """Управляет вызовами SQL-агрегации и каскадным выполнением цепочки агрегаторов."""

    def __init__(self, connection_manager: TelemetryConnectionManager) -> None:
        """Инициализирует SQL-агрегатор телеметрии.

        Args:
            connection_manager: Менеджер подключений SQLite.
        """
        self._cm = connection_manager
        self._scheduler_timer: Optional[threading.Timer] = None
        self._scheduler_interval: float = 300.0
        self._scheduler_running: bool = False

    def start_background_scheduler(self, interval_seconds: float = 300.0) -> None:
        """Запускает фоновый регламентный планировщик агрегации.

        Args:
            interval_seconds: Периодичность запуска каскада агрегации в секундах (по умолчанию 300с = 5 мин).
        """
        if self._cm.read_only:
            return
        self.stop_background_scheduler()
        self._scheduler_interval = max(10.0, float(interval_seconds))
        self._scheduler_running = True
        self._schedule_next_run()
        logger.info(f"Запущен фоновый регламентный планировщик агрегации (квант: {self._scheduler_interval}с)")

    def stop_background_scheduler(self) -> None:
        """Останавливает фоновый регламентный планировщик агрегации."""
        self._scheduler_running = False
        if self._scheduler_timer:
            try:
                self._scheduler_timer.cancel()
            except Exception:
                pass
            self._scheduler_timer = None

    def _schedule_next_run(self) -> None:
        if not self._scheduler_running or self._cm.read_only:
            return
        self._scheduler_timer = threading.Timer(self._scheduler_interval, self._on_scheduler_tick)
        self._scheduler_timer.daemon = True
        self._scheduler_timer.start()

    def _on_scheduler_tick(self) -> None:
        if not self._scheduler_running or self._cm.read_only:
            return
        try:
            self.run_pipeline()
        except Exception as ex:
            logger.debug(f"Ошибка регламентной фоновой агрегации: {ex}")
        finally:
            self._schedule_next_run()

    def aggregate(
        self,
        level: Union[AggregationLevel, str],
        start_epoch: Optional[float] = None,
        end_epoch: Optional[float] = None,
        detect_spikes: bool = True,
    ) -> Dict[str, Any]:
        """Запускает агрегацию указанного уровня в транзакции.

        Args:
            level: Уровень агрегации ('hourly', 'daily', 'weekly', 'monthly', 'yearly').
            start_epoch: Начальная граница диапазона.
            end_epoch: Конечная граница диапазона.
            detect_spikes: Флаг фиксации всплесков.

        Returns:
            Dict[str, Any]: Результаты агрегации.
        """
        if self._cm.read_only:
            return {"level": str(level), "buckets_aggregated": 0, "spikes_recorded": 0, "read_only": True}

        with self._cm.lock, self._cm.get_connection() as conn:
            result = sensors_aggregate(
                conn=conn,
                level=level,
                start_epoch=start_epoch,
                end_epoch=end_epoch,
                detect_spikes=detect_spikes,
            )
            conn.commit()
            return result

    def aggregate_hourly(self, start_epoch: Optional[float] = None, end_epoch: Optional[float] = None, detect_spikes: bool = True) -> Dict[str, Any]:
        """Выполняет почасовую агрегацию сырых замеров."""
        return self.aggregate(AggregationLevel.HOURLY, start_epoch=start_epoch, end_epoch=end_epoch, detect_spikes=detect_spikes)

    def aggregate_daily(self, start_epoch: Optional[float] = None, end_epoch: Optional[float] = None) -> Dict[str, Any]:
        """Выполняет суточную агрегацию из почасовых бакетов."""
        return self.aggregate(AggregationLevel.DAILY, start_epoch=start_epoch, end_epoch=end_epoch)

    def aggregate_weekly(self, start_epoch: Optional[float] = None, end_epoch: Optional[float] = None) -> Dict[str, Any]:
        """Выполняет недельную агрегацию из суточных бакетов."""
        return self.aggregate(AggregationLevel.WEEKLY, start_epoch=start_epoch, end_epoch=end_epoch)

    def aggregate_monthly(self, start_epoch: Optional[float] = None, end_epoch: Optional[float] = None) -> Dict[str, Any]:
        """Выполняет месячную агрегацию из суточных бакетов."""
        return self.aggregate(AggregationLevel.MONTHLY, start_epoch=start_epoch, end_epoch=end_epoch)

    def aggregate_yearly(self, start_epoch: Optional[float] = None, end_epoch: Optional[float] = None) -> Dict[str, Any]:
        """Выполняет годовую агрегацию из месячных бакетов."""
        return self.aggregate(AggregationLevel.YEARLY, start_epoch=start_epoch, end_epoch=end_epoch)

    def run_pipeline(
        self,
        start_epoch: Optional[float] = None,
        end_epoch: Optional[float] = None,
        detect_spikes: bool = True,
    ) -> Dict[str, Any]:
        """Выполняет полный каскад агрегации: raw -> hourly -> daily -> weekly -> monthly -> yearly в одной транзакции.

        Args:
            start_epoch: Начальная граница диапазона.
            end_epoch: Конечная граница диапазона.
            detect_spikes: Флаг фиксации всплесков.

        Returns:
            Dict[str, Any]: Сводная статистика всех уровней агрегации.
        """
        if self._cm.read_only:
            return {"read_only": True}

        with self._cm.lock, self._cm.get_connection() as conn:
            h_res = sensors_aggregate(conn, AggregationLevel.HOURLY, start_epoch, end_epoch, detect_spikes)
            d_res = sensors_aggregate(conn, AggregationLevel.DAILY, start_epoch, end_epoch, False)
            w_res = sensors_aggregate(conn, AggregationLevel.WEEKLY, start_epoch, end_epoch, False)
            m_res = sensors_aggregate(conn, AggregationLevel.MONTHLY, start_epoch, end_epoch, False)
            y_res = sensors_aggregate(conn, AggregationLevel.YEARLY, start_epoch, end_epoch, False)
            conn.commit()

            return {
                "hourly": h_res,
                "daily": d_res,
                "weekly": w_res,
                "monthly": m_res,
                "yearly": y_res,
            }
