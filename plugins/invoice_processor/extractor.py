# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Invoice Data Extractor and Structured Parser
# =============================================================================
# Description:
#   Extracts textual data from invoice files (PDF, images) and parses
#   structured financial records using LLM intelligence.
#
# File: extractor.py
# Package: plugins.invoice_processor
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.logger.logger import logger
from src.utils.pdf_extractor import extract_document_text

INVOICE_FIELDS = [
    "file_name",
    "invoice_number",
    "invoice_date",
    "due_date",
    "vendor_name",
    "vendor_tax_id",
    "customer_name",
    "total_amount",
    "currency",
    "tax_amount",
    "line_items_summary",
    "notes",
]

INVOICE_HEADER_ROW = [
    "File Name",
    "Invoice Number",
    "Invoice Date",
    "Due Date",
    "Vendor / Company",
    "Vendor Tax / VAT ID",
    "Customer Name",
    "Total Amount",
    "Currency",
    "Tax / VAT Amount",
    "Items Summary",
    "Notes / Remarks",
]


async def extract_structured_invoice_data(
    file_path: Union[str, Path],
    ai_model: Any = None,
) -> Dict[str, Any]:
    """Extract structured invoice data from an invoice file.

    Args:
        file_path (Union[str, Path]): Path to PDF or image invoice.
        ai_model (Any): Optional AI model instance.

    Returns:
        Dict[str, Any]: Structured invoice data.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"Invoice file does not exist: {path}")
        return {"file_name": path.name, "error": "File not found"}

    # 1. Extract raw textual content
    raw_text = await extract_document_text(path)
    if not raw_text or not raw_text.strip():
        logger.warning(f"No text extracted from {path.name}")
        return {
            "file_name": path.name,
            "invoice_number": "",
            "invoice_date": "",
            "due_date": "",
            "vendor_name": "",
            "vendor_tax_id": "",
            "customer_name": "",
            "total_amount": "",
            "currency": "",
            "tax_amount": "",
            "line_items_summary": "",
            "notes": "Could not extract text from document",
        }

    # 2. Extract structured fields via LLM
    prompt = (
        "You are an expert accounting AI. Analyze the following invoice document text and extract all required "
        "financial details into a strict, valid JSON object without any Markdown fences or backticks.\n\n"
        "Required JSON format:\n"
        "{\n"
        '  "invoice_number": "string",\n'
        '  "invoice_date": "string in YYYY-MM-DD format if identifiable",\n'
        '  "due_date": "string in YYYY-MM-DD format if identifiable",\n'
        '  "vendor_name": "string (seller/company)",\n'
        '  "vendor_tax_id": "string (Tax/VAT/INN ID)",\n'
        '  "customer_name": "string (buyer/client)",\n'
        '  "total_amount": "number or string",\n'
        '  "currency": "string (e.g. USD, EUR, RUB)",\n'
        '  "tax_amount": "number or string",\n'
        '  "line_items_summary": "concise summary of items/services",\n'
        '  "notes": "remarks or payment instructions"\n'
        "}\n\n"
        f"Document Text:\n{raw_text[:8000]}"
    )

    extracted_dict: Dict[str, Any] = {}
    try:
        response_text = ""
        if ai_model and hasattr(ai_model, "ask"):
            response_text = await ai_model.ask(prompt)
        else:
            from src.ai.gemini.api import GoogleGenerativeAI
            ai = GoogleGenerativeAI()
            response_text = await ai.ask(prompt)

        if response_text:
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                cleaned = re.sub(r"\s*```$", "", cleaned)
            extracted_dict = json.loads(cleaned)
    except Exception as ex:
        logger.warning(f"LLM structured extraction failed for {path.name}: {ex}")

    result: Dict[str, Any] = {
        "file_name": path.name,
        "invoice_number": str(extracted_dict.get("invoice_number", "") or ""),
        "invoice_date": str(extracted_dict.get("invoice_date", "") or ""),
        "due_date": str(extracted_dict.get("due_date", "") or ""),
        "vendor_name": str(extracted_dict.get("vendor_name", "") or ""),
        "vendor_tax_id": str(extracted_dict.get("vendor_tax_id", "") or ""),
        "customer_name": str(extracted_dict.get("customer_name", "") or ""),
        "total_amount": str(extracted_dict.get("total_amount", "") or ""),
        "currency": str(extracted_dict.get("currency", "") or ""),
        "tax_amount": str(extracted_dict.get("tax_amount", "") or ""),
        "line_items_summary": str(extracted_dict.get("line_items_summary", "") or ""),
        "notes": str(extracted_dict.get("notes", "") or ""),
    }

    return result


def invoice_dict_to_row(data: Dict[str, Any]) -> List[Any]:
    """Convert structured invoice dictionary to a row for Google Sheets / CSV.

    Args:
        data (Dict[str, Any]): Invoice data dictionary.

    Returns:
        List[Any]: List of values matching INVOICE_HEADER_ROW.
    """
    return [
        data.get("file_name", ""),
        data.get("invoice_number", ""),
        data.get("invoice_date", ""),
        data.get("due_date", ""),
        data.get("vendor_name", ""),
        data.get("vendor_tax_id", ""),
        data.get("customer_name", ""),
        data.get("total_amount", ""),
        data.get("currency", ""),
        data.get("tax_amount", ""),
        data.get("line_items_summary", ""),
        data.get("notes", ""),
    ]