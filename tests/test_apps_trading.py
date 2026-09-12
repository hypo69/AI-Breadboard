# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unit Tests for apps.trading_terminal
# =============================================================================
# Description:
#   Comprehensive unit tests for TradingDeskEngine, Order execution,
#   FastAPI REST endpoints, and TUI renderer in apps.trading_terminal.
#
# File: test_apps_trading.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for apps.trading_terminal package."""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from apps.trading_terminal import (
    TradingDeskEngine,
    TradingState,
    MarketTicker,
    OrderRequest,
    init_router,
    render_ui,
)


class TestTradingDeskEngineApp:
    """Test suite for apps.trading_terminal.engine."""

    def test_engine_initialization_defaults(self):
        """Engine should initialize with default BTC/USDT values."""
        engine = TradingDeskEngine()
        assert engine.symbol == "BTC/USDT"
        assert engine.balance == 10000.0
        assert engine.position_size == 0.0
        assert engine.realized_pnl == 0.0
        assert engine.current_price > 0

    def test_engine_custom_symbol_and_balance(self):
        """Engine should initialize with custom symbol and balance."""
        engine = TradingDeskEngine(symbol="ETH/USDT", initial_balance=25000.0)
        assert engine.symbol == "ETH/USDT"
        assert engine.balance == 25000.0

    def test_market_update(self):
        """Market update should adjust price and update unrealized PnL."""
        engine = TradingDeskEngine(symbol="BTC/USDT", initial_balance=50000.0)
        engine.place_order("BUY", 0.5)
        old_price = engine.current_price
        engine.update_market(delta_pct=0.05)  # +5%
        assert engine.current_price > old_price
        assert engine.unrealized_pnl > 0

    def test_buy_and_sell_order_lifecycle(self):
        """Test BUY and subsequent profitable SELL order."""
        engine = TradingDeskEngine(symbol="BTC/USDT", initial_balance=100000.0)
        
        # BUY
        buy_success = engine.place_order("BUY", 0.5)
        assert buy_success is True
        assert engine.position_size == 0.5
        assert engine.balance < 100000.0

        # SELL
        sell_success = engine.place_order("SELL", 0.25)
        assert sell_success is True
        assert engine.position_size == 0.25
        assert len(engine.orders) == 2

    def test_invalid_orders(self):
        """Invalid side, negative amount, or insufficient balance should be rejected."""
        engine = TradingDeskEngine(symbol="BTC/USDT", initial_balance=100.0)
        
        assert engine.place_order("INVALID", 1.0) is False
        assert engine.place_order("BUY", -1.0) is False
        assert engine.place_order("BUY", 10.0) is False  # Insufficient funds
        assert engine.place_order("SELL", 1.0) is False  # Insufficient position

    def test_kill_switch_execution(self):
        """Kill-switch closes any active open positions."""
        engine = TradingDeskEngine(symbol="BTC/USDT", initial_balance=100000.0)
        engine.place_order("BUY", 1.0)
        assert engine.position_size == 1.0

        res = engine.trigger_kill_switch()
        assert res["status"] == "executed"
        assert engine.position_size == 0.0

        # Running again when flat should return noop
        noop_res = engine.trigger_kill_switch()
        assert noop_res["status"] == "noop"

    def test_ticker_and_orderbook(self):
        """Engine should generate valid ticker and orderbook."""
        engine = TradingDeskEngine(symbol="BTC/USDT")
        ticker = engine.get_ticker()
        assert isinstance(ticker, MarketTicker)
        assert ticker.symbol == "BTC/USDT"
        assert ticker.ask >= ticker.bid

        ob = engine.get_orderbook(depth=3)
        assert len(ob["asks"]) == 3
        assert len(ob["bids"]) == 3

    def test_get_state(self):
        """Engine state snapshot contains all required fields."""
        engine = TradingDeskEngine(symbol="BTC/USDT", initial_balance=12000.0)
        state = engine.get_state()
        assert isinstance(state, TradingState)
        assert state.symbol == "BTC/USDT"
        assert state.total_equity == 12000.0


class TestTradingFastAPIRouter:
    """Test suite for apps.trading_terminal.router."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client with trading router."""
        app = FastAPI()
        engine = TradingDeskEngine(symbol="BTC/USDT", initial_balance=50000.0)
        app.include_router(init_router(engine=engine))
        return TestClient(app)

    def test_get_status(self, client):
        """GET /api/v1/trading/status returns current desk state."""
        resp = client.get("/api/v1/trading/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["symbol"] == "BTC/USDT"
        assert data["balance"] == 50000.0

    def test_get_ticker(self, client):
        """GET /api/v1/trading/ticker returns valid ticker."""
        resp = client.get("/api/v1/trading/ticker")
        assert resp.status_code == 200
        data = resp.json()
        assert "price" in data
        assert "bid" in data
        assert "ask" in data

    def test_get_orderbook(self, client):
        """GET /api/v1/trading/orderbook returns depth."""
        resp = client.get("/api/v1/trading/orderbook?depth=4")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["asks"]) == 4
        assert len(data["bids"]) == 4

    def test_post_order_and_kill_switch(self, client):
        """POST /api/v1/trading/order places order, then kill-switch liquidates."""
        # Place BUY
        order_payload = {"symbol": "BTC/USDT", "side": "BUY", "amount": 0.1, "order_type": "MARKET"}
        resp = client.post("/api/v1/trading/order", json=order_payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

        # Check orders
        orders_resp = client.get("/api/v1/trading/orders")
        assert orders_resp.status_code == 200
        assert len(orders_resp.json()) >= 1

        # Kill Switch
        kill_resp = client.post("/api/v1/trading/kill-switch")
        assert kill_resp.status_code == 200
        assert kill_resp.json()["status"] == "executed"
