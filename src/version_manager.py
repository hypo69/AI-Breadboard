# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Version manager and automatic update handler
# =============================================================================
# Description:
#   Module for managing application versions, checking updates in Git,
#   downloading and applying updates with backup/restore capabilities.
#
# File: version_manager.py
# Project: ai-breadboard
# Package: src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
Version manager and automatic update handler.
Platform: Windows, Unix
Synopsis: Version manager and automatic updates

Key functions:
- Check version in Git repository
- Download updated files
- Create backups before updating
- Cross-platform support (Windows, Linux, macOS)
"""

import os
import subprocess
import shutil
import asyncio
import tempfile
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from header import __root__
from src.logger import logger

class UpdateStatus(Enum):
    """Application update statuses."""
    CURRENT = "up_to_date"
    UPDATE_AVAILABLE = "update_available"
    ERROR = "error"
    UPDATING = "updating"

@dataclass
class VersionInfo:
    """Information about application version."""
    current_version: str
    remote_version: str
    commit_hash: str
    remote_commit_hash: str
    is_update_available: bool
    update_status: str

class VersionManager:
    """
    Application version and update manager.
    
    Implements functionality:
    - Check current version in Git
    - Check available updates on remote repository
    - Download and apply updates
    - Create backups before updating
    - Restore from backup in case of error
    
    All backups stored in system temp directory for cross-platform compatibility.
    """
    
    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize version manager.
        
        Args:
            repo_path: Path to repository (default: __root__)
        """
        self.repo_path: Path = repo_path or __root__
        self.temp_backup_dir: Path = Path(tempfile.gettempdir()) / 'ai-breadboard' / 'backups'
        self.update_log_dir: Path = Path(tempfile.gettempdir()) / 'ai-breadboard' / 'updates'
        self.current_version: str = "1.0.0"
        self.remote_url: str = "origin"
        
        # Create directories
        self.temp_backup_dir.mkdir(parents=True, exist_ok=True)
        self.update_log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"VersionManager initialized. Repo: {self.repo_path}")
        logger.info(f"Backup directory: {self.temp_backup_dir}")
    
    def _run_git_command(self, command: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        """
        Execute git command.
        
        Args:
            command: List of arguments for git command
            cwd: Working directory (default: repo_path)
            
        Returns:
            Tuple (exit code, stdout, stderr)
        """
        try:
            cwd = cwd or self.repo_path
            result = subprocess.run(
                command,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            logger.error("Git command timeout")
            return -1, "", "Timeout"
        except Exception as ex:
            logger.error(f"Error executing git command: {ex}")
            return -1, "", str(ex)
    
    def get_current_version(self) -> Optional[str]:
        """
        Get current version from git tag or version file.
        
        Returns:
            Version string or None on error
        """
        try:
            # Try to get latest tag (version)
            rc, stdout, stderr = self._run_git_command(["git", "describe", "--tags", "--always"])
            
            if rc == 0 and stdout:
                self.current_version = stdout
                logger.info(f"Current version: {self.current_version}")
                return self.current_version
            
            # If no tags, use commit hash
            rc, stdout, stderr = self._run_git_command(["git", "rev-parse", "--short", "HEAD"])
            if rc == 0 and stdout:
                self.current_version = f"commit-{stdout}"
                logger.info(f"Current version (hash): {self.current_version}")
                return self.current_version
            
            logger.warning("Could not determine current version")
            return None
        except Exception as ex:
            logger.error(f"Error getting current version: {ex}")
            return None
    
    def get_remote_version(self) -> Optional[str]:
        """
        Get version from remote repository.
        
        Returns:
            Version string or None on error
        """
        try:
            # Get remote repository information
            rc, stdout, stderr = self._run_git_command(["git", "ls-remote", "--tags", self.remote_url])
            
            if rc == 0 and stdout:
                lines = stdout.split('\n')
                # Find latest tag
                tags = [line.split()[-1].replace('refs/tags/', '').replace('^{}', '') 
                       for line in lines if 'refs/tags/' in line]
                if tags:
                    # Sort and get latest
                    remote_version = sorted(tags)[-1]
                    logger.info(f"Remote version: {remote_version}")
                    return remote_version
            
            # If no tags, use HEAD of remote repo
            rc, stdout, stderr = self._run_git_command(["git", "ls-remote", self.remote_url, "HEAD"])
            if rc == 0 and stdout:
                remote_hash = stdout.split()[0]
                logger.info(f"Remote version (HEAD): {remote_hash}")
                return f"remote-{remote_hash[:7]}"
            
            logger.warning("Could not determine remote version")
            return None
        except Exception as ex:
            logger.error(f"Error getting remote version: {ex}")
            return None
    
    def check_updates(self) -> Dict:
        """
        Check for available updates.
        
        Returns:
            Dictionary with update information
        """
        try:
            # Get current versions
            current = self.get_current_version()
            remote = self.get_remote_version()
            
            if not current or not remote:
                logger.warning("Could not check updates")
                return {
                    "status": UpdateStatus.ERROR.value,
                    "message": "Could not get version information"
                }
            
            # Get commit hashes
            rc1, curr_hash, _ = self._run_git_command(["git", "rev-parse", "HEAD"])
            rc2, remote_hash, _ = self._run_git_command(["git", "rev-parse", f"{self.remote_url}/main"])
            
            is_update_available = current != remote
            status = UpdateStatus.UPDATE_AVAILABLE if is_update_available else UpdateStatus.CURRENT
            
            result = {
                "status": status.value,
                "current_version": current,
                "remote_version": remote,
                "current_commit": curr_hash if rc1 == 0 else "unknown",
                "remote_commit": remote_hash if rc2 == 0 else "unknown",
                "is_update_available": is_update_available,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Update check: {result['status']}")
            return result
        except Exception as ex:
            logger.error(f"Error checking updates: {ex}")
            return {
                "status": UpdateStatus.ERROR.value,
                "message": str(ex)
            }
    
    def backup_files(self, files_to_backup: Optional[List[str]] = None) -> Optional[Path]:
        """
        Create backup of files before updating.
        
        Args:
            files_to_backup: List of files to backup (default: main project files)
        
        Returns:
            Path to backup directory or None on error
        """
        try:
            # Standard files for backup
            if files_to_backup is None:
                files_to_backup = [
                    "config.json",
                    ".env",
                    "src",
                    "requirements.txt"
                ]
            
            # Create backup directory
            backup_dir = self.temp_backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Creating backup in: {backup_dir}")
            
            backup_count = 0
            for file_item in files_to_backup:
                src = self.repo_path / file_item
                
                if not src.exists():
                    logger.warning(f"Backup file not found: {src}")
                    continue
                
                dst = backup_dir / file_item
                
                try:
                    if src.is_dir():
                        if dst.exists():
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
                    
                    backup_count += 1
                    logger.debug(f"Backed up: {file_item}")
                except Exception as ex:
                    logger.warning(f"Error backing up {file_item}: {ex}")
            
            if backup_count == 0:
                logger.error("Could not create backup (no files)")
                return None
            
            # Save backup information
            backup_info = {
                "timestamp": datetime.now().isoformat(),
                "repo_path": str(self.repo_path),
                "backed_up_files": files_to_backup,
                "backed_up_count": backup_count,
                "version": self.current_version
            }
            
            info_file = backup_dir / ".backup_info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Backup created: {backup_dir}")
            return backup_dir
        except Exception as ex:
            logger.error(f"Error creating backup: {ex}")
            return None
    
    def restore_from_backup(self, backup_path: Path) -> bool:
        """
        Restore files from backup.
        
        Args:
            backup_path: Path to backup directory
            
        Returns:
            True if restore successful, False otherwise
        """
        try:
            if not backup_path.exists():
                logger.error(f"Backup directory not found: {backup_path}")
                return False
            
            logger.info(f"Restoring from backup: {backup_path}")
            
            restore_count = 0
            for item in backup_path.iterdir():
                if item.name == ".backup_info.json":
                    continue
                
                dst = self.repo_path / item.name
                
                try:
                    if item.is_dir():
                        if dst.exists():
                            shutil.rmtree(dst)
                        shutil.copytree(item, dst, dirs_exist_ok=True)
                    else:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, dst)
                    
                    restore_count += 1
                    logger.debug(f"Restored: {item.name}")
                except Exception as ex:
                    logger.warning(f"Error restoring {item.name}: {ex}")
            
            logger.info(f"Restored files: {restore_count}")
            return restore_count > 0
        except Exception as ex:
            logger.error(f"Error restoring from backup: {ex}")
            return False
    
    def fetch_updates(self) -> bool:
        """
        Download updates from remote repository.
        
        Returns:
            True if download successful, False otherwise
        """
        try:
            logger.info(f"Downloading updates from {self.remote_url}...")
            
            # Execute git fetch
            rc, stdout, stderr = self._run_git_command(["git", "fetch", self.remote_url])
            
            if rc != 0:
                logger.error(f"Error git fetch: {stderr}")
                return False
            
            logger.info("Updates downloaded successfully")
            return True
        except Exception as ex:
            logger.error(f"Error downloading updates: {ex}")
            return False
    
    def merge_updates(self, branch: str = "main") -> Tuple[bool, str]:
        """
        Merge updates from remote repository.
        
        Args:
            branch: Branch name (default: main)
            
        Returns:
            Tuple (success, message)
        """
        try:
            logger.info(f"Merging updates from {self.remote_url}/{branch}...")
            
            # Execute git merge
            rc, stdout, stderr = self._run_git_command(
                ["git", "merge", f"{self.remote_url}/{branch}"]
            )
            
            if rc != 0:
                # May be merge conflict
                if "conflict" in stderr.lower():
                    logger.warning(f"Merge conflict: {stderr}")
                    return False, f"Conflict during merge: {stderr}"
                
                logger.error(f"Error git merge: {stderr}")
                return False, f"Error merging: {stderr}"
            
            logger.info("Updates merged successfully")
            return True, stdout
        except Exception as ex:
            logger.error(f"Error merging updates: {ex}")
            return False, str(ex)
    
    async def update_application(self, branch: str = "main", auto_backup: bool = True) -> Dict:
        """
        Perform complete application update.
        
        Process:
        1. Check for available updates
        2. Create backup (if auto_backup=True)
        3. Download updates
        4. Merge updates
        5. Update dependencies (if requirements.txt changed)
        
        Args:
            branch: Branch to update
            auto_backup: Whether to create backup before updating
            
        Returns:
            Dictionary with update result
        """
        try:
            logger.info("Starting application update process...")
            
            # Check for updates
            check_result = self.check_updates()
            if check_result["status"] == UpdateStatus.ERROR.value:
                return {
                    "success": False,
                    "status": UpdateStatus.ERROR.value,
                    "message": "Could not check for updates"
                }
            
            if not check_result.get("is_update_available"):
                logger.info("Application is already up to date")
                return {
                    "success": False,
                    "status": UpdateStatus.CURRENT.value,
                    "message": "No updates available"
                }
            
            # Create backup
            backup_path = None
            if auto_backup:
                backup_path = self.backup_files()
                if not backup_path:
                    return {
                        "success": False,
                        "status": UpdateStatus.ERROR.value,
                        "message": "Could not create backup"
                    }
            
            # Download updates
            if not self.fetch_updates():
                if backup_path:
                    self.restore_from_backup(backup_path)
                return {
                    "success": False,
                    "status": UpdateStatus.ERROR.value,
                    "message": "Error downloading updates"
                }
            
            # Merge updates
            merge_ok, merge_msg = self.merge_updates(branch)
            if not merge_ok:
                if backup_path:
                    self.restore_from_backup(backup_path)
                return {
                    "success": False,
                    "status": UpdateStatus.ERROR.value,
                    "message": f"Error merging: {merge_msg}"
                }
            
            # Save update information
            update_info = {
                "timestamp": datetime.now().isoformat(),
                "from_version": check_result.get("current_version"),
                "to_version": check_result.get("remote_version"),
                "backup_path": str(backup_path) if backup_path else None,
                "branch": branch,
                "status": "success"
            }
            
            update_log_file = self.update_log_dir / f"update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(update_log_file, 'w', encoding='utf-8') as f:
                json.dump(update_info, f, indent=2, ensure_ascii=False)
            
            logger.info(
                f"Application updated: {check_result.get('current_version')} → "
                f"{check_result.get('remote_version')}"
            )
            
            return {
                "success": True,
                "status": UpdateStatus.CURRENT.value,
                "message": "Update completed successfully",
                "version": check_result.get("remote_version"),
                "backup_path": str(backup_path) if backup_path else None
            }
        except Exception as ex:
            logger.error(f"Error updating application: {ex}")
            return {
                "success": False,
                "status": UpdateStatus.ERROR.value,
                "message": str(ex)
            }
    
    def cleanup_old_backups(self, keep_count: int = 5) -> int:
        """
        Delete old backups keeping latest N.
        
        Args:
            keep_count: Number of latest backups to keep
            
        Returns:
            Number of deleted backups
        """
        try:
            if not self.temp_backup_dir.exists():
                return 0
            
            backups = sorted(
                [d for d in self.temp_backup_dir.iterdir() if d.is_dir()],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            deleted_count = 0
            for backup in backups[keep_count:]:
                try:
                    shutil.rmtree(backup)
                    deleted_count += 1
                    logger.debug(f"Deleted old backup: {backup.name}")
                except Exception as ex:
                    logger.warning(f"Error deleting backup: {ex}")
            
            if deleted_count > 0:
                logger.info(f"Deleted old backups: {deleted_count}")
            
            return deleted_count
        except Exception as ex:
            logger.error(f"Error cleaning backups: {ex}")
            return 0

# Global version manager instance
version_manager: Optional[VersionManager] = None

def get_version_manager(repo_path: Optional[Path] = None) -> VersionManager:
    """
    Get global version manager instance (Singleton).
    
    Args:
        repo_path: Path to repository
        
    Returns:
        VersionManager instance
    """
    global version_manager
    if version_manager is None:
        version_manager = VersionManager(repo_path)
    return version_manager
