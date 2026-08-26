# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: FastAPI-роутер чата
# =============================================================================
# Описание:
#   Обработка POST-запросов к /api/chat.
#   Последовательный опрос плагинов, извлечение контекста из пользовательского RAG,
#   прямой вызов AI-модели и автоматическая индексация диалога в User RAG.
#
# File: router_chat.py
# Project: ai-assistant
# Package: src.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import os
import time
import asyncio
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from core.logger import logger
from core.config import ai_cfg, tts_cfg
from core.ai.gemini.user_query_rag import index_user_query, search_user_context

router = APIRouter(prefix='/api/chat', tags=['chat'])


# Короткие слова-продолжения диалога, которые сами по себе не содержат медиа-ключевых слов
_CONTEXT_CONTINUATION_WORDS = {
    'да', 'нет', 'yes', 'no', 'ок', 'ok', 'хочу', 'конечно',
    'давай', 'проверь', 'найди', 'покажи', 'ладно', 'угу', 'yep', 'sure',
    'want', 'check', 'find', 'show', 'okay',
}


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    generation_config: dict = {}


class SaveRagRequest(BaseModel):
    query: str
    chat_text: str
    voice_text: str


class TestModelRequest(BaseModel):
    model: str = ""
    provider: str = ""
    message: str = "Привет! Назови свою модель и провайдера, и подтверди готовность к работе."
    system_instruction: str = ""


def get_chat_model(selected_model_name: str, system_instruction: str = ""):
    """Dynamically construct/retrieve the appropriate AI model instance."""
    is_gemini_cli = selected_model_name.startswith('gemini_cli:') or selected_model_name.startswith('gemini-cli-')
    is_foundry = selected_model_name.startswith('foundry:')
    is_ollama = selected_model_name.startswith('ollama:')
    is_hf = selected_model_name.startswith('hf:') or selected_model_name.startswith('hf::')
    is_onnx = selected_model_name.startswith('onnx:') or selected_model_name.startswith('onnx::')
    openai_prefixes = ('openai:', 'openai::', 'deepseek:', 'groq:', 'openrouter:', 'lmstudio:', 'local:', 'compat:')
    is_openai = any(selected_model_name.startswith(p) for p in openai_prefixes)
    is_agy = selected_model_name.startswith('agy-') or 'agy' in selected_model_name.lower()
    is_gemini = not is_gemini_cli and not is_hf and not is_onnx and not is_openai and (selected_model_name.startswith('gemini-') or 'gemini' in selected_model_name.lower())

    if is_gemini_cli:
        from core.ai.gemini_cli_chat import GeminiCliChatBase
        return GeminiCliChatBase(
            model_id=selected_model_name,
            system_prompt=system_instruction or "You are a helpful AI assistant.",
        )
    elif is_foundry:
        model_id = selected_model_name.split(':', 1)[-1]
        from core.ai.foundry_chat import FoundryChatBase
        return FoundryChatBase(
            model_id=model_id,
            system_prompt=system_instruction or "You are a helpful AI assistant.",
        )
    elif is_ollama:
        model_id = selected_model_name.split(':', 1)[-1]
        from core.ai.ollama_chat import OllamaChatBase
        ollama_url = ai_cfg.ollama_base_url if ai_cfg else 'http://localhost:11434'
        return OllamaChatBase(
            model_id=model_id,
            system_prompt=system_instruction or "You are a helpful AI assistant.",
            api_url=ollama_url
        )
    elif is_hf:
        model_id = selected_model_name.split(':', 1)[-1].lstrip(':')
        from core.ai.hf_chat import HFChatBase
        return HFChatBase(
            model_id=model_id,
            system_prompt=system_instruction or "You are a helpful AI assistant.",
        )
    elif is_onnx:
        model_id = selected_model_name.split(':', 1)[-1].lstrip(':')
        from core.ai.onnx_chat import ONNXChatBase
        return ONNXChatBase(
            model_id=model_id,
            system_prompt=system_instruction or "You are a helpful AI assistant.",
        )
    elif is_openai:
        prov_part, model_part = selected_model_name.split(':', 1)
        model_id = model_part.lstrip(':')
        prov_name = prov_part.lower().rstrip(':')
        if prov_name == 'compat':
            prov_name = 'openai'
        from core.ai.openai_compat_chat import OpenAICompatChat
        return OpenAICompatChat.create_for_provider(
            provider_name=prov_name,
            model_id=model_id,
            system_prompt=system_instruction or "You are a helpful AI assistant.",
        )
    elif is_agy:
        from core.ai.agy_chat import AgyChatBase
        return AgyChatBase(
            model_id=selected_model_name,
            system_prompt=system_instruction or "You are a helpful AI assistant.",
        )
    elif is_gemini:
        from core.ai.gemini.generative_ai import GoogleGenerativeAI
        _api_key_names = [n.strip() for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',') if n.strip()]
        return GoogleGenerativeAI(
            model_name=selected_model_name,
            api_key_names=_api_key_names,
            system_instruction=system_instruction,
            sleep_on_exhausted=False,
        )
    else:
        # По умолчанию - Foundry для неизвестных моделей (обратная совместимость)
        from core.ai.foundry_chat import FoundryChatBase
        return FoundryChatBase(
            model_id=selected_model_name,
            system_prompt=system_instruction or "You are a helpful AI assistant.",
        )


