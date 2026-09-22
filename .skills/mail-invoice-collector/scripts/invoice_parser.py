# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Multilingual Invoice & Receipt Parser
# =============================================================================
# Description:
#   Модуль для извлечения финансовых реквизитов (номер счета, дата, поставщик,
#   ИНН/ח.פ, сумма, валюта, НДС/מע"מ) из текста писем и вложенных файлов (PDF, изображения).
#   Поддерживает русский, английский языки и иврит.
#
# Examples:
#   >>> from invoice_parser import InvoiceParser
#   >>> parser = InvoiceParser()
#   >>> result = parser.parse_text("חשבונית מס מספר 12345 סה\"כ 500 ש\"ח מע\"מ 85 ש\"ח")
#   >>> print(result["invoice_number"], result["total_amount"])
#
# File: invoice_parser.py
# Package: .agents.skills.mail-invoice-collector.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""Модуль извлечения структурированных данных счетов-фактур на русском, английском и иврите."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from logger.logger import logger
except ImportError:
    logger = logging.getLogger("mail_invoice_collector")


INVOICE_CSV_COLUMNS: List[str] = [
    "email_date",
    "email_from",
    "email_subject",
    "invoice_number",
    "invoice_date",
    "due_date",
    "vendor_name",
    "vendor_tax_id",
    "customer_name",
    "total_amount",
    "currency",
    "tax_amount",
    "items_summary",
    "attachment_file",
    "status",
]


