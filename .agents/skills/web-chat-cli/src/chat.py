# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: RAG-плагин для Web Chat CLI.
# =============================================================================
# Description:
#   Консольный интерфейс для взаимодействия с RAG-системой медиатеки.
#
# File: chat.py
# Project: ai-breadboard
# Package: .skills.web-chat-cli.src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sys
import argparse
import asyncio
import os
from typing import AsyncGenerator, Optional, Dict, Any

# Добавление пути к корню проекта для импортов
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from src.ai.gemini.user_query_rag import search_user_context, index_user_query
from src.ai.orchestration.unified_chat import UnifiedChatModel
from logger import logger

class RAGPlugin:
    """Реализация RAG-плагина для обогащения ответов контекстом."""
    
    def __init__(self, ai_model: UnifiedChatModel, api_key: Optional[str] = None):
        """Инициализация RAG-плагина.

        Args:
            ai_model (UnifiedChatModel): Модель чата для генерации ответов.
            api_key (Optional[str]): API ключ Gemini (опционально).
        """
        self.ai_model = ai_model
        self.api_key = api_key or os.getenv("GEMINI_API_KEY_1") or os.getenv("GEMINI_API_KEY")
    
    async def _handle(self, message: str, **kwargs: Any) -> AsyncGenerator[Dict[str, str], None]:
        """Обработка сообщения с использованием RAG-контекста.

        Args:
            message (str): Сообщение пользователя.
            **kwargs (Any): Дополнительные параметры (например, model_name).

        Yields:
            Dict[str, str]: Статус или текст ответа.
        """
        yield {"status": "🔍 Поиск в RAG..."}
        
        try:
            results = search_user_context(user_id="anon", api_key=self.api_key, query=message)
            
            context = ""
            if results:
                context = "\n".join([r['text'] for r in results])
                prompt = f"Контекст: {context}\nСообщение: {message}"
            else:
                prompt = message
                
            response = await self.ai_model.chat(prompt, model_name=kwargs.get('model_name'))
            
            # Индексация запроса и ответа
            index_user_query(user_id="anon", api_key=self.api_key, query=message, response=response)
            
            if results:
                yield {"text": f"Использованный контекст:\n{context}\n\nОтвет: {response}"}
            else:
                yield {"text": response}
        except Exception as e:
            logger.error(f"Ошибка при обработке RAG: {e}")
            yield {"text": f"Ошибка: {e}"}

    async def handle(self, message: str, **kwargs: Any) -> str:
        """Метод для внешнего вызова (синхронный/асинхронный адаптер).

        Args:
            message (str): Сообщение пользователя.
            **kwargs (Any): Дополнительные параметры.

        Returns:
            str: Ответ модели.
        """
        async for output in self._handle(message, **kwargs):
            if "text" in output:
                return output["text"]
        return "Нет ответа"

def parse_arguments() -> argparse.Namespace:
    """Парсинг аргументов командной строки.

    Returns:
        argparse.Namespace: Аргументы командной строки.
    """
    parser = argparse.ArgumentParser(description="Web Chat CLI")
    parser.add_argument('--model', default='gemini-1.5-flash', help='Имя модели')
    parser.add_argument('--debug', action='store_true', help='Режим отладки')
    return parser.parse_args()

async def chat_loop(args: argparse.Namespace) -> None:
    """Основной цикл интерактивного чата.

    Args:
        args (argparse.Namespace): Аргументы командной строки.
    """
    print(f"Web Chat CLI запущен (Модель: {args.model}). Введите 'exit' для выхода.")
    
    ai_model = UnifiedChatModel(api_key_names=["GEMINI_API_KEY_1", "GEMINI_API_KEY"])
    rag_plugin = RAGPlugin(ai_model)
    
    while True:
        try:
            user_input = input("Вы: ")
            if user_input.lower() == 'exit':
                break
            
            print("Система: Обработка...")
            
            response = None
            async for output in rag_plugin._handle(user_input, model_name=args.model):
                if "text" in output:
                    response = output["text"]
                elif "status" in output:
                    print(f"[{output['status']}]")
            
            if response:
                print(f"Система: {response}")
            else:
                print("Система: (Нет ответа)")
            
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nВыход...")
            break
        except Exception as e:
            logger.error(f"Критическая ошибка в чате: {e}")
            print(f"Система: Произошла ошибка. Проверьте логи.")

if __name__ == '__main__':
    args = parse_arguments()
    asyncio.run(chat_loop(args))
