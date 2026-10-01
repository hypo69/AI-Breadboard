# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Wikillm - Extractor
# =============================================================================
# Description:
#   Извлечение типизированных артефактов (ArtifactInput) из телеметрии, инцидентов,
#
# Usage Examples:
#   Python API:
#     from apps.windows.wikillm.extractor import ArtifactExtractor
#
#     service = ArtifactExtractor()
#
# File: extractor.py
# Project: ai-breadboard
# Package: apps.windows.wikillm
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Извлечение типизированных артефактов (ArtifactInput) из телеметрии, инцидентов,"""

import re
from typing import Any, Dict, List, Optional
from .models import ArtifactInput, ArtifactType
from .normalizer import CanonicalKeyNormalizer


class ArtifactExtractor:
    """Извлекает нормализованные входные артефакты из сырых данных и логов."""

    _ERROR_CODE_REGEX = re.compile(r"\b(0x[0-9a-fA-F]{8}|0x[0-9a-fA-F]{4})\b")
    _EVENT_ID_REGEX = re.compile(r"\b(?:EventID|Event ID|Event|ID)[:\s]+(\d{1,6})\b", re.IGNORECASE)
    _REGISTRY_REGEX = re.compile(r"\b(HKLM\\[a-zA-Z0-9_\\\-]+|HKCU\\[a-zA-Z0-9_\\\-]+|HKEY_[A-Z_]+\\[a-zA-Z0-9_\\\-]+)\b")
    _PROCESS_REGEX = re.compile(r"\b([a-zA-Z0-9_\-\.]+\.(?:exe|dll|sys))\b", re.IGNORECASE)

    @classmethod
    def from_event_dict(cls, event: Dict[str, Any]) -> ArtifactInput:
        """Извлекает артефакт из словаря события Windows Event Log.

        Args:
            event: Словарь с полями события (Provider, EventID, Message, etc.).

        Returns:
            Экземпляр ArtifactInput.
        """
        provider = str(event.get("Provider") or event.get("provider") or event.get("source") or "Generic")
        raw_id = event.get("EventID") or event.get("event_id") or event.get("id")
        event_id: Optional[int] = None
        if raw_id is not None:
            try:
                event_id = int(raw_id)
            except (ValueError, TypeError):
                event_id = None

        message = str(event.get("Message") or event.get("message") or event.get("description") or "")
        process_name = str(event.get("ProcessName") or event.get("process") or "") or None

        return ArtifactInput(
            type=ArtifactType.WINDOWS_EVENT,
            provider=provider,
            event_id=event_id,
            process_name=process_name,
            message=message,
            metadata=event,
        )

    @classmethod
    def from_incident(cls, incident_data: Dict[str, Any]) -> List[ArtifactInput]:
        """Извлекает артефакты из объекта или словаря инцидента Telemetry Engine.

        Args:
            incident_data: Словарь инцидента (category, trigger_type, suspects, error_code).

        Returns:
            Список извлеченных артефактов ArtifactInput.
        """
        artifacts: List[ArtifactInput] = []

        # Базовый артефакт инцидента
        cat = incident_data.get("category", "system")
        trigger = incident_data.get("trigger_type", "anomaly")
        artifacts.append(
            ArtifactInput(
                type=ArtifactType.INCIDENT,
                raw_query=f"{cat}_{trigger}",
                message=incident_data.get("description", ""),
                metadata=incident_data,
            )
        )

        # Извлечение подозреваемых процессов
        suspects = incident_data.get("suspects") or incident_data.get("suspect_processes") or []
        for s in suspects:
            p_name = s.get("name") or s.get("process_name") if isinstance(s, dict) else str(s)
            if p_name:
                artifacts.append(
                    ArtifactInput(
                        type=ArtifactType.PROCESS,
                        process_name=p_name,
                        metadata={"suspect_info": s},
                    )
                )

        # Извлечение кода ошибки при наличии
        err = incident_data.get("error_code") or incident_data.get("hresult")
        if err:
            artifacts.append(
                ArtifactInput(
                    type=ArtifactType.WINDOWS_ERROR,
                    error_code=str(err),
                    message=incident_data.get("title", ""),
                )
            )

        return artifacts

    @classmethod
    def from_raw_text(cls, text: str) -> List[ArtifactInput]:
        """Извлекает распознанные артефакты (ошибки, события, процессы, реестр) из свободного текста.

        Args:
            text: Произвольный текст лога, сообщения об ошибке или диагностического отчета.

        Returns:
            Список обнаруженных артефактов ArtifactInput.
        """
        if not text:
            return []

        results: List[ArtifactInput] = []
        seen_keys = set()

        # 1. Поиск кодов ошибок (0x80070490, 0xc0000005)
        for match in cls._ERROR_CODE_REGEX.finditer(text):
            code = match.group(1)
            art = ArtifactInput(
                type=ArtifactType.WINDOWS_ERROR,
                error_code=code,
                message=text[:200],
            )
            key = CanonicalKeyNormalizer.compute_canonical_key(art)
            if key not in seen_keys:
                seen_keys.add(key)
                results.append(art)

        # 2. Поиск Event ID
        for match in cls._EVENT_ID_REGEX.finditer(text):
            eid_str = match.group(1)
            try:
                eid = int(eid_str)
                art = ArtifactInput(
                    type=ArtifactType.WINDOWS_EVENT,
                    event_id=eid,
                    message=text[:200],
                )
                key = CanonicalKeyNormalizer.compute_canonical_key(art)
                if key not in seen_keys:
                    seen_keys.add(key)
                    results.append(art)
            except ValueError:
                pass

        # 3. Поиск путей реестра
        for match in cls._REGISTRY_REGEX.finditer(text):
            reg = match.group(1)
            art = ArtifactInput(
                type=ArtifactType.REGISTRY_KEY,
                registry_path=reg,
            )
            key = CanonicalKeyNormalizer.compute_canonical_key(art)
            if key not in seen_keys:
                seen_keys.add(key)
                results.append(art)

        # 4. Если ничего специфичного не найдено, упаковываем как симптом
        if not results:
            results.append(
                ArtifactInput(
                    type=ArtifactType.SYMPTOM,
                    raw_query=text.strip()[:120],
                    message=text,
                )
            )

        return results
