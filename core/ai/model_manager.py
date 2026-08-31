# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Normalize model identifier for consistent comparis
# =============================================================================
# Description:
#   Централизованный реестр моделей ИИ для провайдеров Gemini, Gemini CLI, AGY, Foundry и Ollama.
#
# File: model_manager.py
# Project: ai-breadboard
# Package: core.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Set

from google import genai
import aiohttp

from header import __root__
from core.logger.logger import logger
from core.secrets.api_key_state import load_api_keys
from core.utils.jjson import j_dumps, j_loads

_GLOBAL_CONFIG_PATH: Path = __root__ / "config.json"
_GEMINI_CONFIG_PATH: Path = __root__ / "core" / "ai" / "gemini" / "config.json"

# Локальный кэш доступных моделей в оперативной памяти на весь жизненный цикл
_CACHED_MODELS: Dict[str, List[str]] = {}

_DEFAULT_GEMINI_FALLBACK: List[str] = [
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-pro-latest",
]

_GEMINI_PRIORITY_ORDER: List[str] = [
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-pro-latest",
]

_DEFAULT_GEMINI_CLI_FALLBACK: List[str] = [
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-3.1-pro-preview",
    "gemini-3.1-flash-lite-preview",
    "gemini-flash-latest",
    "gemini-pro-latest",
]

_GEMINI_CLI_PRIORITY_ORDER: List[str] = [
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-3.1-pro-preview",
    "gemini-3.1-flash-lite-preview",
    "gemini-flash-latest",
    "gemini-pro-latest",
]

def _normalize_model_name(name: str) -> str:
    """Normalize model identifier for consistent comparison."""
    res: str = name.strip()
    if res.startswith("models/"):
        res = res[len("models/") :]
    return res

def load_unsupported_models(provider: str = "gemini") -> Set[str]:
    """Load list of unsupported models from configuration files.

    Args:
        provider (str): Provider name ('gemini', 'gemini_cli', 'agy', 'foundry', 'ollama').
                        Default: 'gemini'.

    Returns:
        Set[str]: Set of normalized names of unsupported models.

    Examples:
        >>> from core.ai.model_manager import load_unsupported_models
        >>> unsupported: Set[str] = load_unsupported_models('gemini')
        >>> isinstance(unsupported, set)
        True
    """
    prov: str = provider.lower().strip()
    unsupported: Set[str] = set()

    # Loading из конфигурации модуля Gemini при необходимости
    if prov in ("gemini", "gemini_cli", "agy"):
        gemini_cfg = j_loads(_GEMINI_CONFIG_PATH)
        if isinstance(gemini_cfg, dict):
            raw_list = gemini_cfg.get("unsupported_models", [])
            if isinstance(raw_list, list):
                for item in raw_list:
                    if isinstance(item, str) and item.strip():
                        unsupported.add(_normalize_model_name(item))

    # Loading из глобальной конфигурации
    global_cfg = j_loads(_GLOBAL_CONFIG_PATH)
    if isinstance(global_cfg, dict):
        ai_sec = global_cfg.get("ai", {})
        if isinstance(ai_sec, dict):
            unsup_dict = ai_sec.get("unsupported_models", {})
            if isinstance(unsup_dict, dict):
                prov_list = unsup_dict.get(prov, [])
                if isinstance(prov_list, list):
                    for item in prov_list:
                        if isinstance(item, str) and item.strip():
                            unsupported.add(_normalize_model_name(item))

    return unsupported

