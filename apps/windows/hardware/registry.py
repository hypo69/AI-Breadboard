# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Hardware Provider Registry
# =============================================================================
# Description:
#   Центральный реестр всех аппаратных провайдеров. Выполняет автоматическое
#   обнаружение утилит в /bin и регистрацию соответствующих провайдеров.
#
# File: registry.py
# Project: ai-breadboard
# Package: apps.windows.hardware
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Центральный реестр аппаратных провайдеров Windows Diagnostic Engine."""

from __future__ import annotations

from typing import Dict, List, Optional

from logger import logger
from apps.windows.hardware.base import BaseHardwareProvider, ProviderTier
from apps.windows.hardware.discovery import UtilityDiscovery
from apps.windows.hardware.providers.aida64_provider import Aida64Provider
from apps.windows.hardware.providers.cpuz_provider import CpuzProvider
from apps.windows.hardware.providers.gpuz_provider import GpuzProvider
from apps.windows.hardware.providers.hwinfo_provider import HwinfoProvider
from apps.windows.hardware.providers.lhm_provider import LhmProvider
from apps.windows.hardware.providers.native_win_provider import NativeWinProvider
from apps.windows.hardware.providers.smartmontools_provider import SmartmontoolsProvider


class HardwareProviderRegistry:
    """Реестр аппаратных провайдеров с авто-обнаружением внешних утилит."""

    def __init__(self, discovery: Optional[UtilityDiscovery] = None) -> None:
        """Инициализация реестра провайдеров."""
        self.discovery = discovery or UtilityDiscovery()
        self._providers: Dict[str, BaseHardwareProvider] = {}
        self._init_providers()

    def _init_providers(self) -> None:
        """Зарегистрировать все доступные аппаратные провайдеры."""
        # Tier 1: Нативный Windows
        native = NativeWinProvider()
        self._providers["native"] = native

        # Tier 2: AIDA64, HWiNFO, LHM
        aida_path = self.discovery.find_utility("aida64")
        self._providers["aida64"] = Aida64Provider(binary_path=aida_path)

        hwinfo_path = self.discovery.find_utility("hwinfo")
        self._providers["hwinfo"] = HwinfoProvider(binary_path=hwinfo_path)

        lhm_path = self.discovery.find_utility("lhm")
        self._providers["lhm"] = LhmProvider(binary_path=lhm_path)

        # Tier 3: smartctl, CPU-Z, GPU-Z
        smartctl_path = self.discovery.find_utility("smartctl")
        self._providers["smartmontools"] = SmartmontoolsProvider(binary_path=smartctl_path)

        cpuz_path = self.discovery.find_utility("cpuz")
        self._providers["cpuz"] = CpuzProvider(binary_path=cpuz_path)

        gpuz_path = self.discovery.find_utility("gpuz")
        self._providers["gpuz"] = GpuzProvider(binary_path=gpuz_path)

        logger.info(f"Зарегистрировано {len(self._providers)} аппаратных провайдеров")

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
