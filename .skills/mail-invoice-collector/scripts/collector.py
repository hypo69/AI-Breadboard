# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Mail Invoice Collector Orchestrator
# =============================================================================
# Description:
#   Координатор автономного сбора счетов-фактур из входящей почты:
#   подключение к ящику, поиск сообщений, парсинг данных и сохранение в CSV.
#
# Examples:
#   >>> from mail_client import load_mail_config
#   >>> from collector import MailInvoiceCollector
#   >>> cfg = load_mail_config()
#   >>> collector = MailInvoiceCollector(cfg)
#   >>> summary = collector.run(output_csv="data/invoices_summary.csv")
#
# File: collector.py
# Package: .agents.skills.mail-invoice-collector.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""Координатор сбора и сохранения счетов-фактур из входящей почты в CSV."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

try:
    from .invoice_parser import INVOICE_CSV_COLUMNS, InvoiceParser
    from .mail_client import MailAccountConfig, MailClient
except (ImportError, ValueError):
    from invoice_parser import INVOICE_CSV_COLUMNS, InvoiceParser
    from mail_client import MailAccountConfig, MailClient

try:
    from src.logger.logger import logger
except ImportError:
    logger = logging.getLogger("mail_invoice_collector")


class MailInvoiceCollector:
    """Оркестратор извлечения счетов из почты и генерации CSV-реестра."""

    def __init__(
        self,
        config: MailAccountConfig,
        parser: Optional[InvoiceParser] = None,
    ) -> None:
        """Инициализация коллектора счетов.

        Args:
            config (MailAccountConfig): Настройки подключения к почтовому ящику.
            parser (Optional[InvoiceParser]): Парсер счетов.
        """
        self.config = config
        self.client = MailClient(config)
        self.parser = parser or InvoiceParser()

    def run(
        self,
        output_csv: Optional[str | Path] = None,
        max_emails: int = 100,
        keywords: Optional[Sequence[str]] = None,
        download_attachments: bool = True,
        attachments_dir: Optional[str | Path] = None,
    ) -> Dict[str, Any]:
        """Запускает процесс сбора счетов из почты и записи в CSV файл.

        Args:
            output_csv (Optional[str | Path]): Путь к результирующему CSV файлу.
            max_emails (int): Максимальное количество проверяемых писем.
            keywords (Optional[Sequence[str]]): Ключевые слова для поиска.
            download_attachments (bool): Скачивать ли файлы вложений.
            attachments_dir (Optional[str | Path]): Директория для сохранения вложений.

        Returns:
            Dict[str, Any]: Отчет о результатах обработки.
        """
        # 1. Определение путей для сохранения
        base_data_dir = Path.cwd() / "data" / "invoices_collected"
        if not attachments_dir:
            att_path = base_data_dir / "attachments" if download_attachments else None
        else:
            att_path = Path(attachments_dir)

        if not output_csv:
            csv_path = base_data_dir / "mail_invoices_summary.csv"
        else:
            csv_path = Path(output_csv)

        csv_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Начало поиска счетов на {self.config.host} (папка {self.config.folder})...")

        # 2. Поиск и извлечение писем
        emails = self.client.fetch_invoice_emails(
            keywords=keywords,
            max_emails=max_emails,
            download_dir=att_path,
        )

        all_records: List[Dict[str, Any]] = []

        # 3. Парсинг каждого сообщения
        for email_msg in emails:
            parsed_list = self.parser.parse_email_message(email_msg)
            for record in parsed_list:
                all_records.append(record)

        # 4. Сохранение записей в CSV файл
        self._write_to_csv(csv_path, all_records)

        logger.info(
            f"Обработка завершена: найдено писем: {len(emails)}, "
            f"извлечено записей счетов: {len(all_records)}. Сохранено в {csv_path}"
        )

        return {
            "success": True,
            "host": self.config.host,
            "folder": self.config.folder,
            "emails_matched": len(emails),
            "invoices_extracted": len(all_records),
            "csv_path": str(csv_path.resolve()),
            "attachments_dir": str(att_path.resolve()) if att_path else None,
            "records": all_records,
        }

    def _write_to_csv(self, csv_file: Path, records: List[Dict[str, Any]]) -> None:
        """Записывает список счетов в CSV файл в кодировке UTF-8-SIG.

        Args:
            csv_file (Path): Путь к файлу CSV.
            records (List[Dict[str, Any]]): Список словарей с данными счетов.
        """
        # Используем utf-8-sig для безупречной поддержки иврита и кириллицы в Excel
        with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=INVOICE_CSV_COLUMNS,
                extrasaction="ignore",
            )
            writer.writeheader()
            for rec in records:
                writer.writerow(rec)
