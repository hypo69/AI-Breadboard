# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Gmail Assistant & Manager Module
# =============================================================================
# Description:
#   Provides functions to search, fetch, summarize emails, compose and send
#   messages, and manage drafts via Gmail API.
#
# File: gmail_manager.py
# Project: ai-breadboard
# Package: .agents.skills.google-mail.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import argparse
import base64
from email.mime.text import MIMEText
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    build = None
    HttpError = Exception

from src.ai.google_accounts_state import load_account_credentials
from logger.logger import logger

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


class GmailManager:
    """Менеджер взаимодействия с Gmail API."""

    def __init__(self, credentials=None, account_name: Optional[str] = None) -> None:
        """Инициализация сервиса Gmail."""
        self.account_name = account_name
        self.creds = credentials or load_account_credentials(account_name=account_name, scopes=SCOPES)
        self.service = build("gmail", "v1", credentials=self.creds) if (self.creds and build) else None

    def search_messages(self, query: str = "is:unread", max_results: int = 10) -> List[Dict[str, Any]]:
        """Поиск сообщений по запросу (например, 'is:unread', 'from:boss')."""
        if not self.service:
            logger.warning("Gmail сервис не инициализирован (отсутствуют валидные токены).")
            return []

        try:
            results = self.service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
            messages = results.get("messages", [])
            return [self.get_message_summary(msg["id"]) for msg in messages if "id" in msg]
        except Exception as e:
            logger.warning(f"Ошибка поиска писем в Gmail: {e}")
            return []

    def get_message_summary(self, message_id: str) -> Dict[str, Any]:
        """Получение заголовков, сниппета и тела письма по ID."""
        if not self.service:
            return {"id": message_id, "error": "Сервис недоступен"}

        try:
            msg = self.service.users().messages().get(userId="me", id=message_id, format="full").execute()
            payload = msg.get("payload", {})
            headers = payload.get("headers", [])

            subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "(Без темы)")
            sender = next((h["value"] for h in headers if h["name"].lower() == "from"), "(Неизвестный)")
            date = next((h["value"] for h in headers if h["name"].lower() == "date"), "")
            snippet = msg.get("snippet", "")

            return {
                "id": message_id,
                "thread_id": msg.get("threadId"),
                "subject": subject,
                "from": sender,
                "date": date,
                "snippet": snippet,
                "labels": msg.get("labelIds", []),
            }
        except Exception as e:
            logger.error(f"Ошибка получения письма {message_id}: {e}")
            return {"id": message_id, "error": str(e)}

    def create_draft(self, to: str, subject: str, body_text: str) -> Optional[Dict[str, Any]]:
        """Создание черновика письма."""
        if not self.service:
            logger.error("Gmail сервис недоступен.")
            return None

        try:
            message = MIMEText(body_text, _charset="utf-8")
            message["to"] = to
            message["subject"] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            draft = self.service.users().drafts().create(
                userId="me",
                body={"message": {"raw": raw}}
            ).execute()
            logger.info(f"Черновик успешно создан. Draft ID: {draft.get('id')}")
            return draft
        except Exception as e:
            logger.error(f"Ошибка создания черновика: {e}")
            return None

    def send_email(self, to: str, subject: str, body_text: str) -> Optional[Dict[str, Any]]:
        """Прямая отправка электронного письма."""
        if not self.service:
            logger.error("Gmail сервис недоступен.")
            return None

        try:
            message = MIMEText(body_text, _charset="utf-8")
            message["to"] = to
            message["subject"] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            sent = self.service.users().messages().send(
                userId="me",
                body={"raw": raw}
            ).execute()
            logger.info(f"Письмо успешно отправлено адресату {to}. ID: {sent.get('id')}")
            return sent
        except Exception as e:
            logger.error(f"Ошибка отправки письма {to}: {e}")
            return None

    def delete_message(self, message_id: str) -> bool:
        """Удаление письма по ID."""
        if not self.service:
            logger.error("Gmail сервис недоступен.")
            return False

        try:
            self.service.users().messages().delete(userId="me", id=message_id).execute()
            logger.info(f"Письмо {message_id} успешно удалено.")
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления письма {message_id}: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Gmail Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Команды")

    # Search
    search_p = subparsers.add_parser("search", help="Поиск писем")
    search_p.add_argument("--query", "-q", default="is:unread", help="Поисковый запрос")
    search_p.add_argument("--limit", "-l", type=int, default=5, help="Лимит")
    search_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    # Draft
    draft_p = subparsers.add_parser("draft", help="Создать черновик")
    draft_p.add_argument("--to", required=True, help="Получатель")
    draft_p.add_argument("--subject", required=True, help="Тема")
    draft_p.add_argument("--body", required=True, help="Текст письма")
    draft_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    # Send
    send_p = subparsers.add_parser("send", help="Отправить письмо")
    send_p.add_argument("--to", required=True, help="Получатель")
    send_p.add_argument("--subject", required=True, help="Тема")
    send_p.add_argument("--body", required=True, help="Текст письма")
    send_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    # Delete
    delete_p = subparsers.add_parser("delete", help="Удалить письмо")
    delete_p.add_argument("--id", required=True, help="ID письма для удаления")
    delete_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    args = parser.parse_args()
    manager = GmailManager(account_name=getattr(args, "account", None))

    if not manager.service:
        print("❌ Не удалось авторизоваться в Gmail. Проверьте системный плагин google_oauth.")
        sys.exit(1)

    if args.command == "search" or not args.command:
        query = getattr(args, "query", "is:unread")
        limit = getattr(args, "limit", 5)
        print(f"🔍 Поиск писем по запросу: '{query}' (лимит: {limit})...")
        messages = manager.search_messages(query=query, max_results=limit)
        for i, msg in enumerate(messages, 1):
            print(f"\n[{i}] ID: {msg.get('id')}")
            print(f"    От: {msg.get('from')}")
            print(f"    Тема: {msg.get('subject')}")
            print(f"    Дата: {msg.get('date')}")
            print(f"    Сниппет: {msg.get('snippet')}")
    elif args.command == "draft":
        res = manager.create_draft(args.to, args.subject, args.body)
        if res:
            print(f"✅ Черновик создан. ID: {res.get('id')}")
    elif args.command == "send":
        res = manager.send_email(args.to, args.subject, args.body)
        if res:
            print(f"✅ Письмо отправлено на {args.to}. ID: {res.get('id')}")
    elif args.command == "delete":
        if manager.delete_message(args.id):
            print(f"✅ Письмо {args.id} удалено.")
        else:
            print(f"❌ Ошибка удаления письма {args.id}.")


if __name__ == "__main__":
    main()