async def _extract_user_auth(fastapi_req: Request) -> tuple[str, str, str, dict]:
    """Извлекает идентификатор пользователя, системную инструкцию, модель и настройки из JWT/IP."""
    user_identifier = ""
    system_instruction = ""
    selected_model = ""
    settings = {}

    token = fastapi_req.cookies.get('auth_token')
    if token:
        from core.fastapi.router_auth import verify_jwt_token
        user_data = verify_jwt_token(token)
        if user_data:
            from core.user_manager import user_manager
            db_user = await asyncio.to_thread(user_manager.get_user_by_email, user_data.email)
            if db_user:
                user_identifier = str(db_user['id'])
                settings = await asyncio.to_thread(user_manager.get_user_settings, db_user['id']) or {}
                if settings.get('system_instruction'):
                    system_instruction = settings['system_instruction']
                if settings.get('model'):
                    selected_model = settings['model']

    if not user_identifier:
        client_ip = fastapi_req.client.host if fastapi_req.client else 'unknown'
        user_identifier = f"anon_{client_ip}"

    return user_identifier, system_instruction, selected_model, settings


def _get_voice_gender_rule(settings: dict) -> str:
    """Определяет гендерное правило для ответов ассистента на основе настроек голоса TTS."""
    default_voice = getattr(tts_cfg, "default_voice", "ru-RU-DmitryNeural") if tts_cfg else "ru-RU-DmitryNeural"
    tts_voice = settings.get('tts_voice', '') or default_voice
    voice_lower = tts_voice.lower()
    is_male_voice = any(name in voice_lower for name in ("dmitry", "yaraslaus", "male", "bayan", "aidar", "eugene", "georgy"))
    is_female_voice = any(name in voice_lower for name in ("svetlana", "elena", "female", "kseniya", "tanya", "aliona", "dariya"))
    if is_male_voice:
        return "ВАЖНОЕ ПРАВИЛО: Отвечай от мужского лица (например: 'Я нашел', 'Я подобрал')."
    if is_female_voice:
        return "ВАЖНОЕ ПРАВИЛО: Отвечай от женского лица (например: 'Я нашла', 'Я подобрала')."
    return ""


