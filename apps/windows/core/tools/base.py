# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Core Tools - Base
# =============================================================================
# Description:
#   Базовые интерфейсы и модели данных для умных системных инструментов.
#
# Usage Examples:
#   Python API:
#     from apps.windows.core.tools.base import ToolExecutionResult
#
#     service = ToolExecutionResult()
#
# File: base.py
# Project: ai-breadboard
# Package: apps.windows.core.tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:28:28
# =============================================================================

from __future__ import annotations
"""Базовые интерфейсы и модели данных для умных системных инструментов."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from apps.windows.core.models import RiskLevel

@dataclass
class ToolExecutionResult:
    """Результат выполнения инструмента."""
    tool_name: str
    status: str
    data: Any
    message: str = ''
    command_executed: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.SAFE
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование результата в словарь."""
        return {'tool_name': self.tool_name, 'status': self.status, 'data': self.data, 'message': self.message, 'command_executed': self.command_executed, 'risk_level': self.risk_level.value if hasattr(self.risk_level, 'value') else str(self.risk_level), 'metadata': self.metadata}

class BaseTool(ABC):
    """Абстрактный базовый класс системного инструмента."""
    name: str
    title: str
    description: str
    parameters_schema: Dict[str, Any]
    risk_level: RiskLevel = RiskLevel.SAFE
    is_dynamic: bool = False

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolExecutionResult:
        """Исполнение инструмента на хосте с возвратом структурированных данных.

        Args:
            **kwargs: Параметры вызова инструмента.

        Returns:
            ToolExecutionResult: Результат выполнения с собранными фактами.
        """
        pass

    def to_function_definition(self) -> Dict[str, Any]:
        """Преобразование описания инструмента в формат Function Calling.

        Returns:
            Dict[str, Any]: Спецификация функции в формате OpenAPI / Function Call.
        """
        return {'name': self.name, 'description': self.description, 'parameters': self.parameters_schema}