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
# Package: src.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import time
import asyncio
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from logger import logger
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
    rag_name: str = Field(
        default="",
        description="Имя целевой RAG базы данных (например: 'coder', 'secretary', 'technician', 'admin', 'default').",
    )
    role: str = Field(
        default="",
        description="Роль пользователя или ассистента для автоматического выбора RAG базы данных.",
    )

class TestModelRequest(BaseModel):
    """Модель данных для проверочного запроса к AI-модели.

    Введите вручную имя модели и провайдера, иначе будет использована настройка по умолчанию.
    """
    __test__ = False

    model: str = Field(
        default="",
        description="Имя модели. Введите вручную имя модели и провайдера, иначе будет использована настройка по умолчанию.",
    )
    provider: str = Field(
        default="",
        description="Имя провайдера (gemini, agy, foundry, ollama, openai, hf, onnx, gemini_cli). Введите вручную имя модели и провайдера, иначе будет использована настройка по умолчанию.",
    )
    message: str = Field(
        default="Привет! Назови свою модель и провайдера, и подтверди готовность к работе.",
        description="Текст тестового сообщения для валидации связи.",
    )
    system_instruction: str = Field(
        default="",
        description="Опциональная системная инструкция для тестируемой модели.",
    )


class ModelInstructionPayload(BaseModel):
    """Модель данных для обновления системной инструкции AI-модели."""
    instruction: str = Field(
        default="",
        description="Текст системной инструкции для AI-модели.",
    )
    system_instruction: str = Field(
        default="",
        description="Алиас для текста системной инструкции.",
    )
    content: str = Field(
        default="",
        description="Алиас для текста системной инструкции.",
    )
    model: str = Field(
        default="",
        description="Опциональное имя модели.",
    )
    save_to_disk: bool = Field(
        default=False,
        description="Флаг сохранения системной инструкции в файл prompts/chat/system_instruction.md.",
    )

ModelInstructionRequest = ModelInstructionPayload


class SetModelPayload(BaseModel):
    """Модель данных для установки активной AI-модели."""
    model: str = Field(
        ...,
        description="Имя модели для установки (например: gemini-2.5-flash, ollama:llama3.1, agy-gemini-3.6-flash).",
    )
    provider: str = Field(
        default="",
        description="Опциональное имя провайдера (gemini, agy, foundry, ollama, openai, hf, onnx, gemini_cli).",
    )


class ChatSessionPayload(BaseModel):
    id: str = ""
    userId: str = ""
    title: str = "New Chat"
    isCustomTitle: bool = False
    createdAt: int = 0
    updatedAt: int = 0
    messages: list[dict] = []
    chatHistory: list[dict] = []

class SyncSessionsRequest(BaseModel):
    sessions: list[dict] = []

from src.api import chat_sessions_db

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
        ollama_url = getattr(ai_cfg, 'ollama_base_url', None) if ai_cfg else None
        if not ollama_url and ai_cfg and hasattr(ai_cfg, 'providers'):
            providers = getattr(ai_cfg, 'providers', {})
            ollama_cfg = providers.get('ollama', {}) if isinstance(providers, dict) else getattr(providers, 'ollama', {})
            if isinstance(ollama_cfg, dict):
                ollama_url = ollama_cfg.get('base_url') or ollama_cfg.get('ollama_base_url')
            else:
                ollama_url = getattr(ollama_cfg, 'base_url', None) or getattr(ollama_cfg, 'ollama_base_url', None)
        if not ollama_url:
            ollama_url = 'http://localhost:11434'
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
    """Извлекает идентификатор пользователя, системную инструкцию, модель и настройки из JWT/IP без обязательной авторизации."""
    user_identifier = "1"
    system_instruction = ""
    selected_model = ""
    settings = {}

    try:
        from src.api.router_auth import get_current_user_optional
        user_data = get_current_user_optional(fastapi_req) if fastapi_req is not None else None

        from src.user_manager import user_manager
        db_user = None
        if user_data:
            if getattr(user_data, 'id', None):
                db_user = await asyncio.to_thread(user_manager.get_user_by_id, user_data.id)
            if not db_user and getattr(user_data, 'email', None):
                db_user = await asyncio.to_thread(user_manager.get_user_by_email, user_data.email)

        if not db_user:
            db_user = await asyncio.to_thread(user_manager.get_user_by_id, 1)

        if db_user:
            user_identifier = str(db_user.get('id', 1))
            settings = await asyncio.to_thread(user_manager.get_user_settings, db_user.get('id', 1)) or {}
            if settings.get('system_instruction'):
                system_instruction = settings['system_instruction']
            if settings.get('model'):
                selected_model = settings['model']
    except Exception as e:
        logger.debug(f"[router_chat] Failed to extract optional user auth: {e}")

    if not system_instruction:
        system_instruction = _get_default_system_instruction()

    return user_identifier, system_instruction, selected_model, settings

