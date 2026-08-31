# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional


class BaseChatProvider(ABC):
    @classmethod
    def get_available_models(cls, force_refresh: bool = False) -> List[str]:
        return []

    @property
    @abstractmethod
    def system_instruction(self) -> str:
        pass

    @system_instruction.setter
    @abstractmethod
    def system_instruction(self, val: str) -> None:
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
        pass

    async def close(self) -> None:
        pass

    def clear_history(self) -> None:
        pass
