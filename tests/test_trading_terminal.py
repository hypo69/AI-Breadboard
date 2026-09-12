# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests for Trading Terminal and Terminal Manager
# =============================================================================
# Description:
#   Module for testing trading terminal engine and terminal layout manager.
#
# File: test_trading_terminal.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Unit tests for TradingDeskEngine and Terminal Manager."""

import pytest
from scripts.cli.terminal_manager import build_wt_command, get_terminal_profiles, is_windows_terminal_available
from scripts.dev.trading_terminal import TradingDeskEngine


class TestTradingDeskEngine:
    """Test TradingDeskEngine logic and order lifecycle."""

    def test_engine_initialization(self):
        """Engine should initialize with expected default balance and symbol."""
        engine = TradingDeskEngine(symbol="BTC/USDT", initial_balance=5000.0)
        assert engine.symbol == "BTC/USDT"
        assert engine.balance == 5000.0
        assert engine.position_size == 0.0
        assert engine.realized_pnl == 0.0

    def test_market_update_changes_price(self):
        """Market update should update price and unrealized PnL."""
        engine = TradingDeskEngine(symbol="BTC/USDT", initial_balance=5000.0)
        init_price = engine.current_price
        engine.update_market()
        assert engine.current_price > 0.0

    def test_place_buy_order_success(self):
        """Placing a valid BUY order should reduce balance and increase position."""
        engine = TradingDeskEngine(symbol="BTC/USDT", initial_balance=100000.0)
        price_before = engine.current_price
        success = engine.place_order("BUY", 0.5)
        assert success is True
        assert engine.position_size == 0.5
        assert engine.balance < 100000.0
        assert engine.entry_price == pytest.approx(price_before, rel=1e-2)

    def test_place_sell_order_success(self):
        """Placing a SELL order should decrease position and update realized PnL."""
        engine = TradingDeskEngine(symbol="BTC/USDT", initial_balance=100000.0)
        engine.place_order("BUY", 1.0)
        success = engine.place_order("SELL", 0.5)
        assert success is True
        assert engine.position_size == 0.5

    def test_insufficient_funds_buy(self):
        """BUY order with insufficient balance should fail safely."""
        engine = TradingDeskEngine(symbol="BTC/USDT", initial_balance=10.0)
        success = engine.place_order("BUY", 10.0)
        assert success is False
        assert engine.position_size == 0.0

    def test_kill_switch_closes_all_positions(self):
        """Kill-Switch should immediately close any open position."""
        engine = TradingDeskEngine(symbol="BTC/USDT", initial_balance=100000.0)
        engine.place_order("BUY", 0.5)
        assert engine.position_size == 0.5
        engine.trigger_kill_switch()
        assert engine.position_size == 0.0


class TestTerminalManager:
    """Test terminal layout profiles and WT command builder."""

    def test_profiles_available(self):
        """Profiles dict should contain breadboard and trading presets."""
        profiles = get_terminal_profiles()
        assert "breadboard" in profiles
        assert "trading" in profiles
        assert len(profiles["breadboard"]) >= 3
        assert len(profiles["trading"]) >= 2

    def test_build_wt_command(self):
        """WT command should generate valid arguments."""
        cmd = build_wt_command("trading")
        assert cmd is not None
        assert "wt.exe" in cmd
        assert "split-pane" in cmd
