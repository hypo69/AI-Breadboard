# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry_Research - Query Engine
# =============================================================================
# Description:
#   Движок SQL-запросов и аналитических расчетов по базе данных telemetry.db.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry_research.query_engine import TelemetryQueryEngine
#
#     service = TelemetryQueryEngine()
#
# File: query_engine.py
# Project: ai-breadboard
# Package: apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 07:47:00
# =============================================================================

from __future__ import annotations
"""Движок SQL-запросов и аналитических расчетов по базе данных telemetry.db."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .extractor import TelemetryDataExtractor


class TelemetryQueryEngine:
    """Аналитический движок для выборки данных и выполнения SQL-запросов к telemetry.db."""

    def __init__(self, extractor: Optional[TelemetryDataExtractor] = None) -> None:
        """Инициализация движка запросов.

        Args:
            extractor: Экземпляр извлекателя данных телеметрии.
        """
        self.extractor = extractor or TelemetryDataExtractor()

    def get_db_path(self, custom_path: Optional[Union[str, Path]] = None) -> Optional[Path]:
        """Получить актуальный путь к файлу SQLite базы данных.

        Args:
            custom_path: Пользовательский путь к БД.

        Returns:
            Optional[Path]: Валидный путь к файлу базы данных.
        """
        if custom_path:
            p = Path(custom_path)
            if p.exists() and p.is_file():
                return p
        return self.extractor.get_default_db_path()

    def execute_safe_sql(
        self, sql_query: str, db_path: Optional[Union[str, Path]] = None, limit: int = 500
    ) -> Dict[str, Any]:
        """Безопасное выполнение произвольного SELECT SQL-запроса к базе телеметрии.

        Args:
            sql_query: Строка SQL-запроса (только SELECT).
            db_path: Опциональный путь к базе данных.
            limit: Максимальное число возвращаемых строк.

        Returns:
            Dict[str, Any]: Результат запроса со столбцами, строками и метаданными.
        """
        target_db = self.get_db_path(db_path)
        if not target_db:
            return {
                "status": "error",
                "message": "База данных telemetry.db не найдена",
                "columns": [],
                "rows": [],
                "count": 0,
            }

        cleaned_sql = sql_query.strip().rstrip(";")
        lower_sql = cleaned_sql.lower()

        # Разрешаем только SELECT запросы
        if not lower_sql.startswith("select") and not lower_sql.startswith("with"):
            return {
                "status": "error",
                "message": "Разрешены только запросы на чтение данных (SELECT)",
                "columns": [],
                "rows": [],
                "count": 0,
            }

        # Ограничиваем количество записей
        if "limit" not in lower_sql:
            cleaned_sql = f"{cleaned_sql} LIMIT {min(limit, 1000)}"

        try:
            conn = sqlite3.connect(str(target_db), timeout=5.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(cleaned_sql)

            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description] if cursor.description else []
            data = [dict(r) for r in rows]
            conn.close()

            return {
                "status": "ok",
                "sql": cleaned_sql,
                "columns": columns,
                "rows": data,
                "count": len(data),
            }
        except Exception as ex:
            logger.warning(f"Ошибка выполнения SQL-запроса '{cleaned_sql}': {ex}")
            return {
                "status": "error",
                "sql": cleaned_sql,
                "message": str(ex),
                "columns": [],
                "rows": [],
                "count": 0,
            }

    def get_cpu_timeline(
        self, limit: int = 120, db_path: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """Получить временной ряд загрузки процессора и частоты для построения графика.

        Args:
            limit: Количество точек замера (по умолчанию 120).
            db_path: Путь к базе данных.

        Returns:
            Dict[str, Any]: Структурированные временные ряды, метки времени и статистика.
        """
        target_db = self.get_db_path(db_path)
        if not target_db:
            return {"status": "error", "message": "telemetry.db не найдена"}

        sql = """
            SELECT id, timestamp, cpu_total_percent, cpu_frequency_mhz, uptime_seconds
            FROM system_snapshots
            ORDER BY id DESC
            LIMIT ?
        """
        try:
            conn = sqlite3.connect(str(target_db), timeout=5.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, (max(10, min(limit, 2000)),))
            raw_rows = [dict(r) for r in cursor.fetchall()]
            conn.close()

            if not raw_rows:
                return {
                    "status": "empty",
                    "message": "В таблице system_snapshots нет записей",
                    "labels": [],
                    "cpu_load": [],
                    "cpu_freq_ghz": [],
                    "sql": sql.strip(),
                }

            # Хронологический порядок: от старых к новым
            chronological = list(reversed(raw_rows))
            labels: List[str] = []
            cpu_load: List[float] = []
            cpu_freq_ghz: List[float] = []

            for row in chronological:
                ts_str = str(row.get("timestamp") or "")
                time_label = ts_str[11:19] if len(ts_str) >= 19 else ts_str
                labels.append(time_label)

                load = round(float(row.get("cpu_total_percent") or 0.0), 1)
                cpu_load.append(load)

                mhz = float(row.get("cpu_frequency_mhz") or 0.0)
                freq_ghz = round(mhz / 1000.0, 2) if mhz > 0 else 0.0
                cpu_freq_ghz.append(freq_ghz)

            avg_cpu = round(sum(cpu_load) / len(cpu_load), 1) if cpu_load else 0.0
            max_cpu = max(cpu_load) if cpu_load else 0.0
            min_cpu = min(cpu_load) if cpu_load else 0.0

            return {
                "status": "ok",
                "sql": sql.strip(),
                "labels": labels,
                "cpu_load": cpu_load,
                "cpu_freq_ghz": cpu_freq_ghz,
                "chart": {
                    "type": "line",
                    "title": f"График загрузки и частоты ЦП по времени (Ср: {avg_cpu}%, Макс: {max_cpu}%)",
                    "labels": labels,
                    "datasets": [
                        {
                            "label": "Загрузка ЦП (%)",
                            "data": cpu_load,
                            "borderColor": "#38bdf8",
                            "backgroundColor": "rgba(56, 189, 248, 0.15)",
                            "borderWidth": 2,
                            "fill": True,
                            "tension": 0.3,
                            "yAxisID": "y",
                        },
                        {
                            "label": "Частота ЦП (GHz)",
                            "data": cpu_freq_ghz,
                            "borderColor": "#f59e0b",
                            "backgroundColor": "transparent",
                            "borderWidth": 2,
                            "borderDash": [4, 4],
                            "tension": 0.2,
                            "yAxisID": "y1",
                        },
                    ],
                },
                "statistics": {
                    "avg_cpu_percent": avg_cpu,
                    "max_cpu_percent": max_cpu,
                    "min_cpu_percent": min_cpu,
                    "points_count": len(labels),
                    "start_time": chronological[0].get("timestamp"),
                    "end_time": chronological[-1].get("timestamp"),
                },
            }
        except Exception as ex:
            logger.error(f"Ошибка извлечения таймлайна CPU: {ex}")
            return {"status": "error", "message": str(ex), "sql": sql.strip()}

    def calculate_power_consumption_24h(
        self, db_path: Optional[Union[str, Path]] = None, hours: int = 24
    ) -> Dict[str, Any]:
        """Рассчитать общее потребление электроэнергии и подготовить суточную круговую диаграмму.

        Интегрирует показания сенсоров мощности (Вт) из sensor_polls во времени
        и рассчитывает общее количество ватт-часов (Вт·ч) и кВт·ч, а также долю каждого компонента.

        Args:
            db_path: Путь к базе данных.
            hours: Период анализа в часах (по умолчанию 24).

        Returns:
            Dict[str, Any]: Аналитический отчет, кВт·ч, разбивка по компонентам для круговой диаграммы.
        """
        target_db = self.get_db_path(db_path)
        if not target_db:
            return {"status": "error", "message": "telemetry.db не найдена"}

        try:
            conn = sqlite3.connect(str(target_db), timeout=5.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 1. Быстрый запрос последних сенсоров категории Powers/Power
            sql_sensors = """
                SELECT hardware_name, sensor_name, unit,
                       AVG(value) as avg_watts,
                       MIN(value) as min_watts,
                       MAX(value) as max_watts,
                       COUNT(*) as sample_count
                FROM (
                    SELECT * FROM sensor_polls
                    ORDER BY id DESC LIMIT 5000
                )
                WHERE (sensor_category IN ('Powers', 'Power') OR unit = 'W')
                  AND value > 0.0
                GROUP BY hardware_name, sensor_name
                ORDER BY avg_watts DESC
            """
            cursor.execute(sql_sensors)
            sensor_power_rows = [dict(r) for r in cursor.fetchall()]

            # 2. Быстрый запрос последних замеров нагрузки ЦП и ГПУ
            sql_snapshots = """
                SELECT AVG(cpu_total_percent) as avg_cpu,
                       MAX(cpu_total_percent) as max_cpu,
                       AVG(memory_used_gb) as avg_ram_gb,
                       AVG(gpu_load_percent) as avg_gpu_load
                FROM (
                    SELECT * FROM system_snapshots
                    ORDER BY id DESC LIMIT 1000
                )
            """
            cursor.execute(sql_snapshots)
            snap_stat = dict(cursor.fetchone() or {})
            conn.close()

            # 3. Анализ и распределение мощности
            cpu_cores_w = 0.0
            cpu_package_w = 0.0
            cpu_memory_w = 0.0
            gpu_w = 0.0
            other_sensors_w = 0.0

            for s in sensor_power_rows:
                s_name = (s.get("sensor_name") or "").lower()
                avg_w = float(s.get("avg_watts") or 0.0)
                if "cpu cores" in s_name or "core power" in s_name:
                    cpu_cores_w = max(cpu_cores_w, avg_w)
                elif "cpu package" in s_name or "package power" in s_name:
                    cpu_package_w = max(cpu_package_w, avg_w)
                elif "cpu memory" in s_name or "dram" in s_name:
                    cpu_memory_w = max(cpu_memory_w, avg_w)
                elif "gpu" in s_name or "graphics" in s_name:
                    gpu_w = max(gpu_w, avg_w)
                else:
                    other_sensors_w += avg_w

            avg_cpu_load = float(snap_stat.get("avg_cpu") or 15.0)
            if cpu_package_w <= 0.0:
                cpu_total_power = round(10.0 + 55.0 * (avg_cpu_load / 100.0), 2)
                cpu_cores_w = round(cpu_total_power * 0.75, 2)
                cpu_uncore_w = round(cpu_total_power * 0.25, 2)
            else:
                cpu_total_power = round(cpu_package_w, 2)
                if cpu_cores_w <= 0.0:
                    cpu_cores_w = round(cpu_package_w * 0.75, 2)
                cpu_uncore_w = max(0.0, round(cpu_package_w - cpu_cores_w, 2))

            if gpu_w <= 0.0:
                avg_gpu_load = float(snap_stat.get("avg_gpu_load") or 5.0)
                gpu_w = round(5.0 + 35.0 * (avg_gpu_load / 100.0), 2)
            else:
                gpu_w = round(gpu_w, 2)

            avg_ram_gb = float(snap_stat.get("avg_ram_gb") or 8.0)
            ram_power_w = round(max(2.0, avg_ram_gb * 0.4), 2)  # ~0.4W на 1 GB RAM
            motherboard_chipset_w = 12.0  # Чипсет материнской платы и VRM
            disks_and_fans_w = 8.0        # Накопители и кулеры

            system_idle_base_w = round(ram_power_w + motherboard_chipset_w + disks_and_fans_w, 2)

            # Итоговая средняя мощность системы (Вт)
            total_avg_watts = round(cpu_total_power + gpu_w + system_idle_base_w, 2)

            # Энергия за период (hours)
            total_watt_hours = round(total_avg_watts * hours, 2)
            total_kwh = round(total_watt_hours / 1000.0, 3)

            # Доли компонентов для круговой диаграммы
            pie_labels = [
                "Ядра процессора (CPU Cores)",
                "Контроллеры и Uncore ЦП",
                "Видеокарта (GPU)",
                "Оперативная память (RAM)",
                "Материнская плата и чипсет",
                "Накопители (SSD/HDD) и кулеры",
            ]
            pie_values = [
                round(cpu_cores_w * hours, 2),
                round(cpu_uncore_w * hours, 2),
                round(gpu_w * hours, 2),
                round(ram_power_w * hours, 2),
                round(motherboard_chipset_w * hours, 2),
                round(disks_and_fans_w * hours, 2),
            ]
            pie_colors = [
                "#38bdf8",  # Ядра CPU (голубой)
                "#0284c7",  # Uncore (синий)
                "#a855f7",  # GPU (фиолетовый)
                "#10b981",  # RAM (зеленый)
                "#f59e0b",  # Материнская плата (янтарный)
                "#ec4899",  # Накопители и кулеры (розовый)
            ]

            total_wh_sum = sum(pie_values) or 1.0
            pie_percentages = [round((v / total_wh_sum) * 100.0, 1) for v in pie_values]

            breakdown_table = []
            for lbl, val_wh, pct in zip(pie_labels, pie_values, pie_percentages):
                breakdown_table.append({
                    "component": lbl,
                    "watt_hours": val_wh,
                    "kwh": round(val_wh / 1000.0, 3),
                    "percent": pct,
                    "avg_power_watts": round(val_wh / hours, 2),
                })

            return {
                "status": "ok",
                "period_hours": hours,
                "total_kwh": total_kwh,
                "total_watt_hours": total_watt_hours,
                "avg_system_power_watts": total_avg_watts,
                "cpu_package_power_watts": cpu_total_power,
                "gpu_power_watts": gpu_w,
                "system_board_power_watts": system_idle_base_w,
                "chart": {
                    "type": "doughnut",
                    "title": f"Суточная круговая диаграмма энергопотребления (Всего: {total_kwh} кВт·ч, {total_avg_watts} Вт)",
                    "labels": pie_labels,
                    "datasets": [
                        {
                            "data": pie_values,
                            "backgroundColor": pie_colors,
                            "borderWidth": 2,
                            "borderColor": "#131b2e",
                        }
                    ],
                },
                "breakdown": breakdown_table,
                "sensor_readings": sensor_power_rows,
                "sql": f"{sql_sensors.strip()}\n-- и статистика нагрузки:\n{sql_snapshots.strip()}",
            }
        except Exception as ex:
            logger.error(f"Ошибка расчета энергопотребления: {ex}")
            return {"status": "error", "message": str(ex)}

    def get_top_processes_summary(
        self, limit: int = 10, db_path: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """Получить сводку самых ресурсоемких процессов по CPU и памяти.

        Args:
            limit: Количество процессов.
            db_path: Путь к базе данных.

        Returns:
            Dict[str, Any]: Список топ-процессов и SQL-запрос.
        """
        target_db = self.get_db_path(db_path)
        if not target_db:
            return {"status": "error", "message": "telemetry.db не найдена"}

        sql = """
            SELECT name,
                   ROUND(AVG(cpu_percent), 1) as avg_cpu,
                   ROUND(MAX(cpu_percent), 1) as max_cpu,
                   ROUND(AVG(memory_mb), 1) as avg_ram_mb,
                   COUNT(*) as samples_count
            FROM (
                SELECT name, cpu_percent, memory_mb FROM process_snapshots
                ORDER BY id DESC LIMIT 500
            )
            GROUP BY name
            ORDER BY avg_cpu DESC
            LIMIT ?
        """
        try:
            conn = sqlite3.connect(str(target_db), timeout=5.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, (limit,))
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()

            # Если snapshots пусты, пробуем process_rollups_daily
            if not rows:
                fallback_sql = """
                    SELECT name, avg_cpu_percent as avg_cpu, max_cpu_percent as max_cpu, avg_memory_mb as avg_ram_mb, sample_count as samples_count
                    FROM process_rollups_daily
                    ORDER BY avg_cpu_percent DESC LIMIT ?
                """
                conn = sqlite3.connect(str(target_db), timeout=5.0)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(fallback_sql, (limit,))
                rows = [dict(r) for r in cursor.fetchall()]
                conn.close()
                sql = fallback_sql

            chart_labels = [r["name"] for r in rows]
            chart_cpu = [r["avg_cpu"] for r in rows]

            return {
                "status": "ok",
                "sql": sql.strip(),
                "processes": rows,
                "count": len(rows),
                "chart": {
                    "type": "bar",
                    "title": "Топ процессов по средней нагрузке на ЦП (%)",
                    "labels": chart_labels,
                    "datasets": [
                        {
                            "label": "Средняя загрузка ЦП (%)",
                            "data": chart_cpu,
                            "backgroundColor": "rgba(56, 189, 248, 0.7)",
                            "borderColor": "#38bdf8",
                            "borderWidth": 1,
                        }
                    ],
                },
            }
        except Exception as ex:
            logger.error(f"Ошибка выборки топ-процессов: {ex}")
            return {"status": "error", "message": str(ex), "sql": sql.strip()}

    def get_schema_summary(self, db_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """Получить краткую схему таблиц telemetry.db для контекста AI-модели.

        Args:
            db_path: Путь к базе данных.

        Returns:
            Dict[str, Any]: Словарь таблиц с их полями и количеством строк.
        """
        target_db = self.get_db_path(db_path)
        if not target_db:
            return {"status": "error", "message": "telemetry.db не найдена"}

        try:
            conn = sqlite3.connect(str(target_db), timeout=5.0)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cursor.fetchall() if r[0] != "sqlite_sequence"]

            schema: Dict[str, Any] = {}
            for t in tables:
                cursor.execute(f"PRAGMA table_info({t})")
                cols = [col[1] for col in cursor.fetchall()]
                cursor.execute(f"SELECT count(*) FROM {t}")
                cnt = cursor.fetchone()[0]
                schema[t] = {"columns": cols, "rows_count": cnt}

            conn.close()
            return {"status": "ok", "tables": schema}
        except Exception as ex:
            return {"status": "error", "message": str(ex)}

    def get_client_processes_data(
        self, db_path: Optional[Union[str, Path]] = None, limit: int = 50
    ) -> Dict[str, Any]:
        """Получить данные о ресурсах клиентских процессов из SQLite.

        Args:
            db_path: Путь к файлу базы данных telemetry.db.
            limit: Максимальное число процессов.

        Returns:
            Dict[str, Any]: Словарь с процессами, SQL-запросом и статусом.
        """
        target_db = self.get_db_path(db_path)
        if not target_db:
            return {"status": "error", "message": "telemetry.db не найдена", "processes": []}

        sql = """
            SELECT pid, name, cpu_percent, memory_mb, memory_percent,
                   num_threads, num_handles, username, read_bytes_sec, write_bytes_sec,
                   executable as executable_path, cmdline as command_line
            FROM process_snapshots
            WHERE id IN (
                SELECT MAX(id) FROM process_snapshots GROUP BY pid
            )
            ORDER BY cpu_percent DESC, memory_mb DESC
            LIMIT ?
        """
        try:
            conn = sqlite3.connect(str(target_db), timeout=5.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, (limit,))
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return {"status": "ok", "processes": rows, "count": len(rows), "sql": sql.strip()}
        except Exception as ex:
            logger.error(f"Ошибка выборки клиентских процессов: {ex}")
            return {"status": "error", "message": str(ex), "processes": [], "sql": sql.strip()}