def _clean_chat_history(history: list[dict]) -> list[dict]:
    """Очищает историю сообщений перед передачей в модель."""
    if not history:
        return []
    _ERROR_PATTERNS = (
        '❌', 'Ошибка', 'Error', 'TypeError', 'AttributeError', 'Traceback',
        '[Ошибка]', 'Не удалось найти', 'В локальной базе ничего не найдено',
        'DEBUG MODE', 'DEBUG:', '[DEBUG'
    )
    _STATUS_PREFIXES = (
        '🔍', '🌐', '🤖', '🛠️', '🎡', '📡', 'Вызов плагина', 'Генерация', 'Проверка',
        'DEBUG MODE:', 'DEBUG:'
    )

    def _is_clean(entry: dict) -> bool:
        parts = entry.get('parts', [])
        text = ''
        if isinstance(parts, list) and len(parts) > 0:
            p = parts[0]
            text = p if isinstance(p, str) else p.get('text', '') if isinstance(p, dict) else ''
        elif isinstance(parts, str):
            text = parts
        text = (text or '').strip()
        if not text:
            return False
        if any(pfx in text for pfx in _ERROR_PATTERNS):
            return False
        if any(text.startswith(pfx) for pfx in _STATUS_PREFIXES):
            return False
        if text.startswith('{') and ('"title"' in text or '"error"' in text or '"genres"' in text):
            return False
        if 'Ответ модели: {' in text and '"title"' in text:
            return False
        return True

    def _compact_turn(entry: dict) -> dict:
        parts = entry.get('parts', [])
        text = ''
        if isinstance(parts, list) and len(parts) > 0:
            p = parts[0]
            text = p if isinstance(p, str) else p.get('text', '') if isinstance(p, dict) else ''
        elif isinstance(parts, str):
            text = parts

        if entry.get('role') in ('model', 'assistant') and len(text) > 200:
            import re
            compact = re.sub(r'<film>(.*?)</film>', r'«\1»', text, flags=re.IGNORECASE)
            compact = re.sub(r'#+\s*', '', compact)
            compact = re.sub(r'[*_`]+', '', compact)
            compact = re.sub(r'\s+', ' ', compact).strip()
            if len(compact) > 200:
                compact = compact[:197].rsplit(' ', 1)[0] + '...'
            return {'role': entry['role'], 'parts': [compact]}
        return entry

    raw_clean = [e for e in history if _is_clean(e)]
    cleaned_entries: list[dict] = []
    i = 0
    while i < len(raw_clean):
        entry = raw_clean[i]
        if entry.get('role') == 'user':
            if i + 1 < len(raw_clean) and raw_clean[i + 1].get('role') in ('model', 'assistant'):
                cleaned_entries.append(_compact_turn(entry))
                cleaned_entries.append(_compact_turn(raw_clean[i + 1]))
                i += 2
                continue
        i += 1

    return cleaned_entries[-10:]


def _build_debug_prompt(request: ChatRequest, user_context_str: str, voice_gender_rule: str) -> str:
    """Формирует текстовый дамп полного промпта для отладочного режима."""
    full_prompt_parts = []
    dynamic_parts = []
    if voice_gender_rule:
        dynamic_parts.append(voice_gender_rule)
    if user_context_str:
        dynamic_parts.append(user_context_str)
    if dynamic_parts:
        full_prompt_parts.append("── DYNAMIC CONTEXT ──\n" + "\n\n".join(dynamic_parts))

    clean_history = _clean_chat_history(request.history)
    if clean_history:
        full_prompt_parts.append("── CHAT HISTORY (последние 5) ──\n" + "\n---\n".join([
            f"{entry.get('role', 'unknown').upper()}:\n{entry.get('parts', [''])[0] if isinstance(entry.get('parts'), list) else entry.get('parts', '')}"
            for entry in clean_history[-5:]
        ]))

    full_prompt_parts.append(f"── USER MESSAGE ──\n{request.message}")
    return "\n\n".join(full_prompt_parts)




