# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Abstract Base Provider Definition
# =============================================================================
# Description:
#   Defines the base interface for all AI chat and capability providers.
#
# File: base.py
# Package: core.ai.providers
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, Set


class BaseChatProvider(ABC):
    """Abstract base class for all AI model and capability providers."""

    @classmethod
    def get_available_models(cls, force_refresh: bool = False) -> List[str]:
        """Retrieve list of available model names for this provider."""
        return []

    @classmethod
    def is_available(cls) -> bool:
        """Check if provider runtime or backend service is available."""
        return True

    @classmethod
    def get_capabilities(cls) -> Set[str]:
        """Return set of capabilities supported by this provider."""
        return {"chat"}

    @property
    @abstractmethod
    def system_instruction(self) -> str:
        """Get current system instruction prompt."""
        pass

    @system_instruction.setter
    @abstractmethod
    def system_instruction(self, val: str) -> None:
        """Set current system instruction prompt."""
        pass

    @abstractmethod
    async def ask(
        self,
        q: str,
        attempts: int = 15,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        **kwargs: Any,
    ) -> Optional[str]:
        """Execute a single-turn query and return response string."""
        pass

    @abstractmethod
    async def stream_chat(
        self,
        q: str,
        attempts: int = 15,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream response chunks for a query."""
        pass

    async def close(self) -> None:
        """Clean up connections, client sessions, and underlying resources."""
        pass

    def clear_history(self) -> None:
        """Clear local conversation context or cache."""
        pass
