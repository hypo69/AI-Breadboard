# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Hardware Cross Validation Engine
# =============================================================================
# Description:
#   Движок кросс-валидации (Cross-Check & Consensus) аппаратных данных,
#   полученных от независимых провайдеров. Обнаруживает расхождения и
#   формирует события неконсистентности для AI-диагноста.
#
# File: cross_validator.py
# Project: ai-breadboard
# Package: apps.windows.hardware
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Движок кросс-валидации данных оборудования от нескольких провайдеров."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from logger import logger
from apps.windows.hardware.models import (
    CpuInventory,
    GpuInventory,
    MotherboardInventory,
    SensorSnapshot,
    StorageInventory,
    SystemHardwareInventory,
)
from apps.windows.hardware.registry import HardwareProviderRegistry


@dataclass
class DiscrepancyItem:
    """Элемент расхождения между источниками данных."""
    component: str             # CPU, GPU, RAM, Storage, Motherboard
    parameter: str             # Model, Cores, VRAM, Size, etc.
    sources: Dict[str, Any]    # Провайдер -> Значение
    severity: str = "WARNING"  # INFO, WARNING, ERROR
    explanation: Optional[str] = None


@dataclass
class ValidationReport:
    """Сводный отчет кросс-валидации оборудования."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    consensus_score_pct: float = 100.0
    total_checks: int = 0
    discrepancies: List[DiscrepancyItem] = field(default_factory=list)
    active_providers: List[str] = field(default_factory=list)
    normalized_inventory: Optional[SystemHardwareInventory] = None

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь."""
        return asdict(self)


class CrossValidator:
    """Движок кросс-валидации и выявления аппаратных аномалий."""

    def __init__(self, registry: Optional[HardwareProviderRegistry] = None) -> None:
        """Инициализация валидатора."""
        self.registry = registry or HardwareProviderRegistry()

    def run_cross_check(self) -> ValidationReport:
        """Выполнить перекрестную проверку всех доступных провайдеров."""
        available = self.registry.get_available_providers()
        report = ValidationReport(active_providers=[p.name for p in available])

        inventories: Dict[str, SystemHardwareInventory] = {}
        for p in available:
            try:
                inv = p.probe_inventory()
                if inv:
                    inventories[p.name] = inv
            except Exception as e:
                logger.error(f"Ошибка сбора инвентаря от {p.name}: {e}")

        if not inventories:
            return report

        # 1. Кросс-чек CPU (Имя, Количество ядер)
        cpu_models: Dict[str, Any] = {}
        cpu_cores: Dict[str, Any] = {}
        for p_name, inv in inventories.items():
            if inv.cpu:
                cpu_models[p_name] = inv.cpu.model_name
                if inv.cpu.physical_cores:
                    cpu_cores[p_name] = inv.cpu.physical_cores

        report.total_checks += 1
        if len(set(cpu_cores.values())) > 1:
            report.discrepancies.append(
                DiscrepancyItem(
                    component="CPU",
                    parameter="Physical Cores",
                    sources=cpu_cores,
                    severity="WARNING",
                    explanation="Разные провайдеры сообщают различное число физических ядер (возможно, влияние E/P-ядер или HyperThreading).",
                )
            )

        # 2. Формируем нормализованный инвентарь (приоритет: Tier 1 -> Tier 2 -> Tier 3)
        consolidated = SystemHardwareInventory(sources_used=list(inventories.keys()))
        for p_name, inv in inventories.items():
            if not consolidated.cpu and inv.cpu:
                consolidated.cpu = inv.cpu
            if not consolidated.motherboard and inv.motherboard:
                consolidated.motherboard = inv.motherboard
            if not consolidated.memory and inv.memory:
                consolidated.memory = inv.memory
            if not consolidated.storage and inv.storage:
                consolidated.storage = inv.storage
            if not consolidated.gpus and inv.gpus:
                consolidated.gpus = inv.gpus

        report.normalized_inventory = consolidated
        if report.discrepancies:
            report.consensus_score_pct = max(0.0, 100.0 - (len(report.discrepancies) * 15.0))

        return report
