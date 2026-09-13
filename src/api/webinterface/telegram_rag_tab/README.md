# Telegram Channel & Group RAG Search Tab

## Overview
This web interface tab provides an interactive frontend for the `telegram_channel_rag` plugin in AI Breadboard.

## Features
- **Channel & Group Subscription Management**: Add Telegram channel by username or link (e.g., `@canozrimb` or `https://t.me/canozrimb`), choose message fetch depth, view indexed messages, re-index on demand, or unsubscribe.
- **Unified & Per-Channel RAG Search**: Search across all subscribed channels concurrently (Unified Pool) or narrow search down to specific channels.
- **Message Cards & Direct Permalinks**: View matching messages with keyword highlights, channel metadata, author, date, and direct `https://t.me/...` links.
- **Chat Integration**: One-click insert of relevant message citations directly into the main AI chat.

## Files
- `index.html`: Responsive HTML layout with channel management sidebar and search pane.
- `main.js`: Client-side logic for API requests (`/api/telegram_rag/*`) and dynamic result rendering.