def add_unsupported_model(provider: str = "gemini", model_name: str = "", reason: str = "") -> bool:
    """Add unsupported model to configuration file and remove from cache.

    Args:
        provider (str): Provider name ('gemini', 'gemini_cli', 'agy', 'foundry', 'ollama').
                        Default: 'gemini'.
        model_name (str): Model name to exclude.
                          Default: ''.
        reason (str): Reason for exclusion to log.
                      Default: ''.

    Returns:
        bool: Flag indicating successful save to configuration.

    Examples:
        >>> from core.ai.model_manager import add_unsupported_model
        >>> result: bool = add_unsupported_model('gemini', 'gemini-old-model', reason='404 Not Found')
        True
    """
    if not model_name:
        return False

    prov: str = provider.lower().strip()
    norm_name: str = _normalize_model_name(model_name)

    # 1. Update конфигурации Gemini
    if prov in ("gemini", "gemini_cli", "agy"):
        gemini_cfg = j_loads(_GEMINI_CONFIG_PATH)
        if isinstance(gemini_cfg, dict):
            curr_list = gemini_cfg.get("unsupported_models", [])
            if not isinstance(curr_list, list):
                curr_list = []
            if norm_name not in curr_list:
                curr_list.append(norm_name)
                gemini_cfg["unsupported_models"] = sorted(list(set(curr_list)))
                j_dumps(gemini_cfg, _GEMINI_CONFIG_PATH)

    # 2. Update глобальной конфигурации
    global_cfg = j_loads(_GLOBAL_CONFIG_PATH)
    if isinstance(global_cfg, dict):
        ai_sec = global_cfg.get("ai", {})
        if not isinstance(ai_sec, dict):
            ai_sec = {}
        unsup_dict = ai_sec.get("unsupported_models", {})
        if not isinstance(unsup_dict, dict):
            unsup_dict = {}
        prov_list = unsup_dict.get(prov, [])
        if not isinstance(prov_list, list):
            prov_list = []
        if norm_name not in prov_list:
            prov_list.append(norm_name)
            unsup_dict[prov] = sorted(list(set(prov_list)))
            ai_sec["unsupported_models"] = unsup_dict
            global_cfg["ai"] = ai_sec
            j_dumps(global_cfg, _GLOBAL_CONFIG_PATH)

    # 3. Инвалидация модели в оперативной памяти
    if prov in _CACHED_MODELS:
        _CACHED_MODELS[prov] = [m for m in _CACHED_MODELS[prov] if _normalize_model_name(m) != norm_name]

    # Для agy также удаляем agy-<norm_name>
    if "agy" in _CACHED_MODELS:
        _CACHED_MODELS["agy"] = [
            m for m in _CACHED_MODELS["agy"]
            if _normalize_model_name(m.replace("agy-", "")) != norm_name
        ]

    logger.warning(
        f"[ModelManager] Модель '{norm_name}' провайдера '{prov}' добавлена в list неподдерживаемых "
        f"(причина: {reason[:120]})"
    )
    return True

def _fetch_gemini_models_from_sdk(api_key: str = "") -> List[str]:
    """Fetch Gemini models directly via Google GenAI SDK with filtering."""
    api_keys_to_try: List[str] = []
    if api_key:
        api_keys_to_try.append(api_key)
    else:
        keys, _, _ = load_api_keys()
        if keys:
            api_keys_to_try.extend(keys)

    unsupported: Set[str] = load_unsupported_models("gemini")
    fallback_pool: List[str] = [m for m in _DEFAULT_GEMINI_FALLBACK if m not in unsupported]
    if not fallback_pool:
        fallback_pool = ["gemini-flash-latest", "gemini-pro-latest"]

    if not api_keys_to_try:
        return fallback_pool

    last_error: str = ""
    for key in api_keys_to_try:
        try:
            client = genai.Client(api_key=key)
            models: List[str] = []
            for m in client.models.list():
                name: str = _normalize_model_name(m.name)
                # Check поддержки действия генерации контента
                if m.supported_actions and "generateContent" in m.supported_actions:
                    if name in unsupported:
                        continue
                    if any(x in name for x in ("bison", "gecko", "vision", "embedding", "aqa", "imagen")):
                        continue
                    models.append(name)

            if models:
                sorted_models: List[str] = []
                for pm in _GEMINI_PRIORITY_ORDER:
                    if pm in models and pm not in sorted_models:
                        sorted_models.append(pm)
                for m in models:
                    if m not in sorted_models:
                        sorted_models.append(m)
                return sorted_models
        except Exception as e:
            last_error = str(e)
            continue

    if last_error:
        logger.warning(
            f"[ModelManager] Error запроса списка моделей от Google GenAI SDK: {last_error}. "
            f"Используется резервный list моделей."
        )

    return fallback_pool

