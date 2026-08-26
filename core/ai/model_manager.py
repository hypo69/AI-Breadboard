# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Управление жизненным циклом и кэшированием моделей ИИ
# =============================================================================
# Описание:
# Централизованный реестр моделей ИИ для провайдеров Gemini, Gemini CLI, AGY, Foundry и Ollama.
#   Реализация разовой актуализации через SDK, фильтрация устаревших моделей по config.json
#   и долговременное кэширование на протяжении жизненного цикла приложения.
#
# File: model_manager.py
# Project: ai-assistant
# Package: src.ai
# Module: Core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
from pathlib import Path
from typing import Dict, List, Set

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
    """Нормализация идентификатора модели для единообразного сравнения."""
    res = name.strip()
    if res.startswith("models/"):
        res = res[len("models/") :]
    return res


def load_unsupported_models(provider: str = "gemini") -> Set[str]:
    """Загрузка списка неподдерживаемых моделей из файлов конфигурации.

    Args:
        provider (str): Имя провайдера ('gemini', 'gemini_cli', 'agy', 'foundry', 'ollama').
                        Значение по умолчанию: 'gemini'.

    Returns:
        Set[str]: Множество нормализованных имен неподдерживаемых моделей.

    Examples:
        >>> from core.ai.model_manager import load_unsupported_models
        >>> unsupported = load_unsupported_models('gemini')
        >>> isinstance(unsupported, set)
        True
    """
    prov = provider.lower().strip()
    unsupported: Set[str] = set()

    # Загрузка из конфигурации модуля Gemini при необходимости
    if prov in ("gemini", "gemini_cli", "agy"):
        gemini_cfg = j_loads(_GEMINI_CONFIG_PATH)
        if isinstance(gemini_cfg, dict):
            raw_list = gemini_cfg.get("unsupported_models", [])
            if isinstance(raw_list, list):
                for item in raw_list:
                    if isinstance(item, str) and item.strip():
                        unsupported.add(_normalize_model_name(item))

    # Загрузка из глобальной конфигурации
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
    """Добавление неподдерживаемой модели в файл конфигурации и удаление из кэша.

    Args:
        provider (str): Имя провайдера ('gemini', 'gemini_cli', 'agy', 'foundry', 'ollama').
                        Значение по умолчанию: 'gemini'.
        model_name (str): Имя модели для исключения.
                          Значение по умолчанию: ''.
        reason (str): Причина исключения для протоколирования в логах.
                      Значение по умолчанию: ''.

    Returns:
        bool: Флаг успешного сохранения в конфигурацию.

    Examples:
        >>> from core.ai.model_manager import add_unsupported_model
        >>> add_unsupported_model('gemini', 'gemini-old-model', reason='404 Not Found')
        True
    """
    if not model_name:
        return False

    prov = provider.lower().strip()
    norm_name = _normalize_model_name(model_name)

    # 1. Обновление конфигурации Gemini
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

    # 2. Обновление глобальной конфигурации
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
        f"[ModelManager] Модель '{norm_name}' провайдера '{prov}' добавлена в список неподдерживаемых "
        f"(причина: {reason[:120]})"
    )
    return True


def _fetch_gemini_models_from_sdk(api_key: str = "") -> List[str]:
    """Получение моделей Gemini напрямую через Google GenAI SDK с фильтрацией."""
    api_keys_to_try: List[str] = []
    if api_key:
        api_keys_to_try.append(api_key)
    else:
        keys, _, _ = load_api_keys()
        if keys:
            api_keys_to_try.extend(keys)

    unsupported = load_unsupported_models("gemini")
    fallback_pool = [m for m in _DEFAULT_GEMINI_FALLBACK if m not in unsupported]
    if not fallback_pool:
        fallback_pool = ["gemini-flash-latest", "gemini-pro-latest"]

    if not api_keys_to_try:
        return fallback_pool

    last_error = ""
    for key in api_keys_to_try:
        try:
            client = genai.Client(api_key=key)
            models: List[str] = []
            for m in client.models.list():
                name = _normalize_model_name(m.name)
                # Проверка поддержки действия генерации контента
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
            f"[ModelManager] Ошибка запроса списка моделей от Google GenAI SDK: {last_error}. "
            f"Используется резервный список моделей."
        )

    return fallback_pool


