# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Log Data Researcher and Profiler
# =============================================================================
# Description:
#   Performs comprehensive statistical profiling, Exploratory Data Analysis (EDA),
#   redundancy ratio calculation, burst detection, and System Health Scoring
#   over massive Windows Event streams without invoking LLM tokens.
#
# Examples:
#   >>> from apps.windows.log_intelligence.src.data_researcher import LogDataResearcher
#   >>> researcher = LogDataResearcher()
#   >>> profile = researcher.profile_data(entries, channel="System")
#
# File: data_researcher.py
# Project: AI-Breadboard
# Package: apps.windows.log_intelligence.src
# Class: LogDataResearcher
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import collections
import datetime
import math
import re
from typing import Any, Dict, List, Optional, Set

from src.logger import logger
from .models import DataProfileReport, LogEntry, LogSeverity, TimeBurst


class LogDataResearcher:
    """Аналитический движок статистического профилирования и EDA системных журналов."""

    def __init__(self, known_signatures_catalog: Optional[Set[str]] = None) -> None:
        """Инициализация профайлера с каталогом известных сигнатур."""
        self.known_signatures = known_signatures_catalog or {
            "Service Control Manager:7036",
            "Service Control Manager:7040",
            "Microsoft-Windows-Kernel-PnP:566",
            "Microsoft-Windows-Kernel-PnP:902",
            "Microsoft-Windows-Kernel-PnP:903",
            "Microsoft-Windows-DistributedCOM:10016",
        }

    @staticmethod
    def extract_template(message: str) -> str:
        """Извлечь обобщенный шаблон из сообщения путем маскирования динамических сущностей."""
        if not message:
            return ""
        # GUID / UUID
        text = re.sub(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", "<GUID>", message)
        # Hex коды и адреса ошибок
        text = re.sub(r"0x[0-9a-fA-F]+", "<HEX>", text)
        # IP адреса
        text = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "<IP>", text)
        # Пути файлов Windows
        text = re.sub(r"[a-zA-Z]:\\[^\s,;]+", "<PATH>", text)
        # Числовые идентификаторы и счетчики
        text = re.sub(r"\b\d+\b", "<NUM>", text)
        # Очистка пробелов
        return re.sub(r"\s+", " ", text).strip()

    def profile_data(self, entries: List[LogEntry], channel: str = "System") -> DataProfileReport:
        """Выполнить полный статистический срез и профилирование массива логов (EDA).

        Args:
            entries (List[LogEntry]): Входной массив записей.
            channel (str): Название канала.

        Returns:
            DataProfileReport: Структурированный аналитический профиль.
        """
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total = len(entries)
        if total == 0:
            return DataProfileReport(
                channel=channel,
                total_events=0,
                unique_templates_count=0,
                redundancy_ratio_pct=0.0,
                health_score=100.0,
                generated_at=now_str,
            )

        crit_count = 0
        err_count = 0
        warn_count = 0
        info_count = 0

        # Частотный словарь шаблонов
        template_map: Dict[tuple, Dict[str, Any]] = collections.defaultdict(lambda: {
            "count": 0,
            "first_seen": None,
            "last_seen": None,
            "provider": "",
            "event_id": 0,
            "level": "Information",
            "template": "",
            "sample": "",
        })

        # Временные бакеты по минутам для детекции всплесков (Bursts)
        minute_buckets: Dict[str, Dict[str, Any]] = collections.defaultdict(lambda: {
            "count": 0,
            "levels": collections.Counter(),
            "providers": collections.Counter(),
        })

        provider_counts = collections.Counter()

        for e in entries:
            lvl = (e.level or "Information").capitalize()
            lvl_lower = lvl.lower()
            if "crit" in lvl_lower:
                crit_count += 1
            elif "err" in lvl_lower:
                err_count += 1
            elif "warn" in lvl_lower:
                warn_count += 1
            else:
                info_count += 1

            prov = e.provider or e.source or "Unknown"
            provider_counts[prov] += 1

            tmpl = self.extract_template(e.message)
            key = (prov, e.event_id, lvl, tmpl[:100])
            t_item = template_map[key]
            t_item["count"] += 1
            t_item["provider"] = prov
            t_item["event_id"] = e.event_id
            t_item["level"] = lvl
            t_item["template"] = tmpl
            if not t_item["sample"] and e.message:
                t_item["sample"] = e.message
            if not t_item["first_seen"] or (e.timestamp and e.timestamp < t_item["first_seen"]):
                t_item["first_seen"] = e.timestamp
            if not t_item["last_seen"] or (e.timestamp and e.timestamp > t_item["last_seen"]):
                t_item["last_seen"] = e.timestamp

            # Агрегация по минутам для Burst-анализа
            if len(e.timestamp) >= 16:
                min_key = e.timestamp[:16]  # YYYY-MM-DD HH:MM
                mb = minute_buckets[min_key]
                mb["count"] += 1
                mb["levels"][lvl] += 1
                mb["providers"][prov] += 1

        unique_templates = len(template_map)
        redundancy_pct = round((1.0 - (unique_templates / total)) * 100.0, 2)

        # Расчет System Health Score (0 - 100)
        # Штрафные веса: Critical = 10, Error = 5, Warning = 1
        penalty = (crit_count * 15.0 + err_count * 8.0 + warn_count * 1.5) / max(total, 1) * 100.0
        health_score = max(0.0, min(100.0, round(100.0 - penalty, 1)))

        # Определение доминирующего источника шума
        dom_noise = provider_counts.most_common(1)[0][0] if provider_counts else ""

        # Детекция временных всплесков (3x от среднего по минутам)
        bursts: List[TimeBurst] = []
        if minute_buckets:
            avg_per_min = total / len(minute_buckets)
            burst_threshold = max(5, int(avg_per_min * 2.5))
            for m_time, m_data in sorted(minute_buckets.items()):
                if m_data["count"] >= burst_threshold or m_data["levels"]["Error"] > 0 or m_data["levels"]["Critical"] > 0:
                    dom_lvl = m_data["levels"].most_common(1)[0][0] if m_data["levels"] else "Info"
                    dom_prov = m_data["providers"].most_common(1)[0][0] if m_data["providers"] else "System"
                    bursts.append(TimeBurst(
                        time_window=m_time,
                        event_count=m_data["count"],
                        dominant_level=dom_lvl,
                        dominant_provider=dom_prov,
                        summary=f"Всплеск {m_data['count']} событий в {m_time} ({dom_lvl} от {dom_prov})",
                    ))

        # Выделение критических инцидентов и новых сигнатур (Novelty Detection)
        critical_incidents: List[Dict[str, Any]] = []
        novel_sigs: List[Dict[str, Any]] = []
        for (prov, eid, lvl, _), t_data in template_map.items():
            sig_key = f"{prov}:{eid}"
            if lvl.lower() in ("critical", "error"):
                critical_incidents.append({
                    "provider": prov,
                    "event_id": eid,
                    "level": lvl,
                    "count": t_data["count"],
                    "sample": t_data["sample"][:120],
                    "template": t_data.get("template", ""),
                })
            if sig_key not in self.known_signatures and eid > 0:
                novel_sigs.append({
                    "provider": prov,
                    "event_id": eid,
                    "level": lvl,
                    "count": t_data["count"],
                    "sample": t_data["sample"][:120],
                })

        # Топ-10 сжатых кластеров
        sorted_patterns = sorted(template_map.values(), key=lambda x: x["count"], reverse=True)[:10]

        return DataProfileReport(
            channel=channel,
            total_events=total,
            unique_templates_count=unique_templates,
            redundancy_ratio_pct=redundancy_pct,
            health_score=health_score,
            critical_count=crit_count,
            error_count=err_count,
            warning_count=warn_count,
            info_count=info_count,
            dominant_noise_provider=dom_noise,
            bursts=bursts[:5],
            critical_incidents=critical_incidents[:10],
            novel_signatures=novel_sigs[:5],
            top_patterns=sorted_patterns,
            generated_at=now_str,
        )
