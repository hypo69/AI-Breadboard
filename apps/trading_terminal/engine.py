# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Trading Desk State Engine & Order Execution
# =============================================================================
# Description:
#   Exchange engine model managing order placement, position tracking,
#   unrealized/realized PnL calculation, L2 orderbook simulation, and emergency kill-switch.
#
# Examples:
#   >>> engine = TradingDeskEngine(symbol="BTC/USDT", initial_balance=10000.0)
#   >>> engine.place_order("BUY", 0.05)
#   True
#
# File: engine.py
# Project: ai-breadboard
# Package: apps.trading_terminal
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Exchange trading desk engine and portfolio state manager."""

from __future__ import annotations

import random
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.logger import logger
from src.ai.observability.trading_engine import TradingDiagnosticEngine


class OrderRequest(BaseModel):
    """Schema for incoming order placement request."""

    symbol: str = Field(default="BTC/USDT", description="Trading pair symbol")
    side: str = Field(description="Order side: 'BUY' or 'SELL'")
    amount: float = Field(gt=0, description="Order quantity in base asset")
    order_type: str = Field(default="MARKET", description="Order type: 'MARKET' or 'LIMIT'")
    price: Optional[float] = Field(default=None, description="Optional limit price")


class OrderRecord(BaseModel):
    """Execution record for filled or rejected orders."""

    id: str
    timestamp: str
    symbol: str
    side: str
    amount: float
    price: float
    cost: float
    status: str
    pnl: Optional[float] = None


class MarketTicker(BaseModel):
    """Current market ticker data."""

    symbol: str
    price: float
    timestamp: str
    bid: float
    ask: float
    volume_24h: float


class TradingState(BaseModel):
    """Snapshot of the trading desk state."""

    symbol: str
    current_price: float
    balance: float
    position_size: float
    entry_price: float
    unrealized_pnl: float
    realized_pnl: float
    total_equity: float
    recent_logs: List[str]
    recent_orders: List[OrderRecord]


class TradingDeskEngine:
    """Core exchange state engine for trading desk terminal and API."""

    def __init__(self, symbol: str = "BTC/USDT", initial_balance: float = 10000.0) -> None:
        """Initialize trading desk engine state.

        Args:
            symbol (str): Trading pair symbol (e.g. BTC/USDT).
            initial_balance (float): Starting USD account balance.
        """
        self.symbol: str = symbol.upper()
        self.balance: float = float(initial_balance)
        self.position_size: float = 0.0
        self.entry_price: float = 0.0
        self.current_price: float = 65000.0 if "BTC" in self.symbol else (3200.0 if "ETH" in self.symbol else 100.0)
        self.current_price += random.uniform(-50.0, 50.0)
        self.unrealized_pnl: float = 0.0
        self.realized_pnl: float = 0.0
        self.orders: List[OrderRecord] = []
        self.logs: List[str] = [
            f"[{datetime.now().strftime('%H:%M:%S')}] Engine initialized for {self.symbol} with ${self.balance:,.2f}",
            f"[{datetime.now().strftime('%H:%M:%S')}] Market data feed connected (Ready)",
        ]
        self.diagnostician = TradingDiagnosticEngine()
        logger.info(f"TradingDeskEngine started for symbol {self.symbol} with balance ${self.balance:,.2f}")

    async def run_diagnostics(self) -> SystemDiagnosticReport:
        """Run diagnostics on current trading state."""
        from src.ai.observability.models import SystemDiagnosticReport
        state = TradingState(
            symbol=self.symbol,
            current_price=self.current_price,
            balance=self.balance,
            position_size=self.position_size,
            entry_price=self.entry_price,
            unrealized_pnl=self.unrealized_pnl,
            realized_pnl=self.realized_pnl,
            total_equity=self.balance + self.unrealized_pnl,
            recent_logs=self.logs[-10:],
            recent_orders=self.orders
        )
        return await self.diagnostician.diagnose(state)

    def update_market(self, delta_pct: Optional[float] = None) -> float:
        """Update market price and recalculate unrealized PnL.

        Args:
            delta_pct (Optional[float]): Optional specific percentage price change.

        Returns:
            float: New updated current price.
        """
        if delta_pct is None:
            # Random micro walk
            pct_change = random.uniform(-0.002, 0.002)
        else:
            pct_change = delta_pct

        delta = self.current_price * pct_change
        self.current_price = max(1.0, round(self.current_price + delta, 2))

        if self.position_size != 0.0:
            self.unrealized_pnl = round((self.current_price - self.entry_price) * self.position_size, 2)
        else:
            self.unrealized_pnl = 0.0

        return self.current_price

    def place_order(
        self,
        side: str,
        amount: float,
        order_type: str = "MARKET",
        limit_price: Optional[float] = None,
    ) -> bool:
        """Execute or simulate order placement.

        Args:
            side (str): 'BUY' or 'SELL'.
            amount (float): Asset amount to buy or sell.
            order_type (str): 'MARKET' or 'LIMIT'.
            limit_price (Optional[float]): Target price for limit orders.

        Returns:
            bool: True if order executed successfully, False otherwise.
        """
        side = side.upper()
        if side not in ("BUY", "SELL"):
            logger.warning(f"Invalid order side: {side}")
            return False

        if amount <= 0:
            logger.warning(f"Order amount must be positive: {amount}")
            return False

        now_str = datetime.now().strftime("%H:%M:%S")
        exec_price = limit_price if (order_type.upper() == "LIMIT" and limit_price) else self.current_price
        cost = round(amount * exec_price, 2)
        order_id = f"ord_{int(time.time() * 1000)}"

        if side == "BUY":
            if self.balance < cost:
                msg = f"[{now_str}] [WARN] Insufficient funds for BUY {amount:.4f} {self.symbol} (Cost: ${cost:,.2f}, Balance: ${self.balance:,.2f})"
                self._add_log(msg)
                logger.warning(msg)
                return False

            self.balance = round(self.balance - cost, 2)
            total_size = round(self.position_size + amount, 6)
            if total_size > 0:
                self.entry_price = (
                    round((self.entry_price * self.position_size + cost) / total_size, 2)
                    if self.position_size > 0
                    else exec_price
                )
            self.position_size = total_size
            msg = f"[{now_str}] [ORDER] Executed BUY {amount:.4f} {self.symbol} @ ${exec_price:,.2f} (${cost:,.2f})"
            self._add_log(msg)
            logger.info(msg)

            self.orders.append(
                OrderRecord(
                    id=order_id,
                    timestamp=now_str,
                    symbol=self.symbol,
                    side="BUY",
                    amount=amount,
                    price=exec_price,
                    cost=cost,
                    status="FILLED",
                )
            )

        else:  # SELL
            if self.position_size < amount:
                msg = f"[{now_str}] [WARN] Insufficient position to SELL {amount:.4f} {self.symbol} (Holding: {self.position_size:.4f})"
                self._add_log(msg)
                logger.warning(msg)
                return False

            self.balance = round(self.balance + cost, 2)
            trade_pnl = round((exec_price - self.entry_price) * amount, 2)
            self.realized_pnl = round(self.realized_pnl + trade_pnl, 2)
            self.position_size = round(self.position_size - amount, 6)

            if self.position_size == 0.0:
                self.entry_price = 0.0
                self.unrealized_pnl = 0.0

            msg = f"[{now_str}] [ORDER] Executed SELL {amount:.4f} {self.symbol} @ ${exec_price:,.2f} (PnL: ${trade_pnl:+,.2f})"
            self._add_log(msg)
            logger.info(msg)

            self.orders.append(
                OrderRecord(
                    id=order_id,
                    timestamp=now_str,
                    symbol=self.symbol,
                    side="SELL",
                    amount=amount,
                    price=exec_price,
                    cost=cost,
                    status="FILLED",
                    pnl=trade_pnl,
                )
            )

        if len(self.orders) > 50:
            self.orders.pop(0)

        return True

    def trigger_kill_switch(self) -> Dict[str, Any]:
        """Emergency panic button: immediately close all open positions and liquidate at market price.

        Returns:
            Dict[str, Any]: Status summary of closed positions.
        """
        now_str = datetime.now().strftime("%H:%M:%S")
        if self.position_size > 0:
            closed_amount = self.position_size
            self.place_order("SELL", closed_amount, "MARKET")
            msg = f"[{now_str}] [KILL-SWITCH] Closed entire open position ({closed_amount:.4f} {self.symbol})!"
            self._add_log(msg)
            logger.warning(msg)
            return {"status": "executed", "closed_amount": closed_amount, "symbol": self.symbol}

        msg = f"[{now_str}] [KILL-SWITCH] No open positions to close."
        self._add_log(msg)
        return {"status": "noop", "message": "No open positions to liquidate", "symbol": self.symbol}

    def get_ticker(self) -> MarketTicker:
        """Return current market ticker data."""
        spread = round(self.current_price * 0.0002, 2)
        return MarketTicker(
            symbol=self.symbol,
            price=self.current_price,
            timestamp=datetime.now(timezone.utc).isoformat(),
            bid=round(self.current_price - spread, 2),
            ask=round(self.current_price + spread, 2),
            volume_24h=round(12450.5 + random.uniform(-10.0, 10.0), 2),
        )

    def get_orderbook(self, depth: int = 5) -> Dict[str, List[List[float]]]:
        """Generate or retrieve simulated Level 2 orderbook depth.

        Args:
            depth (int): Number of bid/ask levels.

        Returns:
            Dict[str, List[List[float]]]: Bids and asks lists of [price, size].
        """
        step = round(self.current_price * 0.0003, 2)
        asks = []
        for i in range(depth, 0, -1):
            p = round(self.current_price + (i * step), 2)
            size = round(random.uniform(0.1, 2.5), 3)
            asks.append([p, size])

        bids = []
        for i in range(1, depth + 1):
            p = round(self.current_price - (i * step), 2)
            size = round(random.uniform(0.1, 2.5), 3)
            bids.append([p, size])

        return {"symbol": self.symbol, "asks": asks, "bids": bids}

    def get_state(self) -> TradingState:
        """Return full trading desk state snapshot."""
        equity = round(self.balance + (self.position_size * self.current_price), 2)
        return TradingState(
            symbol=self.symbol,
            current_price=self.current_price,
            balance=self.balance,
            position_size=self.position_size,
            entry_price=self.entry_price,
            unrealized_pnl=self.unrealized_pnl,
            realized_pnl=self.realized_pnl,
            total_equity=equity,
            recent_logs=self.logs[-10:],
            recent_orders=self.orders[-10:],
        )

    def _add_log(self, msg: str) -> None:
        """Append log message and maintain fixed history limit."""
        self.logs.append(msg)
        if len(self.logs) > 50:
            self.logs.pop(0)
