## \file .agents/skills/google-workspace/scripts/gsheets_manager.py
# -*- coding: utf-8 -*-
#! venv/Scripts/python.exe

"""
Google Sheets Manager Module.
=============================

Provides functions to read, search, append, and update Google Sheets spreadsheets.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse
import json
import sys

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Ensure scripts directory is on sys.path
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

try:
    from googleapiclient.discovery import build
except ImportError:
    build = None

from src.logger.logger import logger

try:
    from google_auth import get_credentials
except ImportError:
    from .google_auth import get_credentials


class GSheetsManager:
    """Manages interactions with Google Sheets API."""

    def __init__(self, credentials=None, account_name: Optional[str] = None) -> None:
        """Initialize Google Sheets service."""
        if build is None:
            logger.error("google-api-python-client is not installed.")
            self.service = None
            return

        self.account_name = account_name
        self.creds = credentials or get_credentials(account_name=account_name)
        self.service = (
            build("sheets", "v4", credentials=self.creds) if self.creds else None
        )

    def get_spreadsheet_info(self, spreadsheet_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch spreadsheet metadata and sheet list.

        :param spreadsheet_id: The ID of the spreadsheet.
        :return: Dict with spreadsheet properties and sheet list.
        """
        if not self.service:
            logger.error("Sheets service is not initialized.")
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
            logger.error(f"Failed to get spreadsheet info for {spreadsheet_id}: {e}")
            return None

    def read_range(
        self,
        spreadsheet_id: str,
        range_name: str = "A1:Z100",
    ) -> List[List[Any]]:
        """
        Read values from a specific cell range.

        :param spreadsheet_id: The ID of the spreadsheet.
        :param range_name: A1 notation range (e.g., 'Sheet1!A1:E20').
        :return: 2D list of row values.
        """
        if not self.service:
            logger.error("Sheets service is not initialized.")
            return []

        try:
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )
            return result.get("values", [])
        except Exception as e:
            logger.error(f"Failed to read range {range_name} from {spreadsheet_id}: {e}")
            return []

    def append_rows(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> Optional[Dict[str, Any]]:
        """
        Append rows to a sheet.

        :param spreadsheet_id: The ID of the spreadsheet.
        :param range_name: A1 notation range (e.g., 'Sheet1!A1').
        :param values: 2D list of values to append.
        :param value_input_option: 'RAW' or 'USER_ENTERED'.
        :return: API response dict or None.
        """
        if not self.service:
            logger.error("Sheets service is not initialized.")
            return None

        try:
            body = {"values": values}
            result = (
                self.service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption=value_input_option,
                    body=body,
                )
                .execute()
            )
            logger.info(f"Appended {len(values)} rows to {spreadsheet_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to append rows to {spreadsheet_id}: {e}")
            return None

    def update_range(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> Optional[Dict[str, Any]]:
        """
        Update specific cell range with values.

        :param spreadsheet_id: The ID of the spreadsheet.
        :param range_name: A1 notation range (e.g., 'Sheet1!A1:C3').
        :param values: 2D list of values to set.
        :param value_input_option: 'RAW' or 'USER_ENTERED'.
        :return: API response dict or None.
        """
        if not self.service:
            logger.error("Sheets service is not initialized.")
            return None

        try:
            body = {"values": values}
            result = (
                self.service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption=value_input_option,
                    body=body,
                )
                .execute()
            )
            logger.info(f"Updated range {range_name} in {spreadsheet_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to update range {range_name} in {spreadsheet_id}: {e}")
            return None

    def search(
        self,
        spreadsheet_id: str,
        query: str,
        range_name: str = "A1:Z1000",
    ) -> List[Dict[str, Any]]:
        """
        Search for query text across cells within a range.

        :param spreadsheet_id: The ID of the spreadsheet.
        :param query: Search substring (case-insensitive).
        :param range_name: Range to search in.
        :return: List of matches with row index and row content.
        """
        rows = self.read_range(spreadsheet_id, range_name)
        matches = []
        q_lower = query.lower()

        for row_idx, row in enumerate(rows, 1):
            row_str = " ".join(str(cell) for cell in row)
            if q_lower in row_str.lower():
                matches.append({
                    "row_index": row_idx,
                    "values": row,
                })

        return matches


def main():
    parser = argparse.ArgumentParser(description="Google Sheets CLI Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Info
    info_p = subparsers.add_parser("info", help="Get spreadsheet metadata and sheet list")
    info_p.add_argument("--id", required=True, help="Spreadsheet ID")

    # Read
    read_p = subparsers.add_parser("read", help="Read values from range")
    read_p.add_argument("--id", required=True, help="Spreadsheet ID")
    read_p.add_argument("--range", "-r", default="A1:Z50", help="Range (e.g. Sheet1!A1:D10)")

    # Search
    search_p = subparsers.add_parser("search", help="Search text in sheet")
    search_p.add_argument("--id", required=True, help="Spreadsheet ID")
    search_p.add_argument("--query", "-q", required=True, help="Search term")
    search_p.add_argument("--range", "-r", default="A1:Z500", help="Range to search in")

    # Append
    append_p = subparsers.add_parser("append", help="Append row(s) to sheet")
    append_p.add_argument("--id", required=True, help="Spreadsheet ID")
    append_p.add_argument("--range", "-r", default="Sheet1!A1", help="Target range/sheet")
    append_p.add_argument("--data", "-d", required=True, help="JSON list of values, e.g. '[\"val1\", \"val2\"]'")

    args = parser.parse_args()

    manager = GSheetsManager()
    if not manager.service:
        print("❌ Could not authenticate with Google Sheets. Check credentials / service account.")
        sys.exit(1)

    if args.command == "info":
        info = manager.get_spreadsheet_info(args.id)
        if info:
            print(f"📊 Title: {info['title']}")
            print("📑 Sheets:")
            for s in info["sheets"]:
                print(f"  - {s['title']} (Rows: {s['row_count']}, Cols: {s['column_count']})")
        else:
            print("❌ Failed to fetch info.")

    elif args.command == "read":
        rows = manager.read_range(args.id, args.range)
        if not rows:
            print("No data found or empty range.")
        else:
            for r in rows:
                print("\t|\t".join(str(c) for c in r))

    elif args.command == "search":
        matches = manager.search(args.id, args.query, args.range)
        print(f"🔍 Found {len(matches)} matching rows:")
        for m in matches:
            print(f"Row {m['row_index']}: {m['values']}")

    elif args.command == "append":
        try:
            row_data = json.loads(args.data)
            if not isinstance(row_data[0], list):
                row_data = [row_data]
            res = manager.append_rows(args.id, args.range, row_data)
            if res:
                print(f"✅ Appended row to {args.id}")
        except Exception as e:
            print(f"❌ Failed to append: {e}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
