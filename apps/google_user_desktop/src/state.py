"""Модуль управления состоянием и сервисами Google User Desktop."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from logger import logger
from src.ai.google_accounts_state import (
    get_account_info,
    list_google_accounts,
    set_default_account,
)
from src.google_services import (
    get_google_calendar_events,
    get_google_contacts,
    get_google_headers,
    list_google_documents,
)
from .forms import GoogleFormsClient, FormItemSummary


@dataclass
class GoogleAccountSummary:
    """Сводная информация о текущем выбранном Google аккаунте.

    Attributes:
        name: Имя аккаунта (например, 'default', 'work').
        email: Электронная почта аккаунта.
        account_type: Тип аккаунта ('oauth2' или 'service_account').
        status: Статус аккаунта ('active', 'exhausted', 'unconfigured').
        is_default: Флаг активного аккаунта по умолчанию.
    """

    name: str = ""
    email: str = ""
    account_type: str = "oauth2"
    status: str = "unconfigured"
    is_default: bool = False


@dataclass
class MailItemSummary:
    """Сводка отдельного сообщения электронной почты.

    Attributes:
        id: Идентификатор письма.
        thread_id: Идентификатор цепочки писем.
        subject: Тема письма.
        sender: Отправитель письма.
        date: Дата и время получения письма.
        snippet: Краткое описание / фрагмент текста.
    """

    id: str = ""
    thread_id: str = ""
    subject: str = ""
    sender: str = ""
    date: str = ""
    snippet: str = ""


@dataclass
class CalendarEventSummary:
    """Сводка события календаря Google.

    Attributes:
        id: Идентификатор события.
        summary: Заголовок события.
        start_time: Время начала события.
        end_time: Время окончания события.
        location: Место проведения.
        html_link: Ссылка на событие в интерфейсе Google.
    """

    id: str = ""
    summary: str = ""
    start_time: str = ""
    end_time: str = ""
    location: str = ""
    html_link: str = ""


@dataclass
class DocumentItemSummary:
    """Сводка файла Google Документов / Таблиц.

    Attributes:
        id: Идентификатор документа.
        name: Название документа.
        mime_type: MIME-тип файла.
        created_time: Время создания.
        modified_time: Время последнего изменения.
        web_view_link: Ссылка для просмотра в браузере.
    """

    id: str = ""
    name: str = ""
    mime_type: str = "application/vnd.google-apps.document"
    created_time: str = ""
    modified_time: str = ""
    web_view_link: str = ""


@dataclass
class DriveFileSummary:
    """Сводка файла на Google Диске.

    Attributes:
        id: Идентификатор файла.
        name: Имя файла.
        mime_type: Тип файла.
        size_bytes: Размер файла в байтах.
        modified_time: Время модификации.
        web_view_link: Ссылка на веб-просмотр.
    """

    id: str = ""
    name: str = ""
    mime_type: str = ""
    size_bytes: int = 0
    modified_time: str = ""
    web_view_link: str = ""


class GoogleUserDesktopState:
    """Класс управления агрегированным состоянием и API-запросами Google User Desktop.

    Attributes:
        user_id: Идентификатор локального пользователя (по умолчанию 1).
        selected_account_name: Имя текущего выбранного аккаунта Google.
        last_refreshed: Время последнего успешного обновления состояния.
    """

    def __init__(self, user_id: int = 1, account_name: Optional[str] = None) -> None:
        """Инициализация объекта состояния Google User Desktop.

        Args:
            user_id: Идентификатор пользователя.
            account_name: Опциональное имя Google аккаунта.
        """
        self.user_id = user_id
        self.selected_account_name = account_name
        self.last_refreshed: str = ""
        self._accounts_cache: List[Dict[str, Any]] = []
        self._mail_cache: List[MailItemSummary] = []
        self._calendar_cache: List[CalendarEventSummary] = []
        self._docs_cache: List[DocumentItemSummary] = []
        self._drive_cache: List[DriveFileSummary] = []

    def get_active_account(self) -> GoogleAccountSummary:
        """Получить информацию об активном Google аккаунте.

        Returns:
            GoogleAccountSummary: Данные текущего выбранного или основного аккаунта.
        """
        accounts = list_google_accounts()
        self._accounts_cache = accounts
        if not accounts:
            return GoogleAccountSummary(
                name="none",
                email="",
                account_type="none",
                status="unconfigured",
                is_default=False,
            )

        if self.selected_account_name:
            for acc in accounts:
                if acc.get("name") == self.selected_account_name:
                    return GoogleAccountSummary(
                        name=acc.get("name", ""),
                        email=acc.get("email", ""),
                        account_type=acc.get("type", "oauth2"),
                        status=acc.get("status", "active"),
                        is_default=acc.get("is_default", False),
                    )

        info = get_account_info(self.selected_account_name)
        if info:
            return GoogleAccountSummary(
                name=info.get("name", "default"),
                email=info.get("email", ""),
                account_type=info.get("type", "oauth2"),
                status=info.get("status", "active"),
                is_default=info.get("is_default", True),
            )

        first_acc = accounts[0]
        return GoogleAccountSummary(
            name=first_acc.get("name", "default"),
            email=first_acc.get("email", ""),
            account_type=first_acc.get("type", "oauth2"),
            status=first_acc.get("status", "active"),
            is_default=first_acc.get("is_default", False),
        )

    def select_account(self, account_name: str) -> bool:
        """Выбрать активный аккаунт Google по имени.

        Args:
            account_name: Название аккаунта в пуле.

        Returns:
            bool: True в случае успешного переключения.
        """
        accounts = list_google_accounts()
        names = [a.get("name") for a in accounts]
        if account_name in names:
            self.selected_account_name = account_name
            set_default_account(account_name)
            logger.info(f"Выбран активный Google аккаунт: {account_name}")
            return True
        logger.warning(f"Аккаунт '{account_name}' не найден в пуле accounts")
        return False

    def get_accounts_list(self) -> List[Dict[str, Any]]:
        """Получить полный список всех доступных Google аккаунтов.

        Returns:
            List[Dict[str, Any]]: Список словарей с описанием аккаунтов.
        """
        self._accounts_cache = list_google_accounts()
        return self._accounts_cache

    def fetch_calendar_events(self, max_results: int = 20) -> List[CalendarEventSummary]:
        """Загрузить события из Календаря Google.

        Args:
            max_results: Максимальное количество событий.

        Returns:
            List[CalendarEventSummary]: Список объектов событий.
        """
        try:
            items = get_google_calendar_events(user_id=self.user_id, max_results=max_results)
            events: List[CalendarEventSummary] = []
            for item in items:
                start_obj = item.get("start", {})
                start_str = start_obj.get("dateTime") or start_obj.get("date", "")
                end_obj = item.get("end", {})
                end_str = end_obj.get("dateTime") or end_obj.get("date", "")
                events.append(
                    CalendarEventSummary(
                        id=item.get("id", ""),
                        summary=item.get("summary", "Без темы"),
                        start_time=start_str,
                        end_time=end_str,
                        location=item.get("location", ""),
                        html_link=item.get("htmlLink", ""),
                    )
                )
            self._calendar_cache = events
            return events
        except Exception as ex:
            logger.error(f"Ошибка загрузки событий Google Calendar: {ex}")
            return self._calendar_cache

    def fetch_documents(self, page_size: int = 20) -> List[DocumentItemSummary]:
        """Загрузить список Google Документов пользователя.

        Args:
            page_size: Максимальное число файлов.

        Returns:
            List[DocumentItemSummary]: Список документов.
        """
        try:
            files = list_google_documents(user_id=self.user_id, page_size=page_size)
            docs: List[DocumentItemSummary] = []
            for f in files:
                docs.append(
                    DocumentItemSummary(
                        id=f.get("id", ""),
                        name=f.get("name", "Без названия"),
                        mime_type=f.get("mimeType", "application/vnd.google-apps.document"),
                        created_time=f.get("createdTime", ""),
                        modified_time=f.get("modifiedTime", ""),
                        web_view_link=f.get("webViewLink", ""),
                    )
                )
            self._docs_cache = docs
            return docs
        except Exception as ex:
            logger.error(f"Ошибка загрузки списка Google Docs: {ex}")
            return self._docs_cache

    def fetch_drive_files(self, page_size: int = 20) -> List[DriveFileSummary]:
        """Загрузить список файлов с Google Диска.

        Args:
            page_size: Количество файлов.

        Returns:
            List[DriveFileSummary]: Список метаданных файлов.
        """
        headers = get_google_headers(self.user_id)
        if not headers:
            return self._drive_cache
        try:
            import requests

            url = "https://www.googleapis.com/drive/v3/files"
            params = {
                "fields": "files(id, name, mimeType, size, modifiedTime, webViewLink)",
                "pageSize": page_size,
                "q": "trashed=false",
            }
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            if resp.status_code == 200:
                files_data = resp.json().get("files", [])
                drive_files: List[DriveFileSummary] = []
                for f in files_data:
                    drive_files.append(
                        DriveFileSummary(
                            id=f.get("id", ""),
                            name=f.get("name", "Без имени"),
                            mime_type=f.get("mimeType", ""),
                            size_bytes=int(f.get("size", 0)),
                            modified_time=f.get("modifiedTime", ""),
                            web_view_link=f.get("webViewLink", ""),
                        )
                    )
                self._drive_cache = drive_files
                return drive_files
            return self._drive_cache
        except Exception as ex:
            logger.error(f"Ошибка получения списка файлов Google Drive: {ex}")
            return self._drive_cache

    
    # ---------------------------------------------------------------------
    # Методы управления Google Forms (делегируют работу клиенту GoogleFormsClient)
    # ---------------------------------------------------------------------
    def _get_forms_client(self) -> GoogleFormsClient:
        """Получить singleton‑клиент GoogleFormsClient для текущего пользователя."""
        if not hasattr(self, "_forms_client") or self._forms_client is None:
            self._forms_client = GoogleFormsClient(user_id=self.user_id)
        return self._forms_client

    def create_form(self, title: str, description: Optional[str] = None) -> FormItemSummary:
        """Создать форму и добавить её в кеш `_forms_cache`.

        Возвращает объект `FormItemSummary`.
        """
        client = self._get_forms_client()
        summary = client.create_form(title=title, description=description)
        self._forms_cache.append(summary)
        return summary

    def update_form(self, form_id: str, requests: List[Dict[str, Any]]) -> None:
        """Выполнить batchUpdate для указанной формы."""
        client = self._get_forms_client()
        client.batch_update(form_id=form_id, requests=requests)

    def publish_form(self, form_id: str) -> None:
        """Опубликовать форму (включить приём ответов)."""
        client = self._get_forms_client()
        client.set_publish(form_id=form_id, publish=True)
        for f in self._forms_cache:
            if f.form_id == form_id:
                f.published = True
                break

    def close_form(self, form_id: str) -> None:
        """Закрыть форму (отключить приём ответов)."""
        client = self._get_forms_client()
        client.set_publish(form_id=form_id, publish=False)
        for f in self._forms_cache:
            if f.form_id == form_id:
                f.published = False
                break

    def get_form_responses(self, form_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Получить ответы формы через клиент."""
        client = self._get_forms_client()
        return client.get_responses(form_id=form_id, page_size=limit)
