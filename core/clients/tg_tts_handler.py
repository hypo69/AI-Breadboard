# -*- coding: utf-8 -*-
"""
Модуль для интеграции адаптивного TTS-конвейера в Telegram-бота.
Использует библиотеку python-telegram-bot или любой аналогичный фреймворк.
"""
import io
import httpx
import asyncio
from typing import AsyncGenerator
from core.logger import logger
from core.ai.voice_pipeline import generate_voiceover_chunks

# URL нашего локального FastAPI инстанса
API_BASE_URL = "http://127.0.0.1:8000"

async def handle_telegram_voiceover_request(update, context, media_id: int, field: str = "plot"):
    """
    Обработчик запроса озвучки в Telegram.
    Реализует конвейер:
    1. Генерирует адаптированные куски текста с помощью Gemini.
    2. Отправляет в чат текстовую строку "Готовим озвучку...".
    3. Для каждого готового чанка делает запрос к TTS, скачивает mp3 
       и мгновенно отправляет его пользователю в виде голосового сообщения (Voice Message).
    """
    query = update.callback_query if update.callback_query else None
    chat_id = update.effective_chat.id
    
    # 1. Отправляем приветственное сообщение
    status_message = await context.bot.send_message(
        chat_id=chat_id,
        text="🎙 *Начинаю подготовку озвучки...* Текст адаптируется для диктора.",
        parse_mode="Markdown"
    )
    
    # Получаем исходный текст из БД
    # В реальном коде бота вы можете импортировать MediaDatabase напрямую:
    # from plugins.media_organizer.core.database import MediaDatabase
    # db = MediaDatabase(DB_FILE)
    # raw_text = db.get_media_field(media_id, field)
    # Для примера сделаем заглушку, имитирующую получение текста:
    raw_text = "Пример текста из базы данных. 1. Включите вилку в розетку. 2. Нажмите кнопку пуск."
    
    try:
        idx = 1
        async for chunk in generate_voiceover_chunks(raw_text):
            # Извещаем пользователя о подготовке конкретной части
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_message.message_id,
                text=f"⏳ *Синтезирую часть {idx}...*\n\n_{chunk}_",
                parse_mode="Markdown"
            )
            
            # Отправляем запрос к нашему API синтеза (или вызываем edge-tts напрямую)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/api/tts/synthesize",
                    params={"text": chunk},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    # Отправляем аудиофайл как голосовое сообщение в Telegram
                    audio_data = io.BytesIO(response.content)
                    audio_data.name = f"voiceover_part_{idx}.ogg" # Telegram хорошо принимает ogg/mp3
                    
                    await context.bot.send_voice(
                        chat_id=chat_id,
                        voice=audio_data,
                        caption=f"Часть {idx}",
                        title="Диктор"
                    )
                else:
                    logger.error(f"TTS API returned error code {response.status_code}")
                    await context.bot.send_message(chat_id=chat_id, text=f"❌ Ошибка озвучки части {idx}")
            
            idx += 1
            await asyncio.sleep(0.5) # Небольшая пауза между отправкой частей
            
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_message.message_id,
            text="✅ *Вся озвучка готова и отправлена!*",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in TG voiceover handler: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Произошла ошибка при озвучке: {str(e)}"
        )
