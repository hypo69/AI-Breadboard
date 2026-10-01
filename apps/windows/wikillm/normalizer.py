# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm - Normalizer
# =============================================================================
# Description:
#   Нормализация входных артефактов Windows и кода в стабильные канонические ключи
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.normalizer import CanonicalKeyNormalizer
#
#     service = CanonicalKeyNormalizer()
#
# File: normalizer.py
# Project: ai-breadboard
# Package: apps.windows.wikillm
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Нормализация входных артефактов Windows и кода в стабильные канонические ключи"""

import hashlib
import re
from typing import Optional, Tuple
from .models import ArtifactInput, ArtifactType


class CanonicalKeyNormalizer:
    """Генератор детерминированных канонических ключей и шаблонов отпечатков."""

    _HEX_ERROR_RE = re.compile(r"^(0x[0-9a-fA-F]{4,8}|-[0-9]{5,10})$")
    _GUID_RE = re.compile(r"\{?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\}?")
    _HEX_ADDR_RE = re.compile(r"0x[0-9a-fA-F]{6,16}")
    _TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?")
    _PATH_RE = re.compile(r"[a-zA-Z]:\\(?:[^\\/:*?\"<>|\r\n]+\\)*[^\\/:*?\"<>|\r\n]*")

    @classmethod
    def normalize_hex_code(cls, code: str) -> str:
        """Нормализует шестнадцатеричный код ошибки к нижнему регистру формата 0x...

        Args:
            code: Исходная строка кода ошибки (например, 0x80070490, 80070490, -2147023728).

        Returns:
            Нормализованная строка шестнадцатеричного формата (0x80070490).
        """
        raw = code.strip()
        if raw.startswith("-"):
            try:
                val = int(raw) & 0xFFFFFFFF
                return f"0x{val:08x}"
            except ValueError:
                return raw.lower()

        if raw.lower().startswith("0x"):
            return raw.lower()

        if len(raw) in (4, 8) and all(c in "0123456789abcdefABCDEF" for c in raw):
            return f"0x{raw.lower()}"

        return raw.lower()

    @classmethod
    def normalize_registry_path(cls, path: str) -> str:
        """Нормализует путь реестра к стандартным префиксам (HKLM, HKCU, HKCR).

        Args:
            path: Исходный путь реестра.

        Returns:
            Нормализованный путь реестра.
        """
        p = path.strip().replace("/", "\\")
        replacements = [
            ("HKEY_LOCAL_MACHINE\\", "HKLM\\"),
            ("HKEY_CURRENT_USER\\", "HKCU\\"),
            ("HKEY_CLASSES_ROOT\\", "HKCR\\"),
            ("HKEY_USERS\\", "HKU\\"),
            ("HKEY_CURRENT_CONFIG\\", "HKCC\\"),
        ]
        for src, dst in replacements:
            if p.upper().startswith(src):
                p = dst + p[len(src):]
                break
        return p

    @classmethod
    def compute_canonical_key(cls, artifact: ArtifactInput) -> str:
        """Вычисляет стабильный канонический ключ для входного артефакта.

        Args:
            artifact: Входной объект артефакта.

        Returns:
            Строка канонического ключа (например win32:0x80070490, windows_event:DistributedCOM:10016).
        """
        # 1. Если явно задан Event ID и Provider
        if artifact.event_id is not None or (artifact.type == ArtifactType.WINDOWS_EVENT and artifact.provider):
            prov = (artifact.provider or "Generic").strip()
            eid = artifact.event_id if artifact.event_id is not None else 0
            return f"windows_event:{prov}:{eid}"

        # 2. Если задан код ошибки
        if artifact.error_code:
            norm_code = cls.normalize_hex_code(artifact.error_code)
            prefix = "ntstatus" if norm_code.startswith("0xc") else "win32"
            return f"{prefix}:{norm_code}"

        # 3. Если задан путь реестра
        if artifact.registry_path:
            norm_reg = cls.normalize_registry_path(artifact.registry_path)
            return f"registry:{norm_reg}"

        # 4. Если задан процесс
        if artifact.process_name:
            proc = artifact.process_name.strip().lower()
            return f"process:{proc}"

        # 5. Если задана служба
        if artifact.service_name:
            srv = artifact.service_name.strip().lower()
            return f"service:{srv}"

        # 6. Если задан драйвер
        if artifact.driver_name:
            drv = artifact.driver_name.strip().lower()
            return f"driver:{drv}"

        # 7. Если задан символ кода
        if artifact.code_symbol:
            sym = artifact.code_symbol.strip()
            return f"code:{sym}"

        # 8. Анализ сырой строки запроса raw_query
        if artifact.raw_query:
            query = artifact.raw_query.strip()
            # Проверка на код ошибки (0x8007..., 0xc000...)
            if cls._HEX_ERROR_RE.match(query) or query.lower().startswith("0x"):
                norm = cls.normalize_hex_code(query)
                prefix = "ntstatus" if norm.startswith("0xc") else "win32"
                return f"{prefix}:{norm}"

            # Проверка на шаблон "Event ID 10016" или "DistributedCOM 10016"
            ev_match = re.search(r"(?:event\s*id|eventid|event)?\s*[:\s]?\s*([a-zA-Z0-9_\-]+)?\s*[:\s]?\s*(\d{1,6})", query, re.IGNORECASE)
            if ev_match and ev_match.group(2):
                prov = ev_match.group(1) or "Generic"
                return f"windows_event:{prov}:{ev_match.group(2)}"

            # Проверка на реестр
            if any(query.upper().startswith(p) for p in ("HKLM\\", "HKCU\\", "HKEY_")):
                return f"registry:{cls.normalize_registry_path(query)}"

            # Проверка на процесс (*.exe)
            if query.lower().endswith(".exe"):
                return f"process:{query.lower()}"

            # Проверка на драйвер (*.sys)
            if query.lower().endswith(".sys"):
                return f"driver:{query.lower()}"

            # Общий симптом
            slug = re.sub(r"[^a-zA-Z0-9_\-]+", "_", query.lower()).strip("_")
            return f"symptom:{slug[:64]}"

        # Резервный slug по сообщению
        if artifact.message:
            msg_snippet = re.sub(r"[^a-zA-Z0-9_\-]+", "_", artifact.message.lower()[:40]).strip("_")
            return f"generic:{msg_snippet or 'unknown'}"

        return "unknown:unspecified"

    @classmethod
    def sanitize_message_template(cls, message: str) -> str:
        """Очищает текст сообщения от динамических данных (GUID, адреса, даты) для шаблонизации.

        Args:
            message: Исходное сырое сообщение из журнала или лога.

        Returns:
            Очищенный шаблон сообщения.
        """
        if not message:
            return ""
        s = cls._GUID_RE.sub("<GUID>", message)
        s = cls._HEX_ADDR_RE.sub("<ADDR>", s)
        s = cls._TIMESTAMP_RE.sub("<TIMESTAMP>", s)
        s = cls._PATH_RE.sub("<PATH>", s)
        s = re.sub(r"\b\d{4,}\b", "<NUM>", s)
        return re.sub(r"\s+", " ", s).strip()

    @classmethod
    def compute_fingerprint(cls, artifact: ArtifactInput) -> str:
        """Создает хеш-отпечаток (fingerprint) артефакта на основе структурных признаков.

        Args:
            artifact: Входной артефакт.

        Returns:
            Строка отпечатка или sha256-хеш структурного шаблона.
        """
        canonical_key = cls.compute_canonical_key(artifact)
        msg_template = cls.sanitize_message_template(artifact.message or "")
        prov = artifact.provider or ""
        eid = str(artifact.event_id or "")

        combined = f"{canonical_key}|{prov}|{eid}|{msg_template}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:24]
