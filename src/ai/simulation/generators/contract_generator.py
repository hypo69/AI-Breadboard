# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Contract Simulation Generator
# =============================================================================
# Description:
#   Generates realistic mock contracts and agreements based on user queries,
#   extracting counterparty names and producing structured agreement details.
#
# File: contract_generator.py
# Project: ai-breadboard
# Package: src.ai.simulation.generators
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import hashlib
import random
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

from src.ai.simulation.base_generator import BaseSimulationGenerator
from src.ai.simulation.models import EntityType, SimulationRequest, SimulationResult
from src.logger import logger


class ContractSimulationGenerator(BaseSimulationGenerator):
    """Generator for simulated contracts and commercial agreements."""

    @property
    def entity_type(self) -> str:
        """Return the contract entity type."""
        return EntityType.CONTRACT.value

    def can_handle(self, request: SimulationRequest) -> bool:
        """Check if request asks for a contract or agreement."""
        if request.entity_type == EntityType.CONTRACT.value:
            return True
        query = request.query.lower().strip()
        keywords = ("договор", "контракт", "соглашение", "contract", "agreement")
        return any(kw in query for kw in keywords)

    def extract_counterparty(self, query: str) -> str:
        """Extract counterparty/username from query text."""
        patterns = [
            r'(?:договор|контракт|соглашение|contract|agreement)\s+(?:с|на|по|for|with)\s+([A-Za-zА-Яа-я0-9_\-\.\s@«»"\'\<\>]+?)(?:\s*[\?\.,;!:]|$)',
            r'(?:с|with)\s+([A-Za-zА-Яа-я0-9_\-\.\s@«»"\'\<\>]+?)(?:\s+(?:договор|контракт|соглашение|contract|agreement)|\s*[\?\.,;!:]|$)',
        ]
        stop_words = {"кем", "чем", "ним", "ней", "вами", "нами", "whom", "him", "her", "пользователем", "клиентом"}
        for pattern in patterns:
            match = re.search(pattern, query, flags=re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                # Clean up surrounding and internal quotes/brackets if matched symmetrically or at borders
                cleaned = extracted.strip(' \t\n\r\'"`.,;?!')
                if cleaned and cleaned.lower() not in stop_words:
                    return cleaned

        # Fallback to generic user if not specified
        return "Пользователь"

    def _generate_deterministic_seed(self, user_id: str, counterparty: str) -> int:
        """Create integer seed from user_id and counterparty for consistency."""
        key = f"{user_id}_{counterparty.strip().lower()}"
        return int(hashlib.md5(key.encode("utf-8")).hexdigest()[:8], 16)

    async def generate(self, request: SimulationRequest) -> SimulationResult:
        """Generate simulated contract details.

        Args:
            request: Simulation request.

        Returns:
            SimulationResult: Generated contract data and readable markdown text.
        """
        counterparty = request.params.get("counterparty") or self.extract_counterparty(request.query)
        seed = self._generate_deterministic_seed(request.user_id, counterparty)
        rng = random.Random(seed)

        # Generate realistic contract parameters
        prefix = rng.choice(["ДКП", "ДОУ", "СП", "CTR", "NDA", "AGR"])
        year = 2026
        num = rng.randint(100, 999)
        month = rng.randint(1, 9)
        contract_number = f"№ {prefix}-{year}/{month:02d}-{num}"

        base_date = datetime(2026, month, rng.randint(1, 28))
        end_date = base_date + timedelta(days=rng.choice([180, 365, 730]))
        date_str = base_date.strftime("%d.%m.%Y")
        end_date_str = end_date.strftime("%d.%m.%Y")

        subject_options = [
            "Оказание услуг по разработке и технической поддержке программного обеспечения",
            "Предоставление неисключительных прав на использование интеллектуальной собственности",
            "Выполнение научно-исследовательских и опытно-конструкторских работ",
            "Комплексное сервисное обслуживание и аналитическое сопровождение платформы",
        ]
        subject = rng.choice(subject_options)
        amount_rub = rng.randint(150, 1500) * 1000
        formatted_amount = f"{amount_rub:,}".replace(",", " ") + " руб."

        statuses = ["Действующий (подписан сторонами)", "Исполнен", "На согласовании", "Пролонгирован"]
        status = statuses[0] if rng.random() > 0.15 else rng.choice(statuses[1:])

        structured_data = {
            "entity_type": EntityType.CONTRACT.value,
            "contract_number": contract_number,
            "counterparty": counterparty,
            "date_concluded": date_str,
            "date_expires": end_date_str,
            "subject": subject,
            "amount": formatted_amount,
            "status": status,
            "payment_terms": "Поэтапная постоплата в течение 10 рабочих дней с момента подписания акта",
            "client_name": "ООО «АИ Бредборд Технологии»",
        }

        generated_text = (
            f"### 📄 Договор {contract_number}\n\n"
            f"- **Контрагент (Исполнитель / Заказчик):** `{counterparty}`\n"
            f"- **Организация:** {structured_data['client_name']}\n"
            f"- **Дата заключения:** {date_str} (действует до {end_date_str})\n"
            f"- **Предмет договора:** {subject}\n"
            f"- **Сумма договора:** **{formatted_amount}** (вкл. НДС применимо)\n"
            f"- **Условия оплаты:** {structured_data['payment_terms']}\n"
            f"- **Текущий статус:** ✅ *{status}*\n\n"
            f"> *Документ зарегистрирован в реестре соглашений и сохранен в персональный клиентский RAG контекст.*"
        )

        logger.info(f"[Simulation] Generated contract {contract_number} for counterparty '{counterparty}' (User: {request.user_id})")

        return SimulationResult(
            entity_type=EntityType.CONTRACT.value,
            title=f"Договор {contract_number} с {counterparty}",
            generated_text=generated_text,
            structured_data=structured_data,
            is_indexed=False,
        )
