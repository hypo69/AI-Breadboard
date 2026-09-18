# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Application Config Inspector & Secret Sanitizer
# =============================================================================
# Description:
#   Поиск конфигурационных файлов (.json, .ini, .yaml, .xml, .cfg, .toml, .conf),
#   их анализ, определение формата и безопасная санитизация (удаление секретов,
#   токенов, паролей) перед отображением и отправкой в Gemini.
#
# File: config_inspector.py
# Project: ai-breadboard
# Package: apps.software_transparency_scanner.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Инспектор конфигурационных файлов с защитой конфиденциальных данных."""

from __future__ import annotations

import datetime
import json
import os
import re
from pathlib import Path
from typing import List, Optional

from apps.software_transparency_scanner.core.models import (
    ConfigFile,
    EvidenceStatus,
    StorageDirectory,
)


class ConfigInspector:
    """Поиск и санитизация конфигурационных файлов приложений."""

    CONFIG_EXTENSIONS = {".json", ".ini", ".yaml", ".yml", ".xml", ".cfg", ".conf", ".toml", ".config"}
    
    SECRET_REGEX = re.compile(
        r"""(?i)(password|passwd|secret|token|api[_-]?key|bearer|auth|credential|private[_-]?key)\s*[:=]\s*['"]?([^\s'"]+)['"]?"""
    )
    
    BEARER_JWT_REGEX = re.compile(r"(Bearer\s+)[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_.+/=]*")
    GENERIC_KEY_REGEX = re.compile(r"(AIzaSy[A-Za-z0-9_-]{33}|sk-[A-Za-z0-9]{32,})")

    def __init__(self, max_file_size_kb: int = 256):
        self.max_file_size_bytes = max_file_size_kb * 1024

    def inspect_directories_for_configs(self, directories: List[StorageDirectory]) -> List[ConfigFile]:
        """Сканирует указанные каталоги и извлекает конфигурационные файлы."""
        found_configs: List[ConfigFile] = []

        for d in directories:
            if not os.path.exists(d.path) or not os.path.isdir(d.path):
                continue

            try:
                for root, _, files in os.walk(d.path):
                    # Ограничение глубины
                    depth = len(Path(root).relative_to(Path(d.path)).parts)
                    if depth > 3:
                        continue

                    for file in files:
                        ext = Path(file).suffix.lower()
                        if ext in self.CONFIG_EXTENSIONS:
                            full_path = os.path.join(root, file)
                            cfg_item = self._process_config_file(full_path)
                            if cfg_item:
                                found_configs.append(cfg_item)
                                if len(found_configs) >= 20:
                                    return found_configs
            except (OSError, PermissionError):
                continue

        return found_configs

    def _process_config_file(self, full_path: str) -> Optional[ConfigFile]:
        """Читает, санитизирует и формирует объект ConfigFile."""
        try:
            st = os.stat(full_path)
            size = st.st_size
            if size > self.max_file_size_bytes:
                sample = "[Файл превышает лимит размера 256 KB для предпросмотра]"
            else:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    raw_content = f.read(4096)  # Первые 4KB
                sample = self.sanitize_secrets(raw_content)

            mod_time = datetime.datetime.fromtimestamp(st.st_mtime).isoformat()
            ext = Path(full_path).suffix.lower().lstrip(".")
            display_path = self._to_display_path(full_path)

            return ConfigFile(
                path=full_path,
                display_path=display_path,
                filename=Path(full_path).name,
                format=ext or "text",
                size_bytes=size,
                last_modified=mod_time,
                purpose=self._guess_config_purpose(Path(full_path).name),
                is_sanitized=True,
                sample_content=sample,
                status=EvidenceStatus.LOCAL_OBSERVED,
            )
        except (OSError, PermissionError):
            return None

    def sanitize_secrets(self, content: str) -> str:
        """Заменяет пароли, токены и приватные ключи на [REDACTED_SECRET]."""
        if not content:
            return ""

        # 1. Замена Bearer токенов
        sanitized = self.BEARER_JWT_REGEX.sub(r"Bearer [REDACTED_JWT_TOKEN]", content)
        # 2. Замена явных API-ключей Google / OpenAI
        sanitized = self.GENERIC_KEY_REGEX.sub(r"[REDACTED_API_KEY]", sanitized)
        # 3. Замена пар ключ-значение (password: "secret", api_key="secret", etc.)
        secret_kv_pattern = re.compile(
            r"""(?i)(['"]?(?:password|passwd|secret|token|api[_-]?key|auth|credential|private[_-]?key)['"]?\s*[:=]\s*['"])([^'"\r\n]+)(['"])"""
        )
        sanitized = secret_kv_pattern.sub(r"\g<1>[REDACTED_SECRET]\g<3>", sanitized)

        return sanitized

    def _guess_config_purpose(self, filename: str) -> str:
        """Определяет назначение файла по его имени."""
        fn = filename.lower()
        if "settings" in fn or "preferences" in fn or "config" in fn:
            return "Пользовательские настройки и предпочтения"
        if "state" in fn or "session" in fn:
            return "Состояние текущей или последней сессии"
        if "update" in fn:
            return "Параметры и серверы автообновления"
        if "network" in fn or "proxy" in fn:
            return "Сетевая конфигурация и прокси"
        return "Конфигурационные параметры работы программы"

    def _to_display_path(self, full_path: str) -> str:
        """Заменяет абсолютный префикс на макрос окружения."""
        p = full_path
        for env_var in ("APPDATA", "LOCALAPPDATA", "PROGRAMDATA", "USERPROFILE"):
            val = os.getenv(env_var)
            if val and p.lower().startswith(val.lower()):
                return f"%{env_var}%{p[len(val):]}"
        return p
