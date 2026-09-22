# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Invoice Processor Plugin Main Controller
# =============================================================================
# Description:
#   Main plugin adapter for automated invoice information extraction and
#   synchronization into Google Sheets and local data stores.
#
# File: plugin.py
# Package: plugins.invoice_processor
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from logger.logger import logger
from plugins.base import BasePlugin
from plugins.invoice_processor.extractor import (
    INVOICE_HEADER_ROW,
    extract_structured_invoice_data,
    invoice_dict_to_row,
)


class InvoiceProcessorPlugin(BasePlugin):
    """Modular plugin providing automated invoice OCR, extraction, and Google Sheets sync.

    Attributes:
        name (str): 'invoice_processor'.
        title (str): 'Invoice Processor & Google Sheets Sync'.
        version (str): '1.0.0'.
        description (str): Functional summary.
        icon (str): '🧾'.
        category (str): 'tools'.
    """

    name: str = "invoice_processor"
    title: str = "Invoice Processor & Google Sheets Sync"
    title_i18n: Dict[str, str] = {
        "en": "Invoice Processor & Google Sheets Sync",
        "ru": "Обработчик счетов и синхронизация с Google Таблицами",
    }
    version: str = "1.0.0"
    description: str = "Extracts financial metadata from invoices (PDF/images) and syncs rows to Google Sheets."
    description_i18n: Dict[str, str] = {
        "en": "Extracts financial metadata from invoices (PDF/images) and syncs rows to Google Sheets.",
        "ru": "Извлекает структурированные данные из счетов (PDF/сканы) и сохраняет в Google Таблицы.",
    }
    icon: str = "🧾"
    category: str = "tools"
    enabled: bool = True
    is_system: bool = False
    scope: str = "user"

    def __init__(self, ai_model: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the invoice processor plugin."""
        super().__init__(ai_model=ai_model, config=config)
        self.supported_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff", ".tif"}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return LLM function calling tool definitions."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "process_invoices_folder",
                    "description": "Process all invoice/receipt files in a directory and sync extracted data to Google Sheets.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "folder_path": {
                                "type": "string",
                                "description": "Absolute or relative path to the directory containing invoice files.",
                            },
                            "spreadsheet_id": {
                                "type": "string",
                                "description": "Optional Google Spreadsheet ID. If omitted, uses configured ID or local storage.",
                            },
                            "sheet_name": {
                                "type": "string",
                                "description": "Optional sheet/tab name in the spreadsheet. Default is 'Invoices'.",
                            },
                        },
                        "required": ["folder_path"],
                    },
                },
            }
        ]

    def get_actions(self) -> List[Dict[str, Any]]:
        """Return list of executable admin actions."""
        return [
            {
                "id": "process_folder",
                "label": "Process Invoices Folder",
                "description": "Scan a directory with invoice files and sync structured records to Google Sheets.",
                "params": [
                    {"name": "folder_path", "type": "string", "required": True, "label": "Folder Path"},
                    {"name": "spreadsheet_id", "type": "string", "required": False, "label": "Google Spreadsheet ID"},
                    {"name": "sheet_name", "type": "string", "required": False, "label": "Sheet Name", "default": "Invoices"},
                ],
            },
            {
                "id": "process_file",
                "label": "Process Single Invoice",
                "description": "Extract structured details from a single invoice file.",
                "params": [
                    {"name": "file_path", "type": "string", "required": True, "label": "File Path"},
                ],
            },
        ]

    def get_config_fields(self) -> List[Dict[str, Any]]:
        """Return configuration fields for web UI."""
        return [
            {
                "id": "spreadsheet_id",
                "label": "Default Google Spreadsheet ID",
                "type": "string",
                "default": "",
                "description": "Target Google Spreadsheet ID for invoice rows.",
            },
            {
                "id": "sheet_name",
                "label": "Default Sheet Tab Name",
                "type": "string",
                "default": "Invoices",
                "description": "Sheet/tab name inside the spreadsheet.",
            },
            {
                "id": "enable_local_backup",
                "label": "Enable Local CSV Backup",
                "type": "boolean",
                "default": True,
                "description": "Also save processed invoices to local CSV file.",
            },
            {
                "id": "backup_dir",
                "label": "Local Backup Directory",
                "type": "string",
                "default": "data/invoices_processed",
                "description": "Directory where CSV backup will be saved.",
            },
        ]

    async def execute_action(self, action_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute declared admin action."""
        params = params or {}
        if action_id == "process_folder":
            folder_path = params.get("folder_path", "")
            spreadsheet_id = params.get("spreadsheet_id") or self.config.get("spreadsheet_id", "")
            sheet_name = params.get("sheet_name") or self.config.get("sheet_name", "Invoices")
            return await self.process_folder(folder_path=folder_path, spreadsheet_id=spreadsheet_id, sheet_name=sheet_name)

        if action_id == "process_file":
            file_path = params.get("file_path", "")
            return await self.process_single_file(file_path=file_path)

        return await super().execute_action(action_id, params)

    async def process_single_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Process a single invoice file.

        Args:
            file_path (Union[str, Path]): Path to invoice file.

        Returns:
            Dict[str, Any]: Extracted invoice data.
        """
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        data = await extract_structured_invoice_data(path, ai_model=self.ai_model)
        return {"success": True, "data": data}

    async def process_folder(
        self,
        folder_path: Union[str, Path],
        spreadsheet_id: Optional[str] = None,
        sheet_name: str = "Invoices",
    ) -> Dict[str, Any]:
        """Process all invoice files in the specified folder.

        Args:
            folder_path (Union[str, Path]): Target folder path.
            spreadsheet_id (Optional[str]): Target Google Spreadsheet ID.
            sheet_name (str): Target tab name.

        Returns:
            Dict[str, Any]: Processing summary.
        """
        folder = Path(folder_path)
        if not folder.is_dir():
            return {"success": False, "error": f"Directory not found: {folder_path}"}

        files = [
            f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in self.supported_extensions
        ]

        if not files:
            return {"success": False, "error": f"No supported invoice files found in {folder_path}"}

        records: List[Dict[str, Any]] = []
        rows: List[List[Any]] = []

        for file_p in files:
            logger.info(f"Processing invoice: {file_p.name}")
            data = await extract_structured_invoice_data(file_p, ai_model=self.ai_model)
            records.append(data)
            rows.append(invoice_dict_to_row(data))

        # 1. Save local backup CSV if enabled
        backup_csv_path = None
        if self.config.get("enable_local_backup", True):
            backup_dir = Path(self.config.get("backup_dir", "data/invoices_processed"))
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_csv_path = backup_dir / "invoices_summary.csv"

            file_exists = backup_csv_path.exists()
            with open(backup_csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(INVOICE_HEADER_ROW)
                for r in rows:
                    writer.writerow(r)

        # 2. Append to Google Sheets if spreadsheet_id is provided
        gsheet_synced = False
        target_sheet_id = spreadsheet_id or self.config.get("spreadsheet_id", "")
        if target_sheet_id:
            try:
                # Try gsheets_manager from skills
                from src.google_services import (
                    append_google_spreadsheet_values,
                    read_google_spreadsheet_range,
                )
                # Check if header needs to be added
                existing_rows = read_google_spreadsheet_range(user_id=1, spreadsheet_id=target_sheet_id, range_name=f"{sheet_name}!A1:A1")
                if not existing_rows and self.config.get("auto_create_header", True):
                    append_google_spreadsheet_values(user_id=1, spreadsheet_id=target_sheet_id, range_name=f"{sheet_name}!A1", values=[INVOICE_HEADER_ROW])

                append_res = append_google_spreadsheet_values(user_id=1, spreadsheet_id=target_sheet_id, range_name=f"{sheet_name}!A1", values=rows)
                if append_res:
                    gsheet_synced = True
            except Exception as ex:
                logger.warning(f"Failed to append to Google Sheets via google_services: {ex}")
                # Fallback to GSheetsManager
                try:
                    sys_path = Path(__file__).resolve().parents[3] / ".agents" / "skills" / "user-skills" / "google-workspace" / "scripts"
                    if not sys_path.exists():
                        sys_path = Path(__file__).resolve().parents[3] / ".agents" / "skills" / "google-workspace" / "scripts"
                    import sys
                    if sys_path.exists() and str(sys_path) not in sys.path:
                        sys.path.insert(0, str(sys_path))
                    from gsheets_manager import GSheetsManager
                    mgr = GSheetsManager()
                    if mgr.service:
                        existing = mgr.read_range(target_sheet_id, f"{sheet_name}!A1:A1")
                        if not existing:
                            mgr.append_rows(target_sheet_id, f"{sheet_name}!A1", [INVOICE_HEADER_ROW])
                        mgr.append_rows(target_sheet_id, f"{sheet_name}!A1", rows)
                        gsheet_synced = True
                except Exception as ex2:
                    logger.error(f"GSheets fallback sync failed: {ex2}")

        return {
            "success": True,
            "processed_count": len(records),
            "files": [r.get("file_name") for r in records],
            "records": records,
            "gsheet_synced": gsheet_synced,
            "spreadsheet_id": target_sheet_id,
            "local_backup": str(backup_csv_path) if backup_csv_path else None,
        }

    async def handle(self, message: str, **kwargs: Any) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle conversational or natural language invocation."""
        yield {"status": "started", "text": "Analyzing invoice processing request..."}
        # If message contains a folder path
        import re
        path_match = re.search(r'[\'"]?([a-zA-Z]:\\[^\'"\n\r]+|\./[^\'"\n\r]+)[\'"]?', message)
        if path_match:
            folder_path = path_match.group(1)
            res = await self.process_folder(folder_path)
            if res.get("success"):
                yield {
                    "status": "complete",
                    "text": f"Successfully processed {res.get('processed_count')} invoices from {folder_path}.",
                    "result": res,
                }
                return
            yield {"status": "error", "text": f"Error: {res.get('error')}"}
            return

        yield {
            "status": "complete",
            "text": "Please provide a folder path containing invoices/receipts to process.",
        }