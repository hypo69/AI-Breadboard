# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Google_User_Desktop Src - Forms
# =============================================================================
# Description:
#   Модуль управления Google Forms внутри приложения `google_user_desktop`.
#
# Usage Examples:
#   Python API:
#     from apps.google_user_desktop.src.forms import FormItemSummary
#
#     service = FormItemSummary()
#
# File: forms.py
# Project: ai-breadboard
# Package: apps.google_user_desktop.src
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Модуль управления Google Forms внутри приложения `google_user_desktop`."""

# src/forms.py
"""Модуль управления Google Forms внутри приложения `google_user_desktop`.

Предоставляет клиент `GoogleFormsClient` и dataclass `FormItemSummary`.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from logger import logger

# NOTE: В реальном проекте сюда следует добавить импорт OAuth‑креденциалов
# из общей инфраструктуры (например, get_google_headers или отдельный
# get_google_credentials). Для упрощения в этом прототипе будем использовать
# `googleapiclient.discovery.build` без передачи credentials – это заглушка.

@dataclass
class FormItemSummary:
    """Сводка формы Google Forms.

    Attributes:
        form_id: Идентификатор формы.
        title: Заголовок формы.
        document_url: URL к редактированию формы.
        published: Признак, опубликована ли форма (приём ответов включён).
    """
    form_id: str = ""
    title: str = ""
    document_url: str = ""
    published: bool = False


class GoogleFormsClient:
    """Клиент для работы с Google Forms API.

    Использует `googleapiclient.discovery.build`. Для аутентификации требуется
    OAuth‑токен со scopes:
    - https://www.googleapis.com/auth/forms.body
    - https://www.googleapis.com/auth/forms.responses.readonly
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self._service = None

    def _init_service(self):
        if self._service is None:
            try:
                from googleapiclient.discovery import build
                # В реальном коде сюда передаются credentials, полученные из OAuth‑flow.
                self._service = build('forms', 'v1')
                logger.info("Google Forms service инициализирован")
            except Exception as ex:
                logger.error(f"Не удалось инициализировать Google Forms service: {ex}")
                raise
        return self._service

    def create_form(self, title: str, description: Optional[str] = None) -> FormItemSummary:
        service = self._init_service()
        body: Dict[str, Any] = {"info": {"title": title}}
        if description:
            body["info"]["documentTitle"] = description
        result = service.forms().create(body=body).execute()
        form_id = result.get('formId')
        doc_url = f"https://docs.google.com/forms/d/{form_id}/edit"
        logger.info(f"Создана форма {form_id} (title={title})")
        return FormItemSummary(form_id=form_id, title=title, document_url=doc_url, published=False)

    def batch_update(self, form_id: str, requests: List[Dict[str, Any]]) -> None:
        service = self._init_service()
        service.forms().batchUpdate(formId=form_id, body={"requests": requests}).execute()
        logger.info(f"Выполнен batchUpdate для формы {form_id}")

    def set_publish(self, form_id: str, publish: bool) -> None:
        """Опубликовать (или закрыть) форму.

        Параметр `publish` = True – открыть приём ответов, False – закрыть.
        """
        service = self._init_service()
        service.forms().batchUpdate(
            formId=form_id,
            body={"requests": [{"updateFormInfo": {"info": {"published": publish}}}]},
        ).execute()
        action = "опубликована" if publish else "закрыта"
        logger.info(f"Форма {form_id} {action}")

    def get_responses(self, form_id: str, page_size: int = 20) -> List[Dict[str, Any]]:
        service = self._init_service()
        resp = service.forms().responses().list(formId=form_id, pageSize=page_size).execute()
        return resp.get('responses', [])
