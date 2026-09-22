# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Contacts Assistant & Manager Module
# =============================================================================
# Description:
#   Provides functions to search, list, fetch, and create contacts via
#   Google People API (Google Contacts).
#
# File: gcontacts_manager.py
# Project: ai-breadboard
# Package: .agents.skills.google-contacts.scripts
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
from logger.logger import logger

SCOPES = [
    "https://www.googleapis.com/auth/contacts",
    "https://www.googleapis.com/auth/contacts.readonly",
    "https://www.googleapis.com/auth/userinfo.profile",
]


class GContactsManager:
    """Менеджер взаимодействия с Google People API (Контакты)."""

    def __init__(self, credentials=None, account_name: Optional[str] = None) -> None:
        """Инициализация сервиса Google People."""
        self.account_name = account_name
        self.creds = credentials or load_account_credentials(account_name=account_name, scopes=SCOPES)
        self.service = build("people", "v1", credentials=self.creds) if (self.creds and build) else None

    def list_contacts(self, page_size: int = 50) -> List[Dict[str, Any]]:
        """Получение списка контактов пользователя."""
        if not self.service:
            logger.error("Contacts сервис не инициализирован.")
            return []

        try:
            results = self.service.people().connections().list(
                resourceName="people/me",
                pageSize=page_size,
                personFields="names,emailAddresses,phoneNumbers,organizations,photos"
            ).execute()
            connections = results.get("connections", [])
            return [self._parse_person(c) for c in connections]
        except Exception as e:
            logger.error(f"Ошибка получения списка контактов: {e}")
            return []

    def search_contacts(self, query: str, page_size: int = 10) -> List[Dict[str, Any]]:
        """Поиск контактов по имени, email или номеру телефона."""
        if not self.service:
            return []

        try:
            results = self.service.people().searchContacts(
                query=query,
                pageSize=page_size,
                readMask="names,emailAddresses,phoneNumbers,organizations"
            ).execute()
            results_list = results.get("results", [])
            return [self._parse_person(r.get("person", {})) for r in results_list if "person" in r]
        except Exception as e:
            logger.warning(f"Ошибка поиска контактов через searchContacts: {e}. Поиск по локальному списку...")
            # Fallback к фильтрации локального списка
            all_c = self.list_contacts(page_size=100)
            q_low = query.lower()
            return [
                c for c in all_c
                if q_low in c.get("name", "").lower()
                or any(q_low in em.lower() for em in c.get("emails", []))
                or any(q_low in ph for ph in c.get("phones", []))
            ]

    def create_contact(
        self,
        given_name: str,
        family_name: str = "",
        email: str = "",
        phone: str = "",
        organization: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Создание нового контакта в Google Contacts."""
        if not self.service:
            return None

        body: Dict[str, Any] = {
            "names": [{"givenName": given_name, "familyName": family_name}]
        }
        if email:
            body["emailAddresses"] = [{"value": email, "type": "work"}]
        if phone:
            body["phoneNumbers"] = [{"value": phone, "type": "mobile"}]
        if organization:
            body["organizations"] = [{"name": organization}]

        try:
            contact = self.service.people().createContact(body=body).execute()
            logger.info(f"Контакт '{given_name} {family_name}' создан. ResourceName: {contact.get('resourceName')}")
            return self._parse_person(contact)
        except Exception as e:
            logger.error(f"Ошибка создания контакта '{given_name}': {e}")
            return None

    def _parse_person(self, person_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Преобразование структуры People API в удобный словарь."""
        names = person_dict.get("names", [])
        display_name = names[0].get("displayName", "") if names else "(Без имени)"
        emails = [em.get("value") for em in person_dict.get("emailAddresses", []) if em.get("value")]
        phones = [ph.get("value") for ph in person_dict.get("phoneNumbers", []) if ph.get("value")]
        orgs = [o.get("name") for o in person_dict.get("organizations", []) if o.get("name")]

        return {
            "resourceName": person_dict.get("resourceName"),
            "name": display_name,
            "emails": emails,
            "phones": phones,
            "organizations": orgs,
        }


def main():
    parser = argparse.ArgumentParser(description="Google Contacts Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Команды")

    # List
    list_p = subparsers.add_parser("list", help="Список контактов")
    list_p.add_argument("--limit", "-l", type=int, default=20, help="Количество")
    list_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    # Search
    search_p = subparsers.add_parser("search", help="Поиск контакта")
    search_p.add_argument("--query", "-q", required=True, help="Имя, email или телефон")
    search_p.add_argument("--limit", "-l", type=int, default=10, help="Количество")
    search_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    # Create
    create_p = subparsers.add_parser("create", help="Создать контакт")
    create_p.add_argument("--first", required=True, help="Имя")
    create_p.add_argument("--last", default="", help="Фамилия")
    create_p.add_argument("--email", default="", help="Email")
    create_p.add_argument("--phone", default="", help="Телефон")
    create_p.add_argument("--org", default="", help="Организация")
    create_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    args = parser.parse_args()
    manager = GContactsManager(account_name=getattr(args, "account", None))

    if not manager.service:
        print("❌ Не удалось авторизоваться в Google Contacts. Проверьте системный плагин google_oauth.")
        sys.exit(1)

    if args.command == "list" or not args.command:
        limit = getattr(args, "limit", 20)
        contacts = manager.list_contacts(page_size=limit)
        print(f"👥 Найдено {len(contacts)} контактов:")
        for i, c in enumerate(contacts, 1):
            print(f"[{i}] {c['name']} | Email: {', '.join(c['emails']) or '-'} | Телефон: {', '.join(c['phones']) or '-'}")
    elif args.command == "search":
        contacts = manager.search_contacts(query=args.query, page_size=args.limit)
        print(f"🔍 Найдено {len(contacts)} совпадений по '{args.query}':")
        for i, c in enumerate(contacts, 1):
            print(f"[{i}] {c['name']} | Email: {', '.join(c['emails']) or '-'} | Телефон: {', '.join(c['phones']) or '-'}")
    elif args.command == "create":
        c = manager.create_contact(args.first, family_name=args.last, email=args.email, phone=args.phone, organization=args.org)
        if c:
            print(f"✅ Контакт создан: {c['name']}")


if __name__ == "__main__":
    main()

