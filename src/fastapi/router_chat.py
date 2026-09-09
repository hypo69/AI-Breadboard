# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI chat execution and dialogue management router
# =============================================================================
# Description:
#   Handles AI conversational endpoints, streaming responses across multiple providers,
#   user dialogue context retrieval, and RAG query indexing workflows.
#
# File: router_chat.py
# Project: ai-breadboard
# Package: src.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import time
import asyncio
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.logger import logger
from src.config import ai_cfg, tts_cfg
from src.ai.gemini.user_query_rag import index_user_query, search_user_context

from header import __root__

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

class CommentResponderRequest(BaseModel):
    post_title: str = ""
    post_content: str = ""
    comment_author: str = ""
    comment_content: str = ""
    parent_context: str = ""
    model: str = ""
    provider: str = ""
    system_instruction: str = ""

_active_chat_models: dict[str, object] = {}

def _get_default_system_instruction() -> str:
    """Load default system instruction for chat assistant."""
    prompt_file = __root__ / 'prompts' / 'chat' / 'system_instruction.md'
    if prompt_file.exists():
        try:
            content = prompt_file.read_text(encoding='utf-8', errors='replace').strip()
            if content:
                return content
        except Exception as e:
            logger.debug(f"[router_chat] Could not read default prompt file: {e}")
    return "Вы — интеллектуальный ассистент платформы AI Breadboard с доступом к Google Workspace и RAG-базе знаний."

def get_chat_model(selected_model_name: str, system_instruction: str = "", user_id: str = ""):
    """Dynamically construct or retrieve cached AI model instance."""
    eff_sys_prompt = system_instruction.strip() if system_instruction and system_instruction.strip() else _get_default_system_instruction()
    cache_key = f"{user_id}:{selected_model_name}" if user_id else selected_model_name
    if cache_key in _active_chat_models:
        instance = _active_chat_models[cache_key]
        if eff_sys_prompt and hasattr(instance, 'system_instruction'):
            if getattr(instance, 'system_instruction', None) != eff_sys_prompt:
                instance.system_instruction = eff_sys_prompt
        return instance

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
        from src.ai.gemini_cli_chat import GeminiCliChatBase
        inst = GeminiCliChatBase(
            model_id=selected_model_name,
            system_prompt=eff_sys_prompt,
        )
    elif is_foundry:
        model_id = selected_model_name.split(':', 1)[-1]
        from src.ai.foundry_chat import FoundryChatBase
        inst = FoundryChatBase(
            model_id=model_id,
            system_prompt=eff_sys_prompt,
        )
    elif is_ollama:
        model_id = selected_model_name.split(':', 1)[-1]
        from src.ai.ollama_chat import OllamaChatBase
        ollama_url = ai_cfg.ollama_base_url if ai_cfg else 'http://localhost:11434'
        inst = OllamaChatBase(
            model_id=model_id,
            system_prompt=eff_sys_prompt,
            api_url=ollama_url
        )
    elif is_hf:
        model_id = selected_model_name.split(':', 1)[-1].lstrip(':')
        from src.ai.hf_chat import HFChatBase
        inst = HFChatBase(
            model_id=model_id,
            system_prompt=eff_sys_prompt,
        )
    elif is_onnx:
        model_id = selected_model_name.split(':', 1)[-1].lstrip(':')
        from src.ai.onnx_chat import ONNXChatBase
        inst = ONNXChatBase(
            model_id=model_id,
            system_prompt=eff_sys_prompt,
        )
    elif is_openai:
        prov_part, model_part = selected_model_name.split(':', 1)
        model_id = model_part.lstrip(':')
        prov_name = prov_part.lower().rstrip(':')
        if prov_name == 'compat':
            prov_name = 'openai'
        from src.ai.openai_compat_chat import OpenAICompatChat
        inst = OpenAICompatChat.create_for_provider(
            provider_name=prov_name,
            model_id=model_id,
            system_prompt=eff_sys_prompt,
        )
    elif is_agy:
        from src.ai.agy_chat import AgyChatBase
        inst = AgyChatBase(
            model_id=selected_model_name,
            system_prompt=eff_sys_prompt,
        )
    elif is_gemini:
        from src.ai.gemini_chat import GeminiChatBase
        inst = GeminiChatBase(
            model_id=selected_model_name,
            system_prompt=eff_sys_prompt,
        )
    else:
        from src.ai.foundry_chat import FoundryChatBase
        inst = FoundryChatBase(
            model_id=selected_model_name,
            system_prompt=eff_sys_prompt,
        )

    _active_chat_models[cache_key] = inst
    return inst

