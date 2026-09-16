# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: SMTP Mail Core Engine
# =============================================================================
# Description:
#   Ядро для работы с SMTP: загрузка секретов из secrets.json,
#   валидация подключения, сборка MIME-сообщений (HTML/текст, вложения) и отправка писем.
#
# Examples:
#   >>> from smtp_core import load_smtp_config, SmtpClient
#   >>> config = load_smtp_config()
#   >>> client = SmtpClient(config)
#   >>> result = client.test_connection()
#   >>> print(result)
#
# File: smtp_core.py
# Package: .agents.skills.smtp-mail-agent.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""Ядро для работы с SMTP и отправки электронной почты."""

from __future__ import annotations

import json
import mimetypes
import os
import smtplib
import ssl
from dataclasses import dataclass, field
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, make_msgid
from pathlib import Path
from typing import Any, List, Optional, Sequence


@dataclass
class SmtpConfig:
    """Конфигурация подключения к SMTP-серверу."""

    host: str
    port: int = 587
    use_tls: bool = True
    use_ssl: bool = False
    username: str = ""
    password: str = ""
    from_email: str = ""
    from_name: str = ""
    timeout: int = 30
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Валидация и нормализация полей конфигурации."""
        self.host = self.host.strip()
        self.port = int(self.port)
        self.username = self.username.strip()
        self.from_email = (self.from_email or self.username).strip()
        self.from_name = self.from_name.strip()
        if not self.host:
            raise ValueError("Параметр 'host' SMTP-сервера не может быть пустым.")


def find_secrets_file(explicit_path: Optional[str | Path] = None) -> Path:
    """Поиск файла secrets.json по стандартным путям.

    Args:
        explicit_path (Optional[str | Path]): Явно указанный путь к файлу секретов.

    Returns:
        Path: Найденный абсолютный путь к файлу secrets.json.

    Raises:
        FileNotFoundError: Если файл secrets.json не обнаружен.
    """
    if explicit_path:
        path = Path(explicit_path).resolve()
        if path.is_file():
            return path
        raise FileNotFoundError(f"Указанный файл секретов не найден: {path}")

    current_dir = Path(__file__).resolve().parent
    skill_root = current_dir.parent

    search_locations = [
        skill_root / "secrets.json",
        skill_root / ".secrets.json",
        current_dir / "secrets.json",
        Path.cwd() / "secrets.json",
        Path.cwd() / ".secrets.json",
    ]

    for candidate in search_locations:
        if candidate.is_file():
            return candidate.resolve()

    raise FileNotFoundError(
        f"Файл secrets.json не найден ни в одном из стандартных мест: {skill_root}. "
        "Скопируйте secrets.json.example в secrets.json и укажите данные подключения."
    )


def load_smtp_config(secrets_path: Optional[str | Path] = None) -> SmtpConfig:
    """Загрузка конфигурации SMTP из secrets.json или переменных окружения.

    Args:
        secrets_path (Optional[str | Path]): Опциональный путь к secrets.json.

    Returns:
        SmtpConfig: Объект конфигурации с параметрами подключения.

    Raises:
        ValueError: При ошибке структуры JSON или отсутствии обязательных полей.
    """
    try:
        path = find_secrets_file(secrets_path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        smtp_data = data.get("smtp", data)
        return SmtpConfig(
            host=smtp_data.get("host", ""),
            port=int(smtp_data.get("port", 587)),
            use_tls=bool(smtp_data.get("use_tls", True)),
            use_ssl=bool(smtp_data.get("use_ssl", False)),
            username=smtp_data.get("username", ""),
            password=smtp_data.get("password", ""),
            from_email=smtp_data.get("from_email", ""),
            from_name=smtp_data.get("from_name", ""),
            timeout=int(smtp_data.get("timeout", 30)),
            extra={k: v for k, v in smtp_data.items() if k not in {
                "host", "port", "use_tls", "use_ssl", "username", "password",
                "from_email", "from_name", "timeout"
            }},
        )
    except FileNotFoundError:
        # Fallback к переменным окружения
        host = os.getenv("SMTP_HOST") or os.getenv("SMTP_SERVER", "")
        if host:
            return SmtpConfig(
                host=host,
                port=int(os.getenv("SMTP_PORT", 587)),
                use_tls=os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes"),
                use_ssl=os.getenv("SMTP_USE_SSL", "false").lower() in ("1", "true", "yes"),
                username=os.getenv("SMTP_USER", "") or os.getenv("SMTP_USERNAME", ""),
                password=os.getenv("SMTP_PASSWORD", "") or os.getenv("SMTP_PASS", ""),
                from_email=os.getenv("SMTP_FROM_EMAIL", ""),
                from_name=os.getenv("SMTP_FROM_NAME", ""),
                timeout=int(os.getenv("SMTP_TIMEOUT", 30)),
            )
        raise


class SmtpClient:
    """Клиент для выполнения операций с SMTP сервером."""

    def __init__(self, config: SmtpConfig) -> None:
        """Инициализация SMTP клиента с заданной конфигурацией.

        Args:
            config (SmtpConfig): Конфигурация подключения.
        """
        self.config = config

    def _create_connection(self) -> smtplib.SMTP | smtplib.SMTP_SSL:
        """Создание и установление соединения с SMTP сервером.

        Returns:
            smtplib.SMTP | smtplib.SMTP_SSL: Инициализированный объект соединения.
        """
        if self.config.use_ssl:
            context = ssl.create_default_context()
            server: smtplib.SMTP | smtplib.SMTP_SSL = smtplib.SMTP_SSL(
                self.config.host,
                self.config.port,
                context=context,
                timeout=self.config.timeout,
            )
        else:
            server = smtplib.SMTP(
                self.config.host,
                self.config.port,
                timeout=self.config.timeout,
            )
            server.ehlo()
            if self.config.use_tls:
                context = ssl.create_default_context()
                server.starttls(context=context)
                server.ehlo()

        if self.config.username and self.config.password:
            server.login(self.config.username, self.config.password)

        return server

    def test_connection(self) -> dict[str, Any]:
        """Проверка соединения и авторизации на SMTP сервере.

        Returns:
            dict[str, Any]: Результат проверки со статусом и деталями.
        """
        try:
            with self._create_connection() as server:
                server.noop()
            return {
                "status": "success",
                "message": f"Успешное подключение к SMTP-серверу {self.config.host}:{self.config.port}",
                "host": self.config.host,
                "port": self.config.port,
                "authenticated_user": self.config.username,
                "tls_enabled": self.config.use_tls,
                "ssl_enabled": self.config.use_ssl,
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": f"Ошибка подключения к SMTP: {exc}",
                "host": self.config.host,
                "port": self.config.port,
                "error_type": type(exc).__name__,
            }

    def send_mail(
        self,
        to: str | Sequence[str],
        subject: str,
        body_text: str = "",
        body_html: Optional[str] = None,
        attachments: Optional[Sequence[str | Path]] = None,
        cc: Optional[str | Sequence[str]] = None,
        bcc: Optional[str | Sequence[str]] = None,
        extra_headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Отправка электронного письма через SMTP.

        Args:
            to (str | Sequence[str]): Адрес(а) получателя.
            subject (str): Тема письма.
            body_text (str): Текстовое содержимое письма.
            body_html (Optional[str]): HTML содержимое письма (опционально).
            attachments (Optional[Sequence[str | Path]]): Список путей к файлам для вложения.
            cc (Optional[str | Sequence[str]]): Адрес(а) копии.
            bcc (Optional[str | Sequence[str]]): Адрес(а) скрытой копии.
            extra_headers (Optional[dict[str, str]]): Дополнительные заголовки MIME.

        Returns:
            dict[str, Any]: Результат отправки письма.
        """
        # Нормализация списков получателей
        to_list = [to] if isinstance(to, str) else list(to)
        cc_list = ([cc] if isinstance(cc, str) else list(cc)) if cc else []
        bcc_list = ([bcc] if isinstance(bcc, str) else list(bcc)) if bcc else []

        all_recipients = [addr.strip() for addr in (to_list + cc_list + bcc_list) if addr.strip()]
        if not all_recipients:
            return {
                "status": "error",
                "message": "Не указан ни один адрес получателя (to, cc или bcc).",
            }

        # Формирование MIME-сообщения
        msg = MIMEMultipart("mixed")
        msg_id = make_msgid()
        msg["Message-ID"] = msg_id
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = formataddr((str(Header(self.config.from_name, "utf-8")), self.config.from_email))
        msg["To"] = ", ".join(to_list)

        if cc_list:
            msg["Cc"] = ", ".join(cc_list)

        if extra_headers:
            for header_name, header_value in extra_headers.items():
                msg[header_name] = header_value

        # Тело письма (Plain Text и/или HTML)
        if body_html:
            alt_part = MIMEMultipart("alternative")
            if body_text:
                alt_part.attach(MIMEText(body_text, "plain", "utf-8"))
            alt_part.attach(MIMEText(body_html, "html", "utf-8"))
            msg.attach(alt_part)
        else:
            msg.attach(MIMEText(body_text, "plain", "utf-8"))

        # Вложения
        attached_files: List[str] = []
        if attachments:
            for attach_item in attachments:
                file_path = Path(attach_item).resolve()
                if not file_path.is_file():
                    return {
                        "status": "error",
                        "message": f"Файл вложения не найден: {file_path}",
                    }
                mime_type, _ = mimetypes.guess_type(str(file_path))
                if mime_type is None:
                    maintype, subtype = "application", "octet-stream"
                else:
                    maintype, subtype = mime_type.split("/", 1)

                with open(file_path, "rb") as f:
                    part = MIMEBase(maintype, subtype)
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{file_path.name}"',
                )
                msg.attach(part)
                attached_files.append(file_path.name)

        try:
            with self._create_connection() as server:
                server.sendmail(self.config.from_email, all_recipients, msg.as_string())

            return {
                "status": "success",
                "message": "Письмо успешно отправлено.",
                "message_id": msg_id,
                "from": self.config.from_email,
                "to": to_list,
                "cc": cc_list,
                "bcc": bcc_list,
                "subject": subject,
                "attachments": attached_files,
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": f"Ошибка отправки письма через SMTP: {exc}",
                "error_type": type(exc).__name__,
                "to": to_list,
                "subject": subject,
            }