def _fetch_foundry_models_sync(base_url: str = "") -> List[str]:
    """Synchronously fetch list of models from local Foundry server."""
    from core.config import ai_cfg
    url: str = base_url or (getattr(ai_cfg, "foundry_base_url", "http://localhost:54837") if ai_cfg else "http://localhost:54837")
    fallback_id: str = getattr(ai_cfg, "foundry_model_id", "qwen2.5-1.5b-instruct-generic-cpu:4") if ai_cfg else "qwen2.5-1.5b-instruct-generic-cpu:4"
    unsupported: Set[str] = load_unsupported_models("foundry")

    import requests
    try:
        resp = requests.get(f"{url}/v1/models", timeout=5)
        if resp.status_code == 200:
            data: Dict[str, Any] = resp.json()
            models: List[str] = []
            for item in data.get("data", []):
                mid: str = item.get("id", "")
                if mid and _normalize_model_name(mid) not in unsupported:
                    models.append(mid)
            if models:
                return models
    except Exception as e:
        logger.info(f"[ModelManager] Foundry сервер ({url}) недоступен или вернул ошибку: {e}")

    if _normalize_model_name(fallback_id) not in unsupported:
        return [fallback_id]
    return []

def _fetch_ollama_models_sync(base_url: str = "") -> List[str]:
    """Synchronously fetch list of models from Ollama server."""
    from core.config import ai_cfg
    url: str = base_url or (getattr(ai_cfg, "ollama_base_url", "http://localhost:11434") if ai_cfg else "http://localhost:11434")
    fallback_id: str = getattr(ai_cfg, "ollama_model_id", "llama3.1") if ai_cfg else "llama3.1"
    unsupported: Set[str] = load_unsupported_models("ollama")

    import requests
    try:
        resp = requests.get(f"{url}/api/tags", timeout=5)
        if resp.status_code == 200:
            data: Dict[str, Any] = resp.json()
            models: List[str] = []
            for item in data.get("models", []):
                name: str = item.get("name", "")
                if name and _normalize_model_name(name) not in unsupported:
                    models.append(name)
            if models:
                return models
    except Exception as e:
        logger.info(f"[ModelManager] Ollama сервер ({url}) недоступен или вернул ошибку: {e}")

    if _normalize_model_name(fallback_id) not in unsupported:
        return [fallback_id]
    return []

def _fetch_gemini_cli_models_sync() -> List[str]:
    """Synchronously fetch list of models for Gemini CLI with filtering."""
    unsupported: Set[str] = load_unsupported_models("gemini_cli")
    pool: List[str] = [m for m in _DEFAULT_GEMINI_CLI_FALLBACK if m not in unsupported]
    if not pool:
        pool = ["gemini-3.1-flash-lite", "gemini-2.5-flash"]
    return pool

def _fetch_hf_models_sync() -> List[str]:
    """Synchronously fetch list of cached HuggingFace models."""
    unsupported: Set[str] = load_unsupported_models("hf")
    try:
        from core.ai.hf_chat import hf_client
        downloaded: List[Dict[str, Any]] = hf_client.list_downloaded()
        models: List[str] = []
        for item in downloaded:
            mid: str = item.get("id", "")
            if mid and _normalize_model_name(mid) not in unsupported:
                models.append(mid)
        if models:
            return models
    except Exception as e:
        logger.info(f"[ModelManager] HuggingFace list моделей недоступен: {e}")

    fallback: List[str] = ["Qwen/Qwen2.5-0.5B-Instruct", "google/gemma-2-2b-it"]
    return [m for m in fallback if _normalize_model_name(m) not in unsupported]

