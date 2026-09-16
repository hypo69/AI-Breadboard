# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Mail Invoice Collector Scripts Package
# =============================================================================
# Description:
#   Пакет скриптов для подключения к почте, поиска входящих счетов-фактур
#   (invoices, חשבונית) и сохранения их в сводную CSV-таблицу.
#
# File: __init__.py
# Package: .agents.skills.mail-invoice-collector.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""Пакет модулей для сбора счетов-фактур из входящей почты."""

try:
    from .collector import MailInvoiceCollector
    from .invoice_parser import InvoiceParser
    from .mail_client import MailAccountConfig, MailClient
except (ImportError, ValueError):
    from collector import MailInvoiceCollector
    from invoice_parser import InvoiceParser
    from mail_client import MailAccountConfig, MailClient

__all__ = [
    "MailAccountConfig",
    "MailClient",
    "InvoiceParser",
    "MailInvoiceCollector",
]
