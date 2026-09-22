# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Google Drive Assistant & Manager Module
# =============================================================================
# Description:
#   Provides functions to search, list, download, export, and upload files
#   via Google Drive API.
#
# File: gdrive_manager.py
# Project: ai-breadboard
# Package: .agents.skills.google-drive.scripts
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import argparse
import io
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
except ImportError:
    build = None
    MediaFileUpload = None
    MediaIoBaseDownload = None

from src.ai.google_accounts_state import load_account_credentials
from logger.logger import logger

SCOPES = [
    "https://www.googleapis.com/auth/drive",
]


class GDriveManager:
    """Менеджер взаимодействия с Google Drive API."""

    def __init__(self, credentials=None, account_name: Optional[str] = None) -> None:
        """Инициализация сервиса Google Drive."""
        self.account_name = account_name
        self.creds = credentials or load_account_credentials(account_name=account_name, scopes=SCOPES)
        self.service = build("drive", "v3", credentials=self.creds) if (self.creds and build) else None

    def list_files(self, query: Optional[str] = None, page_size: int = 20) -> List[Dict[str, Any]]:
        """Получение списка файлов или поиск в Google Drive."""
        if not self.service:
            logger.error("Drive сервис не инициализирован.")
            return []

        try:
            q = query if query else "trashed = false"
            results = self.service.files().list(
                q=q,
                pageSize=page_size,
                fields="files(id, name, mimeType, modifiedTime, size, webViewLink)"
            ).execute()
            return results.get("files", [])
        except Exception as e:
            logger.error(f"Ошибка получения списка файлов Drive: {e}")
            return []

    def download_or_export_file(self, file_id: str, mime_type: str, dest_path: Path) -> bool:
        """Скачивание бинарного файла или экспорт Google Docs/Sheets в локальный формат."""
        if not self.service:
            return False

        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            request = None

            if mime_type == "application/vnd.google-apps.document":
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                if not dest_path.name.endswith(".docx"):
                    dest_path = dest_path.with_suffix(".docx")
            elif mime_type == "application/vnd.google-apps.spreadsheet":
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                if not dest_path.name.endswith(".xlsx"):
                    dest_path = dest_path.with_suffix(".xlsx")
            elif mime_type == "application/vnd.google-apps.presentation":
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType="application/pdf"
                )
                if not dest_path.name.endswith(".pdf"):
                    dest_path = dest_path.with_suffix(".pdf")
            else:
                request = self.service.files().get_media(fileId=file_id)

            with io.FileIO(str(dest_path), "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()

            logger.info(f"Файл {file_id} успешно сохранен в: {dest_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка загрузки файла {file_id}: {e}")
            return False

    def upload_file(self, local_path: Path, folder_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Загрузка локального файла на Google Drive."""
        if not self.service or not local_path.exists():
            return None

        try:
            file_metadata = {"name": local_path.name}
            if folder_id:
                file_metadata["parents"] = [folder_id]

            media = MediaFileUpload(str(local_path), resumable=True)
            uploaded = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id, name, webViewLink"
            ).execute()
            logger.info(f"Файл {local_path.name} успешно загружен на Drive. ID: {uploaded.get('id')}")
            return uploaded
        except Exception as e:
            logger.error(f"Ошибка выгрузки файла {local_path}: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(description="Google Drive Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Команды")

    # List
    list_p = subparsers.add_parser("list", help="Список файлов")
    list_p.add_argument("--query", "-q", default="trashed = false", help="Поисковый фильтр")
    list_p.add_argument("--limit", "-l", type=int, default=10, help="Лимит")
    list_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    # Download
    down_p = subparsers.add_parser("download", help="Скачать файл")
    down_p.add_argument("--id", required=True, help="ID файла на Drive")
    down_p.add_argument("--mime", default="", help="MIME тип")
    down_p.add_argument("--dest", required=True, help="Путь для сохранения")
    down_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    # Upload
    up_p = subparsers.add_parser("upload", help="Загрузить файл на Drive")
    up_p.add_argument("--file", required=True, help="Локальный путь к файлу")
    up_p.add_argument("--folder", default=None, help="ID папки назначения")
    up_p.add_argument("--account", "-a", default=None, help="Имя аккаунта")

    args = parser.parse_args()
    manager = GDriveManager(account_name=getattr(args, "account", None))

    if not manager.service:
        print("❌ Не удалось авторизоваться в Google Drive. Проверьте системный плагин google_oauth.")
        sys.exit(1)

    if args.command == "list" or not args.command:
        query = getattr(args, "query", "trashed = false")
        limit = getattr(args, "limit", 10)
        files = manager.list_files(query=query, page_size=limit)
        print(f"📁 Найдено {len(files)} файлов на Drive:")
        for i, f in enumerate(files, 1):
            print(f"[{i}] {f.get('name')} (ID: {f.get('id')}, MIME: {f.get('mimeType')})")
    elif args.command == "download":
        dest = Path(args.dest)
        ok = manager.download_or_export_file(args.id, args.mime, dest)
        if ok:
            print(f"✅ Файл сохранен в: {dest}")
    elif args.command == "upload":
        res = manager.upload_file(Path(args.file), folder_id=args.folder)
        if res:
            print(f"✅ Файл загружен. ID: {res.get('id')}, Ссылка: {res.get('webViewLink')}")


if __name__ == "__main__":
    main()