class InvoiceParser:
    """Парсер счетов-фактур, квитанций и налоговых документов."""

    def __init__(self, use_llm: bool = True) -> None:
        """Инициализация парсера счетов.

        Args:
            use_llm (bool): Использовать ли LLM при наличии доступных моделей.
        """
        self.use_llm = use_llm

    def parse_email_message(
        self,
        email_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Парсит входящее письмо и все его вложения, формируя записи счетов.

        Args:
            email_data (Dict[str, Any]): Данные письма из MailClient.

        Returns:
            List[Dict[str, Any]]: Список распознанных счетов-фактур.
        """
        results: List[Dict[str, Any]] = []
        attachments = email_data.get("attachments", [])
        body_text = email_data.get("body_text", "")
        subject = email_data.get("subject", "")
        sender = email_data.get("from", "")
        date_str = email_data.get("date", "")

        # Если есть вложения документов, обрабатываем каждое
        doc_attachments = [
            att for att in attachments
            if att.get("filename", "").lower().endswith(
                (".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".docx", ".xlsx")
            )
        ]

        if doc_attachments:
            for att in doc_attachments:
                file_path = att.get("path")
                extracted_text = ""
                if file_path and Path(file_path).exists():
                    extracted_text = self._extract_file_text(Path(file_path))

                combined_context = f"{subject}\n{body_text}\n{extracted_text}"
                parsed = self.parse_text(combined_context)
                parsed.update({
                    "email_date": date_str,
                    "email_from": sender,
                    "email_subject": subject,
                    "attachment_file": att.get("filename", ""),
                    "status": "attachment_parsed" if extracted_text else "attachment_saved",
                })
                results.append(parsed)
        else:
            # Парсинг непосредственно из темы и тела письма
            combined_context = f"{subject}\n{body_text}"
            parsed = self.parse_text(combined_context)
            parsed.update({
                "email_date": date_str,
                "email_from": sender,
                "email_subject": subject,
                "attachment_file": "",
                "status": "body_parsed",
            })
            results.append(parsed)

        return results

    def parse_text(self, text: str) -> Dict[str, Any]:
        """Извлекает ключевые финансовые параметры из текста (эвристика + регулярные выражения).

        Args:
            text (str): Исходный текст документа или письма.

        Returns:
            Dict[str, Any]: Структурированные параметры счета.
        """
        res = {
            "invoice_number": self._extract_invoice_number(text),
            "invoice_date": self._extract_date(text),
            "due_date": "",
            "vendor_name": self._extract_vendor(text),
            "vendor_tax_id": self._extract_tax_id(text),
            "customer_name": "",
            "total_amount": self._extract_total_amount(text),
            "currency": self._extract_currency(text),
            "tax_amount": self._extract_tax_amount(text),
            "items_summary": self._extract_items_summary(text),
        }
        return res

    def _extract_invoice_number(self, text: str) -> str:
        """Поиск номера счета (Invoice # / חשבונית מס / Счет-фактура №)."""
        patterns = [
            # Hebrew: חשבונית מס / קבלה מס' 12345
            r'(?:חשבונית\s*(?:מס|עסקה)?(?:\s*/\s*קבלה)?|קבלה)\s*(?:מס\'?|מספר|no\.?|#)?\s*[:\-]?\s*([A-Za-z0-9\-_/]+)',
            # Russian: Счет-фактура № 123, Счет № 123
            r'(?:счет(?:-фактура|\s*на\s*оплату)?|счёт(?:-фактура)?|акт)\s*(?:№|номер|#|no\.?)\s*[:\-]?\s*([A-Za-z0-9\-_/]+)',
            # English: Invoice # 123, Tax Invoice No: 123
            r'(?:tax\s+)?invoice\s*(?:number|no\.?|#|num)?\s*[:\-]?\s*([A-Za-z0-9\-_/]+)',
            # Generic: Bill #123, Receipt #123
            r'(?:receipt|bill)\s*(?:no\.?|#|number)\s*[:\-]?\s*([A-Za-z0-9\-_/]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                if len(val) >= 2 and not val.lower() in ("date", "total", "amount", "תאריך", "מס"):
                    return val
        return ""

    def _extract_date(self, text: str) -> str:
        """Поиск даты выставления счета (DD.MM.YYYY, YYYY-MM-DD, DD/MM/YYYY)."""
        patterns = [
            # Hebrew: תאריך: 12/05/2026
            r'(?:תאריך(?:\s*הפקת\s*חשבונית)?|תאריך\s*ערך)\s*[:\-]?\s*(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})',
            # Russian: Дата: 12.05.2026, от 12 мая 2026
            r'(?:дата(?:\s*выставления)?|от)\s*[:\-]?\s*(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})',
            # English: Invoice Date: 2026-05-12, Date: 12/05/2026
            r'(?:invoice\s*date|date|issued)\s*[:\-]?\s*(\d{1,4}[./\-]\d{1,2}[./\-]\d{2,4})',
            # General standalone date
            r'\b(\d{1,2}[./\-]\d{1,2}[./\-]\d{4})\b',
            r'\b(\d{4}[./\-]\d{1,2}[./\-]\d{1,2})\b',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_tax_id(self, text: str) -> str:
        """Поиск налогового номера (ИНН, VAT ID, ח.פ / ע.מ / עוסק מורשה)."""
        patterns = [
            # Hebrew: ח.פ / ע.מ / עוסק מורשה 514123456
            r'(?:ח\.?פ\.?|ע\.?מ\.?|עוסק\s*מורשה|מספר\s*תאגיד)\s*[:\-]?\s*(\d{8,9})',
            # Russian: ИНН 7701234567, КПП
            r'(?:ИНН|инн)\s*[:\-]?\s*(\d{10,12})',
            # English: VAT / Tax ID / EIN
            r'(?:vat\s*(?:id|no\.?|reg)?|tax\s*id|ein)\s*[:\-]?\s*([A-Za-z0-9\-]{6,15})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_total_amount(self, text: str) -> str:
        """Поиск итоговой суммы к оплате."""
        patterns = [
            # Hebrew: סה"כ לתשלום: 1,250.00 ש"ח, סה"כ: 500
            r'(?:סה"?כ(?:\s*כולל\s*מע"?מ|\s*לתשלום)?|סכום\s*כולל)\s*[:\-]?\s*([₪$€]?\s*[\d,]+(?:\.\d{1,2})?\s*(?:ש"?ח|ILS|USD|EUR|RUB|руб)?)\b',
            # Russian: Итого к оплате: 12 500.00 руб, Всего: 5000.00
            r'(?:итого(?:\s*к\s*оплате|\s*с\s*ндс)?|всего(?:\s*к\s*оплате)?|сумма\s*к\s*оплате)\s*[:\-]?\s*([$€₽]?\s*[\d\s]+(?:[.,]\d{1,2})?\s*(?:руб|₽|USD|EUR|ILS)?)\b',
            # English: Total Amount: $1,250.00, Grand Total: 500.00 EUR
            r'(?:grand\s*total|total\s*amount|total\s*due|amount\s*due|total)\s*[:\-]?\s*([$€£₪]?\s*[\d,]+(?:\.\d{1,2})?\s*(?:USD|EUR|ILS|GBP|RUB)?)\b',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raw_amt = match.group(1).strip()
                # Чистим строку суммы от лишних пробелов и разделителей тысяч
                cleaned_num = re.sub(r'[^\d.]', '', raw_amt.replace(',', '').replace(' ', ''))
                if cleaned_num:
                    return cleaned_num
        return ""

    def _extract_currency(self, text: str) -> str:
        """Определение валюты счета."""
        text_lower = text.lower()
        if "ש\"ח" in text or "שח" in text_lower or "₪" in text or "ils" in text_lower or "nis" in text_lower:
            return "ILS"
        if "$" in text or "usd" in text_lower or "dollar" in text_lower:
            return "USD"
        if "€" in text or "eur" in text_lower or "euro" in text_lower:
            return "EUR"
        if "₽" in text or "руб" in text_lower or "rub" in text_lower:
            return "RUB"
        if "£" in text or "gbp" in text_lower:
            return "GBP"
        return "USD"

    def _extract_tax_amount(self, text: str) -> str:
        """Поиск суммы налога (НДС / מע"מ / VAT)."""
        patterns = [
            # Hebrew: מע"מ (17%): 85.00 ש"ח
            r'(?:מע"?מ(?:\s*\(\d+%\))?|סכום\s*מע"?מ)\s*[:\-]?\s*([₪$€]?\s*[\d,]+(?:\.\d{1,2})?)\b',
            # Russian: В том числе НДС: 1 200.00
            r'(?:в\s*том\s*числе\s*ндс|сумма\s*ндс|ндс(?:\s*\d+%)?)\s*[:\-]?\s*([$€₽]?\s*[\d\s]+(?:[.,]\d{1,2})?)\b',
            # English: VAT Amount: 50.00, Tax: $20.00
            r'(?:vat\s*amount|tax\s*amount|tax|vat)\s*[:\-]?\s*([$€£₪]?\s*[\d,]+(?:\.\d{1,2})?)\b',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                cleaned = re.sub(r'[^\d.]', '', match.group(1).strip().replace(',', '').replace(' ', ''))
                if cleaned:
                    return cleaned
        return ""

    def _extract_vendor(self, text: str) -> str:
        """Поиск названия поставщика / компании."""
        patterns = [
            # Hebrew: שם ספק / חברה: Google Cloud
            r'(?:שם\s*הספק|שם\s*החברה|עוסק|ספק)\s*[:\-]?\s*([^\n\r,;]{3,50})',
            # Russian: Поставщик: ООО "Ромашка"
            r'(?:поставщик|продавец|исполнитель)\s*[:\-]?\s*([^\n\r;]{3,60})',
            # English: Vendor / Billed by / Seller
            r'(?:vendor|seller|from|billed\s*by)\s*[:\-]?\s*([^\n\r;]{3,50})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vendor = match.group(1).strip()
                if len(vendor) > 2 and not vendor.lower().startswith(("date", "invoice", "תאריך")):
                    return vendor
        return ""

    def _extract_items_summary(self, text: str) -> str:
        """Формирование краткого описания товаров или услуг."""
        patterns = [
            r'(?:פירוט|תיאור\s*השירות|פרטים)\s*[:\-]?\s*([^\n\r;]{5,100})',
            r'(?:наименование\s*товара|описание\s*услуг|предмет\s*счета)\s*[:\-]?\s*([^\n\r;]{5,100})',
            r'(?:description|items|service\s*description)\s*[:\-]?\s*([^\n\r;]{5,100})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_file_text(self, file_path: Path) -> str:
        """Извлекает текст из PDF или текстового документа.

        Args:
            file_path (Path): Путь к файлу.

        Returns:
            str: Извлеченный текст.
        """
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(file_path))
                pages_text = [page.extract_text() or "" for page in reader.pages]
                return "\n".join(pages_text)
            except Exception as ex:
                logger.debug(f"pypdf extraction failed for {file_path.name}: {ex}")

            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    pages_text = [page.extract_text() or "" for page in pdf.pages]
                    return "\n".join(pages_text)
            except Exception as ex:
                logger.debug(f"pdfplumber extraction failed for {file_path.name}: {ex}")

        elif ext in (".txt", ".html", ".htm"):
            try:
                return file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass

        return ""
