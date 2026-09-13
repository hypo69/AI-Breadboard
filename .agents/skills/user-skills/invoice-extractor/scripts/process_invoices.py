# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Invoice Extractor Skill CLI Tool
# =============================================================================
# Description:
#   CLI helper script for the invoice-extractor skill. Scans a folder containing
#   invoices (PDF or image files), extracts financial fields, and appends
#   structured rows to Google Sheets and local CSV records.
#
# File: process_invoices.py
# Package: .agents.skills.invoice-extractor.scripts
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add project root to sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from plugins.invoice_processor.plugin import InvoiceProcessorPlugin


async def main_async(args: argparse.Namespace) -> int:
    """Async main routine."""
    plugin = InvoiceProcessorPlugin()

    folder_path = Path(args.folder).resolve()
    if not folder_path.is_dir():
        print(f"❌ Error: Folder does not exist: {folder_path}", file=sys.stderr)
        return 1

    print(f"🔍 Scanning folder: {folder_path} for invoices/receipts...")
    result = await plugin.process_folder(
        folder_path=folder_path,
        spreadsheet_id=args.spreadsheet_id,
        sheet_name=args.sheet_name,
    )

    if not result.get("success"):
        print(f"❌ Processing failed: {result.get('error')}", file=sys.stderr)
        return 1

    count = result.get("processed_count", 0)
    print(f"\n✅ Successfully processed {count} document(s):")
    print("=" * 70)

    for rec in result.get("records", []):
        print(f"📄 File: {rec.get('file_name')}")
        print(f"   • Invoice #: {rec.get('invoice_number') or 'N/A'}")
        print(f"   • Vendor:    {rec.get('vendor_name') or 'N/A'}")
        print(f"   • Date:      {rec.get('invoice_date') or 'N/A'}")
        print(f"   • Amount:    {rec.get('total_amount') or 'N/A'} {rec.get('currency') or ''}")
        print(f"   • Items:     {rec.get('line_items_summary') or 'N/A'}")
        print("-" * 70)

    if result.get("gsheet_synced"):
        print(f"📊 Google Sheets: Synced rows to sheet ID: {result.get('spreadsheet_id')}")
    elif args.spreadsheet_id:
        print("⚠️ Google Sheets sync was not completed (verify service account or OAuth credentials).")

    if result.get("local_backup"):
        print(f"💾 Local Backup: Appended to {result.get('local_backup')}")

    if args.json:
        print("\n--- JSON OUTPUT ---")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0


def main() -> None:
    """Entry point for CLI execution."""
    parser = argparse.ArgumentParser(description="Extract invoices and sync to Google Sheets")
    parser.add_argument("--folder", "-f", required=True, help="Path to folder containing invoice files (PDF/Images)")
    parser.add_argument("--spreadsheet-id", "-s", default="", help="Google Spreadsheet ID")
    parser.add_argument("--sheet-name", "-n", default="Invoices", help="Sheet tab name (default: 'Invoices')")
    parser.add_argument("--json", action="store_true", help="Print complete JSON output")

    args = parser.parse_args()
    code = asyncio.run(main_async(args))
    sys.exit(code)


if __name__ == "__main__":
    main()
