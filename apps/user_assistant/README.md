# User Personal Assistant Desk (`apps/user_assistant`)

**Status:** ✅ Active  
**Language:** English  
**Author:** hypo69  
**Version:** 1.0.0  

---

## 📋 Overview

The **User Assistant** application is an all-in-one personal workspace for managing daily productivity:
- ✉️ **Email Center:** Search inbox messages, review summaries, and generate draft responses via Gmail/IMAP.
- 📅 **Calendar & Scheduling:** View upcoming Google Calendar events, schedule new appointments, and compile daily agendas.
- 📁 **Personal Documents:** Browse sandboxed user files, search documents, and trigger RAG vector ingestion.

---

## 🏛️ Architecture

```
apps/user_assistant/
├── __init__.py
├── __main__.py              # CLI launcher
├── config.json              # App configuration
├── engine.py                # Business logic orchestrator
├── router.py                # FastAPI endpoints (/api/v1/assistant/*)
├── tui.py                   # Rich terminal dashboard
├── README.md
└── src/
    ├── mail_service.py      # Gmail & IMAP integration
    ├── calendar_service.py  # Google Calendar API
    └── docs_service.py      # Personal storage & RAG indexer
```

---

## 🌐 FastAPI REST Endpoints (`/api/v1/assistant`)

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/assistant/agenda` | `GET` | Retrieve daily overview (calendar, unread mail, recent docs) |
| `/api/v1/assistant/mail` | `GET` | List and search inbox messages |
| `/api/v1/assistant/mail/draft` | `POST` | Create a new email draft |
| `/api/v1/assistant/calendar` | `GET` | List upcoming appointments |
| `/api/v1/assistant/calendar/event` | `POST` | Schedule a new calendar event |
| `/api/v1/assistant/documents` | `GET` | List personal document files |

---

## 💻 Terminal Command

Launch the interactive terminal desk:
```powershell
python -m apps.user_assistant
```
