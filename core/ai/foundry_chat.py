# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Foundry Chat Interface
# =============================================================================
# Description:
#   Parent class for Foundry model chat interactions.
#   Provides ask() and chat() methods with retry logic and model switching.
#   Follows Gemini pattern: model selection at initialization, error handling.
#   Integrated with RAG semantic movie database index.
#
# File: src/ai/foundry_chat.py
# Project: mediateka
# =============================================================================

import asyncio
import logging
import time
from typing import Optional, List, Dict, Any

from core.logger.logger import logger

logger = logging.getLogger(__name__)


class FoundryChatBase:
    """
    Базовый класс для чат-интерфейса с Foundry моделями.
    
    Паттерн инициализации:
        ai = FoundryChatBase(model_id="qwen3-0.6b-generic-cpu:4")
    
    Паттерн использования:
        # Одиночный запрос
        answer = await ai.ask("Привет, как дела?")
        
        # Мульти-ток с историей
        answer = await ai.chat("Суммаризируй предыдущее", history=prev_history)
        
        # Очистка истории
        ai.clear_history()
    """

    @classmethod
    def get_available_models(cls, force_refresh: bool = False) -> List[str]:
        """Возвращает список доступных моделей для Foundry через единый менеджер моделей."""
        from core.ai.model_manager import get_available_models as _mgr_get_available_models
        return _mgr_get_available_models(provider="foundry", force_refresh=force_refresh)

    def __init__(
        self,
        model_id: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: str = "You are a helpful AI assistant.",
        api_url: Optional[str] = "",
    ):
        """
        Args:
            model_id: Foundry model ID (e.g. 'qwen3-0.6b-generic-cpu:4')
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            system_prompt: System instruction for chat mode
            api_url: Optional custom Foundry API URL (auto-discovered if empty)
        """
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        
        # Import FoundryClient lazily to avoid circular dependencies
        self._client = False
        self._api_url = api_url
        
        # Chat history (memory mode only)
        self._history: List[Dict[str, str]] = []
        
        # Error tracking
        self._last_error: str = ""
        self._error_count: int = 0
        
        logger.info(f"FoundryChat initialized: model={model_id}")

    @property
    def system_instruction(self) -> str:
        """Возвращает системную инструкцию."""
        return self.system_prompt

    @system_instruction.setter
    def system_instruction(self, val: str) -> None:
        """Устанавливает системную инструкцию."""
        self.system_prompt = val

    async def _get_client(self):
        """Lazy initialization of FoundryClient."""
        if not self._client:
            from ..clients.foundry import FoundryClient
            self._client = FoundryClient(base_url=self._api_url)
        return self._client

    async def close(self):
        """Close client session."""
        if self._client:
            await self._client.close()

    def clear_history(self):
        """Очищает историю чата."""
        self._history = []
        logger.debug("Chat history cleared")

    # ── ask() - одиночный запрос (без сохранения истории) ─────────────────────

    async def ask(
        self,
        q: str,
        attempts: int = 15,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        **kwargs,
    ) -> Optional[str]:
        """
        Отправляет текстовый запрос модели и возвращает ответ.
        Не сохраняет историю между вызовами.
        
        Args:
            q: Текст запроса
            attempts: Максимум попыток (retry logic)
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            
        Returns:
            Optional[str]: Ответ модели или None при критической ошибке
        """
        if not q or not q.strip():
            logger.warning("Empty query, skipping")
            return None

        # Поиск по RAG контексту (при наличии)
        context = kwargs.get('dynamic_context', '')

        prompt = q
        if context:
            prompt = f"{q}{context}"

        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens

        for attempt in range(1, attempts + 1):
            try:
                logger.info(f"[{self.model_id}] ask attempt {attempt}/{attempts}")

                client = await self._get_client()
                result = await client.generate_text(
                    prompt=prompt,
                    model=self.model_id,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                if result.get("success") and result.get("content"):
                    content = result["content"]
                    self._error_count = 0  # Reset error count on success
                    logger.debug(f"[{self.model_id}] ask success: {content[:80]}...")
                    return content

                # Handle model not loaded error
                error_code = result.get("error_code")
                if error_code == "model_not_loaded":
                    logger.warning(f"Model {self.model_id} not loaded, attempting to load...")
                    load_result = await client.load_model(self.model_id)
                    if load_result.get("success"):
                        logger.info(f"Model {self.model_id} loaded successfully")
                        continue  # Retry after load
                    else:
                        load_err = load_result.get('error', '')
                        logger.error(f"Failed to load model {self.model_id}: {load_err}")
                        from core.ai.model_manager import add_unsupported_model
                        add_unsupported_model('foundry', self.model_id, reason=f"Load failed: {load_err}")
                        return None

                # Other error - log and retry
                error_msg = result.get("error", "Unknown error")
                if "404" in error_msg or "not found" in error_msg.lower():
                    from core.ai.model_manager import add_unsupported_model
                    add_unsupported_model('foundry', self.model_id, reason=error_msg)
                    return None
                logger.warning(f"[{self.model_id}] attempt {attempt} failed: {error_msg}")

                if attempt < attempts:
                    wait = 2 ** min(attempt, 5)  # Exponential backoff: 2, 4, 8, 16, 32s
                    logger.info(f"Waiting {wait}s before retry...")
                    time.sleep(wait)

            except Exception as ex:
                logger.error(f"[{self.model_id}] exception on attempt {attempt}: {ex}")
                self._last_error = str(ex)
                self._error_count += 1

                if attempt < attempts:
                    wait = 2 ** min(attempt, 5)
                    logger.info(f"Waiting {wait}s before retry...")
                    time.sleep(wait)
                else:
                    logger.error(f"[{self.model_id}] All {attempts} attempts failed")
                    return None

        return None

    # ── chat() - мульти-ток с историей ────────────────────────────────────────

    async def chat(
        self,
        q: str,
        history: Optional[List[Dict]] = [],
        save_history: bool = True,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        system_instruction: Optional[str] = "",
        attempts: int = 15,
        flag: str = "save_chat",
        **kwargs,
    ) -> Optional[str]:
        """
        Обрабатывает чат-запрос с историей.
        
        Args:
            q: Текст запроса
            history: История чата из БД (опционально)
            save_history: Сохранять ли новую пару в локальную историю
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            system_instruction: Временная системная инструкция
            attempts: Максимальное количество попыток
            flag: Управление историей (для совместимости с интерфейсом Gemini)
            
        Returns:
            Optional[str]: Ответ модели
        """
        if not q or not q.strip():
            logger.warning("Empty chat message, skipping")
            return ""

        # If history is passed, use it instead of local _history
        if history:
            self._history = history.copy()
        elif flag == "clear" or flag == "start_new":
            self.clear_history()

        # Поиск по RAG контексту (при наличии)
        context = kwargs.get('dynamic_context', '')

        eff_temp = temperature if temperature and temperature > 0 else self.temperature
        eff_tokens = max_tokens if max_tokens and max_tokens > 0 else self.max_tokens

        # Prepare messages with system prompt
        sys_prompt = system_instruction or self.system_prompt
        if context:
            sys_prompt = f"{sys_prompt}{context}"

        messages = [{"role": "system", "content": sys_prompt}]
        messages.extend(self._history)
        messages.append({"role": "user", "content": q})

        for attempt in range(1, attempts + 1):
            try:
                logger.info(f"[{self.model_id}] chat attempt {attempt}/{attempts}")

                client = await self._get_client()
                result = await client.generate_text(
                    prompt="",  # Not used when messages provided
                    model=self.model_id,
                    temperature=eff_temp,
                    max_tokens=eff_tokens,
                    messages=messages,
                )

                if result.get("success") and result.get("content"):
                    answer = result["content"]
                    
                    # Save to history
                    if save_history:
                        self._history.append({"role": "user", "content": q})
                        self._history.append({"role": "assistant", "content": answer})
                    
                    self._error_count = 0
                    logger.debug(f"[{self.model_id}] chat success: {answer[:80]}...")
                    return answer

                # Handle model not loaded error
                error_code = result.get("error_code")
                if error_code == "model_not_loaded":
                    logger.warning(f"Model {self.model_id} not loaded, attempting to load...")
                    load_result = await client.load_model(self.model_id)
                    if load_result.get("success"):
                        logger.info(f"Model {self.model_id} loaded successfully")
                        continue  # Retry after load
                    else:
                        load_err = load_result.get('error', '')
                        logger.error(f"Failed to load model {self.model_id}: {load_err}")
                        from core.ai.model_manager import add_unsupported_model
                        add_unsupported_model('foundry', self.model_id, reason=f"Load failed: {load_err}")
                        return ""

                error_msg = result.get("error", "Unknown error")
                logger.warning(f"[{self.model_id}] chat attempt {attempt} failed: {error_msg}")

                if attempt < attempts:
                    time.sleep(2 ** min(attempt, 5))

            except Exception as ex:
                logger.error(f"[{self.model_id}] chat exception: {ex}")
                self._last_error = str(ex)
                if attempt >= attempts:
                    return ""
                time.sleep(2 ** min(attempt, 5))

        return ""

    async def chat_stream(
        self,
        q: str,
        history: Optional[List[Dict]] = [],
        save_history: bool = True,
        temperature: Optional[float] = 0.0,
        max_tokens: Optional[int] = 0,
        system_instruction: Optional[str] = "",
        attempts: int = 15,
        model_name: Optional[str] = "",
        generation_config: dict = {},
        **kwargs,
    ):
        """
        Стриминговый интерфейс для чата (возвращает генератор с чанк-ответом).
        """
        response = await self.chat(
            q=q,
            history=history,
            save_history=save_history,
            temperature=temperature,
            max_tokens=max_tokens,
            system_instruction=system_instruction,
            attempts=attempts,
            **kwargs,
        )
        if response:
            yield response
        else:
            if self._last_error:
                raise Exception(self._last_error)
            else:
                raise Exception(f"Failed to generate response using model {self.model_id}")

    # ── Свойства ───────────────────────────────────────────────────────────────

    @property
    def history(self) -> List[Dict[str, str]]:
        """Возвращает текущую историю чата (без system prompt)."""
        return list(self._history)

    @property
    def last_error(self) -> str:
        """Возвращает последнюю ошибку."""
        return self._last_error

    @property
    def error_count(self) -> int:
        """Возвращает количество последовательных ошибок."""
        return self._error_count


# ── Простой чат-интерфейс (с одним экземпляром клиента) ──────────────────────

class FoundrySimpleChat(FoundryChatBase):
    """
    Упрощённый чат-интерфейс для Foundry.
    Используется, когда нужна только генерация текста без сохранения истории.
    
    Пример:
        chat = FoundrySimpleChat(model_id="qwen3-0.6b-generic-cpu:4")
        answer = await chat.ask("Привет")
    """

    def __init__(self, model_id: str, **kwargs):
        super().__init__(model_id, **kwargs)
        logger.info(f"FoundrySimpleChat initialized: model={model_id}")


# ── Модульный уровень (для быстрого старта) ──────────────────────────────────

# Глобальный экземпляр (один на весь процесс)
_default_chat: Any = False


def get_foundry_chat(model_id: Optional[str] = "") -> FoundryChatBase:
    """
    Возвращает глобальный экземпляр чата.
    
    Args:
        model_id: Если указан, создаёт новый экземпляр с этой моделью
        
    Returns:
        FoundryChatBase: Экземпляр чата
    """
    global _default_chat
    
    if model_id:
        _default_chat = FoundryChatBase(model_id=model_id)
    
    if not _default_chat:
        raise ValueError("No default chat initialized. Call get_foundry_chat(model_id='...') first")
    
    return _default_chat


def set_foundry_chat(chat: FoundryChatBase):
    """Устанавливает глобальный экземпляр чата."""
    global _default_chat
    _default_chat = chat
    logger.info("Global FoundryChat instance set")


# ── Импорт совместимости ─────────────────────────────────────────────────────

# Для совместимости с существующим кодом
FoundryClient = FoundryChatBase
