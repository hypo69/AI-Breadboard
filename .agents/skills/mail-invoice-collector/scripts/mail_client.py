# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Mail Account Client & Inbox Search Engine
# =============================================================================
# Description:
#   Модуль подключения к почтовому ящику (IMAP/SMTP), аутентификации,
#   поиска входящих сообщений по ключевым словам и извлечения вложений.
#
# Examples:
#   >>> from mail_client import MailAccountConfig, MailClient
#   >>> cfg = MailAccountConfig(host="imap.example.com", username="user@example.com", password="pwd")
#   >>> client = MailClient(cfg)
#   >>> client.test_connection()
#
# File: mail_client.py
# Package: .agents.skills.mail-invoice-collector.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""Клиент для взаимодействия с почтовым сервером через IMAP и SMTP."""

from __future__ import annotations

import email
import email.header
import imaplib
import json
import logging
import os
import smtplib
import ssl
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    from logger.logger import logger
except ImportError:
    logger = logging.getLogger("mail_invoice_collector")


@dataclass
class MailAccountConfig:
    """Конфигурация параметров подключения к почтовому ящику."""

    host: str
    username: str
    password: str
    port: int = 993
    use_ssl: bool = True
    use_tls: bool = False
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    folder: str = "INBOX"
    timeout: int = 30
    keywords: List[str] = field(
        default_factory=lambda: [
            "invoice",
            "tax invoice",
            "bill",
            "receipt",
            "חשבונית",
            "חשבונית מס",
            "קבלה",
            "счет",
            "счёт",
            "счет-фактура",
            "счёт-фактура",
            "заказ",
            "квитанция",
            "акт",
        ]
    )
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Валидация и нормализация полей конфигурации."""
        self.host = self.host.strip()
        self.username = self.username.strip()
        self.port = int(self.port)
        self.smtp_port = int(self.smtp_port) if self.smtp_port else 587
        self.folder = (self.folder or "INBOX").strip()
        if not self.host:
            raise ValueError("Параметр 'host' (IMAP-сервер) не может быть пустым.")
        if not self.username:
            raise ValueError("Параметр 'username' не может быть пустым.")
        if not self.password:
            raise ValueError("Параметр 'password' не может быть пустым.")


def load_mail_config_central(
    account_key: str,
    explicit_path: str | Path = Path("src/secrets/mailboxes.json"),
) -> MailAccountConfig:
    """Загрузка конфигурации из централизованного файла."""
    if not Path(explicit_path).exists():
        raise FileNotFoundError(f"Файл конфигурации не найден: {explicit_path}")

    with open(explicit_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Ищем по прямому ключу или по алиасам
    config_data = None
    if account_key in data:
        config_data = data[account_key]
    else:
        for key, val in data.items():
            if account_key.lower() in [a.lower() for a in val.get("aliases", [])]:
                config_data = val
                break
    
    if not config_data:
        raise ValueError(f"Почтовый ящик '{account_key}' не найден в конфигурации.")

    return MailAccountConfig(
        host=config_data["imap_host"],
        username=config_data["username"],
        password=config_data["password"],
        port=int(config_data.get("imap_port", 993)),
        smtp_host=config_data.get("smtp_host"),
        smtp_port=int(config_data.get("smtp_port", 587)),
        keywords=config_data.get("keywords", ["invoice", "счет", "заказ"]),
    )


def load_mail_config(
    explicit_path: Optional[str | Path] = None,
    host: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    port: Optional[int] = None,
    use_ssl: Optional[bool] = None,
    folder: Optional[str] = None,
) -> MailAccountConfig:
    """Загрузка конфигурации из CLI аргументов, secrets.json или переменных окружения.

    Args:
        explicit_path (Optional[str | Path]): Путь к файлу secrets.json.
        host (Optional[str]): Адрес IMAP-сервера.
        username (Optional[str]): Имя пользователя / Email.
        password (Optional[str]): Пароль / App Password.
        port (Optional[int]): Порт IMAP (обычно 993).
        use_ssl (Optional[bool]): Использовать ли SSL.
        folder (Optional[str]): Папка для поиска (по умолчанию INBOX).

    Returns:
        MailAccountConfig: Готовый объект конфигурации.
    """
    file_data: Dict[str, Any] = {}
    search_paths: List[Path] = []

    if explicit_path:
        search_paths.append(Path(explicit_path).resolve())
    else:
        current_dir = Path(__file__).resolve().parent
        skill_root = current_dir.parent
        search_paths.extend([
            skill_root / "secrets.json",
            skill_root / ".secrets.json",
            Path.cwd() / "secrets.json",
            Path.cwd() / ".secrets.json",
        ])

    for candidate in search_paths:
        if candidate.is_file():
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                break
            except Exception as ex:
                logger.warning(f"Не удалось прочитать файл секретов {candidate}: {ex}")

    resolved_host = (
        host
        or file_data.get("imap_host")
        or file_data.get("host")
        or os.getenv("MAIL_IMAP_HOST")
        or os.getenv("MAIL_HOST")
        or ""
    )
    resolved_user = (
        username
        or file_data.get("username")
        or file_data.get("email")
        or os.getenv("MAIL_USERNAME")
        or os.getenv("MAIL_EMAIL")
        or ""
    )
    resolved_pass = (
        password
        or file_data.get("password")
        or file_data.get("app_password")
        or os.getenv("MAIL_PASSWORD")
        or os.getenv("MAIL_APP_PASSWORD")
        or ""
    )
    resolved_port = port or file_data.get("imap_port") or file_data.get("port") or 993
    resolved_ssl = (
        use_ssl
        if use_ssl is not None
        else file_data.get("use_ssl", True)
    )
    resolved_folder = folder or file_data.get("folder") or "INBOX"

    return MailAccountConfig(
        host=resolved_host,
        username=resolved_user,
        password=resolved_pass,
        port=int(resolved_port),
        use_ssl=bool(resolved_ssl),
        smtp_host=file_data.get("smtp_host") or os.getenv("MAIL_SMTP_HOST"),
        smtp_port=int(file_data.get("smtp_port", 587)),
        folder=resolved_folder,
        extra=file_data,
    )


def decode_mime_header(header_value: Optional[str]) -> str:
    """Декодирует MIME-заголовок письма (RFC 2047).

    Args:
        header_value (Optional[str]): Исходный заголовок.

    Returns:
        str: Декодированная строка.
    """
    if not header_value:
        return ""
    try:
        decoded_fragments = email.header.decode_header(header_value)
        parts = []
        for content, encoding in decoded_fragments:
            if isinstance(content, bytes):
                enc = encoding or "utf-8"
                try:
                    parts.append(content.decode(enc, errors="replace"))
                except (LookupError, UnicodeDecodeError):
                    parts.append(content.decode("utf-8", errors="replace"))
            else:
                parts.append(str(content))
        return "".join(parts).strip()
    except Exception:
        return str(header_value)


class MailClient:
    """Клиент для подключения к почте и чтения сообщений."""

    def __init__(self, config: MailAccountConfig) -> None:
        """Инициализация почтового клиента.

        Args:
            config (MailAccountConfig): Конфигурация доступа.
        """
        self.config = config

    def create_imap_connection(self) -> imaplib.IMAP4 | imaplib.IMAP4_SSL:
        """Создает и возвращает авторизованное IMAP-соединение.

        Returns:
            imaplib.IMAP4 | imaplib.IMAP4_SSL: Подключенное соединение.
        """
        if self.config.use_ssl:
            ssl_context = ssl.create_default_context()
            client = imaplib.IMAP4_SSL(
                host=self.config.host,
                port=self.config.port,
                ssl_context=ssl_context,
                timeout=self.config.timeout,
            )
        else:
            client = imaplib.IMAP4(
                host=self.config.host,
                port=self.config.port,
                timeout=self.config.timeout,
            )
            if self.config.use_tls:
                client.starttls()

        client.login(self.config.username, self.config.password)
        return client

    def test_connection(self) -> Dict[str, Any]:
        """Тестирует подключение к IMAP серверу.

        Returns:
            Dict[str, Any]: Результат проверки соединения.
        """
        try:
            client = self.create_imap_connection()
            status, folders = client.list()
            client.logout()
            return {
                "success": True,
                "host": self.config.host,
                "port": self.config.port,
                "username": self.config.username,
                "folders_count": len(folders) if folders else 0,
                "message": "Успешная авторизация на почтовом сервере.",
            }
        except Exception as ex:
            logger.error(f"Ошибка проверки подключения к {self.config.host}: {ex}")
            return {
                "success": False,
                "host": self.config.host,
                "port": self.config.port,
                "username": self.config.username,
                "error": str(ex),
                "message": f"Не удалось подключиться к серверу: {ex}",
            }

    def fetch_invoice_emails(
        self,
        keywords: Optional[Sequence[str]] = None,
        max_emails: int = 100,
        download_dir: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """Ищет и извлекает письма со счетами-фактурами и вложениями.

        Args:
            keywords (Optional[Sequence[str]]): Ключевые слова для фильтрации.
            max_emails (int): Максимальное количество проверяемых сообщений.
            download_dir (Optional[Path]): Директория для сохранения вложений.

        Returns:
            List[Dict[str, Any]]: Список извлеченных сообщений и вложений.
        """
        search_terms = list(keywords) if keywords else self.config.keywords
        search_terms_lower = [t.lower() for t in search_terms]

        if download_dir:
            download_dir.mkdir(parents=True, exist_ok=True)

        found_messages: List[Dict[str, Any]] = []

        client = self.create_imap_connection()
        try:
            status, _ = client.select(self.config.folder, readonly=True)
            if status != "OK":
                logger.warning(f"Не удалось открыть папку {self.config.folder}")
                return []

            # Получаем список всех ID писем
            status, data = client.search(None, "ALL")
            if status != "OK" or not data or not data[0]:
                logger.info("Почтовый ящик пуст.")
                return []

            email_ids = data[0].split()
            # Берем самые свежие письма с конца
            target_ids = email_ids[-max_emails:]
            target_ids.reverse()

            for msg_id in target_ids:
                try:
                    res, msg_data = client.fetch(msg_id, "(RFC822)")
                    if res != "OK" or not msg_data or not msg_data[0]:
                        continue

                    raw_email = msg_data[0][1]
                    if not isinstance(raw_email, bytes):
                        continue

                    msg = email.message_from_bytes(raw_email)

                    date_hdr = decode_mime_header(msg.get("Date"))
                    from_hdr = decode_mime_header(msg.get("From"))
                    subject_hdr = decode_mime_header(msg.get("Subject"))

                    body_text, attachments = self._extract_parts(msg, download_dir)

                    # Проверка соответствия ключевым словам в теме, теле или именах файлов
                    combined_text = f"{subject_hdr} {body_text} {' '.join(a['filename'] for a in attachments)}".lower()
                    is_invoice = any(term in combined_text for term in search_terms_lower)

                    # Если есть вложения PDF/изображений или найдены ключевые слова
                    has_relevant_attachment = any(
                        a["filename"].lower().endswith((".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".docx", ".xlsx"))
                        for a in attachments
                    )

                    if is_invoice or (attachments and has_relevant_attachment and ("invoice" in combined_text or "счет" in combined_text or "חשבונית" in combined_text)):
                        found_messages.append({
                            "msg_id": msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id),
                            "date": date_hdr,
                            "from": from_hdr,
                            "subject": subject_hdr,
                            "body_text": body_text,
                            "attachments": attachments,
                        })
                except Exception as ex:
                    logger.warning(f"Ошибка при обработке письма ID {msg_id}: {ex}")
        finally:
            try:
                client.close()
            except Exception:
                pass
            try:
                client.logout()
            except Exception:
                pass

        return found_messages

    def _extract_parts(
        self,
        msg: email.message.Message,
        download_dir: Optional[Path] = None,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Извлекает текст письма и сохраняет вложения.

        Args:
            msg (email.message.Message): Объект email-сообщения.
            download_dir (Optional[Path]): Директория для сохранения файлов.

        Returns:
            Tuple[str, List[Dict[str, Any]]]: Текст тела письма и список вложений.
        """
        body_parts: List[str] = []
        attachments: List[Dict[str, Any]] = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                filename = part.get_filename()

                if filename:
                    filename = decode_mime_header(filename)

                if "attachment" in content_disposition or filename:
                    payload = part.get_payload(decode=True)
                    if payload:
                        safe_filename = filename or f"attachment_{len(attachments) + 1}.dat"
                        file_path = None
                        if download_dir:
                            file_path = download_dir / safe_filename
                            with open(file_path, "wb") as f:
                                f.write(payload)

                        attachments.append({
                            "filename": safe_filename,
                            "content_type": content_type,
                            "size": len(payload),
                            "path": str(file_path) if file_path else "",
                            "bytes": payload,
                        })
                elif content_type in ("text/plain", "text/html"):
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        try:
                            text = payload.decode(charset, errors="replace")
                            body_parts.append(text)
                        except Exception:
                            body_parts.append(payload.decode("utf-8", errors="replace"))
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                try:
                    body_parts.append(payload.decode(charset, errors="replace"))
                except Exception:
                    body_parts.append(payload.decode("utf-8", errors="replace"))

        return "\n".join(body_parts).strip(), attachments
