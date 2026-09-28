"""Google Drive Synchronization Service.

Синхронизация локальных данных (базы данных, RAG‑индексы, логи, секреты) с папкой на Google Drive.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import googleapiclient.discovery
from google.auth.transport.requests import Request
from google.auth.transport.requests import Request as UserRequest
from google.oauth2.credentials import Credentials as UserCredentials
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

from logger import logger


class GoogleDriveSync:
    """Управляет синхронизацией данных на Google Drive."""

    SERVICE_ACCOUNT_FILE = 'src/secrets/google_sa_account_service_account.json'
    SCOPES = ['https://www.googleapis.com/auth/drive']

    def __init__(self, service_account_file: Optional[str] = None) -> None:
        """Инициализация сервиса синхронизации.

        Args:
            service_account_file: Путь к файлу сервис‑аккаунта (опционально).
        """
        self.service_account_file = service_account_file or self.SERVICE_ACCOUNT_FILE
        self.drive_service = None
        self.root_folder_id = None
        self.sync_state: Dict[str, Any] = {}
        self._initialize_service()

    def _initialize_service(self) -> None:
        """Инициализирует Google Drive API сервис."""
        try:
            if os.path.exists(self.service_account_file):
                credentials = Credentials.from_service_account_file(
                    self.service_account_file, scopes=self.SCOPES
                )
                self.drive_service = googleapiclient.discovery.build(
                    'drive', 'v3', credentials=credentials
                )
                logger.info('Google Drive сервис инициализирован (service account)')
            else:
                logger.warning(f'Файл сервис‑аккаунта не найден: {self.service_account_file}')
        except Exception as e:
            logger.error(f'Ошибка инициализации Google Drive: {e}')

    def ensure_sync_folder(self, folder_name: str = 'AI-Breadboard-Sync') -> Optional[str]:
        """Убедиться, что папка синхронизации существует на Google Drive.

        Args:
            folder_name: Название папки на Google Drive.

        Returns:
            Optional[str]: ID папки на Google Drive или None в случае ошибки.
        """
        if self.root_folder_id:
            return self.root_folder_id
        if self.drive_service is None:
            logger.error('Google Drive сервис не инициализирован')
            return None
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = (
                self.drive_service.files()
                .list(q=query, spaces='drive', fields='files(id, name)', pageSize=1)
                .execute()
            )
            files = results.get('files', [])
            if files:
                self.root_folder_id = files[0]['id']
                logger.info(f'Папка синхронизации найдена: {self.root_folder_id}')
                return self.root_folder_id
            file_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
            folder = self.drive_service.files().create(body=file_metadata).execute()
            self.root_folder_id = folder['id']
            logger.info(f'Папка синхронизации создана: {self.root_folder_id}')
            return self.root_folder_id
        except Exception as e:
            logger.error(f'Ошибка при работе с папкой синхронизации: {e}')
            return None

    def _get_or_create_subfolder(self, parent_id: str, folder_name: str) -> Optional[str]:
        """Получить или создать подпапку.

        Args:
            parent_id: ID родительской папки.
            folder_name: Название подпапки.

        Returns:
            Optional[str]: ID подпапки или None.
        """
        if self.drive_service is None:
            return None
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
            results = (
                self.drive_service.files()
                .list(q=query, spaces='drive', fields='files(id)', pageSize=1)
                .execute()
            )
            files = results.get('files', [])
            if files:
                return files[0]['id']
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id],
            }
            folder = self.drive_service.files().create(body=file_metadata).execute()
            return folder['id']
        except Exception as e:
            logger.error(f'Ошибка при создании подпапки {folder_name}: {e}')
            return None

    def _calculate_file_hash(self, file_path: str) -> str:
        """Расчёт MD5 хеша файла для проверки изменений.

        Args:
            file_path: Путь к файлу.

        Returns:
            str: MD5 хеш файла.
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f'Ошибка при расчёте хеша {file_path}: {e}')
            return ''

    def _find_drive_file(
        self, parent_id: str, local_path: str, file_hash: str = ''
    ) -> Optional[str]:
        """Найти файл на Google Drive.

        Args:
            parent_id: ID папки на Google Drive.
            local_path: Локальный путь к файлу.
            file_hash: Хеш файла для проверки.

        Returns:
            Optional[str]: ID файла на Google Drive или None.
        """
        if self.drive_service is None:
            return None
        try:
            file_name = os.path.basename(local_path)
            query = f"name='{file_name}' and '{parent_id}' in parents and trashed=false"
            results = (
                self.drive_service.files()
                .list(q=query, spaces='drive', fields='files(id, name)', pageSize=1)
                .execute()
            )
            files = results.get('files', [])
            return files[0]['id'] if files else None
        except Exception as e:
            logger.error(f'Ошибка при поиске файла {local_path}: {e}')
            return None

    def upload_file(
        self,
        local_path: str,
        drive_parent_id: str,
        is_update: bool = False,
        drive_file_id: str = '',
    ) -> bool:
        """Загрузить или обновить файл на Google Drive.

        Args:
            local_path: Локальный путь к файлу.
            drive_parent_id: ID папки на Google Drive.
            is_update: Обновление существующего файла.
            drive_file_id: ID файла на Google Drive (для обновления).

        Returns:
            bool: True если успешно, False в противном случае.
        """
        if self.drive_service is None:
            logger.error('Google Drive сервис не инициализирован')
            return False
        try:
            if not os.path.exists(local_path):
                logger.warning(f'Файл не найден: {local_path}')
                return False
            file_name = os.path.basename(local_path)
            if local_path.endswith('.db'):
                mime_type = 'application/x-sqlite3'
            elif local_path.endswith('.json'):
                mime_type = 'application/json'
            elif local_path.endswith('.log'):
                mime_type = 'text/plain'
            else:
                mime_type = 'application/octet-stream'
            media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)
            if is_update and drive_file_id:
                self.drive_service.files().update(fileId=drive_file_id, media_body=media).execute()
                logger.info(f'Файл обновлён: {file_name}')
            else:
                file_metadata = {'name': file_name, 'parents': [drive_parent_id]}
                self.drive_service.files().create(body=file_metadata, media_body=media).execute()
                logger.info(f'Файл загружен: {file_name}')
            return True
        except Exception as e:
            logger.error(f'Ошибка при загрузке {local_path}: {e}')
            return False

    def sync_directory(
        self,
        local_dir: str,
        drive_parent_id: str,
        recursive: bool = True,
        exclude_patterns: Optional[List[str]] = None,
    ) -> Dict[str, int]:
        """Синхронизировать директорию с Google Drive.

        Args:
            local_dir: Локальный путь к директории.
            drive_parent_id: ID родительской папки на Google Drive.
            recursive: Рекурсивная синхронизация.
            exclude_patterns: Шаблоны файлов для исключения.

        Returns:
            Dict[str, int]: Статистика синхронизации.
        """
        exclude_patterns = exclude_patterns or ['*.pyc', '__pycache__', '.git']
        stats = {'uploaded': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        try:
            if not os.path.isdir(local_dir):
                logger.warning(f'Директория не найдена: {local_dir}')
                return stats
            dir_name = os.path.basename(local_dir)
            drive_dir_id = self._get_or_create_subfolder(drive_parent_id, dir_name)
            if not drive_dir_id:
                stats['failed'] += 1
                return stats
            for root, dirs, files in os.walk(local_dir):
                if root != local_dir and (not recursive):
                    break
                for file in files:
                    if any(file.endswith(pattern.lstrip('*')) for pattern in exclude_patterns):
                        stats['skipped'] += 1
                        continue
                    local_file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(local_file_path, local_dir)
                    current_drive_id = drive_dir_id
                    if os.path.dirname(rel_path):
                        for folder in os.path.dirname(rel_path).split(os.sep):
                            current_drive_id = self._get_or_create_subfolder(
                                current_drive_id, folder
                            )
                            if not current_drive_id:
                                break
                    if current_drive_id and self.upload_file(local_file_path, current_drive_id):
                        stats['uploaded'] += 1
                    else:
                        stats['failed'] += 1
            logger.info(f'Синхронизация директории завершена: {stats}')
            return stats
        except Exception as e:
            logger.error(f'Ошибка при синхронизации {local_dir}: {e}')
            return stats

    def sync_all_data(self) -> Dict[str, Any]:
        """Синхронизировать все данные на Google Drive.

        Returns:
            Dict[str, Any]: Полная статистика синхронизации.
        """
        self.ensure_sync_folder()
        if not self.root_folder_id:
            logger.error('Не удалось создать папку синхронизации')
            return {}
        sync_results: Dict[str, Any] = {}
        logger.info('Синхронизация данных (data)...')
        data_results = self.sync_directory('data', self.root_folder_id, recursive=True)
        sync_results['data'] = data_results
        logger.info('Синхронизация логов (logs)...')
        logs_results = self.sync_directory('logs', self.root_folder_id, recursive=False)
        sync_results['logs'] = logs_results
        logger.info('Синхронизация секретов (secrets)...')
        secrets_results = self.sync_directory(
            'src/secrets', self.root_folder_id, recursive=False
        )
        sync_results['secrets'] = secrets_results
        logger.info('Синхронизация конфигов...')
        config_files = ['config.json', '.env', '.env.example']
        configs_drive_id = self._get_or_create_subfolder(self.root_folder_id, 'configs')
        if configs_drive_id:
            for config_file in config_files:
                if os.path.exists(config_file):
                    if self.upload_file(config_file, configs_drive_id):
                        sync_results.setdefault('configs', {'uploaded': 0})['uploaded'] += 1
        self._save_sync_state(sync_results)
        return sync_results

    def _save_sync_state(self, results: Dict[str, Any]) -> None:
        """Сохранить информацию о состоянии синхронизации.

        Args:
            results: Результаты синхронизации.
        """
        try:
            state_file = 'sync_state.json'
            state_data = {
                'timestamp': datetime.now().isoformat(),
                'results': results,
                'root_folder_id': self.root_folder_id,
            }
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            logger.info(f'Состояние синхронизации сохранено: {state_file}')
        except Exception as e:
            logger.error(f'Ошибка при сохранении состояния синхронизации: {e}')

    def get_sync_status(self) -> Dict[str, Any]:
        """Получить статус последней синхронизации.

        Returns:
            Dict[str, Any]: Статус синхронизации.
        """
        try:
            state_file = 'sync_state.json'
            if os.path.exists(state_file):
                with open(state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f'Ошибка при чтении состояния синхронизации: {e}')
        return {}


def sync_to_google_drive() -> Dict[str, Any]:
    """Функция для синхронизации всех данных на Google Drive.

    Returns:
        Dict[str, Any]: Результаты синхронизации.
    """
    sync = GoogleDriveSync()
    results = sync.sync_all_data()
    print('\n=== Результаты синхронизации ===')
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return results


if __name__ == '__main__':
    import logging

    logging.basicConfig(level=logging.INFO)
    sync_to_google_drive()
