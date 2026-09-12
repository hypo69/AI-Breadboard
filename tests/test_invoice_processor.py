# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Invoice Processor Unit Tests
# =============================================================================
# Description:
#   Unit tests for invoice extraction, row conversion, plugin actions,
#   and CLI processing pipeline.
#
# File: test_invoice_processor.py
# Package: tests
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from plugins.invoice_processor.extractor import (
    INVOICE_FIELDS,
    INVOICE_HEADER_ROW,
    extract_structured_invoice_data,
    invoice_dict_to_row,
)
from plugins.invoice_processor.plugin import InvoiceProcessorPlugin


@pytest.mark.asyncio
async def test_extractor_non_existent_file():
    """Test extractor behavior with non-existent file path."""
    res = await extract_structured_invoice_data("non_existent_invoice.pdf")
    assert res.get("file_name") == "non_existent_invoice.pdf"
    assert "error" in res


@pytest.mark.asyncio
async def test_extractor_with_mock_text(tmp_path):
    """Test structured extraction using mocked AI model response."""
    fake_invoice = tmp_path / "invoice_101.pdf"
    fake_invoice.write_text("Dummy content for PDF", encoding="utf-8")

    mock_llm_response = json.dumps({
        "invoice_number": "INV-2026-999",
        "invoice_date": "2026-09-12",
        "due_date": "2026-10-12",
        "vendor_name": "Acme Corp Ltd.",
        "vendor_tax_id": "TAX-123456",
        "customer_name": "Global Tech Services",
        "total_amount": "4500.00",
        "currency": "USD",
        "tax_amount": "900.00",
        "line_items_summary": "Cloud Server Infrastructure & Maintenance",
        "notes": "Payment due within 30 days"
    })

    mock_ai = MagicMock()
    mock_ai.ask = AsyncMock(return_value=mock_llm_response)

    with patch("plugins.invoice_processor.extractor.extract_document_text", AsyncMock(return_value="INVOICE INV-2026-999 Acme Corp")):
        data = await extract_structured_invoice_data(fake_invoice, ai_model=mock_ai)

    assert data["invoice_number"] == "INV-2026-999"
    assert data["vendor_name"] == "Acme Corp Ltd."
    assert data["total_amount"] == "4500.00"
    assert data["currency"] == "USD"
    assert data["file_name"] == "invoice_101.pdf"

    row = invoice_dict_to_row(data)
    assert len(row) == len(INVOICE_HEADER_ROW)
    assert row[0] == "invoice_101.pdf"
    assert row[1] == "INV-2026-999"
    assert row[4] == "Acme Corp Ltd."


@pytest.mark.asyncio
async def test_plugin_process_folder(tmp_path):
    """Test processing a folder with invoice files."""
    invoices_dir = tmp_path / "invoices"
    invoices_dir.mkdir()

    file1 = invoices_dir / "inv1.png"
    file1.write_bytes(b"PNG_FAKE_DATA")
    file2 = invoices_dir / "inv2.pdf"
    file2.write_bytes(b"PDF_FAKE_DATA")

    plugin = InvoiceProcessorPlugin(config={
        "enable_local_backup": True,
        "backup_dir": str(tmp_path / "backup")
    })

    mock_record = {
        "file_name": "inv1.png",
        "invoice_number": "123",
        "invoice_date": "2026-09-01",
        "due_date": "",
        "vendor_name": "Supplier A",
        "vendor_tax_id": "111",
        "customer_name": "Client B",
        "total_amount": "100.0",
        "currency": "USD",
        "tax_amount": "20.0",
        "line_items_summary": "Services",
        "notes": ""
    }

    with patch("plugins.invoice_processor.plugin.extract_structured_invoice_data", AsyncMock(return_value=mock_record)):
        res = await plugin.process_folder(invoices_dir)

    assert res["success"] is True
    assert res["processed_count"] == 2
    assert len(res["records"]) == 2
    assert Path(res["local_backup"]).exists()


@pytest.mark.asyncio
async def test_plugin_actions_and_manifest():
    """Test plugin manifest and action execution."""
    plugin = InvoiceProcessorPlugin()
    manifest = plugin.get_manifest()

    assert manifest["name"] == "invoice_processor"
    assert len(manifest["actions"]) >= 2
    assert len(manifest["tools"]) >= 1

    action_res = await plugin.execute_action("unknown_action")
    assert action_res["success"] is False
