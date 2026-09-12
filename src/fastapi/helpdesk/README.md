# Helpdesk Subsystem (`src/fastapi/helpdesk`)

The `src/fastapi/helpdesk` package provides an enterprise-ready support ticket and centralized chat management solution with real-time WebSocket communication, operator assignment, SLA/priority tracking, and standalone web UI (`/helpdesk`).

---

## 🏛️ Architecture Overview

```
src/fastapi/helpdesk/
├── __init__.py          # Package initialization and exports
├── database.py          # SQLite WAL schema, connection pooling & migrations
├── models.py            # Pydantic models for tickets, messages & statistics
├── router_helpdesk.py   # REST and WebSocket API endpoints
├── ws_manager.py        # Real-time WebSocket connection hub & dispatcher
├── helpdesk.db          # SQLite persistent database file
└── README.md            # English package documentation
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/helpdesk/tickets` | Query and filter support tickets by status, priority, or user |
| `POST` | `/api/helpdesk/tickets` | Create a new support ticket and send initial message |
| `GET` | `/api/helpdesk/tickets/{id}` | Retrieve ticket details and conversation thread |
| `PATCH` | `/api/helpdesk/tickets/{id}` | Update ticket status, priority, or assign operator |
| `POST` | `/api/helpdesk/tickets/{id}/messages` | Send message/reply or internal operator note |
| `GET` | `/api/helpdesk/stats` | Aggregate metrics (open, in-progress, resolved, urgent) |
| `WS` | `/api/helpdesk/ws/{client_id}` | Real-time WebSocket stream for tickets & chat |

---

## 💻 Web Management Interface

A dedicated web UI is accessible at `/helpdesk` providing:
- Real-time ticket list with status and priority badges.
- Active ticket conversation view with markdown rendering.
- Quick status changers (`Open`, `In Progress`, `Resolved`, `Closed`).
- Priority controls (`Low`, `Normal`, `High`, `Urgent`).
- Internal notes toggle (for operator-only annotations).
- Live alerts for new incoming customer tickets.

---

**Author:** hypo69  
**Version:** 1.0  
**License:** Standard AI-Breadboard License
