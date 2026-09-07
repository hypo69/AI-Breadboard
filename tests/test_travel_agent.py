# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit and Integration Tests for Travel Agent & Tools
# =============================================================================
# Description:
#   Comprehensive tests for TravelAgent, flight_search tool, flight_price_calculator,
#   and multi-server MCPClientManager.
#
# File: test_travel_agent.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from src.ai.agents.tools import flight_price_calculator, flight_search
from src.ai.agents.travel_agent import TravelAgent
from src.ai.agents.mcp_client import MCPClientManager


class TestFlightTools:
    """Test suite for flight-specific tools."""

    def test_flight_price_calculator_basic(self):
        """Test basic price calculation for 1 passenger without extras."""
        raw_res = flight_price_calculator(base_price=300.0, currency="USD")
        data = json.loads(raw_res)
        assert data["currency"] == "USD"
        assert data["passengers_count"] == 1
        assert data["base_price_per_passenger"] == 300.0
        assert data["total_overall"] == 300.0

    def test_flight_price_calculator_full_breakdown(self):
        """Test calculation with baggage, taxes, discount, and multiple passengers."""
        raw_res = flight_price_calculator(
            base_price=500.0,
            currency="EUR",
            baggage_fee=50.0,
            passengers=2,
            tax_rate=10.0,
            discount_percent=20.0,
        )
        data = json.loads(raw_res)
        # Subtotal per person = 500 + 50 = 550
        # Taxes = 55.0 -> Total before discount = 605.0
        # Discount = 20% of 605 = 121.0
        # Final per person = 484.0
        # Total for 2 = 968.0
        assert data["currency"] == "EUR"
        assert data["passengers_count"] == 2
        assert data["tax_amount_per_passenger"] == 55.0
        assert data["discount_per_passenger"] == 121.0
        assert data["final_per_passenger"] == 484.0
        assert data["total_overall"] == 968.0

    @pytest.mark.asyncio
    async def test_flight_search_tool(self):
        """Test flight_search tool with mocked unified chat model."""
        with patch("src.fastapi.router_chat.get_chat_model") as mock_get_chat_model:
            mock_model = MagicMock()
            mock_model.ask = AsyncMock(return_value="Найден рейс El Al TLV-CDG 420$ прямым рейсом.")
            mock_get_chat_model.return_value = mock_model

            res = await flight_search(
                origin="TLV",
                destination="CDG",
                date="2026-10-15",
                return_date="2026-10-22",
                passengers=1,
                travel_class="economy"
            )
            assert "El Al TLV-CDG" in res
            assert "Google Flights" in res
            assert "Aviasales" in res
            assert "Skyscanner" in res


class TestMCPClientManagerMultiServer:
    """Test multi-server MCP connections loading."""

    @pytest.mark.asyncio
    async def test_mcp_client_manager_load_servers(self):
        """Test loading multiple servers from config."""
        manager = MCPClientManager()
        async with manager:
            # MultiServerMCPClient is instantiated or gracefully handled
            tools = await manager.get_tools()
            assert isinstance(tools, list)


class TestTravelAgent:
    """Test suite for TravelAgent execution."""

    def test_travel_agent_init(self):
        """Test TravelAgent initialization and system prompt."""
        agent = TravelAgent()
        assert agent.llm_type in ["gemini", "ollama"]
        assert len(agent.native_tools) >= 5
        prompt = agent._build_system_prompt()
        assert "Travel Agent" in prompt
        assert "flight_search" in prompt
        assert "flight_price_calculator" in prompt

    @pytest.mark.asyncio
    async def test_travel_agent_search_mocked(self):
        """Test TravelAgent.search() execution with mocked react agent or fallback."""
        agent = TravelAgent()
        mock_msg = MagicMock()
        mock_msg.content = json.dumps({
            "action": "flight_results",
            "summary": "Found 3 flights",
            "flights": [
                {"airline": "Air France", "price": "450 USD", "type": "Direct"}
            ]
        })

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_msg)
        mock_llm.ask = AsyncMock(return_value=mock_msg.content)

        with patch.object(agent, "_get_llm", return_value=mock_llm):
            res = await agent.search("Find flights to Paris")
            assert res.get("action") == "flight_results"
            assert len(res.get("flights", [])) == 1

    @pytest.mark.asyncio
    async def test_travel_agent_search_stream_mocked(self):
        """Test streaming generator for TravelAgent."""
        agent = TravelAgent()
        with patch.object(agent, "search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = {"action": "flight_results", "data": "OK"}
            statuses = []
            async for update in agent.search_stream("Test query"):
                statuses.append(update)

            assert len(statuses) >= 3
            assert "status" in statuses[0]
            assert "result" in statuses[-1]
