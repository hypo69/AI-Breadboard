"""Пакет модулей для сбора счетов-фактур из входящей почты."""
try:
    from .collector import MailInvoiceCollector
    from .invoice_parser import InvoiceParser
    from .mail_client import MailAccountConfig, MailClient
except (ImportError, ValueError):
    from collector import MailInvoiceCollector
    from invoice_parser import InvoiceParser
    from mail_client import MailAccountConfig, MailClient
__all__ = ['MailAccountConfig', 'MailClient', 'InvoiceParser', 'MailInvoiceCollector']