# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Sampling Controller
# =============================================================================
# Description:
#   Контроллер адаптивного изменения частоты сбора телеметрии (Sampling Controller).
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.sampling_controller import SamplingController
#
#     service = SamplingController()
#
# File: sampling_controller.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Контроллер адаптивного изменения частоты сбора телеметрии (Sampling Controller)."""

import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    import psutil
    BOOT_TIME = psutil.boot_time()
except Exception:
    BOOT_TIME = time.time()

try:
    from logger import logger
except ImportError:
    from logger import logger

from .models import SamplingMode


class SamplingController:
    """Контроллер режимов сбора телеметрии и адаптивного интервала."""

    def __init__(
        self,
        initial_mode: SamplingMode = SamplingMode.BOOT_AGGRESSIVE,
        boot_epoch: Optional[float] = None,
    ) -> None:
        """Инициализирует контроллер режимов сбора.

        Args:
            initial_mode: Начальный режим работы (по умолчанию BOOT_AGGRESSIVE).
            boot_epoch: Время старта ОС или сервиса в секундах Unix epoch.
        """
        self._mode = initial_mode
        self._boot_epoch = boot_epoch if boot_epoch is not None else BOOT_TIME
        self._start_epoch = time.time()
        self._incident_expiry_epoch: Optional[float] = None
        self._previous_mode: SamplingMode = SamplingMode.MONITORING

    @property
    def mode(self) -> SamplingMode:
        """Возвращает текущий режим сбора с учетом авто-истечения инцидентов."""
        self._check_incident_expiration()
        return self._mode

    def set_mode(self, mode: SamplingMode) -> None:
        """Принудительно устанавливает режим сбора телеметрии.

        Args:
            mode: Новый режим работы.
        """
        self._mode = mode
        if mode != SamplingMode.INCIDENT:
            self._incident_expiry_epoch = None
        logger.info(f"Режим сбора телеметрии переключен на: {self._mode.value}")

    def trigger_incident_mode(self, duration_seconds: float = 1200.0) -> None:
        """Переводит сборщик в режим INCIDENT (1-секундный захват) на заданную длительность.

        Args:
            duration_seconds: Длительность удержания режима инцидента (по умолчанию 20 минут = 1200 сек).
        """
        if self._mode != SamplingMode.INCIDENT:
            self._previous_mode = self._mode
        self._mode = SamplingMode.INCIDENT
        self._incident_expiry_epoch = time.time() + max(0.01, duration_seconds)
        logger.warning(f"Активирован режим INCIDENT на {duration_seconds} сек.")

    def get_current_interval(self) -> float:
        """Возвращает текущий рекомендуемый интервал опроса телеметрии в секундах.

        Returns:
            float: Интервал в секундах.
        """
        self._check_incident_expiration()

        if self._mode == SamplingMode.INCIDENT:
            return 1.0

        if self._mode == SamplingMode.FORENSIC:
            return 1.0

        if self._mode == SamplingMode.BOOT_AGGRESSIVE:
            # Адаптивная кривая после старта Windows / сервиса
            uptime = time.time() - self._boot_epoch
            if uptime < 0:
                uptime = time.time() - self._start_epoch

            if uptime <= 600.0:  # 0–10 минут: 1-секундные данные
                return 1.0
            elif uptime <= 3600.0:  # 10–60 минут: 5-секундные
                return 5.0
            elif uptime <= 86400.0:  # 1–24 часа: 30-секундные
                return 30.0
            else:
                # После 24 часов переходим в дежурный мониторинг
                return 60.0

        if self._mode == SamplingMode.MONITORING:
            return 30.0

        if self._mode == SamplingMode.NORMAL:
            return 60.0

        return 30.0

    def should_collect_per_process_details(self) -> bool:
        """Определяет, требуется ли собирать глубокий срез по всем процессам на текущем тике.

        В высокочастотных режимах (1s) подробный опрос всех процессов может отфильтровываться
        по топ-N / дельте, чтобы не нагружать процессор.
        """
        interval = self.get_current_interval()
        if interval <= 1.0:
            return True
        return True

    def _check_incident_expiration(self) -> None:
        """Проверяет истечение времени режима инцидента и возвращает предыдущий режим."""
        if self._mode == SamplingMode.INCIDENT and self._incident_expiry_epoch is not None:
            if time.time() >= self._incident_expiry_epoch:
                logger.info("Время фиксации инцидента истекло. Возврат в штатный режим.")
                self._mode = self._previous_mode
                self._incident_expiry_epoch = None

    def get_status(self) -> Dict[str, Any]:
        """Возвращает статус контроллера опроса.

        Returns:
            Dict[str, Any]: Словарь с текущим режимом, интервалом и временем старта.
        """
        return {
            "mode": self.mode.value,
            "current_interval_sec": self.get_current_interval(),
            "boot_epoch": self._boot_epoch,
            "incident_active": self._mode == SamplingMode.INCIDENT,
            "incident_remaining_sec": max(0.0, (self._incident_expiry_epoch - time.time())) if self._incident_expiry_epoch else 0.0,
        }
