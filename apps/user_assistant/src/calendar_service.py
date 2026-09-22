# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: User Assistant Calendar Service
# =============================================================================
# Description:
#   Provides calendar events retrieval, agenda compilation, and event scheduling
#   via Google Calendar and CalDAV endpoints.
#
# File: calendar_service.py
# Package: apps.user_assistant.src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from logger import logger


class CalendarService:
    """Manages user calendar schedule, agenda, and event creation."""

    def __init__(self, account_name: Optional[str] = None) -> None:
        """Initialize calendar service."""
        self.account_name = account_name

    def list_upcoming_events(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """List upcoming calendar events.

        Args:
            days_ahead (int): Number of days forward to search.

        Returns:
            List[Dict[str, Any]]: List of calendar event objects.
        """
        try:
            from src.ai.google_accounts_state import load_account_credentials
            from googleapiclient.discovery import build

            creds = load_account_credentials(self.account_name)
            if not creds:
                return []

            service = build("calendar", "v3", credentials=creds)
            now = datetime.now(timezone.utc).isoformat()
            time_max = (datetime.now(timezone.utc) + timedelta(days=days_ahead)).isoformat()

            events_result = service.events().list(
                calendarId="primary",
                timeMin=now,
                timeMax=time_max,
                maxResults=20,
                singleEvents=True,
                orderBy="startTime",
            ).execute()

            items = events_result.get("items", [])
            results = []
            for ev in items:
                start = ev.get("start", {}).get("dateTime", ev.get("start", {}).get("date"))
                end = ev.get("end", {}).get("dateTime", ev.get("end", {}).get("date"))
                results.append({
                    "id": ev.get("id"),
                    "summary": ev.get("summary", "No Title"),
                    "start": start,
                    "end": end,
                    "location": ev.get("location", ""),
                    "description": ev.get("description", ""),
                })
            return results
        except Exception as ex:
            logger.debug(f"Calendar service list_events: {ex}")
            return []

    def create_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: str = "",
        location: str = "",
    ) -> Dict[str, Any]:
        """Create a new event in user primary calendar."""
        try:
            from src.ai.google_accounts_state import load_account_credentials
            from googleapiclient.discovery import build

            creds = load_account_credentials(self.account_name)
            if not creds:
                return {"success": False, "error": "No valid calendar credentials"}

            service = build("calendar", "v3", credentials=creds)
            body = {
                "summary": summary,
                "description": description,
                "location": location,
                "start": {"dateTime": start_time} if "T" in start_time else {"date": start_time},
                "end": {"dateTime": end_time} if "T" in end_time else {"date": end_time},
            }
            res = service.events().insert(calendarId="primary", body=body).execute()
            return {"success": True, "event_id": res.get("id"), "event": res}
        except Exception as ex:
            logger.warning(f"Failed to create calendar event: {ex}")
            return {"success": False, "error": str(ex)}
