# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry_Research - Assistant
# =============================================================================
# Description:
#   Интеллектуальный AI-ассистент анализа системной телеметрии и построения графиков.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry_research.assistant import TelemetryAssistant
#
#     service = TelemetryAssistant()
#
# File: assistant.py
# Project: ai-breadboard
# Package: apps.windows.telemetry_research
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-04 07:48:00
# =============================================================================

from __future__ import annotations
"""Интеллектуальный AI-ассистент анализа системной телеметрии, ресурсов программ клиента и построения графиков."""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .query_engine import TelemetryQueryEngine
from .client_resource_analyzer import ClientResourceAnalyzer

try:
    from src.ai.orchestration.unified_chat import UnifiedChatModel
except Exception as ex:
    logger.warning(f"Не удалось импортировать UnifiedChatModel: {ex}")
    UnifiedChatModel = None


class TelemetryAssistant:
    """Ассистент для диалогового исследования телеметрии с генерацией графиков и SQL."""

    SYSTEM_INSTRUCTION = """Ты — интеллектуальный эксперт по анализу системной телеметрии Windows и энергопотреблению компьютера в проекте AI-Breadboard.
Твоя задача — отвечать на вопросы пользователя четко, профессионально и на русском языке, анализировать показатели загрузки ЦП, видеокарты, дисков, температурных датчиков, энергопотребления и процессов.
Когда пользователю требуется визуализация (график, круговая диаграмма, столбчатая диаграмма), ты формируешь развернутый ответ с выводами, рекомендациями и структурированными данными.
Всегда приводи конкретные числовые значения (кВт·ч, Вт, %, ГГц, МБ) и объясняй их физический и системный смысл."""

    def __init__(
        self,
        query_engine: Optional[TelemetryQueryEngine] = None,
        chat_model: Optional[Any] = None,
        client_analyzer: Optional[ClientResourceAnalyzer] = None,
    ) -> None:
        """Инициализация ассистента.

        Args:
            query_engine: Экземпляр движка запросов telemetry.db.
            chat_model: Модель чата (по умолчанию UnifiedChatModel).
            client_analyzer: Анализатор ресурсов программ клиента.
        """
        self.query_engine = query_engine or TelemetryQueryEngine()
        self._chat_model = chat_model
        self.client_analyzer = client_analyzer or ClientResourceAnalyzer(
            query_engine=self.query_engine, chat_model=self._chat_model
        )

    @property
    def chat_model(self) -> Any:
        """Получить активную модель LLM."""
        if self._chat_model is None and UnifiedChatModel is not None:
            try:
                self._chat_model = UnifiedChatModel(system_instruction=self.SYSTEM_INSTRUCTION)
                if self.client_analyzer and self.client_analyzer._chat_model is None:
                    self.client_analyzer._chat_model = self._chat_model
            except Exception as ex:
                logger.warning(f"Не удалось инициализировать UnifiedChatModel: {ex}")
                self._chat_model = None
        return self._chat_model

    async def handle_query(
        self,
        user_message: str,
        source_path: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Обработать пользовательский запрос на естественном языке.

        Args:
            user_message: Текст запроса пользователя.
            source_path: Путь к выбранному файлу БД или логов.
            history: История диалога.

        Returns:
            Dict[str, Any]: Ответ ассистента со структурированным текстом, графиком и SQL.
        """
        msg_lower = user_message.strip().lower()

        # 1. Распознавание интента: Ресурсы клиентских программ и оценка Gemini
        if self._is_client_resources_query(msg_lower):
            return await self._handle_client_resources_query(user_message, source_path)

        # 2. Распознавание интента: График загрузки ЦПУ по времени
        if self._is_cpu_timeline_query(msg_lower):
            return await self._handle_cpu_timeline_query(user_message, source_path)

        # 3. Распознавание интента: Потребление энергии и суточная круговая диаграмма
        if self._is_power_query(msg_lower):
            return await self._handle_power_consumption_query(user_message, source_path)

        # 4. Распознавание интента: Топ процессов
        if self._is_top_processes_query(msg_lower):
            return await self._handle_top_processes_query(user_message, source_path)

        # 5. Произвольный SELECT SQL запрос от пользователя
        if msg_lower.startswith("select ") or msg_lower.startswith("with "):
            return self._handle_direct_sql_query(user_message, source_path)

        # 6. Общий аналитический запрос с обращением к LLM
        return await self._handle_general_ai_query(user_message, source_path, history)

    def _is_client_resources_query(self, msg: str) -> bool:
        """Проверить, относится ли запрос к ресурсам программ клиента или оценке Gemini."""
        has_prog = any(w in msg for w in ["программ", "приложен", "софт", "клиент", "пользовател", "запущенн"])
        has_res = any(w in msg for w in ["мест", "ресурс", "занимает", "жрет", "памят", "диск", "объем", "тяжел", "неизвестн", "gemini", "нормальн"])
        return (has_prog and has_res) or ("сколько места" in msg) or ("неизвестная программа" in msg)

    def _is_cpu_timeline_query(self, msg: str) -> bool:
        """Проверить, относится ли запрос к графику ЦП по времени."""
        keywords = ["график", "таймлайн", "timeline", "динамик", "истори", "по времени"]
        targets = ["цпу", "cpu", "процессор", "загрузк", "нагрузк", "частот"]
        has_kw = any(k in msg for k in keywords)
        has_target = any(t in msg for t in targets)
        return (has_kw and has_target) or ("загрузк" in msg and ("цпу" in msg or "cpu" in msg or "процессор" in msg))

    def _is_power_query(self, msg: str) -> bool:
        """Проверить, относится ли запрос к энергопотреблению или круговой диаграмме мощности."""
        keywords = [
            "энерг",
            "электроэнерг",
            "потреблен",
            "ватт",
            "квт",
            "мощност",
            "кругов",
            "диаграмм",
            "pie",
            "doughnut",
            "power",
        ]
        return any(k in msg for k in keywords) and any(
            t in msg for t in ["компьют", "пк", "систем", "потреблен", "суточн", "кругов", "ватт", "энерг", "power"]
        )

    def _is_top_processes_query(self, msg: str) -> bool:
        """Проверить, относится ли запрос к ресурсоемким процессам."""
        return "процесс" in msg and any(k in msg for k in ["топ", "нагруж", "жрет", "груз", "памят", "cpu", "цпу", "ресурс"])

    async def _handle_cpu_timeline_query(
        self, user_message: str, source_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Сформировать ответ для графика загрузки ЦП."""
        timeline_data = self.query_engine.get_cpu_timeline(limit=120, db_path=source_path)
        if timeline_data.get("status") != "ok":
            return {
                "status": "error",
                "reply": f"⚠️ Не удалось извлечь данные по загрузке ЦП: {timeline_data.get('message')}",
                "chart": None,
                "sql_queries": [timeline_data.get("sql", "")],
                "metrics_summary": {},
                "quick_followups": [
                    "Посчитай суточное потребление энергии (круговая диаграмма)",
                    "Какие процессы больше всего нагружают ЦП?",
                ],
            }

        stats = timeline_data.get("statistics", {})
        avg_cpu = stats.get("avg_cpu_percent", 0.0)
        max_cpu = stats.get("max_cpu_percent", 0.0)
        points_count = stats.get("points_count", 0)

        # Формирование базового отчета
        explanation = (
            f"### 📈 Анализ динамики загрузки и частоты процессора (CPU)\n\n"
            f"Отрисован временной ряд по последним **{points_count} точкам замера** телеметрии:\n\n"
            f"- **Средняя загрузка ЦП:** `{avg_cpu}%`\n"
            f"- **Пиковая нагрузка ЦП:** `{max_cpu}%`\n"
            f"- **Минимальная загрузка:** `{stats.get('min_cpu_percent', 0.0)}%`\n"
            f"- **Временной интервал:** с `{stats.get('start_time', '')[:19]}` по `{stats.get('end_time', '')[:19]}`\n\n"
        )

        if max_cpu > 85.0:
            explanation += "⚠️ **Внимание:** Зафиксированы пиковые всплески нагрузки свыше 85%. Рекомендуется проверить фоновые задачи и процессы в топе.\n"
        else:
            explanation += "✅ **Статус:** Нагрузка на процессор находится в пределах нормы, троттлинг не выражен.\n"

        # Дополнение от LLM
        if self.chat_model and hasattr(self.chat_model, "ask"):
            try:
                llm_prompt = (
                    f"Пользователь спросил: '{user_message}'.\n"
                    f"Данные выборки ЦП: Средняя={avg_cpu}%, Максимум={max_cpu}%, Всего точек={points_count}.\n"
                    f"Дай краткий аналитический комментарий (2-3 предложения) о профиле нагрузки и энергоэффективности процессора."
                )
                ai_comment = await asyncio.wait_for(self.chat_model.ask(llm_prompt), timeout=3.5)
                if ai_comment and len(ai_comment.strip()) > 10:
                    explanation += f"\n💡 **AI-анализ:** {ai_comment.strip()}\n"
            except Exception as ex:
                logger.debug(f"LLM ask fallback: {ex}")

        return {
            "status": "ok",
            "reply": explanation,
            "chart": timeline_data.get("chart"),
            "sql_queries": [timeline_data.get("sql", "")],
            "metrics_summary": {
                "avg_cpu_percent": f"{avg_cpu}%",
                "max_cpu_percent": f"{max_cpu}%",
                "points_analyzed": points_count,
            },
            "quick_followups": [
                "Посчитай суточное потребление энергии (круговая диаграмма)",
                "Топ процессов по нагрузке на ЦП",
                "Были ли критические перезагрузки системы?",
            ],
        }

    async def _handle_power_consumption_query(
        self, user_message: str, source_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Сформировать ответ для расчета энергопотребления и суточной круговой диаграммы."""
        power_data = self.query_engine.calculate_power_consumption_24h(db_path=source_path, hours=24)
        if power_data.get("status") != "ok":
            return {
                "status": "error",
                "reply": f"⚠️ Ошибка расчета энергопотребления: {power_data.get('message')}",
                "chart": None,
                "sql_queries": [],
                "metrics_summary": {},
                "quick_followups": ["Покажи график загрузки ЦПУ по времени"],
            }

        total_kwh = power_data.get("total_kwh", 0.0)
        total_wh = power_data.get("total_watt_hours", 0.0)
        avg_watts = power_data.get("avg_system_power_watts", 0.0)
        cpu_w = power_data.get("cpu_package_power_watts", 0.0)
        gpu_w = power_data.get("gpu_power_watts", 0.0)
        breakdown = power_data.get("breakdown", [])

        table_rows = []
        for item in breakdown:
            table_rows.append(
                f"| {item['component']} | {item['avg_power_watts']} Вт | {item['watt_hours']} Вт·ч | {item['kwh']} кВт·ч | **{item['percent']}%** |"
            )
        table_md = "\n".join(table_rows)

        explanation = (
            f"### ⚡ Расчет суточного энергопотребления компьютера и круговая диаграмма\n\n"
            f"На основе телеметрии аппаратных датчиков мощности (`sensor_polls`) и загрузки компонентов за **24 часа**:\n\n"
            f"- 🔋 **Общее суточное потребление:** **`{total_kwh} кВт·ч`** (`{total_wh} Вт·ч`)\n"
            f"- 🔌 **Средняя мощность всей системы:** **`{avg_watts} Вт`**\n"
            f"- 💻 **Мощность процессора (CPU Package):** `{cpu_w} Вт`\n"
            f"- 🎮 **Мощность видеокарты (GPU):** `{gpu_w} Вт`\n\n"
            f"#### 📊 Детализация энергопотребления по узлам системы:\n\n"
            f"| Компонент / Подсистема | Средняя мощность | За 24ч (Вт·ч) | Энергия (кВт·ч) | Доля (%) |\n"
            f"| :--- | :--- | :--- | :--- | :--- |\n"
            f"{table_md}\n\n"
        )

        est_cost_rub = round(total_kwh * 5.80, 2)
        est_cost_usd = round(total_kwh * 0.15, 2)
        explanation += (
            f"💰 *Примерная стоимость электроэнергии за сутки:* ~**{est_cost_rub} ₽** (или ~**${est_cost_usd}** при среднем тарифе).\n"
        )

        if self.chat_model and hasattr(self.chat_model, "ask"):
            try:
                llm_prompt = (
                    f"Пользователь спросил: '{user_message}'.\n"
                    f"Суточное энергопотребление ПК: Всего={total_kwh} кВт*ч, Средняя мощность={avg_watts} Вт (CPU={cpu_w}W, GPU={gpu_w}W).\n"
                    f"Дай краткий совет (2 предложения) по оптимизации энергопотребления и профилю электропитания Windows."
                )
                ai_comment = await asyncio.wait_for(self.chat_model.ask(llm_prompt), timeout=3.5)
                if ai_comment and len(ai_comment.strip()) > 10:
                    explanation += f"\n💡 **AI-рекомендация:** {ai_comment.strip()}\n"
            except Exception as ex:
                logger.debug(f"LLM ask fallback: {ex}")

        return {
            "status": "ok",
            "reply": explanation,
            "chart": power_data.get("chart"),
            "sql_queries": [power_data.get("sql", "")],
            "metrics_summary": {
                "total_kwh_24h": f"{total_kwh} кВт·ч",
                "avg_power_watts": f"{avg_watts} Вт",
                "cpu_power_watts": f"{cpu_w} Вт",
                "gpu_power_watts": f"{gpu_w} Вт",
            },
            "quick_followups": [
                "Покажи график загрузки ЦПУ по времени",
                "Топ процессов по нагрузке на ЦП",
                "Какая средняя температура видеокарты и процессора?",
            ],
        }

    async def _handle_top_processes_query(
        self, user_message: str, source_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Сформировать ответ по топ-процессам."""
        proc_data = self.query_engine.get_top_processes_summary(limit=10, db_path=source_path)
        processes = proc_data.get("processes", [])

        if not processes:
            return {
                "status": "ok",
                "reply": "В исследуемой выборке не обнаружено записей о процессах.",
                "chart": None,
                "sql_queries": [proc_data.get("sql", "")],
                "metrics_summary": {},
                "quick_followups": ["Покажи график загрузки ЦПУ по времени"],
            }

        rows_md = []
        for idx, p in enumerate(processes, 1):
            rows_md.append(f"| {idx} | **{p.get('name')}** | {p.get('avg_cpu', 0)}% | {p.get('max_cpu', 0)}% | {p.get('avg_ram_mb', 0)} MB |")
        table_md = "\n".join(rows_md)

        explanation = (
            f"### 🔥 Топ ресурсоемких процессов по загрузке ЦП и памяти\n\n"
            f"Рейтинг сформирован на основе снимков процессов (`process_snapshots` / `process_rollups`):\n\n"
            f"| № | Процесс | Средний CPU | Пиковый CPU | Память RAM |\n"
            f"| :- | :--- | :--- | :--- | :--- |\n"
            f"{table_md}\n\n"
        )

        return {
            "status": "ok",
            "reply": explanation,
            "chart": proc_data.get("chart"),
            "sql_queries": [proc_data.get("sql", "")],
            "metrics_summary": {
                "top_process_name": processes[0].get("name") if processes else "—",
                "top_process_cpu": f"{processes[0].get('avg_cpu', 0)}%" if processes else "0%",
            },
            "quick_followups": [
                "Покажи график загрузки ЦПУ по времени",
                "Посчитай суточное потребление энергии (круговая диаграмма)",
            ],
        }

    async def _handle_client_resources_query(
        self, user_message: str, source_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Сформировать подробный отчет по ресурсам программ клиента и оценке неизвестных процессов в Gemini."""
        summary = await self.client_analyzer.analyze_client_resources(
            db_path=source_path, ask_gemini_for_unknown=True, limit=20
        )
        progs = summary.programs

        if not progs:
            return {
                "status": "ok",
                "reply": "🔍 В текущей телеметрии не обнаружено активных программ, запущенных клиентом.",
                "chart": None,
                "sql_queries": [],
                "metrics_summary": {"total_programs": 0},
                "quick_followups": ["Покажи график загрузки ЦПУ по времени"],
            }

        # Таблица распределения ресурсов
        rows_md = []
        for idx, p in enumerate(progs[:12], 1):
            disk_str = f"{p.disk_size_mb} MB" if p.disk_size_mb else "N/A"
            status_badge = "✅ Известная" if p.is_known_software else ("⚠️ Неизвестная (Heavy)" if p.is_resource_heavy else "ℹ️ Неизвестная")
            rows_md.append(
                f"| {idx} | **{p.display_name or p.name}** | `{p.name}` | {p.cpu_percent}% | {p.memory_mb} MB | {disk_str} | {status_badge} |"
            )
        table_md = "\n".join(rows_md)

        explanation = (
            f"### 💻 Ресурсы программ, запущенных клиентом\n\n"
            f"Проведен детальный аудит запущенного клиентского ПО и занимаемых ресурсов (память RAM, нагрузка CPU, файлы на диске):\n\n"
            f"- 📊 **Всего клиентских программ:** `{summary.total_client_programs}`\n"
            f"- 🧠 **Суммарно занято памяти RAM:** **`{summary.total_ram_mb} MB`** (~`{round(summary.total_ram_mb / 1024, 2)} GB`)\n"
            f"- ⚡ **Суммарная нагрузка на ЦП:** **`{summary.total_cpu_percent}%`**\n"
            f"- 📁 **Общий объем файлов на диске:** `{summary.total_disk_size_mb} MB`\n"
            f"- 🚨 **Неизвестных ресурсоемких программ:** **`{summary.unknown_heavy_programs_count}`**\n\n"
            f"#### 📋 Детализация по программам:\n\n"
            f"| № | Программа | Процесс | CPU (%) | RAM (MB) | Диск (файл) | Статус |\n"
            f"| :- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            f"{table_md}\n\n"
        )

        # Вывод оценок от Gemini для неизвестных тяжелых программ
        if summary.evaluations:
            explanation += "### 🤖 Экспертное заключение модели Gemini по неизвестным ресурсоемким программам:\n\n"
            for ev in summary.evaluations:
                norm_icon = "✅ Штатно" if ev.is_normal else "🚨 Аномалия / Риск"
                explanation += (
                    f"#### 🔎 Программа: `{ev.program_name}` (PID: {ev.pid})\n"
                    f"- **Вердикт Gemini:** **{ev.verdict}** ({norm_icon}, Риск: `{ev.risk_level.upper()}`)\n"
                    f"- **Потребление ресурсов:** CPU `{ev.cpu_percent}%`, RAM `{ev.memory_mb} MB`, Диск `{ev.disk_io_mb_s} MB/s`\n"
                    f"- **Путь запуска:** `{ev.executable_path or 'N/A'}`\n"
                    f"- **Анализ:** {ev.analysis}\n"
                )
                if ev.recommendations:
                    recs_str = "\n".join([f"  * {r}" for r in ev.recommendations])
                    explanation += f"- **Рекомендации:**\n{recs_str}\n\n"
        else:
            explanation += "✅ **Все ресурсоемкие программы классифицированы как известные и доверенные.** Аномальных неизвестных процессов не обнаружено.\n"

        # Chart configuration for top client programs RAM & CPU
        chart_labels = [p.display_name or p.name for p in progs[:8]]
        chart_ram = [p.memory_mb for p in progs[:8]]
        chart = {
            "type": "bar",
            "title": "Потребление оперативной памяти RAM клиентскими программами (МБ)",
            "labels": chart_labels,
            "datasets": [
                {
                    "label": "Память RAM (МБ)",
                    "data": chart_ram,
                    "backgroundColor": "rgba(99, 102, 241, 0.7)",
                    "borderColor": "#6366f1",
                    "borderWidth": 1,
                }
            ],
        }

        return {
            "status": "ok",
            "reply": explanation,
            "chart": chart,
            "sql_queries": [],
            "metrics_summary": {
                "total_client_programs": summary.total_client_programs,
                "total_ram_mb": f"{summary.total_ram_mb} MB",
                "total_cpu_percent": f"{summary.total_cpu_percent}%",
                "unknown_heavy_count": summary.unknown_heavy_programs_count,
            },
            "quick_followups": [
                "Покажи график загрузки ЦПУ по времени",
                "Посчитай суточное потребление энергии (круговая диаграмма)",
                "Топ процессов по нагрузке на ЦП",
            ],
        }

    def _handle_direct_sql_query(
        self, sql_query: str, source_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Выполнить прямой SELECT SQL-запрос."""
        res = self.query_engine.execute_safe_sql(sql_query, db_path=source_path)
        if res.get("status") != "ok":
            return {
                "status": "error",
                "reply": f"❌ Ошибка выполнения SQL-запроса:\n```\n{res.get('message')}\n```",
                "chart": None,
                "sql_queries": [res.get("sql", sql_query)],
                "metrics_summary": {},
                "quick_followups": ["Покажи график загрузки ЦПУ по времени"],
            }

        cols = res.get("columns", [])
        rows = res.get("rows", [])
        count = res.get("count", 0)

        header_md = "| " + " | ".join(cols) + " |"
        sep_md = "| " + " | ".join([":---"] * len(cols)) + " |"
        data_md = []
        for r in rows[:15]:
            vals = [str(r.get(c, "")) for c in cols]
            data_md.append("| " + " | ".join(vals) + " |")

        table_str = f"{header_md}\n{sep_md}\n" + "\n".join(data_md)

        explanation = (
            f"### 📋 Результаты SQL-запроса к telemetry.db\n\n"
            f"Возвращено строк: **{count}**\n\n"
            f"{table_str}\n\n"
        )
        if count > 15:
            explanation += f"*Отображены первые 15 строк из {count}.*\n"

        return {
            "status": "ok",
            "reply": explanation,
            "chart": None,
            "sql_queries": [res.get("sql", "")],
            "metrics_summary": {"rows_count": count},
            "quick_followups": [
                "Покажи график загрузки ЦПУ по времени",
                "Посчитай суточное потребление энергии (круговая диаграмма)",
            ],
        }

    async def _handle_general_ai_query(
        self,
        user_message: str,
        source_path: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Обработать общий запрос через LLM с контекстом схемы базы данных."""
        schema_info = self.query_engine.get_schema_summary(db_path=source_path)

        context_prompt = (
            f"Пользователь задал вопрос о телеметрии Windows: '{user_message}'.\n"
            f"Доступные таблицы в telemetry.db: {list(schema_info.get('tables', {}).keys())}.\n"
            f"Ответь информативно и структурированно на русском языке. "
            f"Если пользователю нужны графики, предложи ему готовые фразы ('покажи график загрузки цпу по времени' или 'посчитай потребление энергии')."
        )

        reply_text = ""
        if self.chat_model and hasattr(self.chat_model, "ask"):
            try:
                reply_text = await asyncio.wait_for(self.chat_model.ask(context_prompt), timeout=4.0)
            except Exception as ex:
                logger.warning(f"Ошибка вызова LLM: {ex}")

        if not reply_text:
            reply_text = (
                f"Я готов помочь вам с исследованием системной телеметрии Windows!\n\n"
                f"**Доступные команды и возможности:**\n"
                f"- 📈 **График ЦП:** введите *«покажи график загрузки цпу по времени»*\n"
                f"- ⚡ **Энергопотребление:** введите *«Посчитай примерное общее потребление электроэнергии компьютером и покажи суточную круговую диаграмму»*\n"
                f"- 🔥 **Топ процессов:** введите *«топ процессов по cpu»*\n"
                f"- 📋 **SQL-запросы:** введите любой запрос, начинающийся с `SELECT ...` к базе `telemetry.db`"
            )

        return {
            "status": "ok",
            "reply": reply_text,
            "chart": None,
            "sql_queries": [],
            "metrics_summary": {},
            "quick_followups": [
                "Покажи график загрузки цпу по времени",
                "Посчитай суточное потребление энергии (круговая диаграмма)",
                "Топ процессов по нагрузке на ЦП",
            ],
        }