def _fetch_onnx_models_sync() -> List[str]:
    """Synchronously fetch list of ONNX models."""
    unsupported: Set[str] = load_unsupported_models("onnx")
    try:
        from core.ai.onnx_chat import onnx_client
        loaded: List[Dict[str, Any]] = onnx_client.list_loaded()
        models: List[str] = []
        for item in loaded:
            mid: str = item.get("id", "")
            if mid and _normalize_model_name(mid) not in unsupported:
                models.append(mid)
        if models:
            return models
    except Exception as e:
        logger.info(f"[ModelManager] ONNX list моделей недоступен: {e}")

    return []

def _fetch_openai_compat_models_sync() -> List[str]:
    """Synchronously fetch list of OpenAI-compatible provider models."""
    unsupported: Set[str] = load_unsupported_models("openai")
    global_cfg: Dict[str, Any] = j_loads(_GLOBAL_CONFIG_PATH)
    models: List[str] = []
    if isinstance(global_cfg, dict):
        compat_sec: Dict[str, Any] = global_cfg.get("openai_compat", {})
        if isinstance(compat_sec, dict):
            for prov_name, prov_data in compat_sec.get("providers", {}).items():
                if isinstance(prov_data, dict):
                    for m in prov_data.get("models", []):
                        if isinstance(m, str) and m and _normalize_model_name(m) not in unsupported:
                            if prov_name != "openai" and not any(m.startswith(f"{p}:") for p in ("openai", "deepseek", "groq", "openrouter", "lmstudio", "local")):
                                models.append(f"{prov_name}:{m}")
                            else:
                                models.append(m)
    if not models:
        models: List[str] = ["gpt-4o-mini", "gpt-4o", "deepseek:deepseek-chat"]
    return [m for m in models if _normalize_model_name(m) not in unsupported]

def get_available_models(
    provider: str = "gemini",
    api_key: str = "",
    force_refresh: bool = False,
) -> List[str]:
    """Get list of current available models for given provider.

    Uses single fetch via SDK/API with subsequent caching in memory
    for the entire application lifecycle. Excludes unsupported models from config.json.

    Args:
        provider (str): Provider name ('gemini', 'gemini_cli', 'agy', 'foundry', 'ollama', 'hf', 'onnx', 'openai').
                        Default: 'gemini'.
        api_key (str): Optional API key for Gemini.
                       Default: ''.
        force_refresh (bool): Force cache reset and re-query provider.
                              Default: False.

    Returns:
        List[str]: List of available model identifiers.

    Examples:
        >>> from core.ai.model_manager import get_available_models
        >>> models: List[str] = get_available_models('gemini')
        >>> len(models) > 0
        True
    """
    prov: str = provider.lower().strip()

    # Быстрый возврат из кэша в оперативной памяти
    if not force_refresh and prov in _CACHED_MODELS and _CACHED_MODELS[prov]:
        return list(_CACHED_MODELS[prov])

    result_models: List[str] = []

    if prov == "gemini":
        result_models = _fetch_gemini_models_from_sdk(api_key=api_key)
        _CACHED_MODELS["gemini"] = result_models
        return list(result_models)

    elif prov in ("gemini_cli", "gemini-cli"):
        result_models = _fetch_gemini_cli_models_sync()
        _CACHED_MODELS["gemini_cli"] = result_models
        return list(result_models)

    elif prov == "agy":
        gemini_models: List[str] = get_available_models("gemini", api_key=api_key, force_refresh=force_refresh)
        agy_unsupported: Set[str] = load_unsupported_models("agy")
        result_models = [
            f"agy-{m}" for m in gemini_models
            if _normalize_model_name(m) not in agy_unsupported and f"agy-{m}" not in agy_unsupported
        ]
        _CACHED_MODELS["agy"] = result_models
        return list(result_models)

    elif prov == "foundry":
        result_models = _fetch_foundry_models_sync()
        _CACHED_MODELS["foundry"] = result_models
        return list(result_models)

    elif prov == "ollama":
        result_models = _fetch_ollama_models_sync()
        _CACHED_MODELS["ollama"] = result_models
        return list(result_models)

    elif prov in ("hf", "huggingface"):
        result_models = _fetch_hf_models_sync()
        _CACHED_MODELS["hf"] = result_models
        return list(result_models)

    elif prov == "onnx":
        result_models = _fetch_onnx_models_sync()
        _CACHED_MODELS["onnx"] = result_models
        return list(result_models)

    elif prov in ("openai", "openai_compat", "openai-compat", "deepseek", "groq", "openrouter", "lmstudio"):
        result_models = _fetch_openai_compat_models_sync()
        _CACHED_MODELS["openai"] = result_models
        return list(result_models)

    return result_models

