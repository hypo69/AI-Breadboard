# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Интерактивный чат-клиент CLI
# =============================================================================
# Описание:
#   Консольный интерфейс для взаимодействия с RAG-системой медиатеки.
#
# File: src/chat.py
# Project: ai-assistant
# Package: src
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import sys
import argparse
import asyncio
# Импортируем RAG-плагин для использования логики
from plugins.rag import RAGPlugin

class FakeAIModel:
    """Фиктивный объект модели для инициализации плагина."""
    async def chat(self, message: str, system_instruction: str = "", model_name: str = "") -> str:
        """Эмуляция ответа ИИ."""
        return f"Ответ от {model_name} на: {message}"

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
    
    # Инициализация плагина
    ai_model = FakeAIModel()
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
            print(f"Ошибка: {e}")

if __name__ == '__main__':
    args = parse_arguments()
    asyncio.run(chat_loop(args))
