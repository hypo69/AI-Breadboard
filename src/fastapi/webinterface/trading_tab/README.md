# Trading Terminal Admin Tab (`src/fastapi/webinterface/trading_tab`)

**Status:** ✅ Active  
**Language:** English  
**Authors:** hypo69  

---

## 📋 Overview

The `trading_tab` module provides the administrative web UI for the standalone **Trading Terminal** (`/apps/trading_terminal`). It enables real-time price monitoring, Level 2 orderbook inspection, buy/sell order placement, portfolio equity tracking, and one-click emergency liquidation (Kill-Switch).

---

## 🚀 Key Features

- **Real-Time WebSocket Stream:** Dynamic state updates and price ticks over `/api/v1/trading/ws/stream`.
- **Level 2 Orderbook:** Interactive depth visualization for bids and asks.
- **Order Execution:** Instant market and limit order execution via `/api/v1/trading/order`.
- **Kill-Switch:** Emergency panic button to close all open market positions via `/api/v1/trading/kill-switch`.
- **Order History:** Real-time log of executed orders.
