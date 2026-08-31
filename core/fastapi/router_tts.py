# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Синтезирует отдельный чанк текста при помощи Modul
# =============================================================================
# Description:
#   Module for AI Breadboard project.
#
# File: router_tts.py
# Project: ai-breadboard
# Package: core.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import os
import re
import uuid
import asyncio
from pathlib import Path
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, FileResponse

from core.logger import logger
from core.ai.voice_pipeline import generate_voiceover_chunks

_ROOT = Path(__file__).parent.parent.parent
# Директория для хранения сгенерированных аудиофайлов TTS
TTS_CACHE_DIR = _ROOT / "tmp" / "tts_cache"
TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

from core.tts import synthesize_speech

async def _synthesize_chunk_to_file(text: str, file_path: Path, tts_system: str = "edge-tts", voice: str = "ru-RU-DmitryNeural"):
    """Синтезирует отдельный чанк текста при помощи Moduleной TTS системы."""
    await synthesize_speech(text, file_path, tts_system, voice)

def _get_user_tts_config(request: Request) -> tuple[str, str]:
    """Returns (tts_system, tts_voice) для текущего пользователя или дефолтные значения."""
    tts_system = "edge-tts"
    from core.config import tts_cfg
    tts_voice = getattr(tts_cfg, "default_voice", "ru-RU-DmitryNeural") if tts_cfg else "ru-RU-DmitryNeural"
    
    token = request.cookies.get('auth_token')
    if token:
        try:
            from core.fastapi.router_auth import verify_jwt_token
            from core.user_manager import user_manager
            user_data = verify_jwt_token(token)
            if user_data and user_data.email:
                db_user = user_manager.get_user_by_email(user_data.email)
                if db_user:
                    settings = user_manager.get_user_settings(db_user['id'])
                    tts_system = settings.get('tts_system') or tts_system
                    tts_voice = settings.get('tts_voice') or tts_voice
        except Exception as e:
            logger.error(f"Error getting user TTS settings: {e}")
            
    return tts_system, tts_voice

def _adjust_voice_for_language(text: str, current_voice: str) -> str:
    """Эвристически определяет язык текста и подменяет голос, если он не совпадает с языком."""
    import re
    # Подсчитываем количество букв кириллицы и латиницы
    ru_count = len(re.findall(r'[А-Яа-яЁё]', text))
    en_count = len(re.findall(r'[A-Za-z]', text))
    
    # Если кириллицы больше, считаем текст русским
    if ru_count >= en_count:
        if current_voice.lower().startswith('en-'):
            # Возвращаем дефолтный русский голос
            return "ru-RU-DmitryNeural"
    else:
        # Считаем текст английским
        if current_voice.lower().startswith('ru-'):
            # Возвращаем дефолтный английский голос
            return "en-US-AriaNeural"
            
    return current_voice

