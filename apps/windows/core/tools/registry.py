# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Dynamic Windows Tool Registry
# =============================================================================
# Description:
#   Реестр инструментов (ToolRegistry) для централизованного хранения,
#   динамической регистрации, поиска и формирования Function Calling схем.
#
# Examples:
#   >>> from apps.windows.core.tools.registry import ToolRegistry
#   >>> registry = ToolRegistry()
#   >>> tools_defs = registry.get_function_definitions()
#
# File: registry.py
# Project: AI-Breadboard
# Package: apps.windows.core.tools
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""Реестр системных и динамических инструментов подсистемы Windows."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.logger import logger
from apps.windows.core.tools.base import BaseTool, ToolExecutionResult


class ToolRegistry:
    """Реестр встроенных и динамически сгенерированных инструментов."""

    def __init__(self) -> None:
        """Инициализация реестра."""
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool, overwrite: bool = True) -> bool:
        """Регистрация инструмента в реестре.

        Args:
            tool: Экземпляр BaseTool.
            overwrite: Перезаписывать ли существующий инструмент с таким именем.

        Returns:
            bool: True если зарегистрирован успешно, False если инструмент уже существовал.
        """
        if not tool or not getattr(tool, "name", None):
            logger.warning("[ToolRegistry] Попытка зарегистрировать невалидный инструмент.")
            return False

        if tool.name in self._tools and not overwrite:
            logger.debug(f"[ToolRegistry] Инструмент '{tool.name}' уже зарегистрирован.")
            return False

        self._tools[tool.name] = tool
        logger.info(f"[ToolRegistry] Зарегистрирован инструмент '{tool.name}' ({tool.title})")
        return True

    def unregister(self, tool_name: str) -> bool:
        """Удаление инструмента из реестра.

        Args:
            tool_name: Имя инструмента.

        Returns:
            bool: True если инструмент был удален.
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.info(f"[ToolRegistry] Инструмент '{tool_name}' удален из реестра.")
            return True
        return False

    def get(self, tool_name: str) -> Optional[BaseTool]:
        """Получение инструмента по имени.

        Args:
            tool_name: Имя инструмента.

        Returns:
            Optional[BaseTool]: Экземпляр инструмента или None.
        """
        return self._tools.get(tool_name)

    def has(self, tool_name: str) -> bool:
        """Проверка наличия инструмента в реестре.

        Args:
            tool_name: Имя инструмента.

        Returns:
            bool: True если инструмент присутствует в реестре.
        """
        return tool_name in self._tools

    def list_tools(self) -> List[BaseTool]:
        """Возвращает список всех зарегистрированных инструментов."""
        return list(self._tools.values())

    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """Формирует список схем вызовов в стандарте Function Calling OpenAPI.

        Returns:
            List[Dict[str, Any]]: Список определений функций для LLM.
        """
        return [tool.to_function_definition() for tool in self._tools.values()]

    def get_definitions(self) -> List[Dict[str, Any]]:
        """Алиас для get_function_definitions."""
        return self.get_function_definitions()

    async def execute(self, _tool_name: str, **kwargs: Any) -> ToolExecutionResult:
        """Исполнение зарегистрированного инструмента по имени.

        Args:
            _tool_name: Имя инструмента в реестре.
            **kwargs: Аргументы для выполнения.

        Returns:
            ToolExecutionResult: Результат исполнения.
        """
        tool = self.get(_tool_name)
        if not tool:
            return ToolExecutionResult(
                tool_name=_tool_name,
                status="error",
                data=None,
                message=f"Инструмент '{_tool_name}' не найден в реестре.",
            )
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"[ToolRegistry] Сбой выполнения инструмента '{_tool_name}': {e}", exc_info=True)
            return ToolExecutionResult(
                tool_name=_tool_name,
                status="error",
                data=None,
                message=f"Ошибка выполнения инструмента '{_tool_name}': {e}",
            )

