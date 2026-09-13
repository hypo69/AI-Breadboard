# Google Workspace Skill

## Overview
Google Workspace integration (Gmail, Google Drive, Google Sheets, Google Docs) for email triage, document search, spreadsheet manipulation, and RAG ingestion.

## Location
`.agents/skills/google-workspace/`

## Components
- `scripts/google_auth.py`: Multi-mode authentication engine supporting Service Accounts, OAuth 2.0, and environment credentials.
- `scripts/gsheets_manager.py`: Google Sheets manipulation (metadata, reading cell ranges, appending rows, searching).
- `scripts/gdrive_manager.py`: Google Drive file listing, querying, and downloading/exporting.
- `scripts/gmail_manager.py`: Gmail triage, unread digest, and draft creation.
- `scripts/sync_drive_rag.py`: Google Drive to RAG document ingestion pipeline.
