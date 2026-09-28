# -*- coding: utf-8 -*-
"""Примерный агент, демонстрирующий базовый шаблон создания агента.

Этот агент показывает, как:
- объявлять набор инструментов;
- лениво инициализировать LLM;
- формировать системный промпт;
- запускать ReAct‑агент;
- возвращать структурированный JSON‑результат.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict

from logger import logger
from src.ai.agents.tools import python_eval, file_read
from src.ai.agents.prompts import (
    GENERAL_AGENT_SYSTEM_PROMPT,
    TOOL_SELECTION_GUIDELINES,
    RESULT_FORMAT_INSTRUCTIONS,
)


class ExampleAgent:
    """Примерный агент для демонстрации структуры и работы.

    Параметры конфигурации читаются из ``config.json`` (раздел ``langchain``).
    """

    def __init__(self, config_path: Path = Path("config.json"), ai_model: Any = None) -> None:
        self.config = json.loads(config_path.read_text(encoding="utf-8"))
        self.ai_model = ai_model
        langchain_cfg = self.config.get("langchain", {})
        self.llm_type: str = langchain_cfg.get("default_llm", "gemini")
        self.max_steps: int = langchain_cfg.get("max_agent_steps", 10)
        self.timeout: int = langchain_cfg.get("search_timeout_seconds", 30)
        self._llm: Any | None = None
        # Инструменты, всегда доступные
        self.native_tools = [python_eval, file_read]
        logger.info(
            f"[ExampleAgent] Инициализирован: llm={self.llm_type}, max_steps={self.max_steps}, timeout={self.timeout}"
        )

    # ------------------------------------------------------------------
    # Ленивая инициализация LLM
    # ------------------------------------------------------------------
    def _get_llm(self) -> Any:
        if self._llm is not None:
            return self._llm
        if self.llm_type == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI

            model_name = self.config.get("langchain", {}).get("gemini_model", "gemini-1.5-flash")
            api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                logger.error("[ExampleAgent] GEMINI_API_KEY не найден в окружении")
                raise EnvironmentError("GEMINI_API_KEY not set")
            self._llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=0.0)
        else:
            from langchain_ollama import ChatOllama

            model_name = self.config.get("langchain", {}).get("ollama_model", "qwen2.5:7b")
            base_url = self.config.get("langchain", {}).get("ollama_base_url", "http://localhost:11434")
            self._llm = ChatOllama(model=model_name, base_url=base_url, temperature=0.0)
        logger.info(f"[ExampleAgent] LLM создан: {self.llm_type}")
        return self._llm

    # ------------------------------------------------------------------
    # Системный промпт
    # ------------------------------------------------------------------
    def _build_system_prompt(self) -> str:
        return "\n\n".join(
            [
                GENERAL_AGENT_SYSTEM_PROMPT,
                TOOL_SELECTION_GUIDELINES,
                RESULT_FORMAT_INSTRUCTIONS,
            ]
        )

    # ------------------------------------------------------------------
    # Основной метод выполнения запроса
    # ------------------------------------------------------------------
    async def run(self, query: str) -> Dict[str, Any]:
        """Выполняет запрос и возвращает результат в виде словаря.

        Возврат всегда JSON‑совместим.
        """
        try:
            from langgraph.prebuilt import create_react_agent

            llm = self._get_llm()
            system_prompt = self._build_system_prompt()
            agent_executor = create_react_agent(llm, self.native_tools, prompt=system_prompt)
            result = await asyncio.wait_for(
                agent_executor.ainvoke({"messages": [("user", query)]}), timeout=self.timeout
            )
            # Выделяем последний ответ
            messages = result.get("messages", [])
            if not messages:
                return {"action": "error", "message": "Нет ответа от агента"}
            raw = getattr(messages[-1], "content", "")
            if isinstance(raw, list):
                raw = "".join(item.get("text", "") if isinstance(item, dict) else str(item) for item in raw)
            cleaned = raw.strip()
            # Убираем возможные markdown‑обёртки
            if cleaned.startswith("```"):
                cleaned = cleaned.lstrip("`json").strip("`").strip()
            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
            return {"action": "info", "text": cleaned}
        except asyncio.TimeoutError:
            logger.error(f"[ExampleAgent] Таймаут ({self.timeout}s) при запросе: {query}")
            return {"action": "error", "message": "Timeout"}
        except Exception as exc:
            logger.error(f"[ExampleAgent] Ошибка: {exc}")
            return {"action": "error", "message": str(exc)}

    # ------------------------------------------------------------------
    # Потоковый интерфейс (для UI)
    # ------------------------------------------------------------------
    async def run_stream(self, query: str):
        yield {"status": "🔎 Инициализация ExampleAgent..."}
        result = await self.run(query)
        yield {"result": result}
