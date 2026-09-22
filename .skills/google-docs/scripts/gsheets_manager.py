# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Sheets Assistant & Manager Module
# =============================================================================
# Description:
#   Provides functions to read, search, append, and update Google Sheets spreadsheets.
#
# File: gsheets_manager.py
# Project: ai-breadboard
# Package: .agents.skills.google-docs.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import argparse
import json
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
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class GSheetsManager:
    """Менеджер взаимодействия с Google Sheets API."""

    def __init__(self, credentials=None, account_name: Optional[str] = None) -> None:
        """Инициализация сервиса Google Sheets."""
        self.account_name = account_name
        self.creds = credentials or load_account_credentials(account_name=account_name, scopes=SCOPES)
        self.service = build("sheets", "v4", credentials=self.creds) if (self.creds and build) else None

    def get_spreadsheet_info(self, spreadsheet_id: str) -> Optional[Dict[str, Any]]:
        """Получение метаданных таблицы и списка листов."""
        if not self.service:
            logger.error("Sheets сервис не инициализирован.")
            return None

        try:
            result = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheets = [
                {
                    "sheet_id": s["properties"]["sheetId"],
                    "title": s["properties"]["title"],
                    "index": s["properties"].get("index", 0),
                    "row_count": s["properties"]["gridProperties"].get("rowCount", 0),
                    "column_count": s["properties"]["gridProperties"].get("columnCount", 0),
                }
                for s in result.get("sheets", [])
            ]
            return {
                "spreadsheet_id": spreadsheet_id,
                "title": result.get("properties", {}).get("title", ""),
                "sheets": sheets,
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации о таблице {spreadsheet_id}: {e}")
            return None

    def read_range(self, spreadsheet_id: str, range_name: str = "A1:Z100") -> List[List[Any]]:
        """Чтение значений из указанного диапазона (например, 'Лист1!A1:D20')."""
        if not self.service:
            return []

        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range_name
            ).execute()
            return result.get("values", [])
        except Exception as e:
            logger.error(f"Ошибка чтения диапазона {range_name} в {spreadsheet_id}: {e}")
            return []

    def append_rows(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> Optional[Dict[str, Any]]:
        """Добавление строк в таблицу."""
        if not self.service:
            return None

        try:
            body = {"values": values}
            result = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body,
            ).execute()
            logger.info(f"Добавлено {len(values)} строк в {spreadsheet_id}")
            return result
        except Exception as e:
            logger.error(f"Ошибка добавления строк в {spreadsheet_id}: {e}")
            return None

    def update_range(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> Optional[Dict[str, Any]]:
        """Обновление ячеек в диапазоне."""
        if not self.service:
            return None

        try:
            body = {"values": values}
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body,
            ).execute()
            logger.info(f"Обновлен диапазон {range_name} в {spreadsheet_id}")
            return result
        except Exception as e:
            logger.error(f"Ошибка обновления ячеек в {spreadsheet_id}: {e}")
            return None

    def search(self, spreadsheet_id: str, query: str, range_name: str = "A1:Z1000") -> List[Dict[str, Any]]:
        """Поиск подстроки по ячейкам диапазона."""
        rows = self.read_range(spreadsheet_id, range_name)
        matches = []
        q_lower = query.lower()

        for row_idx, row in enumerate(rows, 1):
            row_str = " ".join(str(cell) for cell in row)
            if q_lower in row_str.lower():
                matches.append({"row_index": row_idx, "values": row})

        return matches


def main():
    parser = argparse.ArgumentParser(description="Google Sheets Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Команды")

    # Info
    info_p = subparsers.add_parser("info", help="Метаданные таблицы")
    info_p.add_argument("--id", required=True, help="Spreadsheet ID")
    info_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    # Read
    read_p = subparsers.add_parser("read", help="Чтение диапазона")
    read_p.add_argument("--id", required=True, help="Spreadsheet ID")
    read_p.add_argument("--range", "-r", default="A1:Z50", help="Диапазон (например: Sheet1!A1:D10)")
    read_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    # Search
    search_p = subparsers.add_parser("search", help="Поиск текста в таблице")
    search_p.add_argument("--id", required=True, help="Spreadsheet ID")
    search_p.add_argument("--query", "-q", required=True, help="Текст поиска")
    search_p.add_argument("--range", "-r", default="A1:Z500", help="Диапазон поиска")
    search_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    # Append
    append_p = subparsers.add_parser("append", help="Добавить строку")
    append_p.add_argument("--id", required=True, help="Spreadsheet ID")
    append_p.add_argument("--range", "-r", default="Sheet1!A1", help="Целевой диапазон/лист")
    append_p.add_argument("--data", "-d", required=True, help="JSON массив значений, напр: '[\"val1\", \"val2\"]'")
    append_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    args = parser.parse_args()
    manager = GSheetsManager(account_name=getattr(args, "account", None))

    if not manager.service:
        print("❌ Не удалось авторизоваться в Google Sheets. Проверьте системный плагин google_oauth.")
        sys.exit(1)

    if args.command == "info":
        info = manager.get_spreadsheet_info(args.id)
        if info:
            print(f"📊 Название: {info['title']}")
            for s in info["sheets"]:
                print(f"  - {s['title']} (Строк: {s['row_count']}, Колонок: {s['column_count']})")
    elif args.command == "read":
        rows = manager.read_range(args.id, args.range)
        for r in rows:
            print("\t|\t".join(str(c) for c in r))
    elif args.command == "search":
        matches = manager.search(args.id, args.query, args.range)
        print(f"🔍 Найдено {len(matches)} совпадений:")
        for m in matches:
            print(f"Строка {m['row_index']}: {m['values']}")
    elif args.command == "append":
        try:
            row_data = json.loads(args.data)
            if not isinstance(row_data[0], list):
                row_data = [row_data]
            manager.append_rows(args.id, args.range, row_data)
            print(f"✅ Строка успешно добавлена в {args.id}")
        except Exception as e:
            print(f"❌ Ошибка добавления: {e}")


if __name__ == "__main__":
    main()

