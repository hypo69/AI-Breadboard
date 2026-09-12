## \file .agents/skills/gdrive-organizer/scripts/gdrive_scanner.py
# -*- coding: utf-8 -*-
#! venv/Scripts/python.exe

"""
Google Drive Scanner Module.
============================

Recursively traverses Google Drive items, builds parent-child folder structures,
and collects comprehensive file metadata (mimeType, size, modified dates, parent IDs).
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import sys

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Ensure google-workspace scripts directory is on sys.path for google_auth
_GW_SCRIPTS_DIR = _REPO_ROOT / ".agents" / "skills" / "google-workspace" / "scripts"
if str(_GW_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_GW_SCRIPTS_DIR))

from src.logger.logger import logger

try:
    from googleapiclient.discovery import build
    from google_auth import get_credentials
except ImportError:
    build = None
    get_credentials = None


FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"


class GDriveScanner:
    """Recursively scans and builds file/folder hierarchy from Google Drive."""

    def __init__(self, service=None, credentials=None, account_name: Optional[str] = None) -> None:
        """
        Initialize Google Drive scanner service.

        :param service: Optional pre-configured Google Drive API client.
        :param credentials: Optional credentials object.
        :param account_name: Optional specific account name from secrets pool.
        """
        if service:
            self.service = service
        elif build and get_credentials:
            creds = credentials or get_credentials(account_name=account_name)
            self.service = build("drive", "v3", credentials=creds) if creds else None
        else:
            self.service = None

    def fetch_all_items(
        self,
        folder_id: Optional[str] = None,
        include_trashed: bool = False,
        page_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all accessible files and folders with pagination.

        :param folder_id: Optional root/subfolder ID to constrain search.
        :param include_trashed: Whether to include trashed files.
        :param page_size: Results per page.
        :return: List of file/folder metadata dictionaries.
        """
        if not self.service:
            logger.error("Google Drive API service is not initialized.")
            return []

        query_parts = []
        if not include_trashed:
            query_parts.append("trashed = false")
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")

        query = " and ".join(query_parts) if query_parts else ""

        items: List[Dict[str, Any]] = []
        page_token = None

        fields = (
            "nextPageToken, files(id, name, mimeType, modifiedTime, createdTime, "
            "size, md5Checksum, parents, webViewLink, shared)"
        )

        try:
            while True:
                response = (
                    self.service.files()
                    .list(
                        q=query or None,
                        pageSize=page_size,
                        fields=fields,
                        pageToken=page_token,
                        supportsAllDrives=True,
                        includeItemsFromAllDrives=True,
                    )
                    .execute()
                )

                items.extend(response.get("files", []))
                page_token = response.get("nextPageToken")
                if not page_token:
                    break

            logger.info(f"Retrieved {len(items)} items from Google Drive.")
            return items
        except Exception as ex:
            logger.error(f"Error fetching Google Drive items: {ex}")
            return items

    def build_hierarchy(self, raw_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build an indexed hierarchy mapping paths, folder trees, and item parents.

        :param raw_items: List of item dictionaries from Drive API.
        :return: Structured hierarchy dictionary with items_by_id, folder_map, and file_paths.
        """
        items_by_id: Dict[str, Dict[str, Any]] = {item["id"]: item for item in raw_items}
        folders: Dict[str, Dict[str, Any]] = {}
        files: List[Dict[str, Any]] = []

        for item in raw_items:
            if item.get("mimeType") == FOLDER_MIME_TYPE:
                folders[item["id"]] = item
            else:
                files.append(item)

        # Compute full paths for each item
        paths_by_id: Dict[str, str] = {}

        def get_item_path(item_id: str, visited: Optional[set] = None) -> str:
            if visited is None:
                visited = set()
            if item_id in visited:
                return "/<loop>/"
            visited.add(item_id)

            if item_id in paths_by_id:
                return paths_by_id[item_id]

            item = items_by_id.get(item_id)
            if not item:
                return "/<unknown>/"

            parents = item.get("parents", [])
            name = item.get("name", "Untitled")

            if not parents:
                path = f"/{name}"
            else:
                parent_id = parents[0]
                if parent_id in folders:
                    parent_path = get_item_path(parent_id, visited)
                    path = f"{parent_path.rstrip('/')}/{name}"
                else:
                    path = f"/[Root]/{name}"

            paths_by_id[item_id] = path
            return path

        for item_id, item in items_by_id.items():
            item["full_path"] = get_item_path(item_id)

        return {
            "items_by_id": items_by_id,
            "folders": folders,
            "files": files,
            "paths_by_id": paths_by_id,
        }