def _resolve_target_rag_name(rag_req: SaveRagRequest, settings: dict) -> str:
    """Определяет наименование целевой RAG базы данных по запросу и настройкам пользователя.

    :param rag_req: Запрос с опциональными rag_name или role.
    :param settings: Словарь настроек текущего пользователя.
    :returns: Строковое имя целевой RAG базы данных.
    """
    if rag_req and rag_req.rag_name and rag_req.rag_name.strip():
        return rag_req.rag_name.strip()
    if rag_req and rag_req.role and rag_req.role.strip():
        return rag_req.role.strip()
    if settings:
        if settings.get('active_rag') and str(settings['active_rag']).strip():
            return str(settings['active_rag']).strip()
        if settings.get('role') and str(settings['role']).strip():
            return str(settings['role']).strip()
    return "default"

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

def _get_available_providers_and_models(profile: str = "") -> dict:
    """Получает список всех доступных провайдеров и их моделей из конфигурации.

    :param profile: Опциональное имя профиля конфигурации.
    :returns: Словарь {provider_name: {"model": model_name, "enabled": bool}, ...}
    """
    import json
    from pathlib import Path

    cfg_env = os.getenv("AIBREADBOARD_CONFIG") or os.getenv("CONFIG_FILE")
    active_path = None
    if profile in ("tc", "test-computer", "test_computer", "apps_tc"):
        for candidate in [__root__ / "start_scenarios_config" / "tc.json", __root__ / "config" / "tc.json", __root__ / "config_tc.json", __root__ / "tc.json"]:
            if candidate.exists():
                active_path = candidate
                break
    elif cfg_env:
        p = Path(cfg_env)
        active_path = p if p.is_absolute() else (__root__ / cfg_env)

    if not active_path or not active_path.exists():
        for candidate in [__root__ / "start_scenarios_config" / "tc.json", __root__ / "config" / "tc.json", __root__ / "config_tc.json", __root__ / "tc.json"]:
            if candidate.exists() and not (__root__ / "config.json").exists() and not (__root__ / "config" / "dashboard.json").exists():
                active_path = candidate
                break
        if not active_path or not active_path.exists():
            active_path = (__root__ / "start_scenarios_config" / "dashboard.json") if (__root__ / "start_scenarios_config" / "dashboard.json").exists() else ((__root__ / "config" / "dashboard.json") if (__root__ / "config" / "dashboard.json").exists() else (__root__ / "config.json"))

    providers_list = {}

    if active_path and active_path.exists():
        try:
            with open(active_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                ai_sec = data.get("ai", {})
                
                # New format: providers.<prov>.enabled + providers.<prov>.model
                if isinstance(ai_sec.get("providers"), dict):
                    providers = ai_sec.get("providers", {})
                    for prov_key, prov_cfg in providers.items():
                        if isinstance(prov_cfg, dict):
                            model = prov_cfg.get("model")
                            enabled = prov_cfg.get("enabled", False)
                            if model:  # Добавляем только если есть модель
                                providers_list[prov_key] = {
                                    "model": model,
                                    "enabled": enabled if isinstance(enabled, bool) else (str(enabled).lower() == "true")
                                }
                # Legacy format: use_agy, use_gemini, use_ollama, use_foundry
                else:
                    if ai_sec.get("use_agy"):
                        providers_list["agy"] = {
                            "model": ai_sec.get("agy_model_id") or ai_sec.get("model") or "",
                            "enabled": True
                        }
                    if ai_sec.get("use_gemini"):
                        providers_list["gemini"] = {
                            "model": ai_sec.get("gemini_model_id") or ai_sec.get("model") or "",
                            "enabled": True
                        }
                    if ai_sec.get("use_ollama"):
                        providers_list["ollama"] = {
                            "model": ai_sec.get("ollama_model_id") or ai_sec.get("model") or "",
                            "enabled": True
                        }
                    if ai_sec.get("use_foundry"):
                        providers_list["foundry"] = {
                            "model": ai_sec.get("foundry_model_id") or ai_sec.get("model") or "",
                            "enabled": True
                        }
        except Exception as e:
            logger.debug(f"[router_chat] Could not read active config {active_path}: {e}")

    return providers_list


def _resolve_default_model_and_provider(profile: str = "") -> tuple[str, str, str]:
    """Определяет провайдер и имя модели по умолчанию из активного конфигурационного файла.

    :param profile: Опциональное имя профиля конфигурации.
    :returns: Кортеж (provider, model_name, config_file).
    """
    import json
    from pathlib import Path

    cfg_env = os.getenv("AIBREADBOARD_CONFIG") or os.getenv("CONFIG_FILE")
    active_path = None
    if profile in ("tc", "test-computer", "test_computer", "apps_tc"):
        for candidate in [__root__ / "start_scenarios_config" / "tc.json", __root__ / "config" / "tc.json", __root__ / "config_tc.json", __root__ / "tc.json"]:
            if candidate.exists():
                active_path = candidate
                break
    elif cfg_env:
        p = Path(cfg_env)
        active_path = p if p.is_absolute() else (__root__ / cfg_env)

    if not active_path or not active_path.exists():
        for candidate in [__root__ / "start_scenarios_config" / "tc.json", __root__ / "config" / "tc.json", __root__ / "config_tc.json", __root__ / "tc.json"]:
            if candidate.exists() and not (__root__ / "config.json").exists() and not (__root__ / "config" / "dashboard.json").exists():
                active_path = candidate
                break
        if not active_path or not active_path.exists():
            active_path = (__root__ / "start_scenarios_config" / "dashboard.json") if (__root__ / "start_scenarios_config" / "dashboard.json").exists() else ((__root__ / "config" / "dashboard.json") if (__root__ / "config" / "dashboard.json").exists() else (__root__ / "config.json"))

    provider = "GEMINI"
    model_name = "gemini-2.5-flash"
    config_file = active_path.name if active_path else "config.json"

    if active_path and active_path.exists():
        try:
            with open(active_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                ai_sec = data.get("ai", {})
                # Format in tc.json or explicit provider: ai.provider = "gemini_cli", ai.gemini_cli.model = "..."
                if ai_sec.get("provider"):
                    prov_key = str(ai_sec.get("provider")).lower()
                    provider = prov_key.upper()
                    if isinstance(ai_sec.get(prov_key), dict) and ai_sec[prov_key].get("model"):
                        model_name = ai_sec[prov_key].get("model")
                    elif isinstance(ai_sec.get("providers"), dict) and isinstance(ai_sec["providers"].get(prov_key), dict) and ai_sec["providers"][prov_key].get("model"):
                        model_name = ai_sec["providers"][prov_key].get("model")
                    elif ai_sec.get(f"{prov_key}_model_id"):
                        model_name = ai_sec.get(f"{prov_key}_model_id")
                    elif ai_sec.get("model"):
                        model_name = ai_sec.get("model")
                # New format: providers.<prov>.enabled + providers.<prov>.model
                # Используем первый enabled провайдер как дефолтный
                elif isinstance(ai_sec.get("providers"), dict):
                    providers = ai_sec.get("providers", {})
                    for prov_key, prov_cfg in providers.items():
                        if isinstance(prov_cfg, dict) and prov_cfg.get("enabled"):
                            provider = prov_key.upper()
                            model_name = prov_cfg.get("model") or model_name
                            break
                # Legacy format: use_agy, use_gemini, use_ollama, use_foundry
                elif ai_sec.get("use_agy"):
                    provider = "AGY"
                    model_name = ai_sec.get("agy_model_id") or ai_sec.get("model") or "gemini-3.6-flash"
                elif ai_sec.get("use_gemini"):
                    provider = "GEMINI"
                    model_name = ai_sec.get("gemini_model_id") or ai_sec.get("model") or "gemini-2.5-flash"
                elif ai_sec.get("use_ollama"):
                    provider = "OLLAMA"
                    model_name = ai_sec.get("ollama_model_id") or ai_sec.get("model") or "llama3.1"
                elif ai_sec.get("use_foundry"):
                    provider = "FOUNDRY"
                    model_name = ai_sec.get("foundry_model_id") or ai_sec.get("model") or "local"
                elif ai_sec.get("model"):
                    model_name = ai_sec.get("model")
                    provider = "AI"
        except Exception as e:
            logger.debug(f"[router_chat] Could not read active config {active_path}: {e}")

    return provider, model_name, config_file

async def _get_effective_model_and_provider(fastapi_req: Request = None, profile: str = "") -> tuple[str, str, str]:
    """Получает эффективный провайдер и модель с учетом активной конфигурации и настроек текущего пользователя."""
    provider, model_name, config_file = _resolve_default_model_and_provider(profile=profile)
    if fastapi_req is not None:
        try:
            _, _, user_selected_model, _ = await _extract_user_auth(fastapi_req)
            if user_selected_model:
                if ':' in user_selected_model:
                    p_prefix, m_suffix = user_selected_model.split(':', 1)
                    provider = p_prefix.upper()
                    model_name = m_suffix
                elif user_selected_model.startswith('agy-'):
                    provider = "AGY"
                    model_name = user_selected_model
                elif 'gemini' in user_selected_model.lower():
                    provider = "GEMINI"
                    model_name = user_selected_model
                else:
                    model_name = user_selected_model
        except Exception:
            pass
    return provider, model_name, config_file

def _normalize_model_and_provider(target_model: str = "", target_provider: str = "") -> tuple[str, str]:
    """Нормализует имя модели и провайдера, разрешая значения по умолчанию и форматируя префиксы."""
    model = (target_model or "").strip()
    provider = (target_provider or "").strip().lower()

    if not provider:
        if model.startswith('foundry:'):
            provider = 'foundry'
        elif model.startswith('ollama:'):
            provider = 'ollama'
        elif model.startswith('agy-'):
            provider = 'agy'
        elif model.startswith('gemini_cli:'):
            provider = 'gemini_cli'
        elif model.startswith('hf:') or model.startswith('hf::'):
            provider = 'hf'
        elif model.startswith('onnx:') or model.startswith('onnx::'):
            provider = 'onnx'
        elif any(model.startswith(p) for p in ('openai:', 'deepseek:', 'groq:', 'openrouter:', 'lmstudio:', 'local:', 'compat:')):
            provider = 'openai'
        elif 'gemini' in model.lower():
            provider = 'gemini'
        else:
            provider = 'gemini'

    if not model:
        if provider == 'gemini':
            model = 'gemini-2.5-flash'
        elif provider == 'agy':
            model = 'gemini-3.6-flash'
        elif provider == 'ollama':
            model = 'llama3.1'
        elif provider == 'foundry':
            model = 'local'
        elif provider in ('gemini_cli', 'gemini-cli'):
            model = 'gemini-3-flash-preview'
        elif provider in ('openai', 'openai_compat', 'openai-compat', 'deepseek', 'groq', 'openrouter', 'lmstudio'):
            model = 'gpt-4o-mini'
        elif provider in ('hf', 'huggingface'):
            model = 'microsoft/Phi-3-mini-4k-instruct'
        elif provider == 'onnx':
            model = 'cpu-int4-rt'
        else:
            model = 'gemini-2.5-flash'

    if provider == 'foundry' and not model.startswith('foundry:'):
        model = f"foundry:{model}"
    elif provider == 'ollama' and not model.startswith('ollama:'):
        model = f"ollama:{model}"
    elif provider == 'agy' and not model.startswith('agy-'):
        model = f"agy-{model}"
    elif provider in ('gemini_cli', 'gemini-cli') and not model.startswith('gemini_cli:'):
        model = f"gemini_cli:{model}"
    elif provider in ('openai', 'openai_compat', 'openai-compat', 'deepseek', 'groq', 'openrouter', 'lmstudio'):
        openai_prefixes = ('openai:', 'deepseek:', 'groq:', 'openrouter:', 'lmstudio:', 'local:', 'compat:')
        if not any(model.startswith(p) for p in openai_prefixes):
            model = f"{provider}:{model}"
    elif provider in ('hf', 'huggingface') and not model.startswith('hf:'):
        model = f"hf:{model}"
    elif provider == 'onnx' and not model.startswith('onnx:'):
        model = f"onnx:{model}"

    return model, provider.upper()

def init_router(chat_model, narrator_model, plugins: dict = {}) -> APIRouter:
    """Initialization роутера чата с привязкой моделей (chat и narrator)."""
    if hasattr(narrator_model, 'gemini_model') and narrator_model.gemini_model:
        narrator_model.gemini_model.save_history_chat = False

    @router.get('/models')
    async def get_models(fastapi_req: Request, refresh: bool = False, include_unsupported: bool = False) -> dict:
        """Получение списка доступных моделей, сгруппированных по провайдеру."""
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

    @router.get('/available-models')
    async def get_available_models_endpoint(fastapi_req: Request, profile: str = "") -> dict:
        """Получение списка всех доступных провайдеров и их моделей из конфигурации."""
        try:
            providers_list = _get_available_providers_and_models(profile=profile)
            return {
                "status": "ok",
                "providers": providers_list,
            }
        except Exception as e:
            logger.error(f"[router_chat] Failed to get available models: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get('/active-model')
    async def get_active_model_endpoint(fastapi_req: Request, profile: str = "") -> dict:
        """Получение текущей активной модели и провайдера ИИ на основе профиля и пользовательских настроек."""
        provider, model_name, config_file = await _get_effective_model_and_provider(fastapi_req, profile=profile)
        return {
            "status": "ok",
            "provider": provider,
            "model": model_name,
            "display": f"{provider}: {model_name}",
            "config_file": config_file,
        }

    @router.post('/set-active-model')
    async def set_active_model_endpoint(req: SetModelPayload, fastapi_req: Request) -> dict:
        """Установка активной модели для текущего пользователя и сессии."""
        try:
            target_model = req.model.strip()
            if not target_model:
                raise HTTPException(status_code=400, detail="Имя модели не может быть пустым")

            normalized_model, provider = _normalize_model_and_provider(target_model, req.provider)
            user_identifier, _, _, _ = await _extract_user_auth(fastapi_req)

            try:
                from src.user_manager import user_manager
                user_id_int = int(user_identifier) if str(user_identifier).isdigit() else 1
                await asyncio.to_thread(user_manager.update_user_settings, user_id_int, model=normalized_model)
            except Exception as e:
                logger.debug(f"[router_chat] Не удалось обновить model в user_settings: {e}")

            # Обновление состояния базового chat_model
            active_chat_ref = getattr(getattr(fastapi_req, "app", None), "state", None)
            target_chat_model = getattr(active_chat_ref, "chat_model", None) if active_chat_ref else None
            if not target_chat_model:
                target_chat_model = chat_model
            if target_chat_model:
                if hasattr(target_chat_model, "_model_name"):
                    target_chat_model._model_name = normalized_model
                if hasattr(target_chat_model, "model_name"):
                    target_chat_model.model_name = normalized_model

            return {
                "status": "success",
                "message": "Модель успешно обновлена",
                "model": normalized_model,
                "provider": provider,
            }
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"[router_chat] Ошибка при установке модели: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    @router.get('/provider')
    async def get_provider_endpoint(fastapi_req: Request, profile: str = "") -> dict:
        """Получение текущего активного AI-провайдера."""
        provider, model_name, config_file = await _get_effective_model_and_provider(fastapi_req, profile=profile)
        return {
            "status": "success",
            "provider": provider,
            "model": model_name,
            "display": f"{provider}: {model_name}",
            "config_file": config_file,
        }


    @router.get('/model-instruction')
    async def get_model_instruction(fastapi_req: Request, model: str = "") -> dict:
        """Получение текущей системной инструкции для AI-модели или чата."""
        try:
            user_identifier, system_instruction, selected_model, settings = await _extract_user_auth(fastapi_req)
            effective_model = model.strip() or selected_model or ""
            provider, resolved_model, config_file = _resolve_default_model_and_provider()

            if not effective_model:
                effective_model = resolved_model

            source = "user_settings" if (settings and settings.get("system_instruction")) else "file_default"

            return {
                "status": "success",
                "instruction": system_instruction,
                "system_instruction": system_instruction,
                "model": effective_model,
                "provider": provider,
                "source": source,
            }
        except Exception as exc:
            logger.error(f"[router_chat] Ошибка при получении системной инструкции: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    @router.post('/model-instruction')
    async def set_model_instruction(req: ModelInstructionPayload, fastapi_req: Request) -> dict:
        """Установка и сохранение системной инструкции для AI-модели или чата."""
        try:
            raw_instruction = req.instruction.strip() or req.system_instruction.strip() or req.content.strip()
            if not raw_instruction:
                raise HTTPException(status_code=400, detail="Инструкция не может быть пустой")

            user_identifier, _, selected_model, _ = await _extract_user_auth(fastapi_req)

            # 1. Обновляем настройки пользователя в базе данных
            try:
                from src.user_manager import user_manager
                user_id_int = int(user_identifier) if str(user_identifier).isdigit() else 1
                await asyncio.to_thread(user_manager.update_user_settings, user_id_int, system_instruction=raw_instruction)
            except Exception as e:
                logger.debug(f"[router_chat] Не удалось обновить user_settings: {e}")

            # 2. Обновляем базовый chat_model (из app.state или переданный при инициализации)
            active_chat_ref = getattr(getattr(fastapi_req, "app", None), "state", None)
            target_chat_model = getattr(active_chat_ref, "chat_model", None) if active_chat_ref else None
            if not target_chat_model:
                target_chat_model = chat_model

            if target_chat_model and hasattr(target_chat_model, "update_system_instruction"):
                try:
                    target_chat_model.update_system_instruction(raw_instruction)
                except Exception as e:
                    logger.debug(f"[router_chat] Не удалось обновить chat_model system_instruction: {e}")

            # 3. Обновляем все кэшированные инстансы _active_chat_models
            for cached_instance in _active_chat_models.values():
                if hasattr(cached_instance, "system_instruction"):
                    setattr(cached_instance, "system_instruction", raw_instruction)
                elif hasattr(cached_instance, "system_prompt"):
                    setattr(cached_instance, "system_prompt", raw_instruction)

            # 4. Сохранение на диск в файл prompts/chat/system_instruction.md по запросу
            if req.save_to_disk:
                prompt_file = __root__ / 'prompts' / 'chat' / 'system_instruction.md'
                prompt_file.parent.mkdir(parents=True, exist_ok=True)
                prompt_file.write_text(raw_instruction, encoding='utf-8')

            return {
                "status": "success",
                "message": "Системная инструкция успешно обновлена",
                "instruction": raw_instruction,
                "system_instruction": raw_instruction,
                "model": req.model or selected_model or "",
            }
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"[router_chat] Ошибка при сохранении системной инструкции: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    @router.post('/test-model')
    async def test_model(req: TestModelRequest, fastapi_req: Request) -> dict:
        """Проверочный запрос к указанной AI-модели для валидации связи (Запрос -> Ответ).
        
        Введите вручную имя модели и провайдера, иначе будет использована настройка по умолчанию.
        """
        start_time = time.perf_counter()
        target_model = req.model.strip()
        provider = req.provider.strip().lower()

        # Если модель или провайдер не указаны вручную, используем настройку по умолчанию
        if not target_model or not provider:
            def_provider, def_model, _ = await _get_effective_model_and_provider(fastapi_req)
            if not target_model and not provider:
                target_model = def_model
                provider = def_provider.lower()
            elif not target_model:
                if provider == def_provider.lower() and def_model:
                    target_model = def_model
                elif provider == 'gemini':
                    target_model = 'gemini-2.5-flash'
                elif provider == 'agy':
                    target_model = 'gemini-3.6-flash'
                elif provider == 'ollama':
                    target_model = 'llama3.1'
                elif provider == 'foundry':
                    target_model = 'local'
                else:
                    target_model = def_model
            elif not provider:
                if target_model.startswith('foundry:'):
                    provider = 'foundry'
                elif target_model.startswith('ollama:'):
                    provider = 'ollama'
                elif target_model.startswith('agy-'):
                    provider = 'agy'
                elif target_model.startswith('gemini_cli:'):
                    provider = 'gemini_cli'
                elif target_model.startswith('hf:') or target_model.startswith('hf::'):
                    provider = 'hf'
                elif target_model.startswith('onnx:') or target_model.startswith('onnx::'):
                    provider = 'onnx'
                elif any(target_model.startswith(p) for p in ('openai:', 'deepseek:', 'groq:', 'openrouter:', 'lmstudio:', 'local:', 'compat:')):
                    provider = 'openai'
                elif 'gemini' in target_model.lower():
                    provider = 'gemini'
                else:
                    provider = def_provider.lower()

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

    @router.get('/model-errors')
    async def get_model_errors_endpoint(provider: str = "", limit: int = 50) -> dict:
        """Получить список последних зафиксированных ошибок AI-моделей.

        :param provider: Опциональный фильтр по провайдеру (gemini, agy, foundry, ollama и т.д.).
        :param limit: Количество записей.
        :returns: JSON-ответ со списком событий ошибок.
        """
        from src.ai.orchestration.model_error_hub import get_model_errors
        events = get_model_errors(provider=provider or None, limit=limit)
        return {
            'status': 'success',
            'errors': [evt.model_dump() for evt in events],
            'count': len(events),
        }

    @router.get('/model-health')
    async def get_model_health_endpoint() -> dict:
        """Получить сводную статистику здоровья и доступности AI-моделей.

        :returns: Агрегированная сводка по ошибкам и провайдерам.
        """
        from src.ai.orchestration.model_error_hub import get_model_health_summary
        summary = get_model_health_summary()
        return {
            'status': 'success',
            'health': summary,
        }


    @router.post('/save-for-rag-indexing')
    async def save_to_rag(rag_req: SaveRagRequest, request: Request):
        """Ручное сохранение одобренного ответа в постоянный JSON-архив с выбором целевой RAG базы."""
        try:
            user_identifier, _, _, settings = await _extract_user_auth(request)
            target_rag = _resolve_target_rag_name(rag_req, settings)

            from src.rag import save_user_approved_response
            save_success = await asyncio.to_thread(
                save_user_approved_response,
                user_identifier, rag_req.query, rag_req.chat_text, rag_req.voice_text, target_rag
            )
            if save_success:
                return {
                    "status": "success",
                    "message": "Успешно сохранено для последующей компиляции RAG",
                    "rag_name": target_rag,
                }
            else:
                raise HTTPException(status_code=500, detail="Ошибка сохранения ответа")
        except Exception as e:
            logger.error("Ошибка при ручном сохранении ответа", e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post('/save-rag-instant')
    async def save_to_rag_instant(rag_req: SaveRagRequest, request: Request):
        """Мгновенное сохранение ответа: запись в JSON + векторизация в FAISS с выбором целевой RAG базы."""
        try:
            user_identifier, _, _, settings = await _extract_user_auth(request)
            target_rag = _resolve_target_rag_name(rag_req, settings)
            api_key = getattr(chat_model, 'api_key', '') or os.getenv('GEMINI_API_KEY', '')

            content_to_index = rag_req.voice_text if rag_req.voice_text.strip() else rag_req.chat_text

            from src.rag import save_user_approved_response, index_user_interaction
            save_success = await asyncio.to_thread(
                save_user_approved_response,
                user_identifier, rag_req.query, rag_req.chat_text, rag_req.voice_text, target_rag
            )
            rag_success = await asyncio.to_thread(
                index_user_interaction, user_identifier, api_key, rag_req.query, content_to_index, target_rag
            )

            if save_success and rag_success:
                return {
                    "status": "success",
                    "message": "Успешно сохранено в архив и проиндексировано в RAG",
                    "rag_name": target_rag,
                }
            elif save_success:
                return {
                    "status": "success",
                    "message": "Сохранено в архив, но произошла ошибка при индексации в RAG",
                    "rag_name": target_rag,
                }
            else:
                raise HTTPException(status_code=500, detail="Ошибка сохранения ответа")
        except Exception as e:
            logger.error("Ошибка при мгновенном сохранении в RAG", e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.get('/sessions')
    async def get_all_sessions(request: Request):
        """Retrieve all chat sessions for the current user or host."""
        try:
            user_identifier, _, _, _ = await _extract_user_auth(request)
            sessions = await asyncio.to_thread(chat_sessions_db.list_sessions, user_identifier)
            return {"status": "success", "sessions": sessions}
        except Exception as e:
            logger.error("Error retrieving chat sessions", e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.get('/sessions/{session_id}')
    async def get_single_session(session_id: str, request: Request):
        """Retrieve a specific chat session by ID."""
        try:
            user_identifier, _, _, _ = await _extract_user_auth(request)
            session_data = await asyncio.to_thread(chat_sessions_db.get_session, session_id, user_identifier)
            if not session_data:
                raise HTTPException(status_code=404, detail="Session not found")
            return {"status": "success", "session": session_data}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving chat session {session_id}", e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post('/sessions')
    async def save_session_endpoint(payload: ChatSessionPayload, request: Request):
        """Save or update a chat session."""
        try:
            user_identifier, _, _, _ = await _extract_user_auth(request)
            data = payload.model_dump()
            saved = await asyncio.to_thread(chat_sessions_db.save_session, data, user_identifier)
            return {"status": "success", "session": saved}
        except Exception as e:
            logger.error("Error saving chat session", e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post('/sessions/sync')
    async def sync_sessions_endpoint(sync_req: SyncSessionsRequest, request: Request):
        """Bulk synchronize chat sessions from client to server."""
        try:
            user_identifier, _, _, _ = await _extract_user_auth(request)
            merged = await asyncio.to_thread(chat_sessions_db.bulk_sync_sessions, sync_req.sessions, user_identifier)
            return {"status": "success", "sessions": merged}
        except Exception as e:
            logger.error("Error synchronizing chat sessions", e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete('/sessions/{session_id}')
    async def delete_session_endpoint(session_id: str, request: Request):
        """Delete a specific chat session."""
        try:
            user_identifier, _, _, _ = await _extract_user_auth(request)
            deleted = await asyncio.to_thread(chat_sessions_db.delete_session, session_id, user_identifier)
            return {"status": "success", "deleted": deleted}
        except Exception as e:
            logger.error(f"Error deleting chat session {session_id}", e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete('/sessions')
    async def clear_all_sessions_endpoint(request: Request):
        """Clear all chat sessions for the current user."""
        try:
            user_identifier, _, _, _ = await _extract_user_auth(request)
            cleared = await asyncio.to_thread(chat_sessions_db.clear_sessions, user_identifier)
            return {"status": "success", "cleared": cleared}
        except Exception as e:
            logger.error("Error clearing chat sessions", e)
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

                # 1. RAG: Поиск по базе знаний (опционально, по умолчанию отключен)
                is_rag_active = bool(chat_req.generation_config.get('rag_enabled', False))

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
                        return
                    context_text = decision.context_text

                # 3. Подготовка контекста для LLM
                dynamic_context_parts = []
                if context_text:
                    dynamic_context_parts.append(context_text)

                user_msg_with_context = chat_req.message
                if dynamic_context_parts:
                    user_msg_with_context = "\n\n".join(dynamic_context_parts) + "\n\n[Запрос пользователя]:\n" + chat_req.message

                # Режим отладки (DEBUG MODE)
                if chat_req.generation_config.get('debug_mode', False):
                    voice_gender_instruction = _get_voice_gender_rule(settings)
                    debug_text = _build_debug_prompt(chat_req, context_text, voice_gender_instruction)
                    yield f"data: {json.dumps({'status': 'DEBUG MODE: Промпт сформирован, не отправляется в модель'})}\n\n"
                    yield f"data: {json.dumps({'text': debug_text})}\n\n"
                    return

                # Интеллектуальный роутинг: Агент анализа системных логов Windows (System Logs Analyzer Agent)
                msg_lower = chat_req.message.lower()
                is_system_logs_request = any(
                    phrase in msg_lower for phrase in (
                        'критические ошибки в операционной системе',
                        'критических ошибок в операционной системе',
                        'ошибки в операционной системе',
                        'ошибок в операционной системе',
                        'критические ошибки в ос',
                        'критических ошибок в ос',
                        'ошибки в ос',
                        'ошибок в ос',
                        'system logs analyzer',
                        'журнал событий windows',
                        'журналы событий windows',
                        'системные логи windows',
                        'системных логах windows',
                    )
                )

                if is_system_logs_request:
                    yield f"data: {json.dumps({'status': '🚀 Запуск System Logs Analyzer Agent...'})}\n\n"
                    from src.ai.agents.system_logs_agent import SystemLogsAgent
                    agent = SystemLogsAgent()
                    
                    selected_model_name = chat_req.generation_config.get('model') or selected_model or 'gemini-2.5-flash'
                    active_model = get_chat_model(selected_model_name, system_instruction or "", user_id=user_identifier)
                    
                    yield f"data: {json.dumps({'status': '🔍 Сбор и кластеризация событий из Windows Event Log...'})}\n\n"
                    agent_report = await agent.run(chat_req.message, active_llm=active_model)
                    
                    yield f"data: {json.dumps({'text': agent_report})}\n\n"
                    return

                token = request.cookies.get('auth_token') if request else None
                from src.api.router_control import get_room_id
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

                yield f"data: {json.dumps({'status': 'Генерация ответа...'})}\n\n"

                chat_kwargs = kwargs.copy()
                chat_kwargs.pop('room_id', '')
                chat_kwargs.pop('search_engine', None)
                gen_cfg = chat_req.generation_config.copy()
                gen_cfg['response_type'] = 'chat'
                chat_kwargs['generation_config'] = gen_cfg

                stream_generator = active_model.chat_stream(user_msg_with_context, **chat_kwargs)

                chat_response = ""
                async for chunk in stream_generator:
                    if chunk:
                        c = chunk.replace("[CHAT]", "").replace("[VOICE]", "")
                        if c:
                            chat_response += c
                            yield f"data: {json.dumps({'text': c})}\n\n"

                # 4. Фоновая индексация взаимодействия в RAG (только если RAG был явно включен)
                if is_rag_active and chat_response and api_key and user_identifier:
                    from src.rag import index_user_interaction
                    asyncio.ensure_future(asyncio.to_thread(
                        index_user_interaction, user_identifier, api_key, chat_req.message, chat_response
                    ))

            except Exception as ex:
                logger.error('Error обработки чат-запроса', ex)
                yield f"data: {json.dumps({'error': str(ex)})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    return router