async def actualize_all_models(force_refresh: bool = True) -> Dict[str, List[str]]:
    """Asynchronously actualize and warm up model caches for all active providers.

    Executes once at server application startup.

    Args:
        force_refresh (bool): Force query to provider SDK/API.
                              Default: True.

    Returns:
        Dict[str, List[str]]: Dictionary with lists of available models by provider.

    Examples:
        >>> import asyncio
        >>> from core.ai.model_manager import actualize_all_models
        >>> pool = asyncio.run(actualize_all_models())
        >>> 'gemini' in pool
        True
    """
    logger.info("[ModelManager] Запуск актуализации моделей для всех провайдеров...")

    loop = asyncio.get_running_loop()

    # Параллельный опрос провайдеров в отдельных потоках
    gemini_task = loop.run_in_executor(None, get_available_models, "gemini", "", force_refresh)
    gemini_cli_task = loop.run_in_executor(None, get_available_models, "gemini_cli", "", force_refresh)
    foundry_task = loop.run_in_executor(None, get_available_models, "foundry", "", force_refresh)
    ollama_task = loop.run_in_executor(None, get_available_models, "ollama", "", force_refresh)
    hf_task = loop.run_in_executor(None, get_available_models, "hf", "", force_refresh)
    onnx_task = loop.run_in_executor(None, get_available_models, "onnx", "", force_refresh)
    openai_task = loop.run_in_executor(None, get_available_models, "openai", "", force_refresh)

    gemini_res, gemini_cli_res, foundry_res, ollama_res, hf_res, onnx_res, openai_res = await asyncio.gather(
        gemini_task, gemini_cli_task, foundry_task, ollama_task, hf_task, onnx_task, openai_task, return_exceptions=True
    )

    gemini_list: List[str] = gemini_res if isinstance(gemini_res, list) else []
    gemini_cli_list: List[str] = gemini_cli_res if isinstance(gemini_cli_res, list) else []
    foundry_list: List[str] = foundry_res if isinstance(foundry_res, list) else []
    ollama_list: List[str] = ollama_res if isinstance(ollama_res, list) else []
    hf_list: List[str] = hf_res if isinstance(hf_res, list) else []
    onnx_list: List[str] = onnx_res if isinstance(onnx_res, list) else []
    openai_list: List[str] = openai_res if isinstance(openai_res, list) else []

    # AGY формируется на основе актуализированных моделей Gemini
    agy_list = get_available_models("agy", force_refresh=force_refresh)

    result_pool: Dict[str, List[str]] = {
        "gemini": gemini_list,
        "gemini_cli": gemini_cli_list,
        "agy": agy_list,
        "foundry": foundry_list,
        "ollama": ollama_list,
        "hf": hf_list,
        "onnx": onnx_list,
        "openai": openai_list,
    }

    logger.info(
        f"[ModelManager] Актуализация завершена: Gemini={len(gemini_list)}, "
        f"Gemini_CLI={len(gemini_cli_list)}, AGY={len(agy_list)}, "
        f"Foundry={len(foundry_list)}, Ollama={len(ollama_list)}, "
        f"HF={len(hf_list)}, ONNX={len(onnx_list)}, OpenAI={len(openai_list)}"
    )
    return result_pool
