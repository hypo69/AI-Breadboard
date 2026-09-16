# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Admin Configuration Manager Module
# =============================================================================
# Description:
#   Управление системными конфигурациями, параметрами RAG, настройками веб-поиска,
#   провайдерами моделей и конфигурационными файлами микроприложений платформы.
#
# Examples:
#   >>> from apps.ai_breadboard_admin.src.config_manager import AdminConfigManager
#   >>> manager = AdminConfigManager()
#   >>> rag_cfg = manager.get_rag_config()
#
# File: config_manager.py
# Project: AI-Breadboard
# Package: apps.ai_breadboard_admin.src
# Module: config_manager
# Class: AdminConfigManager
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from header import __root__
from src.logger import logger


class AdminConfigManager:
    """Менеджер управления конфигурационными параметрами системы.

    Предоставляет методы для чтения и модификации системных параметров:
    режимов RAG, настроек веб-поиска, статуса и конфигураций приложений `/apps`.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        """Инициализация менеджера конфигурации.

        Args:
            root_dir (Optional[Path]): Корневой каталог проекта. Если не передан,
                используется системный `__root__`.
        """
        self.root_dir: Path = root_dir or __root__
        self.config_path: Path = self._resolve_active_config_path()

    def _resolve_active_config_path(self) -> Path:
        """Определение пути к активному файлу конфигурации системы.

        Returns:
            Path: Путь к файлу конфигурации (config.json или config_tc.json).
        """
        cfg_env = os.getenv("AIBREADBOARD_CONFIG") or os.getenv("CONFIG_FILE")
        if cfg_env:
            p = Path(cfg_env)
            return p if p.is_absolute() else (self.root_dir / cfg_env)

        tc_cfg = self.root_dir / "config_tc.json"
        main_cfg = self.root_dir / "config.json"

        if tc_cfg.exists() and not main_cfg.exists():
            return tc_cfg
        return main_cfg

    def get_system_config(self) -> Dict[str, Any]:
        """Чтение полной системной конфигурации.

        Returns:
            Dict[str, Any]: Словарь с конфигурационными параметрами системы.
        """
        if not self.config_path.exists():
            return {}

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as ex:
            logger.error(f"Ошибка чтения конфигурации из {self.config_path}", ex)
            return {}

    def save_system_config(self, config_data: Dict[str, Any]) -> bool:
        """Сохранение системной конфигурации.

        Args:
            config_data (Dict[str, Any]): Словарь с обновленной конфигурацией.

        Returns:
            bool: Результат операции сохранения.
        """
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Системная конфигурация успешно сохранена в {self.config_path}")
            return True
        except Exception as ex:
            logger.error(f"Ошибка сохранения конфигурации в {self.config_path}", ex)
            return False

    def get_rag_config(self) -> Dict[str, str]:
        """Получение текущего режима работы подсистемы RAG.

        Returns:
            Dict[str, str]: Словарь с ключом 'mode' (rag+model, rag, model).
        """
        cfg = self.get_system_config()
        mode = cfg.get("rag", {}).get("mode", "rag+model")
        return {"mode": mode}

    def set_rag_config(self, mode: str) -> bool:
        """Установка режима работы подсистемы RAG.

        Args:
            mode (str): Режим работы RAG ('rag+model', 'rag', 'model').

        Returns:
            bool: True в случае успешного сохранения, иначе False.
        """
        cfg = self.get_system_config()
        if "rag" not in cfg:
            cfg["rag"] = {}
        cfg["rag"]["mode"] = mode
        return self.save_system_config(cfg)

    def get_web_search_config(self) -> Dict[str, str]:
        """Получение параметров конфигурации подсистемы веб-поиска.

        Returns:
            Dict[str, str]: Словарь с настройками поискового движка и моделей.
        """
        cfg = self.get_system_config()
        ws = cfg.get("web_search", {})
        return {
            "engine": ws.get("engine", "playwright"),
            "gemini_model": ws.get("gemini_model", "gemini-2.5-flash"),
            "gemini_cli_model": ws.get("gemini_cli_model", "gemini-3.1-flash-lite"),
            "agy_model": ws.get("agy_model", "agy-flash"),
        }

    def set_web_search_config(
        self,
        engine: str,
        gemini_model: str = "gemini-2.5-flash",
        gemini_cli_model: str = "gemini-3.1-flash-lite",
        agy_model: str = "agy-flash",
    ) -> bool:
        """Сохранение параметров подсистемы веб-поиска.

        Args:
            engine (str): Выбранный движок поиска (playwright, langchain, etc.).
            gemini_model (str): Название модели Gemini для синтеза результатов.
            gemini_cli_model (str): Название модели Gemini CLI.
            agy_model (str): Название модели Antigravity.

        Returns:
            bool: True в случае успешного сохранения, иначе False.
        """
        cfg = self.get_system_config()
        if "web_search" not in cfg:
            cfg["web_search"] = {}
        cfg["web_search"]["engine"] = engine
        cfg["web_search"]["gemini_model"] = gemini_model
        cfg["web_search"]["gemini_cli_model"] = gemini_cli_model
        cfg["web_search"]["agy_model"] = agy_model
        return self.save_system_config(cfg)

    def get_app_config(self, app_name: str) -> Optional[Dict[str, Any]]:
        """Чтение локального конфигурационного файла приложения.

        Args:
            app_name (str): Имя директории приложения в `apps/` или `src/apps/`.

        Returns:
            Optional[Dict[str, Any]]: Данные конфигурации или None, если файл не найден.
        """
        safe_name = "".join(c for c in app_name if c.isalnum() or c in ("_", "-"))
        if not safe_name:
            return None

        candidates = [
            self.root_dir / "src" / "apps" / safe_name / "config.json",
            self.root_dir / "apps" / safe_name / "config.json",
        ]

        for path in candidates:
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception as ex:
                    logger.error(f"Ошибка чтения конфигурации приложения {path}", ex)
                    return None
        return None

    def set_app_config(self, app_name: str, config_data: Dict[str, Any]) -> bool:
        """Сохранение локальной конфигурации приложения.

        Args:
            app_name (str): Имя директории приложения в `apps/`.
            config_data (Dict[str, Any]): Словарь с новыми параметрами.

        Returns:
            bool: True в случае успешного сохранения, иначе False.
        """
        safe_name = "".join(c for c in app_name if c.isalnum() or c in ("_", "-"))
        if not safe_name:
            return False

        candidates = [
            self.root_dir / "src" / "apps" / safe_name / "config.json",
            self.root_dir / "apps" / safe_name / "config.json",
        ]

        target_paths = [p for p in candidates if p.exists()]
        if not target_paths:
            target_paths = [self.root_dir / "apps" / safe_name / "config.json"]

        saved = True
        for path in target_paths:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
            except Exception as ex:
                logger.error(f"Ошибка сохранения конфигурации приложения {path}", ex)
                saved = False

        return saved


__all__ = ["AdminConfigManager"]
