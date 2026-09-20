# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Mail Watcher Engine & Sender Notification Dispatcher
# =============================================================================
# Description:
#   Модуль мониторинга почтового ящика через протокол IMAP.
#   Выполняет поиск входящих писем от заданного отправителя,
#   извлекает содержимое (тема, тело, дата, вложения), сохраняет
#   состояние обработанных писем и отправляет уведомления (Windows Toast,
#   консоль, структурированный JSON).
#
# Examples:
#   >>> from mail_watcher import MailWatcher, load_mail_watcher_config
#   >>> cfg = load_mail_watcher_config(sender="boss@example.com")
#   >>> watcher = MailWatcher(cfg)
#   >>> new_messages = watcher.check_messages()
#
# File: mail_watcher.py
# Package: .agents.skills.mail-watcher.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""Модуль мониторинга входящей почты от заданного отправителя."""

from __future__ import annotations

import email
import email.header
import email.utils
import imaplib
import json
import logging
import os
import re
import ssl
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

try:
    from src.logger.logger import logger
except ImportError:
    logger = logging.getLogger("mail_watcher")


@dataclass
class WatchedMessage:
    """Структура данных найденного входящего письма."""

    msg_id: str
    date: str
    sender: str
    sender_name: str
    sender_email: str
    subject: str
    body_text: str
    has_attachments: bool = False
    attachments_count: int = 0
    attachment_names: List[str] = field(default_factory=list)
    is_unread: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект сообщения в словарь."""
        return asdict(self)

    def format_alert(self) -> str:
        """Форматирует текст уведомления для пользователя или агента."""
        preview = (self.body_text[:200] + "...") if len(self.body_text) > 200 else self.body_text
        preview = preview.strip() or "[Текст сообщения отсутствует или представлен только во вложениях]"
        att_str = f", вложений: {self.attachments_count}" if self.attachments_count else ""
        return (
            f"📨 Новое письмо от: {self.sender}\n"
            f"Тема: {self.subject or '(без темы)'}\n"
            f"Дата: {self.date}\n"
            f"Превью: {preview}{att_str}"
        )


@dataclass
class MailWatcherConfig:
    """Конфигурация подключения к почтовому ящику и параметров отслеживания."""

    host: str
    username: str
    password: str
    port: int = 993
    use_ssl: bool = True
    use_tls: bool = False
    folder: str = "INBOX"
    target_sender: str = ""
    unread_only: bool = True
    mark_as_read: bool = False
    max_emails: int = 50
    timeout: int = 30
    poll_interval: int = 60
    whatsapp_recipient: str = ""
    state_file: Optional[Path] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Валидация и нормализация полей конфигурации."""
        self.host = self.host.strip()
        self.username = self.username.strip()
        self.port = int(self.port)
        self.folder = (self.folder or "INBOX").strip()
        self.target_sender = (self.target_sender or "").strip()
        if not self.host:
            raise ValueError("Параметр 'host' (IMAP-сервер) не может быть пустым.")
        if not self.username:
            raise ValueError("Параметр 'username' не может быть пустым.")
        if not self.password:
            raise ValueError("Параметр 'password' не может быть пустым.")


def decode_mime_header(header_value: Optional[str]) -> str:
    """Декодирует MIME-заголовок письма (RFC 2047).

    Args:
        header_value (Optional[str]): Исходный MIME-заголовок.

    Returns:
        str: Декодированная строка.
    """
    if not header_value:
        return ""
    try:
        decoded_fragments = email.header.decode_header(header_value)
        parts: List[str] = []
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


def parse_sender_info(raw_from: str) -> Tuple[str, str, str]:
    """Извлекает отображаемое имя, email и нормализованную строку отправителя.

    Args:
        raw_from (str): Исходное значение заголовка From.

    Returns:
        Tuple[str, str, str]: (полная строка, имя, email).
    """
    decoded = decode_mime_header(raw_from)
    name, addr = email.utils.parseaddr(decoded)
    name = decode_mime_header(name).strip()
    addr = addr.strip().lower()
    full = f"{name} <{addr}>" if name and addr else (addr or name or decoded)
    return full, name, addr


