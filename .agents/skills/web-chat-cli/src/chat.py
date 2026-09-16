# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Фиктивный объект модели для инициализации плагина.
# =============================================================================
# Description:
#   Консольный интерфейс для взаимодействия с RAG-системой медиатеки.
#
# File: chat.py
# Project: ai-breadboard
# Package: .agents.skills.web-chat-cli.src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sys
import argparse
import asyncio
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))
from src.ai.gemini.user_query_rag import search_user_context, index_user_query
from src.ai.orchestration.unified_chat import UnifiedChatModel

class RAGPlugin:
    """Real RAGPlugin implementation."""
    def __init__(self, ai_model, api_key: str = None):
        self.ai_model = ai_model
        self.api_key = api_key or os.getenv("GEMINI_API_KEY_1") or os.getenv("GEMINI_API_KEY")
    
    async def _handle(self, message: str, **kwargs):
        yield {"status": "🔍 Поиск в RAG..."}
        
        results = search_user_context(user_id="anon", api_key=self.api_key, query=message)
        
        context = ""
        if results:
            context = "\n".join([r['text'] for r in results])
            prompt = f"Context: {context}\nMessage: {message}"
        else:
            prompt = message
            
        response = await self.ai_model.chat(prompt, model_name=kwargs.get('model_name'))
        
        # Index query/response
        index_user_query(user_id="anon", api_key=self.api_key, query=message, response=response)
        
        if results:
            yield {"text": f"Context used:\n{context}\n\nResponse: {response}"}
        else:
            yield {"text": response}

    async def handle(self, message: str, **kwargs) -> str:
        # For simplicity, just use the first yielded text
        async for output in self._handle(message, **kwargs):
            if "text" in output:
                return output["text"]
        return "No response"

def parse_arguments() -> argparse.Namespace:
    """Парсинг аргументов командной строки.

    Args:
        None

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

    Returns:
        None
    """
    print(f"Web Chat CLI запущен (Модель: {args.model}). Введите 'exit' для выхода.")
    
    # Initialization плагина
    ai_model = UnifiedChatModel(api_key_names=["GEMINI_API_KEY_1", "GEMINI_API_KEY"])
    rag_plugin = RAGPlugin(ai_model)
    
    while True:
        try:
            user_input = input("Вы: ")
            if user_input.lower() == 'exit':
                break
            
            # Обработка через плагин (асинхронно)
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
            print(f"Error: {e}")

if __name__ == '__main__':
    args = parse_arguments()
    asyncio.run(chat_loop(args))