def init_router(prefix: str = "/api/tts") -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["tts"])

    @router.get("/stream-text")
    async def stream_text(
        media_id: int = Query(..., description="ID медиафайла в БД"),
        field: str = Query("plot", description="Какое поле озвучить (plot, facts, why_watch, final_verdict)")
    ):
        """
        Стримит адаптированные для диктора куски текста через Server-Sent Events (SSE).
        """
        db = _db()
        # Получаем запись из базы данных по media_id
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT {field}, title_ru FROM media WHERE id = ?", (media_id,))
        row = cursor.fetchone()
        if not row or not row[0]:
            raise HTTPException(status_code=404, detail="Медиафайл или указанное поле не найдены")
        
        raw_text = row[0]
        
        async def sse_generator() -> AsyncGenerator[str, None]:
            try:
                # Генерируем чанки на лету с помощью Gemini
                async for chunk in generate_voiceover_chunks(raw_text):
                    # Отправляем в формате SSE
                    yield f"data: {chunk}\n\n"
            except Exception as e:
                logger.error(f"Error in SSE stream-text: {e}")
                yield f"data: Error при обработке текста: {str(e)}\n\n"

        return StreamingResponse(sse_generator(), media_type="text/event-stream")

    @router.get("/synthesize")
    async def synthesize(
        request: Request,
        text: str = Query(..., description="Текст для озвучки"),
        system: str = Query("", description="TTS система (edge-tts, gtts, silero)"),
        voice: str = Query("", description="Голос диктора")
    ):
        """
        Принимает текст, синтезирует его в аудиофайл и сразу отдает mp3.
        """
        if not text.strip():
            raise HTTPException(status_code=400, detail="Empty text")
        
        # Получаем настройки озвучки текущего пользователя или Parameters запроса
        user_system, user_voice = _get_user_tts_config(request)
        tts_system = system if system != "" else user_system
        tts_voice = voice if voice != "" else user_voice
        
        tts_voice = _adjust_voice_for_language(text, tts_voice)
        
        # Создаем уникальное имя файла на основе хэша текста и настроек озвучки
        import hashlib
        config_str = f"{text}_{tts_system}_{tts_voice}"
        text_hash = hashlib.md5(config_str.encode("utf-8")).hexdigest()
        file_path = TTS_CACHE_DIR / f"{text_hash}.mp3"
        
        if not file_path.exists():
            try:
                await _synthesize_chunk_to_file(text, file_path, tts_system, tts_voice)
            except Exception as e:
                logger.error(f"TTS synthesis error: {e}")
                raise HTTPException(status_code=500, detail=f"Error синтеза речи: {e}")
                
        return FileResponse(file_path, media_type="audio/mpeg", filename="voiceover.mp3")

    @router.get("/stream-audio")
    async def stream_audio(
        request: Request,
        media_id: int = Query(..., description="ID медиафайла в БД"),
        field: str = Query("plot", description="Поле для озвучки"),
        system: str = Query("", description="TTS система"),
        voice: str = Query("", description="Голос диктора")
    ):
        """
        Конвейерный эндпоинт:
        1. На лету разбивает/адаптирует текст через Gemini.
        2. Синтезирует каждый чанк в mp3.
        3. Стримит клиенту JSON-события с текстом чанка и ссылкой на его аудиофайл,
           чтобы фронтенд мог мгновенно проигрывать готовые куски по очереди.
        """
        db = _db()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT {field} FROM media WHERE id = ?", (media_id,))
        row = cursor.fetchone()
        if not row or not row[0]:
            raise HTTPException(status_code=404, detail="Медиафайл или поле не найдены")
        
        raw_text = row[0]
        user_system, user_voice = _get_user_tts_config(request)
        tts_system = system if system != "" else user_system
        tts_voice = voice if voice != "" else user_voice

        async def sse_audio_generator() -> AsyncGenerator[str, None]:
            import json
            import hashlib
            idx = 0
            async for chunk in generate_voiceover_chunks(raw_text):
                # Подстраиваем голос под язык чанка
                adjusted_voice = _adjust_voice_for_language(chunk, tts_voice)
                
                # Для каждого адаптированного текстового чанка запускаем синтез с учетом настроек
                config_str = f"{chunk}_{tts_system}_{adjusted_voice}"
                text_hash = hashlib.md5(config_str.encode("utf-8")).hexdigest()
                file_path = TTS_CACHE_DIR / f"{text_hash}.mp3"
                
                if not file_path.exists():
                    try:
                        await _synthesize_chunk_to_file(chunk, file_path, tts_system, adjusted_voice)
                    except Exception as e:
                        logger.error(f"Failed to synthesize chunk {idx}: {e}")
                        continue
                
                # Отправляем JSON с текстом и ссылкой на скачивание
                audio_url = f"/api/tts/file/{text_hash}.mp3"
                payload = {
                    "index": idx,
                    "text": chunk,
                    "audio_url": audio_url
                }
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                idx += 1

        return StreamingResponse(sse_audio_generator(), media_type="text/event-stream")

    @router.get("/file/{filename}")
    async def get_audio_file(filename: str):
        """Returns аудиофайл из кэша."""
        file_path = TTS_CACHE_DIR / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        return FileResponse(file_path, media_type="audio/mpeg")

    return router