async def _extract_user_auth(fastapi_req: Request) -> tuple[str, str, str, dict]:
    """Извлекает идентификатор пользователя, системную инструкцию, модель и настройки из JWT/IP."""
    user_identifier = ""
    system_instruction = ""
    selected_model = ""
    settings = {}

    from src.fastapi.router_auth import get_current_user_data
    user_data = get_current_user_data(fastapi_req)

    from src.user_manager import user_manager
    db_user = None
    if user_data.id:
        db_user = await asyncio.to_thread(user_manager.get_user_by_id, user_data.id)
    if not db_user and user_data.email:
        db_user = await asyncio.to_thread(user_manager.get_user_by_email, user_data.email)

    if db_user:
        user_identifier = str(db_user.get('id', 1))
        settings = await asyncio.to_thread(user_manager.get_user_settings, db_user.get('id', 1)) or {}
        if settings.get('system_instruction'):
            system_instruction = settings['system_instruction']
        if settings.get('model'):
            selected_model = settings['model']
    else:
        user_identifier = str(user_data.id or 1)

    if not system_instruction:
        system_instruction = _get_default_system_instruction()

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
        '❌', 'Error', 'Error', 'TypeError', 'AttributeError', 'Traceback',
        '[Error]', 'Не удалось найти', 'В локальной базе ничего не найдено',
        'DEBUG MODE', 'DEBUG:', '[DEBUG'
    )
    _STATUS_PREFIXES = (
        '🔍', '🌐', '🤖', '🛠️', '🎡', '📡', 'Вызов плагина', 'Генерация', 'Check',
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
    """Initialization роутера чата с привязкой моделей (chat и narrator)."""
    if hasattr(narrator_model, 'gemini_model') and narrator_model.gemini_model:
        narrator_model.gemini_model.save_history_chat = False

    @router.get('/models')
    async def get_models(fastapi_req: Request, refresh: bool = False, include_unsupported: bool = False) -> dict:
        """Получение списка доступных моделей, сгруппированных по провайдеру."""
        if fastapi_req is not None:
            from src.fastapi.router_auth import get_current_user_data
            get_current_user_data(fastapi_req)
        from src.ai.model_manager import get_available_models, load_unsupported_models

        gemini_models = get_available_models('gemini', force_refresh=refresh, include_unsupported=include_unsupported)
        
        foundry_raw = get_available_models('foundry', force_refresh=refresh, include_unsupported=include_unsupported)
        foundry_models = [f"foundry:{m}" if not m.startswith('foundry:') else m for m in foundry_raw]

        ollama_raw = get_available_models('ollama', force_refresh=refresh, include_unsupported=include_unsupported)
        ollama_models = [f"ollama:{m}" if not m.startswith('ollama:') else m for m in ollama_raw]

        agy_models = get_available_models('agy', force_refresh=refresh, include_unsupported=include_unsupported)

        gemini_cli_raw = get_available_models('gemini_cli', force_refresh=refresh, include_unsupported=include_unsupported)
        gemini_cli_models = [f"gemini_cli:{m}" if not m.startswith('gemini_cli:') else m for m in gemini_cli_raw]

        openai_raw = get_available_models('openai', force_refresh=refresh, include_unsupported=include_unsupported)
        openai_models = [f"openai:{m}" if not any(m.startswith(f"{p}:") for p in ('openai', 'deepseek', 'groq', 'openrouter', 'lmstudio')) else m for m in openai_raw]

        hf_raw = get_available_models('hf', force_refresh=refresh, include_unsupported=include_unsupported)
        hf_models = [f"hf:{m}" if not m.startswith('hf:') else m for m in hf_raw]

        onnx_raw = get_available_models('onnx', force_refresh=refresh, include_unsupported=include_unsupported)
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
            },
            'unsupported_models': {
                'gemini': list(load_unsupported_models('gemini')),
                'foundry': list(load_unsupported_models('foundry')),
                'ollama': list(load_unsupported_models('ollama')),
                'agy': list(load_unsupported_models('agy')),
                'gemini_cli': list(load_unsupported_models('gemini_cli')),
                'openai': list(load_unsupported_models('openai')),
                'hf': list(load_unsupported_models('hf')),
                'onnx': list(load_unsupported_models('onnx')),
            }
        }

    @router.post('/test-model')
    async def test_model(req: TestModelRequest, fastapi_req: Request) -> dict:
        """Проверочный запрос к указанной AI-модели для валидации связи (Запрос -> Ответ)."""
        if fastapi_req is not None:
            from src.fastapi.router_auth import get_current_user_data
            get_current_user_data(fastapi_req)
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
            logger.error(f"[ChatRouter] Error проверочного запроса к модели {target_model}: {exc}", exc_info=True)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 1)
            return {
                'status': 'error',
                'message': str(exc),
                'model': target_model,
                'provider': provider,
                'duration_ms': duration_ms
            }

    @router.post('/comment-responder')
    async def respond_to_comment(req: CommentResponderRequest, fastapi_req: Request) -> dict:
        """Endpoint for WordPress AI Responder plugin to generate context-aware replies to user comments."""
        if fastapi_req is not None:
            from src.fastapi.router_auth import get_current_user_data
            get_current_user_data(fastapi_req)

        start_time = time.perf_counter()
        target_model = req.model.strip() or 'gemini-2.5-flash'
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

        prompt_instructions = [
            "You are an AI assistant responding to user comments on a website/blog (davidka.net).",
            "Generate a polite, helpful, engaging, and concise reply in the same language as the comment (usually Russian).",
            "Do not include unnecessary greetings or preamble if inappropriate; be natural, courteous, and accurate.",
        ]
        if req.system_instruction.strip():
            prompt_instructions.append(f"Custom Persona & Instructions:\n{req.system_instruction.strip()}")

        context_blocks = []
        if req.post_title.strip():
            context_blocks.append(f"Post Title: {req.post_title.strip()}")
        if req.post_content.strip():
            snippet = req.post_content.strip()[:3000]
            context_blocks.append(f"Post Content Excerpt:\n{snippet}")
        if req.parent_context.strip():
            context_blocks.append(f"Comment Thread History:\n{req.parent_context.strip()}")
        if req.comment_author.strip():
            context_blocks.append(f"Comment Author: {req.comment_author.strip()}")
        context_blocks.append(f"User Comment to Reply To:\n{req.comment_content.strip()}")

        full_prompt = "\n\n".join(prompt_instructions) + "\n\n── CONTEXT & COMMENT ──\n" + "\n---\n".join(context_blocks)

        try:
            model_instance = get_chat_model(target_model, system_instruction=req.system_instruction)
            response_text = ""
            if hasattr(model_instance, 'ask'):
                response_text = await model_instance.ask(full_prompt)
            elif hasattr(model_instance, 'chat'):
                response_text = await model_instance.chat(full_prompt)
            elif hasattr(model_instance, 'chat_stream'):
                chunks = []
                async for chunk in model_instance.chat_stream(full_prompt):
                    if chunk:
                        clean_chunk = chunk.replace("[CHAT]", "").replace("[VOICE]", "")
                        if clean_chunk:
                            chunks.append(clean_chunk)
                response_text = "".join(chunks)
            else:
                raise RuntimeError(f"Model {target_model} does not support generation methods")

            duration_ms = round((time.perf_counter() - start_time) * 1000, 1)
            return {
                'status': 'success',
                'reply': response_text.strip(),
                'model': target_model,
                'provider': provider,
                'duration_ms': duration_ms
            }
        except Exception as exc:
            logger.error(f"[ChatRouter] Error generating comment reply: {exc}", exc_info=True)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 1)
            return {
                'status': 'error',
                'message': str(exc),
                'model': target_model,
                'provider': provider,
                'duration_ms': duration_ms
            }

    @router.post('/save-rag')
    async def save_to_rag(rag_req: SaveRagRequest, request: Request):
        """Ручное сохранение одобренного ответа в постоянный JSON-архив."""
        try:
            user_identifier, _, _, _ = await _extract_user_auth(request)
            from src.rag import save_user_approved_response
            save_success = await asyncio.to_thread(
                save_user_approved_response,
                user_identifier, rag_req.query, rag_req.chat_text, rag_req.voice_text
            )
            if save_success:
                return {"status": "success", "message": "Successfully сохранено для последующей компиляции RAG"}
            else:
                raise HTTPException(status_code=500, detail="Error сохранения ответа")
        except Exception as e:
            logger.error("Error при ручном сохранении ответа", e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post('/save-rag-instant')
    async def save_to_rag_instant(rag_req: SaveRagRequest, request: Request):
        """Мгновенное сохранение ответа: запись в JSON + векторизация в FAISS."""
        try:
            user_identifier, _, _, _ = await _extract_user_auth(request)
            api_key = getattr(chat_model, 'api_key', '') or os.getenv('GEMINI_API_KEY', '')

            content_to_index = rag_req.voice_text if rag_req.voice_text.strip() else rag_req.chat_text

            from src.rag import save_user_approved_response, index_user_interaction
            save_success = await asyncio.to_thread(
                save_user_approved_response,
                user_identifier, rag_req.query, rag_req.chat_text, rag_req.voice_text
            )
            rag_success = await asyncio.to_thread(
                index_user_interaction, user_identifier, api_key, rag_req.query, content_to_index
            )

            if save_success and rag_success:
                return {"status": "success", "message": "Successfully сохранено в архив и проиндексировано в RAG"}
            elif save_success:
                return {"status": "success", "message": "Сохранено в архив, но произошла Error при индексации в RAG"}
            else:
                raise HTTPException(status_code=500, detail="Error сохранения ответа")
        except Exception as e:
            logger.error("Error при мгновенном сохранении в RAG", e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post('')
    async def chat(chat_req: ChatRequest, request: Request):
        """Обработка чат-запроса по алгоритму RAG-First: RAG Search -> Direct Match / LLM Fallback -> Auto-Index."""
        from fastapi.responses import StreamingResponse
        import json

        async def event_generator():
            try:
                user_identifier, system_instruction, selected_model, settings = await _extract_user_auth(request)

                api_key = getattr(chat_model, 'api_key', '') or os.getenv('GEMINI_API_KEY', '')

                # 1. RAG-First: Поиск по базе знаний (при включенном RAG)
                rag_enabled_config = chat_req.generation_config.get('rag_enabled')
                if rag_enabled_config is not None:
                    is_rag_active = bool(rag_enabled_config)
                else:
                    is_rag_active = bool(settings.get('rag_enabled', 1))

                context_text = ""
                if is_rag_active:
                    from src.rag import get_rag_engine
                    rag_engine = get_rag_engine()

                    top_k = int(chat_req.generation_config.get('top_k', 3))
                    threshold = float(chat_req.generation_config.get('min_score', chat_req.generation_config.get('threshold', 0.45)))

                    yield f"data: {json.dumps({'status': '🔍 Поиск в базе знаний (RAG)...'})}\n\n"
                    decision = await rag_engine.evaluate(
                        query=chat_req.message,
                        user_identifier=user_identifier,
                        api_key=api_key,
                        threshold=threshold,
                        top_k=top_k
                    )

                    # 2. Если найден точный ответ — мгновенный возврат (Direct RAG)
                    if decision.is_direct:
                        yield f"data: {json.dumps({'status': decision.status_message or '⚡ Ответ найден в базе знаний...'})}\n\n"
                        yield f"data: {json.dumps({'text': decision.direct_text})}\n\n"
                        if decision.direct_voice:
                            yield f"data: {json.dumps({'voice': decision.direct_voice})}\n\n"
                        return
                    context_text = decision.context_text

                # 3. Подготовка контекста для LLM
                voice_gender_instruction = _get_voice_gender_rule(settings)
                dynamic_context_parts = []
                if voice_gender_instruction:
                    dynamic_context_parts.append(f"[Правило]: {voice_gender_instruction}")
                if context_text:
                    dynamic_context_parts.append(context_text)

                user_msg_with_context = chat_req.message
                if dynamic_context_parts:
                    user_msg_with_context = "\n\n".join(dynamic_context_parts) + "\n\n[Запрос пользователя]:\n" + chat_req.message

                # Режим отладки (DEBUG MODE)
                if chat_req.generation_config.get('debug_mode', False):
                    debug_text = _build_debug_prompt(chat_req, context_text, voice_gender_instruction)
                    yield f"data: {json.dumps({'status': 'DEBUG MODE: Промпт сформирован, не отправляется в модель'})}\n\n"
                    yield f"data: {json.dumps({'text': debug_text})}\n\n"
                    return

                token = request.cookies.get('auth_token')
                from src.fastapi.router_control import get_room_id
                room_id = get_room_id(token, None)

                if chat_req.generation_config.get('model'):
                    selected_model = chat_req.generation_config['model']

                clean_history = _clean_chat_history(chat_req.history)
                kwargs = {
                    'history': clean_history,
                    'room_id': room_id,
                    'model_name': selected_model,
                }
                if chat_req.generation_config.get('search_engine'):
                    kwargs['search_engine'] = chat_req.generation_config['search_engine']

                if selected_model:
                    active_model = get_chat_model(selected_model, system_instruction or "", user_id=user_identifier)
                    api_key = getattr(active_model, 'api_key', '') or getattr(chat_model, 'api_key', '') or api_key
                else:
                    active_model = chat_model

                yield f"data: {json.dumps({'status': 'Генерация ответа (этап 1)...'})}\n\n"

                chat_kwargs_1 = kwargs.copy()
                chat_kwargs_1.pop('room_id', '')
                chat_kwargs_1.pop('search_engine', None)
                gen_cfg_1 = chat_req.generation_config.copy()
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

                output_mode = chat_req.generation_config.get('output_mode', 'text_and_voice')
                need_voice = output_mode in ('voice_only', 'text_and_voice', 'voice') or bool(chat_req.generation_config.get('tts_enabled', False))

                voice_response = ""
                if chat_response and need_voice:
                    yield f"data: {json.dumps({'status': 'Генерация голоса (этап 2)...'})}\n\n"

                    chat_kwargs_2 = kwargs.copy()
                    chat_kwargs_2.pop('room_id', '')
                    chat_kwargs_2.pop('search_engine', None)
                    chat_kwargs_2['history'] = []

                    gen_cfg_2 = chat_req.generation_config.copy()
                    gen_cfg_2['response_type'] = 'voice'
                    chat_kwargs_2['generation_config'] = gen_cfg_2

                    stream_generator_2 = narrator_model.chat_stream(chat_response, **chat_kwargs_2)
                    async for chunk in stream_generator_2:
                        if chunk:
                            c = chunk.replace("[CHAT]", "").replace("[VOICE]", "")
                            if c:
                                voice_response += c
                                yield f"data: {json.dumps({'voice': c})}\n\n"

                # 4. Автоматическая фоновая индексация взаимодействия в RAG (только при включенном RAG)
                content_to_index = voice_response if voice_response.strip() else chat_response
                if is_rag_active and content_to_index and api_key and user_identifier:
                    from src.rag import index_user_interaction
                    asyncio.ensure_future(asyncio.to_thread(
                        index_user_interaction, user_identifier, api_key, chat_req.message, content_to_index
                    ))

            except Exception as ex:
                logger.error('Error обработки чат-запроса', ex)
                yield f"data: {json.dumps({'error': str(ex)})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    return router
