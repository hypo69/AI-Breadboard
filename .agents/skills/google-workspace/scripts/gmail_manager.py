## \file .agents/skills/google-workspace/scripts/gmail_manager.py
# -*- coding: utf-8 -*-
#! venv/Scripts/python.exe

"""
Gmail Manager & Triage Module.
==============================

Provides functions to search, fetch, summarize emails and create drafts.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import base64
import argparse
import sys

from googleapiclient.discovery import build

from src.logger.logger import logger
from agents.skills.google_workspace.scripts.google_auth import get_credentials


class GmailManager:
    """Manages interactions with Gmail API."""

    def __init__(self, credentials=None) -> None:
        """Initialize Gmail service."""
        self.creds = credentials or get_credentials()
        self.service = build("gmail", "v1", credentials=self.creds) if self.creds else None

    def search_messages(self, query: str = "is:unread", max_results: int = 10) -> List[Dict[str, Any]]:
        """Search messages in Gmail matching query."""
        if not self.service:
            logger.error("Gmail service is not initialized.")
            return []

        try:
            results = self.service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
            messages = results.get("messages", [])
            return [self.get_message_summary(msg["id"]) for msg in messages if "id" in msg]
        except Exception as e:
            logger.error(f"Failed to search Gmail messages: {e}")
            return []

    def get_message_summary(self, message_id: str) -> Dict[str, Any]:
        """Fetch summary headers and snippet for a specific message ID."""
        if not self.service:
            return {"id": message_id, "error": "No service"}

        try:
            msg = self.service.users().messages().get(userId="me", id=message_id, format="full").execute()
            payload = msg.get("payload", {})
            headers = payload.get("headers", [])

            subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "(No Subject)")
            sender = next((h["value"] for h in headers if h["name"].lower() == "from"), "(Unknown)")
            date = next((h["value"] for h in headers if h["name"].lower() == "date"), "")
            snippet = msg.get("snippet", "")

            return {
                "id": message_id,
                "thread_id": msg.get("threadId"),
                "subject": subject,
                "from": sender,
                "date": date,
                "snippet": snippet,
                "labels": msg.get("labelIds", [])
            }
        except Exception as e:
            logger.error(f"Failed to fetch message {message_id}: {e}")
            return {"id": message_id, "error": str(e)}

    def create_draft(self, to: str, subject: str, body_text: str) -> Optional[Dict[str, Any]]:
        """Create an email draft."""
        if not self.service:
            logger.error("Gmail service not available.")
            return None

        try:
            message_text = f"To: {to}\r\nSubject: {subject}\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{body_text}"
            raw = base64.urlsafe_b64encode(message_text.encode("utf-8")).decode("utf-8")
            draft = self.service.users().drafts().create(
                userId="me",
                body={"message": {"raw": raw}}
            ).execute()
            logger.info(f"Draft created successfully. Draft ID: {draft.get('id')}")
            return draft
        except Exception as e:
            logger.error(f"Failed to create draft: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(description="Gmail CLI Manager")
    parser.add_argument("--query", "-q", default="is:unread", help="Search query (e.g., 'is:unread', 'from:boss')")
    parser.add_argument("--limit", "-l", type=int, default=5, help="Max results to fetch")
    args = parser.parse_args()

    manager = GmailManager()
    if not manager.service:
        print("❌ Could not authenticate with Gmail. Check credentials.json / .env.")
        sys.exit(1)

    print(f"🔍 Searching emails with query: '{args.query}' (limit: {args.limit})...")
    messages = manager.search_messages(query=args.query, max_results=args.limit)
    for i, msg in enumerate(messages, 1):
        print(f"\n[{i}] From: {msg.get('from')}")
        print(f"    Subject: {msg.get('subject')}")
        print(f"    Date: {msg.get('date')}")
        print(f"    Snippet: {msg.get('snippet')}")


if __name__ == "__main__":
    main()
