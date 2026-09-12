# Exchange & Stock Trading Terminal (`apps/trading_terminal`)

**Status:** ✅ Active  
**Language:** English  
**Authors:** hypo69  
**Package:** `apps.trading_terminal`  

---

## 📋 Overview

The **Trading Terminal** is a standalone financial control desk application providing real-time market data monitoring, Level 2 orderbook depth visualization, portfolio position and PnL tracking, order submission, and emergency kill-switch liquidation.

It operates seamlessly as:
1. **Interactive Rich TUI** for console / Windows Terminal split-pane desks.
2. **FastAPI Microservice** mounted under `/api/v1/trading` for web interfaces and external algorithmic trading bots.

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 apps.trading_terminal                        │
├──────────────────────────────┬──────────────────────────────┤
│     Rich TUI Dashboard       │     FastAPI Router           │
│     (tui.py / __main__.py)   │     (router.py)              │
│    • Live depth charts       │    • REST: /status, /ticker  │
│    • Portfolio PnL           │    • REST: /order, /kill     │
│    • Event log stream        │    • WebSocket: /ws/stream   │
└──────────────┬───────────────┴──────────────┬───────────────┘
               │                              │
               └──────────────┬───────────────┘
                              ▼
               ┌──────────────────────────────┐
               │    TradingDeskEngine         │
               │    (engine.py)               │
               │    • State & Balance         │
               │    • Order Execution         │
               │    • PnL Calculations        │
               └──────────────────────────────┘
```

---

## 🚀 CLI Usage

### Launch Interactive TUI
```powershell
# Default BTC/USDT desk
python -m apps.trading_terminal

# Custom pair and update interval
python -m apps.trading_terminal --symbol ETH/USDT --interval 0.25
```

### CLI Flags Reference

| Flag | Type | Default | Description |
|---|---|---|---|
| `--symbol` | `str` | `BTC/USDT` | Trading pair to monitor and trade. |
| `--interval` | `float` | `0.5` | Screen refresh interval in seconds. |
| `--balance` | `float` | `10000.0` | Initial starting account balance in USD. |

---

## 🔌 FastAPI REST & WebSocket Endpoints

Base URL: `/api/v1/trading`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/trading/status` | Returns complete desk state (balance, positions, equity, PnL, logs). |
| `GET` | `/api/v1/trading/ticker` | Returns latest market ticker, bid, ask, and 24h volume. |
| `GET` | `/api/v1/trading/orderbook` | Returns L2 orderbook bids and asks (`?depth=5`). |
| `GET` | `/api/v1/trading/orders` | Returns list of recently executed orders. |
| `POST` | `/api/v1/trading/order` | Place a new BUY or SELL order (`OrderRequest` payload). |
| `POST` | `/api/v1/trading/kill-switch` | Emergency liquidation: closes all open positions at market price. |
| `WS` | `/api/v1/trading/ws/stream` | WebSocket streaming live price ticks and state updates every second. |

### Example Order Request (`POST /api/v1/trading/order`)
```json
{
  "symbol": "BTC/USDT",
  "side": "BUY",
  "amount": 0.05,
  "order_type": "MARKET"
}
```

---

## 🧪 Testing

Run dedicated test suite:
```powershell
pytest tests/test_apps_trading.py -v
```
