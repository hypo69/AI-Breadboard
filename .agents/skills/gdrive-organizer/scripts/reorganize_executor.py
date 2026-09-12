## \file .agents/skills/gdrive-organizer/scripts/reorganize_executor.py
# -*- coding: utf-8 -*-
#! venv/Scripts/python.exe

"""
Google Drive Reorganization Executor.
=====================================

Executes proposed restructuring plans on Google Drive safely with dry-run support,
automatic directory creation, and detailed action logging.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json
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


class GDriveReorganizeExecutor:
    """Executes file moves, folder creation, and renaming on Google Drive."""

    def __init__(self, service=None, credentials=None, account_name: Optional[str] = None) -> None:
        """
        Initialize executor.

        :param service: Optional Google Drive API client.
        :param credentials: Optional credentials.
        :param account_name: Optional specific account name from secrets pool.
        """
        if service:
            self.service = service
        elif build and get_credentials:
            creds = credentials or get_credentials(account_name=account_name)
            self.service = build("drive", "v3", credentials=creds) if creds else None
        else:
            self.service = None

        self._folder_cache: Dict[str, str] = {}  # path -> folder_id

    def get_or_create_folder_path(self, path: str, dry_run: bool = False) -> Optional[str]:
        """
        Recursively get or create folder tree on Google Drive.

        :param path: Destination path (e.g. '/Finance/Invoices & Receipts').
        :param dry_run: If True, simulates folder creation.
        :return: ID of the deepest folder in the path, or a mock ID in dry-run mode.
        """
        clean_path = path.strip("/")
        if not clean_path:
            return "root"

        if clean_path in self._folder_cache:
            return self._folder_cache[clean_path]

        if dry_run:
            mock_id = f"mock_folder_{clean_path.replace('/', '_')}"
            self._folder_cache[clean_path] = mock_id
            return mock_id

        if not self.service:
            logger.error("Drive service not available.")
            return None

        segments = clean_path.split("/")
        current_parent = "root"
        accumulated_path = ""

        for seg in segments:
            accumulated_path = f"{accumulated_path}/{seg}".lstrip("/")
            if accumulated_path in self._folder_cache:
                current_parent = self._folder_cache[accumulated_path]
                continue

            # Query Drive for existing folder with this name under current_parent
            q = f"mimeType = '{FOLDER_MIME_TYPE}' and name = '{seg}' and '{current_parent}' in parents and trashed = false"
            try:
                res = self.service.files().list(q=q, fields="files(id, name)").execute()
                files = res.get("files", [])
                if files:
                    folder_id = files[0]["id"]
                else:
                    # Create folder
                    meta = {
                        "name": seg,
                        "mimeType": FOLDER_MIME_TYPE,
                        "parents": [current_parent],
                    }
                    new_folder = self.service.files().create(body=meta, fields="id").execute()
                    folder_id = new_folder.get("id")
                    logger.info(f"Created Google Drive folder: '{accumulated_path}' (ID: {folder_id})")

                self._folder_cache[accumulated_path] = folder_id
                current_parent = folder_id
            except Exception as e:
                logger.error(f"Failed to find or create folder segment '{seg}': {e}")
                return None

        return current_parent

    def move_file(self, file_id: str, target_folder_id: str, dry_run: bool = False) -> bool:
        """
        Move file into target folder on Google Drive.

        :param file_id: ID of the file to move.
        :param target_folder_id: ID of the destination folder.
        :param dry_run: If True, logs the operation without modifying Drive.
        :return: True if successful, False otherwise.
        """
        if dry_run:
            logger.info(f"[DRY-RUN] Move file {file_id} to folder {target_folder_id}")
            return True

        if not self.service:
            return False

        try:
            # Retrieve existing parents to remove
            file_meta = self.service.files().get(fileId=file_id, fields="parents").execute()
            previous_parents = ",".join(file_meta.get("parents", []))

            self.service.files().update(
                fileId=file_id,
                addParents=target_folder_id,
                removeParents=previous_parents,
                fields="id, parents",
            ).execute()

            logger.info(f"Successfully moved file {file_id} to folder {target_folder_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to move file {file_id}: {e}")
            return False

    def execute_plan(
        self, plan: Dict[str, Any], dry_run: bool = True, log_output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Execute full restructuring plan.

        :param plan: Restructuring plan dictionary.
        :param dry_run: Whether to run in simulation mode.
        :param log_output_path: Optional path to save execution results.
        :return: Execution results summary.
        """
        actions = plan.get("actions", [])
        results: List[Dict[str, Any]] = []

        logger.info(f"Starting plan execution ({len(actions)} actions, dry_run={dry_run})...")

        for act in actions:
            action_type = act.get("action")
            file_id = act.get("file_id")
            target_folder = act.get("target_folder")

            if action_type in ("MOVE", "ARCHIVE_DUPLICATE") and target_folder:
                dest_id = self.get_or_create_folder_path(target_folder, dry_run=dry_run)
                if dest_id:
                    success = self.move_file(file_id, dest_id, dry_run=dry_run)
                    results.append({
                        "action": action_type,
                        "file_id": file_id,
                        "file_name": act.get("file_name"),
                        "status": "SUCCESS" if success else "FAILED",
                        "dry_run": dry_run,
                    })
                else:
                    results.append({
                        "action": action_type,
                        "file_id": file_id,
                        "status": "FAILED",
                        "error": "Could not resolve destination folder.",
                        "dry_run": dry_run,
                    })

        summary = {
            "total_actions": len(actions),
            "executed": len(results),
            "successful": sum(1 for r in results if r.get("status") == "SUCCESS"),
            "failed": sum(1 for r in results if r.get("status") == "FAILED"),
            "dry_run": dry_run,
            "results": results,
        }

        if log_output_path:
            try:
                log_output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(log_output_path, "w", encoding="utf-8") as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved execution log to {log_output_path}")
            except Exception as e:
                logger.error(f"Failed to write execution log: {e}")

        return summary
