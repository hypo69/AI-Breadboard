"""FastAPI роутер для Google User Desktop."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from apps.common.csv_logger import AppCsvLogger
from src.google_services import get_google_document_content
from ..src.state import GoogleUserDesktopState

router = APIRouter(prefix='/api/google-desktop', tags=['google-desktop'])
_state: Optional[GoogleUserDesktopState] = None
_csv_logger = AppCsvLogger('google_user_desktop')


def get_state() -> GoogleUserDesktopState:
    """Получить или создать синглтон-экземпляр GoogleUserDesktopState.

    Returns:
        GoogleUserDesktopState: Активный экземпляр состояния.
    """
    global _state
    if _state is None:
        _state = GoogleUserDesktopState()
    return _state


@router.get('/status')
async def get_status(request: Request) -> Dict[str, Any]:
    """Получить статус подключения и количество ресурсов Google Workspace.

    Args:
        request: FastAPI HTTP запрос.

    Returns:
        Dict[str, Any]: Сводная информация о текущем аккаунте и сервисах.
    """
    state = get_state()
    res = state.refresh_all(probe_network=False)
    _csv_logger.log_poll(
        poll_type='desktop_status',
        metric_name='status',
        value=res['account']['status'],
        unit='string',
        status='OK' if res['account']['status'] == 'active' else 'WARN',
        details={'account': res['account']['name'], 'email': res['account']['email']},
        filename='google_desktop_status_polls.csv',
    )
    return res


@router.get('/accounts')
async def get_accounts(request: Request) -> Dict[str, Any]:
    """Получить список всех настроенных Google аккаунтов.

    Args:
        request: FastAPI HTTP запрос.

    Returns:
        Dict[str, Any]: Активный аккаунт и список всех аккаунтов в пуле.
    """
    state = get_state()
    accs = state.get_accounts_list()
    active = state.get_active_account()
    return {
        'active_account': {
            'name': active.name,
            'email': active.email,
            'status': active.status,
            'type': active.account_type,
        },
        'accounts': accs,
    }


@router.post('/accounts/select')
async def select_account(request: Request, account_name: str = Query(...)) -> Dict[str, Any]:
    """Переключить активный Google аккаунт по имени.

    Args:
        request: FastAPI HTTP запрос.
        account_name: Имя аккаунта в пуле.

    Returns:
        Dict[str, Any]: Результат смены аккаунта.
    """
    state = get_state()
    success = state.select_account(account_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Аккаунт '{account_name}' не найден.")
    _csv_logger.log_event(
        event_type='account_selected',
        status='SUCCESS',
        details={'account_name': account_name},
        filename='google_desktop_events.csv',
    )
    return {'success': True, 'account_name': account_name}


@router.get('/mail/messages')
async def get_mail_messages(
    request: Request, limit: int = Query(default=20, ge=1, le=100)
) -> Dict[str, Any]:
    """Получить список свежих входящих писем Gmail.

    Args:
        request: FastAPI HTTP запрос.
        limit: Максимальное количество сообщений.

    Returns:
        Dict[str, Any]: Список сообщений электронной почты.
    """
    state = get_state()
    msgs = state.fetch_mail_messages(max_results=limit)
    return {
        'count': len(msgs),
        'messages': [
            {
                'id': m.id,
                'thread_id': m.thread_id,
                'subject': m.subject,
                'sender': m.sender,
                'date': m.date,
                'snippet': m.snippet,
            }
            for m in msgs
        ],
    }


@router.get('/calendar/events')
async def get_calendar_events(
    request: Request, limit: int = Query(default=20, ge=1, le=100)
) -> Dict[str, Any]:
    """Получить ближайшие события из Google Calendar.

    Args:
        request: FastAPI HTTP запрос.
        limit: Лимит результатов.

    Returns:
        Dict[str, Any]: Список предстоящих событий.
    """
    state = get_state()
    events = state.fetch_calendar_events(max_results=limit)
    return {
        'count': len(events),
        'events': [
            {
                'id': e.id,
                'summary': e.summary,
                'start_time': e.start_time,
                'end_time': e.end_time,
                'location': e.location,
                'html_link': e.html_link,
            }
            for e in events
        ],
    }


@router.get('/docs/list')
async def get_docs_list(
    request: Request, limit: int = Query(default=20, ge=1, le=100)
) -> Dict[str, Any]:
    """Получить список недавних Google Документов и Таблиц.

    Args:
        request: FastAPI HTTP запрос.
        limit: Лимит результатов.

    Returns:
        Dict[str, Any]: Список документов.
    """
    state = get_state()
    docs = state.fetch_documents(page_size=limit)
    return {
        'count': len(docs),
        'documents': [
            {
                'id': d.id,
                'name': d.name,
                'mime_type': d.mime_type,
                'created_time': d.created_time,
                'modified_time': d.modified_time,
                'web_view_link': d.web_view_link,
            }
            for d in docs
        ],
    }


@router.get('/docs/{document_id}')
async def get_document_content(request: Request, document_id: str) -> Dict[str, Any]:
    """Получить содержимое конкретного Google Документа по ID.

    Args:
        request: FastAPI HTTP запрос.
        document_id: Идентификатор Google Document.

    Returns:
        Dict[str, Any]: Структурное содержимое документа.
    """
    state = get_state()
    doc_content = get_google_document_content(user_id=state.user_id, document_id=document_id)
    if not doc_content:
        raise HTTPException(status_code=404, detail=f"Документ {document_id} не найден или недоступен.")
    return {'document_id': document_id, 'content': doc_content}


@router.get('/drive/files')
async def get_drive_files(
    request: Request, limit: int = Query(default=20, ge=1, le=100)
) -> Dict[str, Any]:
    """Получить список файлов с Google Диска.

    Args:
        request: FastAPI HTTP запрос.
        limit: Лимит результатов.

    Returns:
        Dict[str, Any]: Список файлов с Google Drive.
    """
    state = get_state()
    files = state.fetch_drive_files(page_size=limit)
    return {
        'count': len(files),
        'files': [
            {
                'id': f.id,
                'name': f.name,
                'mime_type': f.mime_type,
                'size_bytes': f.size_bytes,
                'modified_time': f.modified_time,
                'web_view_link': f.web_view_link,
            }
            for f in files
        ],
    }


@router.post('/sync')
async def sync_all_services(request: Request) -> Dict[str, Any]:
    """Принудительно синхронизировать и обновить данные по всем 4 сервисам Google.

    Args:
        request: FastAPI HTTP запрос.

    Returns:
        Dict[str, Any]: Сводный результат обновления.
    """
    state = get_state()
    res = state.refresh_all(probe_network=True)
    _csv_logger.log_event(
        event_type='sync_completed',
        status='SUCCESS',
        details=res,
        filename='google_desktop_events.csv',
    )
    return {'success': True, 'state': res}


_sync_router_included = False


def init_router() -> APIRouter:
    """Инициализировать и вернуть FastAPI роутер для Google User Desktop.

    Returns:
        APIRouter: Экземпляр настроенного роутера.
    """
    global _sync_router_included
    if not _sync_router_included:
        from .sync_router import router as sync_router
        router.include_router(sync_router)
        _sync_router_included = True
    return router


__all__ = ['init_router', 'router', 'get_state']


