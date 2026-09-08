## \file .agents/skills/google-workspace/scripts/gdrive_manager.py
# -*- coding: utf-8 -*-
#! venv/Scripts/python.exe

"""
Google Drive Manager Module.
============================

Provides listing, searching, downloading, and exporting of Google Drive files.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import io
import argparse
import sys

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from src.logger.logger import logger
from agents.skills.google_workspace.scripts.google_auth import get_credentials


class GDriveManager:
    """Manages interactions with Google Drive API."""

    def __init__(self, credentials=None) -> None:
        """Initialize Google Drive service."""
        self.creds = credentials or get_credentials()
        self.service = build("drive", "v3", credentials=self.creds) if self.creds else None

    def list_files(self, query: Optional[str] = None, page_size: int = 20) -> List[Dict[str, Any]]:
        """List or search files in Google Drive."""
        if not self.service:
            logger.error("Drive service is not initialized.")
            return []

        try:
            q = query if query else "trashed = false"
            results = self.service.files().list(
                q=q,
                pageSize=page_size,
                fields="files(id, name, mimeType, modifiedTime, size)"
            ).execute()
            return results.get("files", [])
        except Exception as e:
            logger.error(f"Failed to list Drive files: {e}")
            return []

    def download_or_export_file(self, file_id: str, mime_type: str, dest_path: Path) -> bool:
        """Download binary file or export Google Workspace document to local disk."""
        if not self.service:
            return False

        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            request = None

            # Handle Google Docs formats -> Export to standard formats
            if mime_type == "application/vnd.google-apps.document":
                request = self.service.files().export_media(fileId=file_id, mimeType="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                if not dest_path.name.endswith(".docx"):
                    dest_path = dest_path.with_suffix(".docx")
            elif mime_type == "application/vnd.google-apps.spreadsheet":
                request = self.service.files().export_media(fileId=file_id, mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                if not dest_path.name.endswith(".xlsx"):
                    dest_path = dest_path.with_suffix(".xlsx")
            elif mime_type == "application/vnd.google-apps.presentation":
                request = self.service.files().export_media(fileId=file_id, mimeType="application/pdf")
                if not dest_path.name.endswith(".pdf"):
                    dest_path = dest_path.with_suffix(".pdf")
            else:
                request = self.service.files().get_media(fileId=file_id)

            with io.FileIO(str(dest_path), "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()

            logger.info(f"Successfully downloaded file {file_id} to {dest_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download/export file {file_id}: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Google Drive CLI Manager")
    parser.add_argument("--query", "-q", default="", help="Search query (e.g. name contains 'Report')")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Max files to list")
    args = parser.parse_args()

    manager = GDriveManager()
    if not manager.service:
        print("❌ Could not authenticate with Google Drive. Check credentials.json.")
        sys.exit(1)

    print(f"📁 Listing Drive files (limit: {args.limit})...")
    files = manager.list_files(query=args.query, page_size=args.limit)
    for i, f in enumerate(files, 1):
        print(f"[{i}] {f.get('name')} (ID: {f.get('id')}, Type: {f.get('mimeType')})")


if __name__ == "__main__":
    main()
