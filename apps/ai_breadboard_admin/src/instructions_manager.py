# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Admin Instructions Manager Module
# =============================================================================
# Description:
#   Управление системными инструкциями и стилями промптов, версионирование
#   файлов в prompts/chat и prompts/narrator, активация и тестирование промптов.
#
# Examples:
#   >>> from apps.ai_breadboard_admin.src.instructions_manager import InstructionsManager
#   >>> manager = InstructionsManager()
#   >>> content = manager.get_instruction('chat')
#
# File: instructions_manager.py
# Project: AI-Breadboard
# Package: apps.ai_breadboard_admin.src
# Module: instructions_manager
# Class: InstructionsManager
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from header import __root__
from src.logger import logger


class InstructionsManager:
    """Менеджер управления системными инструкциями и их версиями.

    Обеспечивает загрузку, версионирование, сохранение и активацию
    файлов системных инструкций для чата и диктора.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        """Инициализация менеджера инструкций.

        Args:
            root_dir (Optional[Path]): Корневой каталог проекта. Если не передан,
                используется системный `__root__`.
        """
        self.root_dir: Path = root_dir or __root__
        self.instruction_files: Dict[str, Path] = {
            "chat": self.root_dir / "prompts" / "chat" / "system_instruction.md",
            "narrator": self.root_dir / "prompts" / "narrator" / "narrator_style.md",
        }
        self.versions_dirs: Dict[str, Path] = {
            "chat": self.root_dir / "prompts" / "chat" / "versions",
            "narrator": self.root_dir / "prompts" / "narrator" / "versions",
        }

    def get_active_file(self, mode: str) -> Path:
        """Получение пути к активному файлу инструкции по режиму.

        Args:
            mode (str): Режим ('chat' или 'narrator').

        Returns:
            Path: Путь к активному файлу.

        Exceptions:
            ValueError: Если указан неизвестный режим.
        """
        path = self.instruction_files.get(mode)
        if not path:
            raise ValueError(f"Неизвестный режим: {mode}. Допустимые: chat, narrator")
        return path

    def get_versions_dir(self, mode: str) -> Path:
        """Получение пути к каталогу версий инструкций.

        Args:
            mode (str): Режим ('chat' или 'narrator').

        Returns:
            Path: Путь к каталогу версий.

        Exceptions:
            ValueError: Если указан неизвестный режим.
        """
        path = self.versions_dirs.get(mode)
        if not path:
            raise ValueError(f"Неизвестный режим: {mode}. Допустимые: chat, narrator")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_instruction(self, mode: str = "chat") -> Dict[str, str]:
        """Получение содержимого активной инструкции.

        Args:
            mode (str): Режим инструкции ('chat' или 'narrator').

        Returns:
            Dict[str, str]: Словарь с полями 'content', 'mode', 'file'.
        """
        active_file = self.get_active_file(mode)
        content = ""
        if active_file.exists():
            try:
                content = active_file.read_text(encoding="utf-8")
            except Exception as ex:
                logger.error(f"Ошибка чтения файла инструкции {active_file}", ex)
        return {
            "content": content,
            "mode": mode,
            "file": active_file.name,
        }

    def next_version_number(self, versions_dir: Path) -> int:
        """Вычисление следующего порядкового номера версии.

        Args:
            versions_dir (Path): Каталог с файлами версий.

        Returns:
            int: Следующий номер версии.
        """
        existing = list(versions_dir.glob("v*.md"))
        numbers = []
        for f in existing:
            m = re.match(r"^v(\d+)_", f.name)
            if m:
                numbers.append(int(m.group(1)))
        return max(numbers, default=0) + 1

    def save_instruction(self, mode: str, content: str) -> Dict[str, Any]:
        """Сохранение новой версии инструкции и обновление активного файла.

        Args:
            mode (str): Режим инструкции ('chat' или 'narrator').
            content (str): Новый текст инструкции.

        Returns:
            Dict[str, Any]: Словарь со статусом и именем сохраненной версии.
        """
        active_file = self.get_active_file(mode)
        versions_dir = self.get_versions_dir(mode)

        version_num = self.next_version_number(versions_dir)
        date_str = datetime.now().strftime("%Y-%m-%d")
        version_filename = f"v{version_num}_{date_str}.md"
        version_path = versions_dir / version_filename

        # Сохранение файла версии
        version_path.write_text(content, encoding="utf-8")
        logger.info(f"Сохранена версия инструкции: {version_path}")

        # Перезапись активного файла
        active_file.parent.mkdir(parents=True, exist_ok=True)
        active_file.write_text(content, encoding="utf-8")
        logger.info(f"Обновлен активный файл инструкции: {active_file} (mode={mode})")

        return {
            "status": "ok",
            "message": f"Инструкция сохранена как версия {version_filename}",
            "version": version_filename,
        }

    def list_versions(self, mode: str = "chat") -> Dict[str, Any]:
        """Получение списка всех сохраненных версий инструкций.

        Args:
            mode (str): Режим инструкции ('chat' или 'narrator').

        Returns:
            Dict[str, Any]: Список версий с метаданными и признаком активности.
        """
        versions_dir = self.get_versions_dir(mode)
        active_file = self.get_active_file(mode)

        active_content = ""
        if active_file.exists():
            try:
                active_content = active_file.read_text(encoding="utf-8")
            except Exception as ex:
                logger.warning(f"Ошибка чтения активного файла: {ex}")

        version_files = sorted(
            versions_dir.glob("v*.md"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )

        versions: List[Dict[str, Any]] = []
        for vf in version_files:
            try:
                file_content = vf.read_text(encoding="utf-8")
                stat = vf.stat()
                created_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
                is_active = (file_content.strip() == active_content.strip())
                versions.append({
                    "filename": vf.name,
                    "mode": mode,
                    "is_active": is_active,
                    "created_at": created_at,
                    "size": stat.st_size,
                    "preview": file_content[:120] + "..." if len(file_content) > 120 else file_content,
                })
            except Exception as read_ex:
                logger.warning(f"Не удалось прочитать файл версии {vf}: {read_ex}")

        return {"versions": versions, "mode": mode}

    def activate_version(self, mode: str, filename: str) -> Dict[str, Any]:
        """Активация выбранной версии инструкции.

        Args:
            mode (str): Режим инструкции ('chat' или 'narrator').
            filename (str): Имя файла версии.

        Returns:
            Dict[str, Any]: Результат активации.

        Exceptions:
            FileNotFoundError: Если файл версии не существует.
        """
        versions_dir = self.get_versions_dir(mode)
        active_file = self.get_active_file(mode)

        safe_filename = Path(filename).name
        version_path = versions_dir / safe_filename

        if not version_path.exists():
            raise FileNotFoundError(f"Версия {safe_filename} не найдена")

        content = version_path.read_text(encoding="utf-8")
        active_file.parent.mkdir(parents=True, exist_ok=True)
        active_file.write_text(content, encoding="utf-8")
        logger.info(f"Активирована версия инструкции {safe_filename} (mode={mode})")

        return {
            "status": "ok",
            "message": f"Версия {safe_filename} успешно активирована",
            "version": safe_filename,
            "content": content,
        }


__all__ = ["InstructionsManager"]
