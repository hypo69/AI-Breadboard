# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Modules Hardware - Registry
# =============================================================================
# Description:
#   Центральный реестр аппаратных провайдеров Windows Diagnostic Engine.
#
# Usage Examples:
#   Python API:
#     from apps.windows.modules.hardware.registry import HardwareProviderRegistry
#
#     service = HardwareProviderRegistry()
#
# File: registry.py
# Project: ai-breadboard
# Package: apps.windows.modules.hardware
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Центральный реестр аппаратных провайдеров Windows Diagnostic Engine."""

from typing import Dict, List, Optional
from logger import logger
from apps.windows.hardware.base import BaseHardwareProvider, ProviderTier
from apps.windows.hardware.discovery import UtilityDiscovery
from apps.windows.hardware.providers.aida64_provider import Aida64Provider
from apps.windows.hardware.providers.cpuz_provider import CpuzProvider
from apps.windows.hardware.providers.gpuz_provider import GpuzProvider
from apps.windows.hardware.providers.hwinfo_provider import HwinfoProvider
from apps.windows.hardware.providers.native_win_provider import NativeWinProvider

class HardwareProviderRegistry:
    """Реестр аппаратных провайдеров с авто-обнаружением внешних утилит."""

    def __init__(self, discovery: Optional[UtilityDiscovery]=None) -> None:
        """Инициализация реестра провайдеров."""
        self.discovery = discovery or UtilityDiscovery()
        self._providers: Dict[str, BaseHardwareProvider] = {}
        self._init_providers()

    def _init_providers(self) -> None:
        """Зарегистрировать все доступные аппаратные провайдеры."""
        native = NativeWinProvider()
        self._providers['native'] = native
        aida_path = self.discovery.find_utility('aida64')
        self._providers['aida64'] = Aida64Provider(binary_path=aida_path)
        hwinfo_path = self.discovery.find_utility('hwinfo')
        self._providers['hwinfo'] = HwinfoProvider(binary_path=hwinfo_path)
        cpuz_path = self.discovery.find_utility('cpuz')
        self._providers['cpuz'] = CpuzProvider(binary_path=cpuz_path)
        gpuz_path = self.discovery.find_utility('gpuz')
        self._providers['gpuz'] = GpuzProvider(binary_path=gpuz_path)
        logger.debug(f'Зарегистрировано {len(self._providers)} аппаратных провайдеров')

    def get_provider(self, key: str) -> Optional[BaseHardwareProvider]:
        """Получить конкретный провайдер по ключу."""
        return self._providers.get(key.lower())

    def get_all_providers(self) -> List[BaseHardwareProvider]:
        """Получить список всех зарегистрированных провайдеров."""
        return list(self._providers.values())

    def get_available_providers(self) -> List[BaseHardwareProvider]:
        """Получить список только доступных (активных) провайдеров."""
        return [p for p in self._providers.values() if p.is_available()]

    def get_providers_by_tier(self, tier: ProviderTier) -> List[BaseHardwareProvider]:
        """Фильтрация провайдеров по уровню иерархии."""
        return [p for p in self._providers.values() if p.tier == tier]