def init_router(chat_model, narrator_model, plugins: dict = {}) -> APIRouter:
    """Инициализация роутера чата с привязкой моделей (chat и narrator)."""
    if hasattr(narrator_model, 'gemini_model') and narrator_model.gemini_model:
        narrator_model.gemini_model.save_history_chat = False

    @router.get('/models')
    async def get_models(refresh: bool = False) -> dict:
        """Получение списка доступных моделей, сгруппированных по провайдеру."""
        from core.ai.model_manager import get_available_models

        gemini_models = get_available_models('gemini', force_refresh=refresh)
        
        foundry_raw = get_available_models('foundry', force_refresh=refresh)
        foundry_models = [f"foundry:{m}" if not m.startswith('foundry:') else m for m in foundry_raw]

        ollama_raw = get_available_models('ollama', force_refresh=refresh)
        ollama_models = [f"ollama:{m}" if not m.startswith('ollama:') else m for m in ollama_raw]

        agy_models = get_available_models('agy', force_refresh=refresh)

        gemini_cli_raw = get_available_models('gemini_cli', force_refresh=refresh)
        gemini_cli_models = [f"gemini_cli:{m}" if not m.startswith('gemini_cli:') else m for m in gemini_cli_raw]

        openai_raw = get_available_models('openai', force_refresh=refresh)
        openai_models = [f"openai:{m}" if not any(m.startswith(f"{p}:") for p in ('openai', 'deepseek', 'groq', 'openrouter', 'lmstudio')) else m for m in openai_raw]

        hf_raw = get_available_models('hf', force_refresh=refresh)
        hf_models = [f"hf:{m}" if not m.startswith('hf:') else m for m in hf_raw]

        onnx_raw = get_available_models('onnx', force_refresh=refresh)
        onnx_models = [f"onnx:{m}" if not m.startswith('onnx:') else m for m in onnx_raw]

        return {
            'models': {
                'gemini': gemini_models,
                'foundry': foundry_models,
                'ollama': ollama_models,
                'agy': agy_models,
                'gemini_cli': gemini_cli_models,
                'openai': openai_models,
                'hf': hf_models,
                'onnx': onnx_models,
            }
        }

    @router.post('/test-model')
    async def test_model(req: TestModelRequest) -> dict:
        """Проверочный запрос к указанной AI-модели для валидации связи (Запрос -> Ответ)."""
        start_time = time.perf_counter()
        target_model = req.model.strip()
        provider = req.provider.strip().lower()

        if provider == 'foundry' and target_model and not target_model.startswith('foundry:'):
            target_model = f"foundry:{target_model}"
        elif provider == 'ollama' and target_model and not target_model.startswith('ollama:'):
            target_model = f"ollama:{target_model}"
        elif provider == 'agy' and target_model and not target_model.startswith('agy-'):
            target_model = f"agy-{target_model}"
        elif provider in ('gemini_cli', 'gemini-cli') and target_model and not target_model.startswith('gemini_cli:'):
            target_model = f"gemini_cli:{target_model}"
        elif provider in ('openai', 'openai_compat', 'openai-compat', 'deepseek', 'groq', 'openrouter', 'lmstudio') and target_model:
            openai_prefixes = ('openai:', 'deepseek:', 'groq:', 'openrouter:', 'lmstudio:', 'local:', 'compat:')
            if not any(target_model.startswith(p) for p in openai_prefixes):
                target_model = f"{provider}:{target_model}"
        elif provider in ('hf', 'huggingface') and target_model and not target_model.startswith('hf:'):
            target_model = f"hf:{target_model}"
        elif provider == 'onnx' and target_model and not target_model.startswith('onnx:'):
            target_model = f"onnx:{target_model}"

        if not target_model:
            return {
                'status': 'error',
                'message': 'Имя модели не указано',
                'model': '',
                'provider': provider,
                'duration_ms': 0.0
            }

        test_msg = req.message.strip()
        if not test_msg:
            test_msg = "Привет! Назови свою модель и провайдера, и подтверди готовность к работе."

        try:
            model_instance = get_chat_model(target_model, system_instruction=req.system_instruction)
            response_text = ""

            if hasattr(model_instance, 'ask'):
                response_text = await model_instance.ask(test_msg)
            elif hasattr(model_instance, 'chat'):
                response_text = await model_instance.chat(test_msg)
            elif hasattr(model_instance, 'chat_stream'):
                chunks = []
                async for chunk in model_instance.chat_stream(test_msg):
                    if chunk:
                        clean_chunk = chunk.replace("[CHAT]", "").replace("[VOICE]", "")
                        if clean_chunk:
                            chunks.append(clean_chunk)
                response_text = "".join(chunks)
            else:
                raise RuntimeError(f"Модель {target_model} не поддерживает методы генерации текста")

            duration_ms = round((time.perf_counter() - start_time) * 1000, 1)
            return {
                'status': 'success',
                'response': response_text,
                'model': target_model,
                'provider': provider,
                'duration_ms': duration_ms
            }
        except Exception as exc:
            logger.error(f"[ChatRouter] Ошибка проверочного запроса к модели {target_model}: {exc}", exc_info=True)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 1)
            return {
                'status': 'error',
                'message': str(exc),
                'model': target_model,
                'provider': provider,
                'duration_ms': duration_ms
            }

    @router.post('/save-rag')
    async def save_to_rag(request: SaveRagRequest, fastapi_req: Request):
        """Ручное сохранение одобренного ответа в постоянный JSON-архив."""
        try:
            user_identifier, _, _, _ = await _extract_user_auth(fastapi_req)
            from core.rag import save_user_approved_response
            save_success = await asyncio.to_thread(
                save_user_approved_response,
                user_identifier, request.query, request.chat_text, request.voice_text
            )
            if save_success:
                return {"status": "success", "message": "Успешно сохранено для последующей компиляции RAG"}
            else:
                raise HTTPException(status_code=500, detail="Ошибка сохранения ответа")
        except Exception as e:
            logger.error("Ошибка при ручном сохранении ответа", e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post('/save-rag-instant')
    async def save_to_rag_instant(request: SaveRagRequest, fastapi_req: Request):
        """Мгновенное сохранение ответа: запись в JSON + векторизация в FAISS."""
        try:
            user_identifier, _, _, _ = await _extract_user_auth(fastapi_req)
            api_key = getattr(chat_model, 'api_key', '') or os.getenv('GEMINI_API_KEY', '')

            content_to_index = request.voice_text if request.voice_text.strip() else request.chat_text

            from core.rag import save_user_approved_response, index_user_interaction
            save_success = await asyncio.to_thread(
                save_user_approved_response,
                user_identifier, request.query, request.chat_text, request.voice_text
            )
            rag_success = await asyncio.to_thread(
                index_user_interaction, user_identifier, api_key, request.query, content_to_index
            )

            if save_success and rag_success:
                return {"status": "success", "message": "Успешно сохранено в архив и проиндексировано в RAG"}
            elif save_success:
                return {"status": "success", "message": "Сохранено в архив, но произошла ошибка при индексации в RAG"}
            else:
                raise HTTPException(status_code=500, detail="Ошибка сохранения ответа")
        except Exception as e:
            logger.error("Ошибка при мгновенном сохранении в RAG", e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post('')
    async def chat(request: ChatRequest, fastapi_req: Request):
        """Обработка чат-запроса по алгоритму RAG-First: RAG Search -> Direct Match / LLM Fallback -> Auto-Index."""
        from fastapi.responses import StreamingResponse
        import json

        async def event_generator():
            try:
                user_identifier, system_instruction, selected_model, settings = await _extract_user_auth(fastapi_req)

                api_key = getattr(chat_model, 'api_key', '') or os.getenv('GEMINI_API_KEY', '')

                # 1. RAG-First: Поиск по базе знаний
                from core.rag import get_rag_engine, index_user_interaction
                rag_engine = get_rag_engine()

                yield f"data: {json.dumps({'status': '🔍 Поиск в базе знаний (RAG)...'})}\n\n"
                decision = await rag_engine.evaluate(
                    query=request.message,
                    user_identifier=user_identifier,
                    api_key=api_key
                )

                # 2. Если найден точный ответ — мгновенный возврат (Direct RAG)
                if decision.is_direct:
                    yield f"data: {json.dumps({'status': decision.status_message or '⚡ Ответ найден в базе знаний...'})}\n\n"
                    yield f"data: {json.dumps({'text': decision.direct_text})}\n\n"
                    if decision.direct_voice:
                        yield f"data: {json.dumps({'voice': decision.direct_voice})}\n\n"
                    return

                # 3. Подготовка контекста для LLM
                voice_gender_instruction = _get_voice_gender_rule(settings)
                dynamic_context_parts = []
                if voice_gender_instruction:
                    dynamic_context_parts.append(f"[Правило]: {voice_gender_instruction}")
                if decision.context_text:
                    dynamic_context_parts.append(decision.context_text)

                user_msg_with_context = request.message
                if dynamic_context_parts:
                    user_msg_with_context = "\n\n".join(dynamic_context_parts) + "\n\n[Запрос пользователя]:\n" + request.message

                # Режим отладки (DEBUG MODE)
                if request.generation_config.get('debug_mode', False):
                    debug_text = _build_debug_prompt(request, decision.context_text, voice_gender_instruction)
                    yield f"data: {json.dumps({'status': 'DEBUG MODE: Промпт сформирован, не отправляется в модель'})}\n\n"
                    yield f"data: {json.dumps({'text': debug_text})}\n\n"
                    return

                token = fastapi_req.cookies.get('auth_token')
                from core.fastapi.router_control import get_room_id
                room_id = get_room_id(token, None)

                if request.generation_config.get('model'):
                    selected_model = request.generation_config['model']

                clean_history = _clean_chat_history(request.history)
                kwargs = {
                    'history': clean_history,
                    'room_id': room_id,
                    'model_name': selected_model,
                }
                if request.generation_config.get('search_engine'):
                    kwargs['search_engine'] = request.generation_config['search_engine']

                if selected_model:
                    active_model = get_chat_model(selected_model, None)
                    api_key = getattr(active_model, 'api_key', '') or getattr(chat_model, 'api_key', '') or api_key
                else:
                    active_model = chat_model

                yield f"data: {json.dumps({'status': 'Генерация ответа (этап 1)...'})}\n\n"

                chat_kwargs_1 = kwargs.copy()
                chat_kwargs_1.pop('room_id', '')
                chat_kwargs_1.pop('search_engine', None)
                gen_cfg_1 = request.generation_config.copy()
                gen_cfg_1['response_type'] = 'chat'
                chat_kwargs_1['generation_config'] = gen_cfg_1

                stream_generator_1 = active_model.chat_stream(user_msg_with_context, **chat_kwargs_1)

                chat_response = ""
                async for chunk in stream_generator_1:
                    if chunk:
                        c = chunk.replace("[CHAT]", "").replace("[VOICE]", "")
                        if c:
                            chat_response += c
                            yield f"data: {json.dumps({'text': c})}\n\n"

                voice_response = ""
                if chat_response:
                    yield f"data: {json.dumps({'status': 'Генерация голоса (этап 2)...'})}\n\n"

                    chat_kwargs_2 = kwargs.copy()
                    chat_kwargs_2.pop('room_id', '')
                    chat_kwargs_2.pop('search_engine', None)
                    chat_kwargs_2['history'] = []

                    gen_cfg_2 = request.generation_config.copy()
                    gen_cfg_2['response_type'] = 'voice'
                    chat_kwargs_2['generation_config'] = gen_cfg_2

                    stream_generator_2 = narrator_model.chat_stream(chat_response, **chat_kwargs_2)
                    async for chunk in stream_generator_2:
                        if chunk:
                            c = chunk.replace("[CHAT]", "").replace("[VOICE]", "")
                            if c:
                                voice_response += c
                                yield f"data: {json.dumps({'voice': c})}\n\n"

                # 4. Автоматическая фоновая индексация взаимодействия в RAG
                content_to_index = voice_response if voice_response.strip() else chat_response
                if content_to_index and api_key and user_identifier:
                    asyncio.ensure_future(asyncio.to_thread(
                        index_user_interaction, user_identifier, api_key, request.message, content_to_index
                    ))

            except Exception as ex:
                logger.error('Ошибка обработки чат-запроса', ex)
                yield f"data: {json.dumps({'error': str(ex)})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    return router
