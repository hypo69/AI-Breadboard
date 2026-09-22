# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Trading Desk FastAPI Router & WebSocket Stream
# =============================================================================
# Description:
#   FastAPI REST and WebSocket endpoints for trading terminal state inspection,
#   order placement, emergency kill-switch liquidation, and real-time streaming.
#
# Examples:
#   >>> from fastapi import FastAPI
#   >>> from apps.trading_terminal.router import init_router
#   >>> app = FastAPI()
#   >>> app.include_router(init_router())
#
# File: router.py
# Project: ai-breadboard
# Package: apps.trading_terminal
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI router and WebSocket endpoints for trading terminal."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from logger import logger
from apps.common.csv_logger import AppCsvLogger
from .engine import (

    MarketTicker,
    OrderRecord,
    OrderRequest,
    TradingDeskEngine,
    TradingState,
)

# Global default desk engine instance for REST/WebSocket access
_default_engine: Optional[TradingDeskEngine] = None


def get_engine(symbol: str = "BTC/USDT") -> TradingDeskEngine:
    """Retrieve or initialize default trading desk engine singleton.

    Args:
        symbol (str): Trading pair symbol.

    Returns:
        TradingDeskEngine: Engine instance.
    """
    global _default_engine
    if _default_engine is None:
        _default_engine = TradingDeskEngine(symbol=symbol)
    return _default_engine


def init_router(engine: Optional[TradingDeskEngine] = None) -> APIRouter:
    """Initialize and configure Trading Terminal FastAPI router.

    Args:
        engine (Optional[TradingDeskEngine]): Optional custom engine instance.

    Returns:
        APIRouter: Configured FastAPI router.
    """
    router = APIRouter(prefix="/api/v1/trading", tags=["Trading Terminal"])
    active_engine = engine or get_engine()

    @router.get("/status", response_model=TradingState)
    async def get_trading_status() -> TradingState:
        """Retrieve full status of the trading desk."""
        st = active_engine.get_state()
        _default_csv_log = AppCsvLogger("trading_terminal")
        _default_csv_log.log_poll(
            poll_type="desk_status",
            metric_name="equity",
            value=st.total_equity,
            unit="USD",
            status="OK",
            details={"balance": st.balance, "position": st.position_size, "unrealized_pnl": st.unrealized_pnl},
            filename="trading_terminal_status_polls.csv",
        )
        return st


    @router.get("/ticker", response_model=MarketTicker)
    async def get_ticker() -> MarketTicker:
        """Retrieve real-time market ticker for active pair."""
        return active_engine.get_ticker()

    @router.get("/orderbook", response_model=Dict[str, Any])
    async def get_orderbook(depth: int = Query(default=5, ge=1, le=50)) -> Dict[str, Any]:
        """Retrieve Level 2 orderbook depth."""
        return active_engine.get_orderbook(depth=depth)

    @router.get("/orders", response_model=List[OrderRecord])
    async def list_orders() -> List[OrderRecord]:
        """List recently placed and executed orders."""
        return active_engine.orders

    @router.post("/order", response_model=Dict[str, Any])
    async def place_order(req: OrderRequest) -> Dict[str, Any]:
        """Submit a new buy or sell order."""
        success = active_engine.place_order(
            side=req.side,
            amount=req.amount,
            order_type=req.order_type,
            limit_price=req.price,
        )
        if not success:
            raise HTTPException(status_code=400, detail="Order execution rejected by trading engine")
        return {
            "status": "success",
            "message": f"Order {req.side.upper()} {req.amount} {active_engine.symbol} executed",
            "balance": active_engine.balance,
            "position": active_engine.position_size,
        }

    @router.post("/kill-switch", response_model=Dict[str, Any])
    async def trigger_kill_switch() -> Dict[str, Any]:
        """Emergency panic button: immediately close all open positions."""
        result = active_engine.trigger_kill_switch()
        return result

    @router.websocket("/ws/stream")
    async def trading_ws_stream(websocket: WebSocket) -> None:
        """Stream real-time price ticks and state updates to connected clients."""
        await websocket.accept()
        try:
            while True:
                active_engine.update_market()
                state = active_engine.get_state()
                await websocket.send_json(state.model_dump())
                await asyncio.sleep(1.0)
        except WebSocketDisconnect:
            logger.info("Client disconnected from trading stream WebSocket")
        except Exception as ex:
            logger.error("Error in trading WebSocket stream", exc_info=True)
            try:
                await websocket.send_json({"error": str(ex)})
            except Exception:
                pass

    return router
