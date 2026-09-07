# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Simulation System Unit and Integration Tests
# =============================================================================
# Description:
#   Test suite for simulation engine, contract generator, LLM enrichment, and client RAG indexing.
#
# File: test_simulation.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.ai.simulation import (
    BaseSimulationGenerator,
    ContractSimulationGenerator,
    EntityType,
    GenericSimulationGenerator,
    SimulationEngine,
    SimulationRequest,
    SimulationResult,
    enrich_simulation_with_llm,
    get_simulation_engine,
)


@pytest.mark.asyncio
async def test_contract_generator_extraction():
    """Test extracting counterparty from various natural language queries."""
    generator = ContractSimulationGenerator()

    assert generator.extract_counterparty("Найди договор с ivan_petrov") == "ivan_petrov"
    assert generator.extract_counterparty("Покажи контракт с ООО «Вектор»") == "ООО «Вектор»"
    assert generator.extract_counterparty("Договор с <username>") == "<username>"
    assert generator.extract_counterparty("Find agreement with alex_smith?") == "alex_smith"
    assert generator.extract_counterparty("Найди договор с @dev_lead") == "@dev_lead"


@pytest.mark.asyncio
async def test_contract_generator_generation():
    """Test generating a mock contract with structured details."""
    generator = ContractSimulationGenerator()
    request = SimulationRequest(
        query="Найди договор с ivan_petrov",
        user_id="test_user_1",
    )

    assert generator.can_handle(request) is True
    result = await generator.generate(request)

    assert result.entity_type == EntityType.CONTRACT.value
    assert "ivan_petrov" in result.title
    assert "ivan_petrov" in result.generated_text
    assert "№" in result.generated_text
    assert "contract_number" in result.structured_data
    assert result.structured_data["counterparty"] == "ivan_petrov"
    assert "amount" in result.structured_data


@pytest.mark.asyncio
async def test_contract_generator_deterministic_seed():
    """Test that the same user and counterparty yield consistent contract numbers."""
    generator = ContractSimulationGenerator()
    req1 = SimulationRequest(query="Найди договор с user_abc", user_id="user_99")
    req2 = SimulationRequest(query="Договор с user_abc", user_id="user_99")

    res1 = await generator.generate(req1)
    res2 = await generator.generate(req2)

    assert res1.structured_data["contract_number"] == res2.structured_data["contract_number"]
    assert res1.structured_data["amount"] == res2.structured_data["amount"]


@pytest.mark.asyncio
async def test_generic_generator_fallback():
    """Test fallback simulation for arbitrary query types."""
    generator = GenericSimulationGenerator()
    request = SimulationRequest(
        query="Покажи отчет по расходам за май",
        user_id="test_user_2",
        entity_type="expense_report",
    )

    assert generator.can_handle(request) is True
    result = await generator.generate(request)

    assert result.entity_type == "expense_report"
    assert "SIM-" in result.generated_text


@pytest.mark.asyncio
async def test_simulation_engine_dispatch_and_indexing():
    """Test SimulationEngine coordinating generator selection and RAG indexing."""
    engine = SimulationEngine()
    request = SimulationRequest(
        query="Найди договор с super_partner",
        user_id="client_42",
        api_key="mock_gemini_api_key",
    )

    with patch("src.ai.simulation.engine.index_user_query", return_value=True) as mock_index:
        result = await engine.simulate(request, auto_index=True)

        assert result.entity_type == EntityType.CONTRACT.value
        assert result.is_indexed is True
        mock_index.assert_called_once()
        args, kwargs = mock_index.call_args
        assert args[0] == "client_42"
        assert args[1] == "mock_gemini_api_key"
        assert args[2] == "Найди договор с super_partner"
        assert "super_partner" in args[3]


@pytest.mark.asyncio
async def test_simulation_engine_custom_generator_registration():
    """Test registering a custom generator on the fly."""
    class CustomInvoiceGen(BaseSimulationGenerator):
        @property
        def entity_type(self) -> str:
            return "invoice"

        def can_handle(self, req: SimulationRequest) -> bool:
            return "счет" in req.query.lower()

        async def generate(self, req: SimulationRequest) -> SimulationResult:
            return SimulationResult(
                entity_type="invoice",
                title="Счет на оплату",
                generated_text="Счет № 9999",
            )

    engine = SimulationEngine()
    engine.register_generator(CustomInvoiceGen())

    req = SimulationRequest(query="Выстави счет на оплату", user_id="user_7")
    res = await engine.simulate(req, auto_index=False)

    assert res.entity_type == "invoice"
    assert "Счет № 9999" in res.generated_text


@pytest.mark.asyncio
async def test_llm_enrichment_integration():
    """Test enriching simulated document with mock LLM model."""
    mock_model = MagicMock()
    mock_model.chat = AsyncMock(return_value="### Обогащенный договор с экспертными комментариями юриста")

    engine = SimulationEngine(llm_model=mock_model)
    req = SimulationRequest(
        query="Найди договор с ivan_petrov",
        user_id="user_llm_test",
        api_key="mock_key",
    )

    with patch("src.ai.simulation.engine.index_user_query", return_value=True):
        res = await engine.simulate(req, auto_index=True, enrich_with_llm=True)

        assert "Обогащенный договор" in res.generated_text
        mock_model.chat.assert_called_once()


@pytest.mark.asyncio
async def test_llm_enrichment_fallback_on_error():
    """Test graceful fallback to raw template when LLM model throws exception."""
    mock_model = MagicMock()
    mock_model.chat = AsyncMock(side_effect=RuntimeError("LLM API Timeout"))

    engine = SimulationEngine(llm_model=mock_model)
    req = SimulationRequest(
        query="Найди договор с ivan_petrov",
        user_id="user_llm_err",
    )

    res = await engine.simulate(req, auto_index=False, enrich_with_llm=True)
    # Should fallback to base template text without crashing
    assert "Договор" in res.generated_text
    assert "ivan_petrov" in res.generated_text


@pytest.mark.asyncio
async def test_singleton_engine():
    """Test global singleton retrieval and model configuration."""
    engine1 = get_simulation_engine()
    engine2 = get_simulation_engine()
    assert engine1 is engine2

    engine1.llm_model = "test_model_ref"
    assert engine2.llm_model == "test_model_ref"
