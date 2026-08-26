# Simple Assistant Prototype

## Purpose
Minimalist user interface for testing conversational streaming interactions directly with the backend FastAPI endpoints.

---

## Components
- `index.html`: Lightweight chat page layout.
- `style.css`: Clean responsive light-theme styling.
- `main.js`: SSE token consumption and chat history state.

---

## Integration
- Serviced via FastAPI at `/simple-assistant/`.
- Sends requests directly to `POST /api/chat`.
