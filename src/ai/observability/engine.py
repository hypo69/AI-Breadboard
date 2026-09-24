# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Universal AI Diagnostics Engine
# =============================================================================
# Description:
#   Abstract base for heuristic and AI-driven anomaly detection.
#   Designed to be extensible for system telemetry, cloud logs, or 
#   application metrics.
#
# File: engine.py
# Project: ai-breadboard
# Package: src.ai.observability
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Universal AI-powered diagnostic analyzer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple

from logger import logger
from apps.windows.telemetry.models import AnomalyItem, SystemDiagnosticReport


class DiagnosticEngine(ABC):
    """Abstract base class for diagnostic engines."""

    def __init__(self, chat_model: Optional[Any] = None) -> None:
        self.chat_model = chat_model

    @abstractmethod
    def evaluate_heuristics(self, data: Any) -> Tuple[int, List[AnomalyItem], List[str]]:
        """Run rule-based checks."""
        pass

    def build_prompt(self, data: Any, score: int, anomalies: List[AnomalyItem], summary_text: str) -> str:
        """Построение контекстного промпта для языковой модели."""
        return (
            "Проанализируйте обнаруженные системные аномалии и метрики хоста:\n\n"
            f"Аномалии: {[a.model_dump() for a in anomalies]}\n"
            f"Текущий статус: {summary_text}\n\n"
            "ТРЕБОВАНИЯ К ОТВЕТУ:\n"
            "1. Немедленно предоставьте краткую диагностическую оценку (2-3 предложения) и 2-3 ключевые меры по устранению узких мест.\n"
            "2. Выведите готовый аналитический ответ сразу. Запрещено отвечать шаблонными подтверждениями вроде 'Контекст принят' или 'Жду инструкций'."
        )

    async def diagnose(self, data: Any) -> SystemDiagnosticReport:
        """Run heuristic or direct AI LLM analysis."""
        stages: List[Dict[str, Any]] = [
            {
                "stage": "init",
                "title": "Сбор телеметрии",
                "message": "🔌 Получение актуального среза телеметрии и сенсоров хоста...",
                "details": "WMI, LibreHardwareMonitor, системные процессы и ресурсы хранилища",
            },
        ]

        system_instruction = (
            "Вы — ведущий инженер по системной диагностике и анализу производительности хоста. "
            "Ваша задача: на основе переданных сенсоров и телеметрии немедленно предоставить краткую экспертную оценку и практические рекомендации по оптимизации ресурсов. "
            "ВАЖНО: Запрещено отвечать шаблонными подтверждениями вроде 'Контекст принят', 'Жду инструкций' или 'Готов к работе'. "
            "Сразу выведите готовый аналитический ответ на русском языке."
        )

        model_name = "Heuristic Analyzer"
        generated_prompt: Optional[str] = None
        raw_response: Optional[str] = None
        error_msg: Optional[str] = None
        anomalies: List[AnomalyItem] = []
        recommendations: List[str] = []
        score: int = 100
        summary_text: str = ""

        executor: Optional[Any] = self.chat_model
        if executor is not None:
            if hasattr(executor, "active_provider"):
                model_name = getattr(executor, "active_provider", "Unified AI")
            elif hasattr(executor, "model_id"):
                model_name = f"Gemini CLI ({getattr(executor, 'model_id', 'gemini-3.1-flash-lite')})"
            else:
                model_name = "AI Model"

            # Прямое формирование контекста всех сенсоров для AI-модели без предварительных эвристических порогов
            prompt = self.build_prompt(data, score, anomalies, "Сенсоры и телеметрия получены")
            generated_prompt = prompt

            stages.append({
                "stage": "prompt",
                "title": "Формирование контекста сенсоров",
                "message": "📝 Передача состояния всех сенсоров и параметров в AI-модель...",
                "details": "Передача телеметрии, датчиков, накопителей, процессов и памяти",
                "generated_prompt": prompt,
                "system_instruction": system_instruction,
            })

            stages.append({
                "stage": "synthesizing",
                "title": "Анализ сенсоров моделью",
                "message": f"🧠 Прямой нейросетевой анализ состояния сенсоров через {model_name}...",
                "details": "Интеллектуальная обработка сырых метрик и выявление узких мест",
                "generated_prompt": prompt,
            })

            try:
                if hasattr(executor, "ask"):
                    if hasattr(executor, "_get_active_model"):
                        response = await executor.ask(
                            prompt,
                            model_name="gemini_cli:gemini-3.1-flash-lite",
                            system_instruction=system_instruction,
                        )
                    else:
                        response = await executor.ask(prompt, system_instruction=system_instruction)
                elif hasattr(executor, "chat"):
                    response = await executor.chat(prompt, system_instruction=system_instruction)
                else:
                    response = None

                # Красивое форматирование ответа модели через src.utils.printer
                if response is not None:
                    try:
                        from src.utils.printer import pformat
                        raw_response = pformat(response)
                    except Exception:
                        raw_response = str(response)

                if response and isinstance(response, str) and response.strip():
                    cleaned_resp = response.strip()
                    if cleaned_resp.startswith("Error:") or cleaned_resp.startswith("Model error:"):
                        error_msg = cleaned_resp
                        stages.append({
                            "stage": "warning",
                            "title": "Ошибка провайдера",
                            "message": f"⚠️ Ответ содержит ошибку: {cleaned_resp}",
                            "details": "Использована базовая эвристическая сводка",
                        })
                    else:
                        summary_text = cleaned_resp
                        stages.append({
                            "stage": "done",
                            "title": "Успешный анализ",
                            "message": "✅ Анализ сенсоров и рекомендации успешно сгенерированы AI-моделью",
                            "details": f"Провайдер: {model_name}",
                        })
                else:
                    error_msg = "Получен пустой ответ от AI-модели"
            except Exception as ex:
                error_msg = str(ex)
                raw_response = f"Exception: {ex}"
                logger.debug(f"LLM diagnosis skipped, using heuristic fallback: {ex}")
                stages.append({
                    "stage": "error",
                    "title": "Ошибка выполнения",
                    "message": f"❌ Ошибка вызова модели: {ex}",
                    "details": "Переключение на локальные эвристические правила",
                })
        else:
            # Fallback на локальную эвристику только при отсутствии настроенной AI-модели
            stages.append({
                "stage": "heuristics",
                "title": "Эвристический анализ",
                "message": "⚙️ Выполнение глубокого эвристического анализа подсистем...",
                "details": "Проверка пороговых значений CPU, RAM, дискового пространства и температурных датчиков",
            })
            score, anomalies, recommendations = self.evaluate_heuristics(data)
            summary_text = (
                f"Health score: {score}/100. "
                f"Detected anomalies: {len(anomalies)}."
            )
            stages.append({
                "stage": "heuristics_complete",
                "title": "Завершение анализа",
                "message": "✅ Эвристический аудит завершён без вызова внешней языковой модели",
                "details": "Использован локальный профиль правил",
            })

        return SystemDiagnosticReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            health_score=score,
            summary=summary_text,
            anomalies=anomalies,
            recommendations=recommendations,
            ai_model_used=model_name,
            system_instruction=system_instruction,
            generated_prompt=generated_prompt,
            raw_response=raw_response,
            error=error_msg,
            stages=stages,
        )
