# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: .. module:: core.version_manager
# =============================================================================
# Description:
#   Module для управления версиями приложения, проверки обновлений в Git,
#
# File: version_manager.py
# Project: ai-breadboard
# Package: core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""
.. module:: core.version_manager
    :platform: Windows, Unix
    :synopsis: Менеджер версий и автоматических обновлений
   
Основные функции:
- Check версии в Git репозитории
- Скачивание обновлённых файлов
- Создание резервных копий перед обновлением
- Кроссплатформенная поддержка (Windows, Linux, macOS)
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
from core.logger import logger

class UpdateStatus(Enum):
    """Статусы обновления приложения."""
    CURRENT = "up_to_date"
    UPDATE_AVAILABLE = "update_available"
    ERROR = "error"
    UPDATING = "updating"

@dataclass
class VersionInfo:
    """Info о версии приложения."""
    current_version: str
    remote_version: str
    commit_hash: str
    remote_commit_hash: str
    is_update_available: bool
    update_status: str

class VersionManager:
    """
    Менеджер версий и обновлений приложения.
    
    Реализует функциональность:
    - Check текущей версии в Git
    - Check доступных обновлений на удалённом репозитории
    - Скачивание и применение обновлений
    - Создание резервных копий перед обновлением
    - Восстановление из резервной копии в случае ошибки
    
    Все резервные копии хранятся в системной temp директории для
    кроссплатформенной совместимости.
    """
    
    def __init__(self, repo_path: Optional[Path] = None):
        """
        Инициализирует менеджер версий.
        
        Args:
            repo_path: Путь к репозиторию (по умолчанию __root__)
        """
        self.repo_path: Path = repo_path or __root__
        self.temp_backup_dir: Path = Path(tempfile.gettempdir()) / 'ai-breadboard' / 'backups'
        self.update_log_dir: Path = Path(tempfile.gettempdir()) / 'ai-breadboard' / 'updates'
        self.current_version: str = "1.0.0"
        self.remote_url: str = "origin"
        
        # Создание директорий
        self.temp_backup_dir.mkdir(parents=True, exist_ok=True)
        self.update_log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"VersionManager инициализирован. Репо: {self.repo_path}")
        logger.info(f"Директория backup: {self.temp_backup_dir}")
    
    def _run_git_command(self, command: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        """
        Performs git команду.
        
        Args:
            command: List аргументов для git команды
            cwd: Рабочая директория (по умолчанию repo_path)
            
        Returns:
            Tuple (код выхода, stdout, stderr)
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
            logger.error("Git команда истекла по таймауту")
            return -1, "", "Timeout"
        except Exception as ex:
            logger.error(f"Error выполнения git команды: {ex}")
            return -1, "", str(ex)
    
    def get_current_version(self) -> Optional[str]:
        """
        Receives текущую версию из git тега или версии файла.
        
        Returns:
            String версии или None при ошибке
        """
        try:
            # Пытаемся получить последний тег (версию)
            rc, stdout, stderr = self._run_git_command(["git", "describe", "--tags", "--always"])
            
            if rc == 0 and stdout:
                self.current_version = stdout
                logger.info(f"Текущая версия: {self.current_version}")
                return self.current_version
            
            # Если тегов нет, используем хеш коммита
            rc, stdout, stderr = self._run_git_command(["git", "rev-parse", "--short", "HEAD"])
            if rc == 0 and stdout:
                self.current_version = f"commit-{stdout}"
                logger.info(f"Текущая версия (хеш): {self.current_version}")
                return self.current_version
            
            logger.warning("Не удалось определить текущую версию")
            return None
        except Exception as ex:
            logger.error(f"Error получения текущей версии: {ex}")
            return None
    
    def get_remote_version(self) -> Optional[str]:
        """
        Receives версию из удалённого репозитория.
        
        Returns:
            String версии или None при ошибке
        """
        try:
            # Получаем информацию об удалённом репозитории
            rc, stdout, stderr = self._run_git_command(["git", "ls-remote", "--tags", self.remote_url])
            
            if rc == 0 and stdout:
                lines = stdout.split('\n')
                # Ищем последний тег
                tags = [line.split()[-1].replace('refs/tags/', '').replace('^{}', '') 
                       for line in lines if 'refs/tags/' in line]
                if tags:
                    # Сортируем и берём последний
                    remote_version = sorted(tags)[-1]
                    logger.info(f"Удалённая версия: {remote_version}")
                    return remote_version
            
            # Если тегов нет, используем HEAD удалённого репо
            rc, stdout, stderr = self._run_git_command(["git", "ls-remote", self.remote_url, "HEAD"])
            if rc == 0 and stdout:
                remote_hash = stdout.split()[0]
                logger.info(f"Удалённая версия (HEAD): {remote_hash}")
                return f"remote-{remote_hash[:7]}"
            
            logger.warning("Не удалось определить удалённую версию")
            return None
        except Exception as ex:
            logger.error(f"Error получения удалённой версии: {ex}")
            return None
    
    def check_updates(self) -> Dict:
        """
        Checks доступность обновлений.
        
        Returns:
            Dictionary с информацией об обновлениях
        """
        try:
            # Получаем текущие версии
            current = self.get_current_version()
            remote = self.get_remote_version()
            
            if not current or not remote:
                logger.warning("Не удалось проверить обновления")
                return {
                    "status": UpdateStatus.ERROR.value,
                    "message": "Не удалось получить информацию о версиях"
                }
            
            # Получаем хеши коммитов
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
            
            logger.info(f"Check обновлений: {result['status']}")
            return result
        except Exception as ex:
            logger.error(f"Error проверки обновлений: {ex}")
            return {
                "status": UpdateStatus.ERROR.value,
                "message": str(ex)
            }
    
    def backup_files(self, files_to_backup: Optional[List[str]] = None) -> Optional[Path]:
        """
        Creates резервную копию файлов перед обновлением.
        
        Args:
            files_to_backup: List файлов для резервного копирования 
                            (по умолчанию основные файлы проекта)
        
        Returns:
            Путь к директории с резервной копией или None при ошибке
        """
        try:
            # Стандартные файлы для резервного копирования
            if files_to_backup is None:
                files_to_backup = [
                    "config.json",
                    ".env",
                    "core",
                    "requirements.txt"
                ]
            
            # Создаём директорию для резервной копии
            backup_dir = self.temp_backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Создание резервной копии в: {backup_dir}")
            
            backup_count = 0
            for file_item in files_to_backup:
                src = self.repo_path / file_item
                
                if not src.exists():
                    logger.warning(f"Файл для резервного копирования не найден: {src}")
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
                    logger.debug(f"Скопирован: {file_item}")
                except Exception as ex:
                    logger.warning(f"Error копирования {file_item}: {ex}")
            
            if backup_count == 0:
                logger.error("Не удалось создать резервную копию (нет файлов)")
                return None
            
            # Сохраняем информацию о резервной копии
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
            
            logger.success(f"Резервная копия создана: {backup_dir}")
            return backup_dir
        except Exception as ex:
            logger.error(f"Error создания резервной копии: {ex}")
            return None
    
    def restore_from_backup(self, backup_path: Path) -> bool:
        """
        Восстанавливает файлы из резервной копии.
        
        Args:
            backup_path: Путь к директории с резервной копией
            
        Returns:
            True если восстановление successfully, False иначе
        """
        try:
            if not backup_path.exists():
                logger.error(f"Директория резервной копии не найдена: {backup_path}")
                return False
            
            logger.info(f"Восстановление из резервной копии: {backup_path}")
            
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
                    logger.debug(f"Восстановлен: {item.name}")
                except Exception as ex:
                    logger.warning(f"Error восстановления {item.name}: {ex}")
            
            logger.success(f"Восстановлено файлов: {restore_count}")
            return restore_count > 0
        except Exception as ex:
            logger.error(f"Error восстановления из резервной копии: {ex}")
            return False
    
    def fetch_updates(self) -> bool:
        """
        Downloads обновления из удалённого репозитория.
        
        Returns:
            True если скачивание successfully, False иначе
        """
        try:
            logger.info(f"Скачивание обновлений с {self.remote_url}...")
            
            # Выполняем git fetch
            rc, stdout, stderr = self._run_git_command(["git", "fetch", self.remote_url])
            
            if rc != 0:
                logger.error(f"Error git fetch: {stderr}")
                return False
            
            logger.success("Обновления скачаны successfully")
            return True
        except Exception as ex:
            logger.error(f"Error скачивания обновлений: {ex}")
            return False
    
    def merge_updates(self, branch: str = "main") -> Tuple[bool, str]:
        """
        Объединяет обновления из удалённого репозитория.
        
        Args:
            branch: Название ветки (по умолчанию main)
            
        Returns:
            Tuple (success, сообщение)
        """
        try:
            logger.info(f"Объединение обновлений из {self.remote_url}/{branch}...")
            
            # Выполняем git merge
            rc, stdout, stderr = self._run_git_command(
                ["git", "merge", f"{self.remote_url}/{branch}"]
            )
            
            if rc != 0:
                # Может быть конфликт слияния
                if "conflict" in stderr.lower():
                    logger.warning(f"Конфликт слияния: {stderr}")
                    return False, f"Конфликт при объединении: {stderr}"
                
                logger.error(f"Error git merge: {stderr}")
                return False, f"Error объединения: {stderr}"
            
            logger.success("Обновления объединены successfully")
            return True, stdout
        except Exception as ex:
            logger.error(f"Error объединения обновлений: {ex}")
            return False, str(ex)
    
    async def update_application(self, branch: str = "main", auto_backup: bool = True) -> Dict:
        """
        Performs полное update приложения.
        
        Процесс:
        1. Checks наличие обновлений
        2. Creates резервную копию (если auto_backup=True)
        3. Downloads обновления
        4. Объединяет обновления
        5. Обновляет зависимости (если requirements.txt изменился)
        
        Args:
            branch: Ветка для обновления
            auto_backup: Создавать ли резервную копию перед обновлением
            
        Returns:
            Dictionary с результатом обновления
        """
        try:
            logger.info("Запуск процесса обновления приложения...")
            
            # Проверяем обновления
            check_result = self.check_updates()
            if check_result["status"] == UpdateStatus.ERROR.value:
                return {
                    "success": False,
                    "status": UpdateStatus.ERROR.value,
                    "message": "Не удалось проверить обновления"
                }
            
            if not check_result.get("is_update_available"):
                logger.info("Приложение уже на последней версии")
                return {
                    "success": False,
                    "status": UpdateStatus.CURRENT.value,
                    "message": "Обновления не доступны"
                }
            
            # Создаём резервную копию
            backup_path = None
            if auto_backup:
                backup_path = self.backup_files()
                if not backup_path:
                    return {
                        "success": False,
                        "status": UpdateStatus.ERROR.value,
                        "message": "Не удалось создать резервную копию"
                    }
            
            # Скачиваем обновления
            if not self.fetch_updates():
                if backup_path:
                    self.restore_from_backup(backup_path)
                return {
                    "success": False,
                    "status": UpdateStatus.ERROR.value,
                    "message": "Error при скачивании обновлений"
                }
            
            # Объединяем обновления
            merge_ok, merge_msg = self.merge_updates(branch)
            if not merge_ok:
                if backup_path:
                    self.restore_from_backup(backup_path)
                return {
                    "success": False,
                    "status": UpdateStatus.ERROR.value,
                    "message": f"Error объединения: {merge_msg}"
                }
            
            # Сохраняем информацию об обновлении
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
            
            logger.success(
                f"Приложение обновлено: {check_result.get('current_version')} → "
                f"{check_result.get('remote_version')}"
            )
            
            return {
                "success": True,
                "status": UpdateStatus.CURRENT.value,
                "message": "Update выполнено successfully",
                "version": check_result.get("remote_version"),
                "backup_path": str(backup_path) if backup_path else None
            }
        except Exception as ex:
            logger.error(f"Error обновления приложения: {ex}")
            return {
                "success": False,
                "status": UpdateStatus.ERROR.value,
                "message": str(ex)
            }
    
    def cleanup_old_backups(self, keep_count: int = 5) -> int:
        """
        Deletes старые резервные копии, сохраняя последние N.
        
        Args:
            keep_count: Количество последних резервных копий для сохранения
            
        Returns:
            Количество удалённых резервных копий
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
                    logger.debug(f"Удалена старая резервная копия: {backup.name}")
                except Exception as ex:
                    logger.warning(f"Error удаления резервной копии: {ex}")
            
            if deleted_count > 0:
                logger.info(f"Удалено старых резервных копий: {deleted_count}")
            
            return deleted_count
        except Exception as ex:
            logger.error(f"Error очистки резервных копий: {ex}")
            return 0

# Глобальный экземпляр менеджера версий
version_manager: Optional[VersionManager] = None

def get_version_manager(repo_path: Optional[Path] = None) -> VersionManager:
    """
    Receives глобальный экземпляр менеджера версий (Singleton).
    
    Args:
        repo_path: Путь к репозиторию
        
    Returns:
        Экземпляр VersionManager
    """
    global version_manager
    if version_manager is None:
        version_manager = VersionManager(repo_path)
    return version_manager