def fetch_mail_messages(self, max_results: int = 20) -> List[MailItemSummary]:
        """Загрузить входящие сообщения Gmail.

        Args:
            max_results: Число возвращаемых писем.

        Returns:
            List[MailItemSummary]: Список сообщений.
        """
        headers = get_google_headers(self.user_id)
        if not headers:
            return self._mail_cache
        try:
            import requests

            url = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
            params = {"maxResults": max_results, "q": "label:INBOX"}
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            if resp.status_code != 200:
                return self._mail_cache

            raw_messages = resp.json().get("messages", [])
            messages: List[MailItemSummary] = []
            for msg_meta in raw_messages[:max_results]:
                msg_id = msg_meta.get("id", "")
                if not msg_id:
                    continue
                detail_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}"
                detail_resp = requests.get(
                    detail_url,
                    headers=headers,
                    params={"format": "full"},
                    timeout=5,
                )
                if detail_resp.status_code == 200:
                    d = detail_resp.json()
                    payload = d.get("payload", {})
                    headers_list = payload.get("headers", [])
                    subject = next(
                        (h["value"] for h in headers_list if h.get("name", "").lower() == "subject"),
                        "(Без темы)",
                    )
                    sender = next(
                        (h["value"] for h in headers_list if h.get("name", "").lower() == "from"),
                        "Неизвестно",
                    )
                    date_val = next(
                        (h["value"] for h in headers_list if h.get("name", "").lower() == "date"),
                        "",
                    )
                    messages.append(
                        MailItemSummary(
                            id=msg_id,
                            thread_id=d.get("threadId", ""),
                            subject=subject,
                            sender=sender,
                            date=date_val,
                            snippet=d.get("snippet", ""),
                        )
                    )
            self._mail_cache = messages
            return messages
        except Exception as ex:
            logger.error(f"Ошибка загрузки сообщений Gmail: {ex}")
            return self._mail_cache

    def refresh_all(self, probe_network: bool = True) -> Dict[str, Any]:
        """Обновить сводное состояние интеграций Google Workspace.

        Args:
            probe_network: Если True, выполняются реальные HTTP-запросы к Google API.

        Returns:
            Dict[str, Any]: Полная структура состояния.
        """
        account = self.get_active_account()
        if probe_network and account.status != "unconfigured":
            self.fetch_calendar_events()
            self.fetch_documents()
            self.fetch_drive_files()
            self.fetch_mail_messages()

        self.last_refreshed = datetime.now(timezone.utc).isoformat()
        return {
            "account": {
                "name": account.name,
                "email": account.email,
                "type": account.account_type,
                "status": account.status,
                "is_default": account.is_default,
            },
            "mail_count": len(self._mail_cache),
            "calendar_events_count": len(self._calendar_cache),
            "docs_count": len(self._docs_cache),
            "drive_files_count": len(self._drive_cache),
            "last_refreshed": self.last_refreshed,
        }
