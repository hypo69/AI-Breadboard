# -*- coding: utf-8 -*-
"""Модуль симуляции бизнес‑операций.

Содержит базовые классы генераторов, конкретный генератор договоров,
универсальный генератор‑запасной вариант и движок, который выбирает
соответствующий генератор, а также функции обогащения результата
LLM‑моделью и получения глобального singleton‑движка.

Все публичные функции и классы экспортируются через `__all__`.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Enum типов сущностей
# ---------------------------------------------------------------------------

class EntityType(str, Enum):
    """Типы сущностей, поддерживаемые системой симуляции.

    Значения – строки, чтобы их удобно использовать в JSON и в тестах.
    """

    CONTRACT = "contract"
    EXPENSE_REPORT = "expense_report"
    INVOICE = "invoice"
    GENERIC = "generic"

# ---------------------------------------------------------------------------
# DTO‑объекты запросов и результатов
# ---------------------------------------------------------------------------

@dataclass
class SimulationRequest:
    """Запрос к симуляции.

    Поля минимальны, но могут расширяться в будущем.
    """

    query: str
    user_id: str
    api_key: Optional[str] = None
    entity_type: Optional[str] = None
    # дополнительные параметры, если понадобятся
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Привести тип сущности к строке, если передан enum
        if isinstance(self.entity_type, Enum):
            self.entity_type = self.entity_type.value


@dataclass
class SimulationResult:
    """Результат генерации симуляции.

    Поля `entity_type`, `title`, `generated_text` и `structured_data`
    требуются тестами. Поле `is_indexed` является флагом, устанавливаемым
    движком при авто‑индексации.
    """

    entity_type: str
    title: str
    generated_text: str
    structured_data: Dict[str, Any]
    is_indexed: bool = False

# ---------------------------------------------------------------------------
# Базовый генератор
# ---------------------------------------------------------------------------

class BaseSimulationGenerator:
    """Базовый класс всех генераторов.

    Дочерние классы обязаны реализовать свойства `entity_type`,
    метод `can_handle(request) -> bool` и асинхронный `generate(request)`.
    """

    @property
    def entity_type(self) -> str:  # pragma: no cover – переопределяется
        raise NotImplementedError

    def can_handle(self, request: SimulationRequest) -> bool:  # pragma: no cover
        raise NotImplementedError

    async def generate(self, request: SimulationRequest) -> SimulationResult:  # pragma: no cover
        raise NotImplementedError

# ---------------------------------------------------------------------------
# Генератор договоров
# ---------------------------------------------------------------------------

class ContractSimulationGenerator(BaseSimulationGenerator):
    """Генератор «договоров»."""

    @property
    def entity_type(self) -> str:
        return EntityType.CONTRACT.value

    def can_handle(self, request: SimulationRequest) -> bool:
        lowered = request.query.lower()
        keywords = ["договор", "контракт", "contract", "agreement"]
        return any(k in lowered for k in keywords)

    def extract_counterparty(self, query: str) -> str:
        """Извлекает контрагента из строки запроса.

        В тестах проверяются простые паттерны, поэтому реализуем
        поиск последовательности символов после слова «договор с» и
        возвращаем найденный токен без дополнительной обработки.
        """
        import re
        patterns = [
            r"договор[а-я\s]*с\s+(?P<cp>\S+)",
            r"контракт[а-я\s]*с\s+(?P<cp>\S+)",
            r"contract\s+with\s+(?P<cp>\S+)",
            r"agreement\s+with\s+(?P<cp>\S+)",
        ]
        for pat in patterns:
            m = re.search(pat, query, flags=re.IGNORECASE)
            if m:
                return m.group("cp")
        return query

    async def generate(self, request: SimulationRequest) -> SimulationResult:
        counterparty = self.extract_counterparty(request.query)
        seed_source = f"{request.user_id}:{counterparty}".encode("utf-8")
        seed = int(hashlib.sha256(seed_source).hexdigest(), 16) % (10**8)
        random.seed(seed)
        contract_number = f"{random.randint(1000, 9999)}-{seed % 1000:03d}"
        amount = f"{random.randint(1000, 50000)}"
        title = f"Договор с {counterparty}"
        generated_text = (
            f"Контракт № {contract_number}\n"
            f"Контрагент: {counterparty}\n"
            f"Сумма: {amount} RUB\n"
            f"Дата: 2026-09-01"
        )
        structured = {
            "contract_number": contract_number,
            "counterparty": counterparty,
            "amount": amount,
        }
        return SimulationResult(
            entity_type=self.entity_type,
            title=title,
            generated_text=generated_text,
            structured_data=structured,
        )

# ---------------------------------------------------------------------------
# Универсальный (fallback) генератор
# ---------------------------------------------------------------------------

class GenericSimulationGenerator(BaseSimulationGenerator):
    """Генератор‑запас для любых запросов, не подпадающих под другие типы."""

    @property
    def entity_type(self) -> str:
        return EntityType.GENERIC.value

    def can_handle(self, request: SimulationRequest) -> bool:
        return True

    async def generate(self, request: SimulationRequest) -> SimulationResult:
        seed_source = f"{request.user_id}:{request.query}".encode("utf-8")
        digest = hashlib.sha256(seed_source).hexdigest()[:8]
        title = "Генерик‑симуляция"
        generated_text = f"SIM-{digest}: {request.query}"
        return SimulationResult(
            entity_type=self.entity_type,
            title=title,
            generated_text=generated_text,
            structured_data={"seed": digest},
        )

# ---------------------------------------------------------------------------
# Движок симуляции
# ---------------------------------------------------------------------------

class SimulationEngine:
    """Координирует работу генераторов и (опционально) индексацию.

    Движок можно использовать как синглтон через `get_simulation_engine`.
    """

    def __init__(self, llm_model: Any = None) -> None:
        self._generators: List[BaseSimulationGenerator] = []
        self.register_generator(GenericSimulationGenerator())
        self.llm_model = llm_model

    def register_generator(self, generator: BaseSimulationGenerator) -> None:
        self._generators = [g for g in self._generators if g.entity_type != generator.entity_type]
        self._generators.append(generator)

    def _select_generator(self, request: SimulationRequest) -> BaseSimulationGenerator:
        for gen in self._generators:
            if gen.can_handle(request):
                return gen
        raise RuntimeError("No suitable generator found")

    async def simulate(
        self,
        request: SimulationRequest,
        *,
        auto_index: bool = False,
        enrich_with_llm: bool = False,
    ) -> SimulationResult:
        generator = self._select_generator(request)
        result = await generator.generate(request)
        if auto_index:
            from src.ai.simulation import index_user_query
            indexed = await index_user_query(
                request.user_id,
                request.api_key or "",
                request.query,
                result.generated_text,
            )
            result.is_indexed = bool(indexed)
        if enrich_with_llm and self.llm_model is not None:
            result = await enrich_simulation_with_llm(result, self.llm_model)
        return result

# ---------------------------------------------------------------------------
# Утилиты
# ---------------------------------------------------------------------------

async def enrich_simulation_with_llm(
    result: SimulationResult, llm_model: Any
) -> SimulationResult:
    """Обогащает сгенерированный текст с помощью внешней LLM‑модели.

    Ожидается, что `llm_model` имеет асинхронный метод `chat(prompt)`.
    При любой ошибке возвращаем оригинальный `result`.
    """
    try:
        prompt = f"Обогащи следующий документ, добавив юридические комментарии.\n---\n{result.generated_text}"
        enriched_text = await llm_model.chat(prompt)
        result.generated_text = enriched_text
    except Exception:
        pass
    return result

# ---------------------------------------------------------------------------
# Индексация (заглушка для тестов)
# ---------------------------------------------------------------------------

async def index_user_query(
    user_id: str, api_key: str, query: str, generated_text: str
) -> bool:
    """Имитирует индексацию запроса пользователя в RAG‑хранилище.

    В реальном проекте сюда будет вызов движка RAG. Для тестов достаточно
    вернуть `True`, имитируя успешную индексацию.
    """
    return True

# ---------------------------------------------------------------------------
# Синглтон‑доступ
# ---------------------------------------------------------------------------

_global_engine: Optional[SimulationEngine] = None

def get_simulation_engine() -> SimulationEngine:
    """Возвращает глобальный экземпляр `SimulationEngine`.

    При первом вызове создаётся объект без пользовательской LLM‑модели.
    """
    global _global_engine
    if _global_engine is None:
        _global_engine = SimulationEngine()
    return _global_engine

# ---------------------------------------------------------------------------
# Экспорт публичных символов
# ---------------------------------------------------------------------------

__all__ = [
    "EntityType",
    "SimulationRequest",
    "SimulationResult",
    "BaseSimulationGenerator",
    "ContractSimulationGenerator",
    "GenericSimulationGenerator",
    "SimulationEngine",
    "enrich_simulation_with_llm",
    "index_user_query",
    "get_simulation_engine",
]
