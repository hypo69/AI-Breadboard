# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Calendar Assistant & Manager Module
# =============================================================================
# Description:
#   Provides functions to list, create, search, and manage Google Calendar events
#   and appointments.
#
# File: gcalendar_manager.py
# Project: ai-breadboard
# Package: .agents.skills.google-calendar.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from googleapiclient.discovery import build
except ImportError:
    build = None

from src.ai.google_accounts_state import load_account_credentials
from src.logger.logger import logger

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]


class GCalendarManager:
    """Менеджер взаимодействия с Google Calendar API."""

    def __init__(self, credentials=None, account_name: Optional[str] = None) -> None:
        """Инициализация сервиса Google Calendar."""
        self.account_name = account_name
        self.creds = credentials or load_account_credentials(account_name=account_name, scopes=SCOPES)
        self.service = build("calendar", "v3", credentials=self.creds) if (self.creds and build) else None

    def list_events(
        self,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results: int = 10,
        calendar_id: str = "primary",
    ) -> List[Dict[str, Any]]:
        """Получение списка событий календаря."""
        if not self.service:
            logger.error("Calendar сервис не инициализирован.")
            return []

        if not time_min:
            time_min = datetime.now(timezone.utc).isoformat()

        try:
            params = {
                "calendarId": calendar_id,
                "timeMin": time_min,
                "singleEvents": True,
                "orderBy": "startTime",
                "maxResults": max_results,
            }
            if time_max:
                params["timeMax"] = time_max

            events_result = self.service.events().list(**params).execute()
            items = events_result.get("items", [])
            return [
                {
                    "id": ev.get("id"),
                    "summary": ev.get("summary", "(Без названия)"),
                    "description": ev.get("description", ""),
                    "start": ev.get("start", {}).get("dateTime", ev.get("start", {}).get("date")),
                    "end": ev.get("end", {}).get("dateTime", ev.get("end", {}).get("date")),
                    "htmlLink": ev.get("htmlLink"),
                    "attendees": [a.get("email") for a in ev.get("attendees", [])],
                }
                for ev in items
            ]
        except Exception as e:
            logger.error(f"Ошибка получения событий календаря: {e}")
            return []

    def create_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: str = "",
        attendees: Optional[List[str]] = None,
        calendar_id: str = "primary",
    ) -> Optional[Dict[str, Any]]:
        """Создание нового события в календаре.

        Args:
            summary: Название события
            start_time: Начало в ISO формате (например, '2026-09-17T10:00:00+03:00')
            end_time: Окончание в ISO формате
            description: Описание события
            attendees: Список email участников
            calendar_id: ID календаря (по умолчанию 'primary')
        """
        if not self.service:
            return None

        event_body: Dict[str, Any] = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_time},
            "end": {"dateTime": end_time},
        }

        if attendees:
            event_body["attendees"] = [{"email": email.strip()} for email in attendees]

        try:
            event = self.service.events().insert(
                calendarId=calendar_id, body=event_body
            ).execute()
            logger.info(f"Событие '{summary}' создано в календаре. ID: {event.get('id')}")
            return event
        except Exception as e:
            logger.error(f"Ошибка создания события в календаре: {e}")
            return None

    def delete_event(self, event_id: str, calendar_id: str = "primary") -> bool:
        """Удаление события из календаря."""
        if not self.service:
            return False

        try:
            self.service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            logger.info(f"Событие {event_id} удалено из календаря.")
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления события {event_id}: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Google Calendar Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Команды")

    # List
    list_p = subparsers.add_parser("list", help="Список предстоящих событий")
    list_p.add_argument("--limit", "-l", type=int, default=10, help="Количество событий")
    list_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    # Create
    create_p = subparsers.add_parser("create", help="Создать событие")
    create_p.add_argument("--summary", "-s", required=True, help="Название события")
    create_p.add_argument("--start", required=True, help="Время начала (ISO формат)")
    create_p.add_argument("--end", required=True, help="Время окончания (ISO формат)")
    create_p.add_argument("--desc", default="", help="Описание")
    create_p.add_argument("--attendees", default="", help="Email участников через запятую")
    create_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    # Delete
    del_p = subparsers.add_parser("delete", help="Удалить событие")
    del_p.add_argument("--id", required=True, help="ID события")
    del_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    args = parser.parse_args()
    manager = GCalendarManager(account_name=getattr(args, "account", None))

    if not manager.service:
        print("❌ Не удалось авторизоваться в Google Calendar. Проверьте системный плагин google_oauth.")
        sys.exit(1)

    if args.command == "list" or not args.command:
        limit = getattr(args, "limit", 10)
        events = manager.list_events(max_results=limit)
        print(f"📅 Найдено {len(events)} событий:")
        for i, ev in enumerate(events, 1):
            print(f"[{i}] {ev['summary']} ({ev['start']} - {ev['end']}) ID: {ev['id']}")
    elif args.command == "create":
        att_list = [a.strip() for a in args.attendees.split(",") if a.strip()] if args.attendees else None
        ev = manager.create_event(args.summary, args.start, args.end, description=args.desc, attendees=att_list)
        if ev:
            print(f"✅ Событие создано. ID: {ev.get('id')}, Ссылка: {ev.get('htmlLink')}")
    elif args.command == "delete":
        ok = manager.delete_event(args.id)
        if ok:
            print(f"✅ Событие {args.id} удалено.")


if __name__ == "__main__":
    main()

