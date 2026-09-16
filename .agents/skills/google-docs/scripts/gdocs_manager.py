# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Docs Assistant & Manager Module
# =============================================================================
# Description:
#   Provides functions to create, read, and insert text into Google Documents
#   via Google Docs API v1.
#
# File: gdocs_manager.py
# Project: ai-breadboard
# Package: .agents.skills.google-docs.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import argparse
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
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]


class GDocsManager:
    """Менеджер взаимодействия с Google Docs API."""

    def __init__(self, credentials=None, account_name: Optional[str] = None) -> None:
        """Инициализация сервиса Google Docs."""
        self.account_name = account_name
        self.creds = credentials or load_account_credentials(account_name=account_name, scopes=SCOPES)
        self.service = build("docs", "v1", credentials=self.creds) if (self.creds and build) else None
        self.drive_service = build("drive", "v3", credentials=self.creds) if (self.creds and build) else None

    def create_document(self, title: str) -> Optional[Dict[str, Any]]:
        """Создание нового Google Документа."""
        if not self.service:
            logger.error("Docs сервис не инициализирован.")
            return None

        try:
            body = {"title": title}
            doc = self.service.documents().create(body=body).execute()
            doc_id = doc.get("documentId")
            logger.info(f"Google Документ '{title}' успешно создан. ID: {doc_id}")
            return doc
        except Exception as e:
            logger.error(f"Ошибка создания документа '{title}': {e}")
            return None

    def get_document_text(self, document_id: str) -> str:
        """Извлечение полного текстового содержимого документа."""
        if not self.service:
            return ""

        try:
            doc = self.service.documents().get(documentId=document_id).execute()
            content = doc.get("body", {}).get("content", [])
            text_chunks = []
            for element in content:
                if "paragraph" in element:
                    for el in element["paragraph"].get("elements", []):
                        text_run = el.get("textRun", {})
                        if "content" in text_run:
                            text_chunks.append(text_run["content"])
            return "".join(text_chunks)
        except Exception as e:
            logger.error(f"Ошибка чтения документа {document_id}: {e}")
            return ""

    def append_text(self, document_id: str, text: str) -> bool:
        """Добавление текста в конец документа."""
        if not self.service:
            return False

        try:
            doc = self.service.documents().get(documentId=document_id).execute()
            content = doc.get("body", {}).get("content", [])
            end_index = 1
            if content:
                end_index = content[-1].get("endIndex", 1) - 1

            requests_list = [
                {
                    "insertText": {
                        "location": {"index": max(1, end_index)},
                        "text": text if text.endswith("\n") else text + "\n",
                    }
                }
            ]
            self.service.documents().batchUpdate(
                documentId=document_id,
                body={"requests": requests_list}
            ).execute()
            logger.info(f"Текст успешно добавлен в документ {document_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления текста в документ {document_id}: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Google Docs Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Команды")

    # Create
    create_p = subparsers.add_parser("create", help="Создать документ")
    create_p.add_argument("--title", "-t", required=True, help="Название документа")
    create_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    # Read
    read_p = subparsers.add_parser("read", help="Прочитать документ")
    read_p.add_argument("--id", required=True, help="ID документа")
    read_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    # Append
    app_p = subparsers.add_parser("append", help="Добавить текст в документ")
    app_p.add_argument("--id", required=True, help="ID документа")
    app_p.add_argument("--text", required=True, help="Текст для вставки")
    app_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    args = parser.parse_args()
    manager = GDocsManager(account_name=getattr(args, "account", None))

    if not manager.service:
        print("❌ Не удалось авторизоваться в Google Docs. Проверьте системный плагин google_oauth.")
        sys.exit(1)

    if args.command == "create":
        doc = manager.create_document(args.title)
        if doc:
            print(f"✅ Документ создан: '{doc.get('title')}' (ID: {doc.get('documentId')})")
    elif args.command == "read":
        text = manager.get_document_text(args.id)
        print(f"📄 Содержимое документа:\n{text}")
    elif args.command == "append":
        ok = manager.append_text(args.id, args.text)
        if ok:
            print(f"✅ Текст успешно добавлен в документ {args.id}")


if __name__ == "__main__":
    main()

