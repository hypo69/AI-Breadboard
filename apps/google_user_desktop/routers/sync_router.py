"""FastAPI REST API роутер для синхронизации Google Drive.

Включает эндпоинты управления состоянием и запуск планировщика.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from logger import logger
from ..src.google_drive_sync import GoogleDriveSync
from ..src.sync_scheduler import ManualSyncHandler, SyncScheduler, get_scheduler

router = APIRouter(prefix='/api/sync', tags=['sync'])


class SyncRequest(BaseModel):
    """Запрос на синхронизацию."""

    sync_interval_hours: int = 6
    include_data: bool = True
    include_logs: bool = True
    include_secrets: bool = True
    include_configs: bool = True


class SyncDirectoryRequest(BaseModel):
    """Запрос на синхронизацию директории."""

    local_path: str
    folder_name: Optional[str] = None
    recursive: bool = True


class SyncFileRequest(BaseModel):
    """Запрос на синхронизацию файла."""

    file_path: str
    folder_name: str = 'uploads'


class SyncStatus(BaseModel):
    """Статус синхронизации."""

    is_running: bool
    last_sync_time: Optional[str]
    next_sync_time: Optional[str]
    sync_interval_hours: int
    root_folder_id: Optional[str]


class SyncResults(BaseModel):
    """Результаты синхронизации."""

    data: Optional[Dict] = None
    logs: Optional[Dict] = None
    secrets: Optional[Dict] = None
    configs: Optional[Dict] = None
    timestamp: str = ''


@router.get('/status', response_model=SyncStatus, summary='Получить статус синхронизации')
async def get_sync_status() -> SyncStatus:
    """Получить текущий статус синхронизации.

    Returns:
        SyncStatus: Статус синхронизации и информация о планировщике.
    """
    try:
        scheduler = get_scheduler()
        status = scheduler.get_status()
        return SyncStatus(
            is_running=status['is_running'],
            last_sync_time=status['last_sync_time'],
            next_sync_time=status['next_sync_time'],
            sync_interval_hours=status['sync_interval_hours'],
            root_folder_id=scheduler.drive_sync.root_folder_id,
        )
    except Exception as e:
        logger.error(f'Ошибка при получении статуса: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/start', summary='Запустить планировщик синхронизации')
async def start_scheduler(request: SyncRequest) -> Dict[str, str]:
    """Запустить планировщик синхронизации.

    Args:
        request: Параметры синхронизации.

    Returns:
        Dict[str, str]: Статус запуска.
    """
    try:
        scheduler = get_scheduler()
        if scheduler.is_running:
            return {'status': 'already_running', 'message': 'Планировщик уже запущен'}
        scheduler.sync_interval_hours = request.sync_interval_hours
        scheduler.start()
        return {
            'status': 'started',
            'message': f'Планировщик запущен с интервалом {request.sync_interval_hours} часов',
        }
    except Exception as e:
        logger.error(f'Ошибка при запуске планировщика: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/stop', summary='Остановить планировщик синхронизации')
async def stop_scheduler() -> Dict[str, str]:
    """Остановить планировщик синхронизации.

    Returns:
        Dict[str, str]: Статус остановки.
    """
    try:
        scheduler = get_scheduler()
        if not scheduler.is_running:
            return {'status': 'not_running', 'message': 'Планировщик не запущен'}
        scheduler.stop()
        return {'status': 'stopped', 'message': 'Планировщик остановлен'}
    except Exception as e:
        logger.error(f'Ошибка при остановке планировщика: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/sync-now', summary='Выполнить синхронизацию немедленно')
async def sync_now(background_tasks: BackgroundTasks) -> Dict[str, str]:
    """Выполнить синхронизацию всех данных немедленно.

    Args:
        background_tasks: Фоновые задачи FastAPI.

    Returns:
        Dict[str, str]: Статус начала синхронизации.
    """
    try:
        scheduler = get_scheduler()
        background_tasks.add_task(scheduler.sync_now)
        return {'status': 'syncing', 'message': 'Синхронизация началась в фоновом режиме'}
    except Exception as e:
        logger.error(f'Ошибка при начале синхронизации: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/sync-directory', summary='Синхронизировать директорию')
async def sync_directory(
    request: SyncDirectoryRequest, background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """Синхронизировать конкретную директорию.

    Args:
        request: Параметры синхронизации директории.
        background_tasks: Фоновые задачи FastAPI.

    Returns:
        Dict[str, str]: Статус начала синхронизации.
    """
    try:
        handler = ManualSyncHandler()
        background_tasks.add_task(
            handler.sync_single_directory, request.local_path, request.folder_name
        )
        return {
            'status': 'syncing',
            'message': f'Синхронизация директории {request.local_path} началась',
        }
    except Exception as e:
        logger.error(f'Ошибка при синхронизации директории: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/sync-file', summary='Синхронизировать файл')
async def sync_file(
    request: SyncFileRequest, background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """Синхронизировать конкретный файл.

    Args:
        request: Параметры синхронизации файла.
        background_tasks: Фоновые задачи FastAPI.

    Returns:
        Dict[str, str]: Статус начала синхронизации.
    """
    try:
        handler = ManualSyncHandler()
        background_tasks.add_task(
            handler.sync_single_file, request.file_path, request.folder_name
        )
        return {
            'status': 'syncing',
            'message': f'Синхронизация файла {request.file_path} началась',
        }
    except Exception as e:
        logger.error(f'Ошибка при синхронизации файла: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/sync-history', summary='Получить историю синхронизации')
async def get_sync_history(limit: int = Query(10, ge=1, le=100)) -> Dict[str, Any]:
    """Получить историю синхронизации.

    Args:
        limit: Максимальное количество записей.

    Returns:
        Dict[str, Any]: История синхронизации.
    """
    try:
        sync = GoogleDriveSync()
        status = sync.get_sync_status()
        return {'status': status, 'note': 'Для полной истории используйте систему логирования'}
    except Exception as e:
        logger.error(f'Ошибка при получении истории: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/drive-info', summary='Получить информацию о папке на Google Drive')
async def get_drive_info() -> Dict[str, Optional[str]]:
    """Получить информацию о папке синхронизации на Google Drive.

    Returns:
        Dict[str, Optional[str]]: Информация о папке.
    """
    try:
        sync = GoogleDriveSync()
        sync.ensure_sync_folder()
        return {
            'root_folder_id': sync.root_folder_id,
            'folder_name': 'AI-Breadboard-Sync',
            'drive_url': f'https://drive.google.com/drive/folders/{sync.root_folder_id}',
        }
    except Exception as e:
        logger.error(f'Ошибка при получении информации: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/test-connection', summary='Проверить подключение к Google Drive')
async def test_connection() -> Dict[str, Optional[str]]:
    """Проверить подключение к Google Drive API.

    Returns:
        Dict[str, Optional[str]]: Результат проверки.
    """
    try:
        sync = GoogleDriveSync()
        if sync.drive_service is None:
            raise Exception('Google Drive сервис не инициализирован')
        sync.ensure_sync_folder()
        return {
            'status': 'connected',
            'message': 'Подключение к Google Drive успешно',
            'root_folder_id': sync.root_folder_id,
        }
    except Exception as e:
        logger.error(f'Ошибка при проверке подключения: {e}')
        return {'status': 'error', 'message': f'Ошибка подключения: {str(e)}'}


def include_sync_routes(app) -> None:
    """Включить маршруты синхронизации в основное приложение FastAPI.

    Args:
        app: Приложение FastAPI.
    """
    app.include_router(router)
    logger.info('Маршруты синхронизации подключены')


__all__ = [
    'router',
    'include_sync_routes',
    'SyncRequest',
    'SyncDirectoryRequest',
    'SyncFileRequest',
    'SyncStatus',
    'SyncResults',
]