def send_windows_notification(title: str, message: str) -> bool:
    """Отправляет всплывающее уведомление Windows (Toast Notification).

    Args:
        title (str): Заголовок уведомления.
        message (str): Текст уведомления.

    Returns:
        bool: True в случае успешной отправки, иначе False.
    """
    try:
        safe_title = title.replace("'", "''").replace('"', '`"')
        safe_msg = message.replace("'", "''").replace('"', '`"')
        ps_script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$textNodes = $template.GetElementsByTagName("text")
$textNodes.Item(0).AppendChild($template.CreateTextNode('{safe_title}')) > $null
$textNodes.Item(1).AppendChild($template.CreateTextNode('{safe_msg}')) > $null
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("AI Breadboard")
$notification = [Windows.UI.Notifications.ToastNotification]::new($template)
$notifier.Show($notification)
"""
        cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return res.returncode == 0
    except Exception as ex:
        logger.debug(f"[mail_watcher] Ошибка отправки Windows Toast: {ex}")
        return False


def extract_mailbox_data(raw_data: Dict[str, Any], account: Optional[str] = None) -> Dict[str, Any]:
    """Извлекает параметры почтового ящика из общего пула mailboxes.json или плоского словаря.

    Args:
        raw_data (Dict[str, Any]): Данные из JSON-файла секретов.
        account (Optional[str]): Имя или алиас аккаунта (например, 'default', 'work', 'личная').

    Returns:
        Dict[str, Any]: Параметры конкретного ящика.
    """
    if not isinstance(raw_data, dict) or not raw_data:
        return {}

    # Если файл уже плоский с одиночной конфигурацией ящика
    if "host" in raw_data or "imap_host" in raw_data or "username" in raw_data:
        return raw_data

    target = (account or "").strip().lower()

    # 1. Поиск по прямому имени ключа
    if target:
        for k, v in raw_data.items():
            if isinstance(v, dict) and k.strip().lower() == target:
                return v

        # 2. Поиск по алиасам ящиков
        for k, v in raw_data.items():
            if isinstance(v, dict):
                aliases = v.get("aliases", [])
                if isinstance(aliases, list):
                    if any(str(a).strip().lower() == target for a in aliases):
                        return v

    # 3. Fallback: поиск по стандартным ключам ('default', 'main', 'primary', 'personal')
    for def_key in ("default", "main", "primary", "personal"):
        for k, v in raw_data.items():
            if isinstance(v, dict) and k.strip().lower() == def_key:
                return v

    # 4. Fallback: первый словарь, содержащий параметры подключения
    for k, v in raw_data.items():
        if isinstance(v, dict) and ("imap_host" in v or "host" in v or "username" in v):
            return v

    return {}


def load_mail_watcher_config(
    explicit_path: Optional[str | Path] = None,
    account: Optional[str] = None,
    sender: str = "",
    host: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    port: Optional[int] = None,
    use_ssl: Optional[bool] = None,
    folder: Optional[str] = None,
    unread_only: bool = True,
    mark_as_read: bool = False,
    max_emails: int = 50,
    whatsapp_recipient: Optional[str] = None,
    state_file: Optional[Path] = None,
) -> MailWatcherConfig:
    """Загружает параметры конфигурации из mailboxes.json, secrets.json, окружения или аргументов.

    Args:
        explicit_path (Optional[str | Path]): Путь к файлу mailboxes.json / secrets.json.
        account (Optional[str]): Имя или алиас аккаунта из mailboxes.json (напр. 'default', 'work').
        sender (str): Целевой адрес или имя отправителя.
        host (Optional[str]): Адрес IMAP-сервера.
        username (Optional[str]): Имя пользователя / Email.
        password (Optional[str]): Пароль / App Password.
        port (Optional[int]): Порт IMAP.
        use_ssl (Optional[bool]): Использовать ли SSL.
        folder (Optional[str]): Папка для проверки (по умолчанию INBOX).
        unread_only (bool): Проверять только непрочитанные письма.
        mark_as_read (bool): Помечать ли найденные письма как прочитанные.
        max_emails (int): Максимальное количество проверяемых сообщений.
        whatsapp_recipient (Optional[str]): Номер телефона для пересылки в WhatsApp.
        state_file (Optional[Path]): Путь к файлу сохранения состояния обработанных писем.

    Returns:
        MailWatcherConfig: Сформированный объект конфигурации.
    """
    file_data: Dict[str, Any] = {}
    search_paths: List[Path] = []

    if explicit_path:
        search_paths.append(Path(explicit_path).resolve())
    else:
        try:
            from header import __root__
            search_paths.append(__root__ / "src" / "secrets" / "mailboxes.json")
        except Exception:
            pass

        current_dir = Path(__file__).resolve().parent
        skill_root = current_dir.parent
        search_paths.extend([
            Path.cwd() / "src" / "secrets" / "mailboxes.json",
            skill_root / "secrets.json",
            skill_root / ".secrets.json",
            Path.cwd() / "secrets.json",
            Path.cwd() / ".secrets.json",
        ])

    target_account = account or os.getenv("MAIL_ACCOUNT") or os.getenv("MAILBOX_NAME") or "default"

    for candidate in search_paths:
        if candidate.is_file():
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    raw_content = json.load(f)
                extracted = extract_mailbox_data(raw_content, account=target_account)
                if extracted:
                    file_data = extracted
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
    resolved_sender = sender or file_data.get("target_sender") or os.getenv("MAIL_TARGET_SENDER", "")
    resolved_whatsapp = (
        whatsapp_recipient
        or file_data.get("whatsapp_recipient")
        or file_data.get("whatsapp_to")
        or os.getenv("WHATSAPP_RECIPIENT_DEFAULT")
        or os.getenv("WHATSAPP_TO", "")
    )

    if state_file is None:
        env_state = os.getenv("MAIL_WATCHER_STATE_FILE")
        if env_state:
            state_file = Path(env_state)
        else:
            state_dir = Path.home() / ".ai_breadboard" / "mail_watcher"
            state_dir.mkdir(parents=True, exist_ok=True)
            state_file = state_dir / "seen_emails.json"

    return MailWatcherConfig(
        host=resolved_host,
        username=resolved_user,
        password=resolved_pass,
        port=int(resolved_port),
        use_ssl=bool(resolved_ssl),
        folder=resolved_folder,
        target_sender=resolved_sender,
        unread_only=unread_only,
        mark_as_read=mark_as_read,
        max_emails=max_emails,
        whatsapp_recipient=resolved_whatsapp,
        state_file=state_file,
        extra=file_data,
    )


class MailWatcher:
    """Класс для проверки почтового ящика и мониторинга писем от отправителя."""

    def __init__(self, config: MailWatcherConfig) -> None:
        """Инициализация монитора почты.

        Args:
            config (MailWatcherConfig): Конфигурация параметров.
        """
        self.config = config
        self._seen_ids: Set[str] = self._load_state()

    def _load_state(self) -> Set[str]:
        """Загружает список ранее обработанных идентификаторов писем."""
        if not self.config.state_file or not self.config.state_file.is_file():
            return set()
        try:
            with open(self.config.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return set(str(x) for x in data)
                if isinstance(data, dict):
                    return set(str(x) for x in data.get("seen_ids", []))
        except Exception as ex:
            logger.debug(f"[mail_watcher] Ошибка загрузки состояния: {ex}")
        return set()

    def _save_state(self) -> None:
        """Сохраняет список обработанных идентификаторов писем в файл."""
        if not self.config.state_file:
            return
        try:
            self.config.state_file.parent.mkdir(parents=True, exist_ok=True)
            # Ограничиваем историю последними 2000 записями
            saved_list = list(self._seen_ids)[-2000:]
            with open(self.config.state_file, "w", encoding="utf-8") as f:
                json.dump({"seen_ids": saved_list, "updated_at": time.time()}, f, ensure_ascii=False, indent=2)
        except Exception as ex:
            logger.debug(f"[mail_watcher] Ошибка сохранения состояния: {ex}")

    def create_connection(self) -> imaplib.IMAP4 | imaplib.IMAP4_SSL:
        """Создает и аутентифицирует IMAP-соединение.

        Returns:
            imaplib.IMAP4 | imaplib.IMAP4_SSL: Подключенный клиент IMAP.
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
        """Тестирует подключение к серверу IMAP.

        Returns:
            Dict[str, Any]: Результат проверки соединения.
        """
        try:
            client = self.create_connection()
            status, folders = client.list()
            client.logout()
            return {
                "success": True,
                "host": self.config.host,
                "port": self.config.port,
                "username": self.config.username,
                "folders_count": len(folders) if folders else 0,
                "message": "Успешное подключение к почтовому серверу.",
            }
        except Exception as ex:
            logger.error(f"[mail_watcher] Ошибка подключения к {self.config.host}: {ex}")
            return {
                "success": False,
                "host": self.config.host,
                "port": self.config.port,
                "username": self.config.username,
                "error": str(ex),
                "message": f"Не удалось подключиться: {ex}",
            }

    def _matches_sender(self, sender_raw: str, sender_name: str, sender_email: str, target: str) -> bool:
        """Проверяет соответствие отправителя целевому фильтру.

        Args:
            sender_raw (str): Полная строка заголовка From.
            sender_name (str): Имя отправителя.
            sender_email (str): Email отправителя.
            target (str): Целевой фильтр поиска.

        Returns:
            bool: True, если отправитель соответствует фильтру.
        """
        if not target:
            return True
        t_low = target.lower().strip()
        # Проверяем вхождение в email, имя или сырую строку
        if t_low in sender_email.lower():
            return True
        if t_low in sender_name.lower():
            return True
        if t_low in sender_raw.lower():
            return True
        # Проверка регулярного выражения, если целевой шаблон содержит спецсимволы
        try:
            if re.search(target, sender_raw, re.IGNORECASE):
                return True
        except re.error:
            pass
        return False

    def _extract_body_and_attachments(
        self, msg: email.message.Message
    ) -> Tuple[str, List[str]]:
        """Извлекает текст тела письма и имена вложений.

        Args:
            msg (email.message.Message): Объект сообщения.

        Returns:
            Tuple[str, List[str]]: (текст письма, список имен файлов вложений).
        """
        body_parts: List[str] = []
        attachment_names: List[str] = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                filename = part.get_filename()

                if filename:
                    filename = decode_mime_header(filename)

                if "attachment" in content_disposition or filename:
                    attachment_names.append(filename or "unnamed_attachment")
                elif content_type in ("text/plain", "text/html"):
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        try:
                            text = payload.decode(charset, errors="replace")
                            # Если HTML, очищаем простые теги для превью
                            if content_type == "text/html":
                                text = re.sub(r"<[^>]+>", " ", text)
                            body_parts.append(text)
                        except Exception:
                            body_parts.append(payload.decode("utf-8", errors="replace"))
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                content_type = msg.get_content_type()
                try:
                    text = payload.decode(charset, errors="replace")
                    if content_type == "text/html":
                        text = re.sub(r"<[^>]+>", " ", text)
                    body_parts.append(text)
                except Exception:
                    body_parts.append(payload.decode("utf-8", errors="replace"))

        cleaned_body = "\n".join(b.strip() for b in body_parts if b.strip()).strip()
        return cleaned_body, attachment_names

    def check_messages(
        self,
        sender: Optional[str] = None,
        unread_only: Optional[bool] = None,
        max_emails: Optional[int] = None,
        mark_as_read: Optional[bool] = None,
        notify_toast: bool = False,
        forward_whatsapp: Optional[str] = None,
    ) -> List[WatchedMessage]:
        """Выполняет проверку почтового ящика на наличие писем от целевого отправителя.

        Args:
            sender (Optional[str]): Переопределение целевого отправителя.
            unread_only (Optional[bool]): Проверять только непрочитанные.
            max_emails (Optional[int]): Лимит количества сообщений.
            mark_as_read (Optional[bool]): Помечать ли как прочитанные.
            notify_toast (bool): Посылать ли Windows Toast уведомления.
            forward_whatsapp (Optional[str]): Телефон для пересылки в WhatsApp.

        Returns:
            List[WatchedMessage]: Список найденных новых сообщений.
        """
        target_sender = sender if sender is not None else self.config.target_sender
        is_unread = unread_only if unread_only is not None else self.config.unread_only
        limit = max_emails or self.config.max_emails
        should_mark_read = mark_as_read if mark_as_read is not None else self.config.mark_as_read

        matched_messages: List[WatchedMessage] = []
        client = self.create_connection()

        try:
            status, _ = client.select(self.config.folder, readonly=not should_mark_read)
            if status != "OK":
                logger.error(f"[mail_watcher] Не удалось открыть папку {self.config.folder}")
                return []

            # Формируем поисковый запрос IMAP
            search_criteria = "UNSEEN" if is_unread else "ALL"
            status, data = client.search(None, search_criteria)
            if status != "OK" or not data or not data[0]:
                return []

            email_ids = data[0].split()
            # Берем самые свежие письма с конца
            target_ids = email_ids[-limit:]
            target_ids.reverse()

            for msg_id_bytes in target_ids:
                msg_id_str = msg_id_bytes.decode(errors="ignore") if isinstance(msg_id_bytes, bytes) else str(msg_id_bytes)

                try:
                    res, msg_data = client.fetch(msg_id_bytes, "(RFC822 FLAGS)")
                    if res != "OK" or not msg_data or not msg_data[0]:
                        continue

                    raw_email = None
                    flags_raw = ""
                    for item in msg_data:
                        if isinstance(item, tuple) and len(item) == 2:
                            raw_email = item[1]
                            flags_raw = str(item[0])
                            break

                    if not isinstance(raw_email, bytes):
                        continue

                    msg = email.message_from_bytes(raw_email)

                    message_id_header = decode_mime_header(msg.get("Message-ID", "")).strip() or f"imap_{msg_id_str}"
                    # Если письмо уже было обработано и зафиксировано в состоянии, пропускаем
                    if message_id_header in self._seen_ids:
                        continue

                    from_header = decode_mime_header(msg.get("From"))
                    sender_full, sender_name, sender_email = parse_sender_info(from_header)

                    if not self._matches_sender(sender_full, sender_name, sender_email, target_sender):
                        continue

                    date_header = decode_mime_header(msg.get("Date"))
                    subject_header = decode_mime_header(msg.get("Subject"))
                    body_text, attachment_names = self._extract_body_and_attachments(msg)
                    is_unread_flag = "\\Seen" not in flags_raw

                    watched_msg = WatchedMessage(
                        msg_id=message_id_header,
                        date=date_header,
                        sender=sender_full,
                        sender_name=sender_name,
                        sender_email=sender_email,
                        subject=subject_header,
                        body_text=body_text,
                        has_attachments=bool(attachment_names),
                        attachments_count=len(attachment_names),
                        attachment_names=attachment_names,
                        is_unread=is_unread_flag,
                    )

                    matched_messages.append(watched_msg)
                    self._seen_ids.add(message_id_header)

                    if should_mark_read:
                        client.store(msg_id_bytes, "+FLAGS", "\\Seen")

                    if notify_toast:
                        send_windows_notification(
                            title=f"Письмо от {sender_name or sender_email}",
                            message=subject_header or "(без темы)",
                        )

                    # Пересылка в WhatsApp, если указан получатель
                    target_wa = forward_whatsapp or self.config.whatsapp_recipient
                    if target_wa:
                        self.forward_to_whatsapp(watched_msg, target_wa)

                except Exception as ex:
                    logger.warning(f"[mail_watcher] Ошибка при обработке письма #{msg_id_str}: {ex}")

            self._save_state()

        finally:
            try:
                client.close()
            except Exception:
                pass
            try:
                client.logout()
            except Exception:
                pass

        return matched_messages

    def forward_to_whatsapp(
        self,
        msg: WatchedMessage,
        recipient: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Пересылает содержимое входящего письма в WhatsApp.

        Args:
            msg (WatchedMessage): Сообщение для пересылки.
            recipient (Optional[str]): Телефон получателя (если не задан, берется из конфигурации).

        Returns:
            Dict[str, Any]: Результат отправки через WhatsApp API.
        """
        target = recipient or self.config.whatsapp_recipient
        if not target:
            return {"success": False, "error": "Не указан получатель WhatsApp."}

        try:
            try:
                from plugins.whatsapp import WhatsAppClient
            except ImportError:
                import sys
                from header import __root__
                plugin_dir = __root__ / "plugins" / "user-plugins" / "whatsapp"
                if plugin_dir.exists() and str(plugin_dir) not in sys.path:
                    sys.path.insert(0, str(plugin_dir))
                from client import WhatsAppClient

            client = WhatsAppClient()
            email_payload = {
                "sender": msg.sender,
                "subject": msg.subject,
                "date": msg.date,
                "body_text": msg.body_text,
            }
            res = client.send_email_alert(to=target, email_data=email_payload)
            logger.info(f"[mail_watcher] Результат пересылки в WhatsApp ({target}): {res}")
            return res
        except Exception as ex:
            logger.error(f"[mail_watcher] Ошибка при пересылке в WhatsApp: {ex}")
            return {"success": False, "error": str(ex)}

    def watch_loop(
        self,
        sender: Optional[str] = None,
        interval: Optional[int] = None,
        callback: Optional[Callable[[WatchedMessage], None]] = None,
        notify_toast: bool = True,
        forward_whatsapp: Optional[str] = None,
        max_iterations: Optional[int] = None,
    ) -> None:
        """Запускает непрерывный мониторинг ящика с заданным интервалом.

        Args:
            sender (Optional[str]): Целевой отправитель.
            interval (Optional[int]): Интервал между проверками в секундах.
            callback (Optional[Callable[[WatchedMessage], None]]): Обработчик каждого нового письма.
            notify_toast (bool): Показывать ли всплывающие уведомления.
            forward_whatsapp (Optional[str]): Номер телефона для пересылки в WhatsApp.
            max_iterations (Optional[int]): Максимальное число циклов (для тестирования или ограничения).
        """
        sleep_sec = interval or self.config.poll_interval
        iterations = 0

        logger.info(f"[mail_watcher] Запуск мониторинга для '{sender or self.config.target_sender}' с интервалом {sleep_sec}с")

        while True:
            try:
                new_msgs = self.check_messages(
                    sender=sender,
                    unread_only=self.config.unread_only,
                    notify_toast=notify_toast,
                    forward_whatsapp=forward_whatsapp,
                )
                for msg in new_msgs:
                    logger.info(f"[mail_watcher] Обнаружено письмо: {msg.format_alert()}")
                    if callback:
                        callback(msg)

                iterations += 1
                if max_iterations and iterations >= max_iterations:
                    break

                time.sleep(sleep_sec)
            except KeyboardInterrupt:
                logger.info("[mail_watcher] Мониторинг остановлен пользователем.")
                break
            except Exception as ex:
                logger.error(f"[mail_watcher] Ошибка в цикле мониторинга: {ex}")
                time.sleep(sleep_sec)
