from __future__ import annotations
from typing import Any, Dict, List, Optional
from apps.user_assistant.src.mail_service import MailService
from apps.user_assistant.src.calendar_service import CalendarService
from apps.user_assistant.src.docs_service import DocsService
from logger import logger

class UserAssistantEngine:
    """Core domain engine coordinating mail, calendar, and documents for a user."""

    def __init__(self, user_id: int=1, account_name: Optional[str]=None) -> None:
        """Initialize user assistant engine."""
        self.user_id = user_id
        self.account_name = account_name
        self.mail = MailService(account_name=account_name)
        self.calendar = CalendarService(account_name=account_name)
        self.docs = DocsService(user_id=user_id)

    def get_daily_agenda(self) -> Dict[str, Any]:
        """Compile a unified daily agenda overview."""
        events = self.calendar.list_upcoming_events(days_ahead=1)
        unread_emails = self.mail.list_messages(query='is:unread', max_results=5)
        files = self.docs.list_user_files(subfolder='files')
        return {'user_id': self.user_id, 'upcoming_events_count': len(events), 'events': events, 'unread_emails_count': len(unread_emails), 'emails': unread_emails, 'recent_files_count': len(files), 'files': files[:5]}