def _fetch_foundry_models_sync(base_url: str = "") -> List[str]:
    """Синхронное получение списка моделей от локального Foundry сервера."""
    from core.config import ai_cfg
    url = base_url or (getattr(ai_cfg, "foundry_base_url", "http://localhost:54837") if ai_cfg else "http://localhost:54837")
    fallback_id = getattr(ai_cfg, "foundry_model_id", "qwen2.5-1.5b-instruct-generic-cpu:4") if ai_cfg else "qwen2.5-1.5b-instruct-generic-cpu:4"
    unsupported = load_unsupported_models("foundry")

    import requests
    try:
        resp = requests.get(f"{url}/v1/models", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            models: List[str] = []
            for item in data.get("data", []):
                mid = item.get("id", "")
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
    """Синхронное получение списка моделей от сервера Ollama."""
    from core.config import ai_cfg
    url = base_url or (getattr(ai_cfg, "ollama_base_url", "http://localhost:11434") if ai_cfg else "http://localhost:11434")
    fallback_id = getattr(ai_cfg, "ollama_model_id", "llama3.1") if ai_cfg else "llama3.1"
    unsupported = load_unsupported_models("ollama")

    import requests
    try:
        resp = requests.get(f"{url}/api/tags", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            models: List[str] = []
            for item in data.get("models", []):
                name = item.get("name", "")
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
    """Синхронное получение списка моделей для Gemini CLI с фильтрацией."""
    unsupported = load_unsupported_models("gemini_cli")
    pool = [m for m in _DEFAULT_GEMINI_CLI_FALLBACK if m not in unsupported]
    if not pool:
        pool = ["gemini-3.1-flash-lite", "gemini-2.5-flash"]
    return pool


def _fetch_hf_models_sync() -> List[str]:
    """Синхронное получение списка кэшированных моделей HuggingFace."""
    unsupported = load_unsupported_models("hf")
    try:
        from core.ai.hf_chat import hf_client
        downloaded = hf_client.list_downloaded()
        models: List[str] = []
        for item in downloaded:
            mid = item.get("id", "")
            if mid and _normalize_model_name(mid) not in unsupported:
                models.append(mid)
        if models:
            return models
    except Exception as e:
        logger.info(f"[ModelManager] HuggingFace список моделей недоступен: {e}")

    fallback = ["Qwen/Qwen2.5-0.5B-Instruct", "google/gemma-2-2b-it"]
    return [m for m in fallback if _normalize_model_name(m) not in unsupported]


def _fetch_onnx_models_sync() -> List[str]:
    """Синхронное получение списка моделей ONNX."""
    unsupported = load_unsupported_models("onnx")
    try:
        from core.ai.onnx_chat import onnx_client
        loaded = onnx_client.list_loaded()
        models: List[str] = []
        for item in loaded:
            mid = item.get("id", "")
            if mid and _normalize_model_name(mid) not in unsupported:
                models.append(mid)
        if models:
            return models
    except Exception as e:
        logger.info(f"[ModelManager] ONNX список моделей недоступен: {e}")

    return []


def _fetch_openai_compat_models_sync() -> List[str]:
    """Синхронное получение списка моделей OpenAI-совместимых провайдеров."""
    unsupported = load_unsupported_models("openai")
    global_cfg = j_loads(_GLOBAL_CONFIG_PATH)
    models: List[str] = []
    if isinstance(global_cfg, dict):
        compat_sec = global_cfg.get("openai_compat", {})
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
        models = ["gpt-4o-mini", "gpt-4o", "deepseek:deepseek-chat"]
    return [m for m in models if _normalize_model_name(m) not in unsupported]


def get_available_models(
    provider: str = "gemini",
    api_key: str = "",
    force_refresh: bool = False,
) -> List[str]:
    """Получение списка актуальных доступных моделей для заданного провайдера.

    Использует разовое получение через SDK/API с последующим кэшированием в памяти
    на весь жизненный цикл приложения. Исключает неподдерживаемые модели из config.json.

    Args:
        provider (str): Имя провайдера ('gemini', 'gemini_cli', 'agy', 'foundry', 'ollama', 'hf', 'onnx', 'openai').
                        Значение по умолчанию: 'gemini'.
        api_key (str): Опциональный API ключ для Gemini.
                       Значение по умолчанию: ''.
        force_refresh (bool): Принудительный сброс кэша и повторный запрос к провайдеру.
                              Значение по умолчанию: False.

    Returns:
        List[str]: Список доступных идентификаторов моделей.

    Examples:
        >>> from core.ai.model_manager import get_available_models
        >>> models = get_available_models('gemini')
        >>> len(models) > 0
        True
    """
    prov = provider.lower().strip()

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
        gemini_models = get_available_models("gemini", api_key=api_key, force_refresh=force_refresh)
        agy_unsupported = load_unsupported_models("agy")
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
    """Асинхронная актуализация и прогрев кэша моделей для всех активных провайдеров.

    Выполняется однократно при запуске серверного приложения.

    Args:
        force_refresh (bool): Принудительный запрос к SDK/API провайдеров.
                              Значение по умолчанию: True.

    Returns:
        Dict[str, List[str]]: Словарь со списками доступных моделей по провайдерам.

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

    gemini_list = gemini_res if isinstance(gemini_res, list) else []
    gemini_cli_list = gemini_cli_res if isinstance(gemini_cli_res, list) else []
    foundry_list = foundry_res if isinstance(foundry_res, list) else []
    ollama_list = ollama_res if isinstance(ollama_res, list) else []
    hf_list = hf_res if isinstance(hf_res, list) else []
    onnx_list = onnx_res if isinstance(onnx_res, list) else []
    openai_list = openai_res if isinstance(openai_res, list) else []

    # AGY формируется на основе актуализированных моделей Gemini
    agy_list = get_available_models("agy", force_refresh=force_refresh)

    result_pool = {
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
