# Trading Controller Skill

This skill provides an interface to control the `trading_terminal` application within the AI Breadboard ecosystem.

## Features
- Real-time market data retrieval.
- Position and PnL monitoring.
- Order management (with mandatory user confirmation).
- Emergency kill-switch for all active orders.

## Requirements
- `trading_terminal` must be running (usually on port 8103).
- Valid configuration in `apps/trading_terminal/config.json`.
