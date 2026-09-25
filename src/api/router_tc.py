# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Computer (TC) Model & Provider Management Router
# =============================================================================
# Description:
#   FastAPI REST эндпоинты для управления активной AI-моделью, провайдером
#   и системной инструкцией в профиле Test Computer (/tc).
#
# Examples:
#   >>> from src.api.router_tc import init_router
#   >>> router = init_router()
#
# File: router_tc.py
# Project: AI-Breadboard
# Package: src.api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""FastAPI роутер для управления AI-моделями, провайдерами и системными инструкциями Test Computer (TC)."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from header import __root__
from logger import logger

# -----------------------------------------------------------------------------
# DTO Models
# -----------------------------------------------------------------------------

class TcModelInstructionPayload(BaseModel):
    """Модель данных для обновления системной инструкции AI-модели Test Computer."""
    instruction: str = Field(
        default="",
        description="Текст системной инструкции для AI-модели Test Computer.",
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
        default=True,
        description="Флаг сохранения системной инструкции в файл prompts/tc/system_instruction.md.",
    )


class TcSetModelPayload(BaseModel):
    """Модель данных для установки активной AI-модели Test Computer."""
    model: str = Field(
        ...,
        description="Имя модели для установки (например: gemini-2.5-flash, gemini-3.1-flash-lite, agy-gemini-3.6-flash, llama3.1).",
    )
    provider: str = Field(
        default="",
        description="Опциональное имя провайдера (gemini, gemini_cli, agy, foundry, ollama, openai, hf, onnx).",
    )
    save_to_config: bool = Field(
        default=True,
        description="Флаг сохранения изменений в конфигурационный файл tc.json.",
    )


class TcSetProviderPayload(BaseModel):
    """Модель данных для установки активного AI-провайдера Test Computer."""
    provider: str = Field(
        ...,
        description="Имя провайдера (gemini, gemini_cli, agy, foundry, ollama, openai, hf, onnx).",
    )
    model: str = Field(
        default="",
        description="Опциональное имя модели. Если не указано, выбирается модель по умолчанию для провайдера.",
    )
    save_to_config: bool = Field(
        default=True,
        description="Флаг сохранения изменений в конфигурационный файл tc.json.",
    )


# -----------------------------------------------------------------------------
# Вспомогательные функции
# -----------------------------------------------------------------------------

def _find_tc_config_path() -> Optional[Path]:
    """Находит актуальный путь к файлу конфигурации Test Computer.

    Returns:
        Optional[Path]: Путь к найденному файлу tc.json или None.
    """
    candidates = [
        __root__ / "start_scenarios_config" / "tc.json",
        __root__ / "config" / "tc.json",
        __root__ / "config_tc.json",
        __root__ / "tc.json",
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]


def _get_tc_default_instruction() -> str:
    """Загружает системную инструкцию по умолчанию для Test Computer.

    Returns:
        str: Текст системной инструкции.
    """
    tc_prompt_file = __root__ / "prompts" / "tc" / "system_instruction.md"
    if tc_prompt_file.exists():
        try:
            content = tc_prompt_file.read_text(encoding="utf-8", errors="replace").strip()
            if content:
                return content
        except Exception as e:
            logger.debug(f"[router_tc] Ошибка чтения prompts/tc/system_instruction.md: {e}")

    chat_prompt_file = __root__ / "prompts" / "chat" / "system_instruction.md"
    if chat_prompt_file.exists():
        try:
            content = chat_prompt_file.read_text(encoding="utf-8", errors="replace").strip()
            if content:
                return content
        except Exception as e:
            logger.debug(f"[router_tc] Ошибка чтения prompts/chat/system_instruction.md: {e}")

    return "Ты — автономный сервисный инженер и диагност операционной системы Windows платформы AI Breadboard Test Computer."


def _resolve_tc_model_and_provider() -> Tuple[str, str, str]:
    """Считывает провайдер и модель по умолчанию из профиля Test Computer (tc.json).

    Returns:
        Tuple[str, str, str]: (provider, model_name, config_filename)
    """
    cfg_path = _find_tc_config_path()
    provider = "GEMINI_CLI"
    model_name = "gemini-3.1-flash-lite"
    config_file = cfg_path.name if cfg_path else "tc.json"

    if cfg_path and cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                ai_sec = data.get("ai", {})
                if ai_sec.get("provider"):
                    prov_key = str(ai_sec.get("provider")).lower()
                    provider = prov_key.upper()
                    if isinstance(ai_sec.get(prov_key), dict) and ai_sec[prov_key].get("model"):
                        model_name = ai_sec[prov_key].get("model")
                    elif isinstance(ai_sec.get("providers"), dict) and isinstance(ai_sec["providers"].get(prov_key), dict) and ai_sec["providers"][prov_key].get("model"):
                        model_name = ai_sec["providers"][prov_key].get("model")
                    elif ai_sec.get("model"):
                        model_name = ai_sec.get("model")
                elif ai_sec.get("model"):
                    model_name = ai_sec.get("model")
        except Exception as e:
            logger.debug(f"[router_tc] Ошибка чтения конфигурации TC {cfg_path}: {e}")

    return provider, model_name, config_file


def _normalize_tc_model_and_provider(target_model: str = "", target_provider: str = "") -> Tuple[str, str]:
    """Нормализует имя модели и провайдера для профиля Test Computer.

    Args:
        target_model: Имя модели.
        target_provider: Имя провайдера.

    Returns:
        Tuple[str, str]: (normalized_model, normalized_provider_upper)
    """
    model = (target_model or "").strip()
    provider = (target_provider or "").strip().lower()

    if not provider:
        if model.startswith("foundry:"):
            provider = "foundry"
        elif model.startswith("ollama:"):
            provider = "ollama"
        elif model.startswith("agy-") or "agy" in model.lower():
            provider = "agy"
        elif model.startswith("gemini_cli:") or model.startswith("gemini-cli-"):
            provider = "gemini_cli"
        elif model.startswith("hf:") or model.startswith("hf::"):
            provider = "hf"
        elif model.startswith("onnx:") or model.startswith("onnx::"):
            provider = "onnx"
        elif any(model.startswith(p) for p in ("openai:", "deepseek:", "groq:", "openrouter:", "lmstudio:", "local:", "compat:")):
            provider = "openai"
        elif "gemini" in model.lower():
            provider = "gemini"
        else:
            provider = "gemini_cli"

    if not model:
        if provider in ("gemini_cli", "gemini-cli"):
            model = "gemini-3.1-flash-lite"
        elif provider == "gemini":
            model = "gemini-2.5-flash"
        elif provider == "agy":
            model = "gemini-3.6-flash"
        elif provider == "ollama":
            model = "llama3.1"
        elif provider == "foundry":
            model = "local"
        elif provider in ("openai", "openai_compat", "deepseek", "groq", "openrouter", "lmstudio"):
            model = "gpt-4o-mini"
        elif provider in ("hf", "huggingface"):
            model = "microsoft/Phi-3-mini-4k-instruct"
        elif provider == "onnx":
            model = "cpu-int4-rt"
        else:
            model = "gemini-3.1-flash-lite"

    return model, provider.upper()


def _save_tc_config_ai(provider: str, model_name: str) -> bool:
    """Сохраняет активный AI-провайдер и модель в конфигурационный файл tc.json.

    Args:
        provider: Имя провайдера (GEMINI_CLI, GEMINI, AGY, OLLAMA и др.).
        model_name: Имя модели.

    Returns:
        bool: True если сохранение прошло успешно.
    """
    cfg_path = _find_tc_config_path()
    if not cfg_path:
        return False

    try:
        data: Dict[str, Any] = {}
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        if "ai" not in data or not isinstance(data["ai"], dict):
            data["ai"] = {}

        prov_key = provider.lower()
        data["ai"]["provider"] = prov_key

        if prov_key not in data["ai"] or not isinstance(data["ai"][prov_key], dict):
            data["ai"][prov_key] = {}
        data["ai"][prov_key]["model"] = model_name

        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        logger.info(f"[router_tc] Конфигурация TC успешно обновлена: {cfg_path} -> provider={prov_key}, model={model_name}")
        return True
    except Exception as e:
        logger.error(f"[router_tc] Ошибка сохранения конфигурации TC в {cfg_path}: {e}", exc_info=True)
        return False


async def _extract_tc_user_auth(fastapi_req: Request) -> Tuple[str, str, str, dict]:
    """Извлекает пользователя и настройки для профиля Test Computer."""
    user_identifier = "1"
    system_instruction = ""
    selected_model = ""
    settings: Dict[str, Any] = {}

    try:
        from src.api.router_auth import get_current_user_optional
        user_data = get_current_user_optional(fastapi_req) if fastapi_req is not None else None

        from src.user_manager import user_manager
        db_user = None
        if user_data:
            if getattr(user_data, "id", None):
                db_user = await asyncio.to_thread(user_manager.get_user_by_id, user_data.id)
            if not db_user and getattr(user_data, "email", None):
                db_user = await asyncio.to_thread(user_manager.get_user_by_email, user_data.email)

        if not db_user:
            db_user = await asyncio.to_thread(user_manager.get_user_by_id, 1)

        if db_user:
            user_identifier = str(db_user.get("id", 1))
            settings = await asyncio.to_thread(user_manager.get_user_settings, db_user.get("id", 1)) or {}
            if settings.get("tc_system_instruction"):
                system_instruction = settings["tc_system_instruction"]
            elif settings.get("system_instruction"):
                system_instruction = settings["system_instruction"]

            if settings.get("tc_model"):
                selected_model = settings["tc_model"]
    except Exception as e:
        logger.debug(f"[router_tc] Ошибка извлечения пользователя: {e}")

    if not system_instruction:
        system_instruction = _get_tc_default_instruction()

    return user_identifier, system_instruction, selected_model, settings


# -----------------------------------------------------------------------------
# Router Initialization
# -----------------------------------------------------------------------------

def init_router() -> APIRouter:
    """Инициализация FastAPI роутера Test Computer (TC).

    Returns:
        APIRouter: Настроенный роутер с маршрутами управления TC.
    """
    router = APIRouter(tags=["Test Computer (TC)"])

    # =========================================================================
    # 1. Системная инструкция: /tc/model_instruction (GET / POST / PUT)
    # =========================================================================

    @router.get("/tc/model_instruction")
    @router.get("/tc/model-instruction")
    @router.get("/api/tc/model_instruction")
    @router.get("/api/tc/model-instruction")
    @router.get("/api/v1/tc/model_instruction")
    @router.get("/api/v1/tc/model-instruction")
    async def get_tc_model_instruction(fastapi_req: Request, model: str = "") -> dict:
        """Получение текущей системной инструкции AI-модели для Test Computer."""
        try:
            user_identifier, system_instruction, selected_model, settings = await _extract_tc_user_auth(fastapi_req)
            provider, default_model, config_file = _resolve_tc_model_and_provider()
            effective_model = model.strip() or selected_model or default_model

            source = "user_settings" if (settings and (settings.get("tc_system_instruction") or settings.get("system_instruction"))) else "file_default"

            return {
                "status": "success",
                "instruction": system_instruction,
                "system_instruction": system_instruction,
                "model": effective_model,
                "provider": provider,
                "source": source,
                "config_file": config_file,
            }
        except Exception as exc:
            logger.error(f"[router_tc] Ошибка при получении системной инструкции TC: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    @router.post("/tc/model_instruction")
    @router.post("/tc/model-instruction")
    @router.post("/api/tc/model_instruction")
    @router.post("/api/tc/model-instruction")
    @router.post("/api/v1/tc/model_instruction")
    @router.post("/api/v1/tc/model-instruction")
    @router.put("/tc/model_instruction")
    @router.put("/tc/model-instruction")
    @router.put("/api/tc/model_instruction")
    @router.put("/api/tc/model-instruction")
    @router.put("/api/v1/tc/model_instruction")
    @router.put("/api/v1/tc/model-instruction")
    async def set_tc_model_instruction(req: TcModelInstructionPayload, fastapi_req: Request) -> dict:
        """Установка и сохранение системной инструкции AI-модели для Test Computer."""
        try:
            raw_instruction = req.instruction.strip() or req.system_instruction.strip() or req.content.strip()
            if not raw_instruction:
                raise HTTPException(status_code=400, detail="Инструкция не может быть пустой")

            user_identifier, _, selected_model, _ = await _extract_tc_user_auth(fastapi_req)

            # 1. Обновляем настройки пользователя в БД
            try:
                from src.user_manager import user_manager
                user_id_int = int(user_identifier) if str(user_identifier).isdigit() else 1
                await asyncio.to_thread(
                    user_manager.update_user_settings,
                    user_id_int,
                    tc_system_instruction=raw_instruction,
                    system_instruction=raw_instruction,
                )
            except Exception as e:
                logger.debug(f"[router_tc] Не удалось обновить user_settings: {e}")

            # 2. Сохранение на диск по требованию (prompts/tc/system_instruction.md)
            if req.save_to_disk:
                tc_prompt_file = __root__ / "prompts" / "tc" / "system_instruction.md"
                tc_prompt_file.parent.mkdir(parents=True, exist_ok=True)
                tc_prompt_file.write_text(raw_instruction, encoding="utf-8")

            return {
                "status": "success",
                "message": "Системная инструкция для Test Computer успешно обновлена",
                "instruction": raw_instruction,
                "system_instruction": raw_instruction,
                "model": req.model or selected_model or "",
            }
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"[router_tc] Ошибка при сохранении системной инструкции TC: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    # =========================================================================
    # 2. Модель: /tc/model (GET / POST / PUT)
    # =========================================================================

    @router.get("/tc/model")
    @router.get("/tc/active_model")
    @router.get("/tc/active-model")
    @router.get("/api/tc/model")
    @router.get("/api/tc/active_model")
    @router.get("/api/tc/active-model")
    @router.get("/api/v1/tc/model")
    @router.get("/api/v1/tc/active_model")
    @router.get("/api/v1/tc/active-model")
    async def get_tc_model(fastapi_req: Request) -> dict:
        """Получение текущей активной AI-модели Test Computer."""
        try:
            _, _, user_selected_model, _ = await _extract_tc_user_auth(fastapi_req)
            provider, default_model, config_file = _resolve_tc_model_and_provider()
            effective_model = user_selected_model or default_model

            return {
                "status": "success",
                "model": effective_model,
                "provider": provider,
                "display": f"{provider}: {effective_model}",
                "config_file": config_file,
            }
        except Exception as exc:
            logger.error(f"[router_tc] Ошибка при получении модели TC: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    @router.post("/tc/model")
    @router.post("/tc/set_model")
    @router.post("/tc/set-model")
    @router.post("/api/tc/model")
    @router.post("/api/tc/set_model")
    @router.post("/api/tc/set-model")
    @router.post("/api/v1/tc/model")
    @router.post("/api/v1/tc/set_model")
    @router.post("/api/v1/tc/set-model")
    @router.put("/tc/model")
    @router.put("/tc/set_model")
    @router.put("/tc/set-model")
    @router.put("/api/tc/model")
    @router.put("/api/tc/set_model")
    @router.put("/api/tc/set-model")
    @router.put("/api/v1/tc/model")
    @router.put("/api/v1/tc/set_model")
    @router.put("/api/v1/tc/set-model")
    async def set_tc_model(req: TcSetModelPayload, fastapi_req: Request) -> dict:
        """Установка активной AI-модели Test Computer."""
        try:
            target_model = req.model.strip()
            if not target_model:
                raise HTTPException(status_code=400, detail="Имя модели не может быть пустым")

            normalized_model, provider = _normalize_tc_model_and_provider(target_model, req.provider)
            user_identifier, _, _, _ = await _extract_tc_user_auth(fastapi_req)

            # 1. Обновляем user_settings в БД
            try:
                from src.user_manager import user_manager
                user_id_int = int(user_identifier) if str(user_identifier).isdigit() else 1
                await asyncio.to_thread(
                    user_manager.update_user_settings,
                    user_id_int,
                    tc_model=normalized_model,
                    model=normalized_model,
                )
            except Exception as e:
                logger.debug(f"[router_tc] Не удалось обновить model в user_settings: {e}")

            # 2. Обновляем конфигурационный файл tc.json
            if req.save_to_config:
                _save_tc_config_ai(provider, normalized_model)

            return {
                "status": "success",
                "message": "Модель Test Computer успешно обновлена",
                "model": normalized_model,
                "provider": provider,
            }
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"[router_tc] Ошибка при установке модели TC: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    # =========================================================================
    # 3. Провайдер: /tc/model_provider (GET / POST / PUT)
    # =========================================================================

    @router.get("/tc/model_provider")
    @router.get("/tc/model-provider")
    @router.get("/tc/provider")
    @router.get("/api/tc/model_provider")
    @router.get("/api/tc/model-provider")
    @router.get("/api/tc/provider")
    @router.get("/api/v1/tc/model_provider")
    @router.get("/api/v1/tc/model-provider")
    @router.get("/api/v1/tc/provider")
    async def get_tc_model_provider(fastapi_req: Request) -> dict:
        """Получение текущего активного AI-провайдера Test Computer."""
        try:
            _, _, user_selected_model, _ = await _extract_tc_user_auth(fastapi_req)
            provider, default_model, config_file = _resolve_tc_model_and_provider()
            effective_model = user_selected_model or default_model

            return {
                "status": "success",
                "provider": provider,
                "model": effective_model,
                "display": f"{provider}: {effective_model}",
                "config_file": config_file,
            }
        except Exception as exc:
            logger.error(f"[router_tc] Ошибка при получении провайдера TC: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    @router.post("/tc/model_provider")
    @router.post("/tc/model-provider")
    @router.post("/tc/set_model_provider")
    @router.post("/tc/set-model-provider")
    @router.post("/tc/set_provider")
    @router.post("/tc/set-provider")
    @router.post("/api/tc/model_provider")
    @router.post("/api/tc/model-provider")
    @router.post("/api/tc/set_model_provider")
    @router.post("/api/tc/set_provider")
    @router.post("/api/tc/set-provider")
    @router.post("/api/v1/tc/model_provider")
    @router.post("/api/v1/tc/model-provider")
    @router.post("/api/v1/tc/set_model_provider")
    @router.post("/api/v1/tc/set_provider")
    @router.post("/api/v1/tc/set-provider")
    @router.put("/tc/model_provider")
    @router.put("/tc/model-provider")
    @router.put("/tc/set_model_provider")
    @router.put("/tc/set_provider")
    @router.put("/tc/set-provider")
    @router.put("/api/tc/model_provider")
    @router.put("/api/tc/model-provider")
    @router.put("/api/tc/set_model_provider")
    @router.put("/api/tc/set_provider")
    @router.put("/api/tc/set-provider")
    @router.put("/api/v1/tc/model_provider")
    @router.put("/api/v1/tc/model-provider")
    @router.put("/api/v1/tc/set_model_provider")
    @router.put("/api/v1/tc/set_provider")
    @router.put("/api/v1/tc/set-provider")
    async def set_tc_model_provider(req: TcSetProviderPayload, fastapi_req: Request) -> dict:
        """Установка активного AI-провайдера Test Computer."""
        try:
            target_provider = req.provider.strip()
            if not target_provider:
                raise HTTPException(status_code=400, detail="Имя провайдера не может быть пустым")

            normalized_model, provider = _normalize_tc_model_and_provider(req.model, target_provider)
            user_identifier, _, _, _ = await _extract_tc_user_auth(fastapi_req)

            # 1. Обновляем user_settings в БД
            try:
                from src.user_manager import user_manager
                user_id_int = int(user_identifier) if str(user_identifier).isdigit() else 1
                await asyncio.to_thread(
                    user_manager.update_user_settings,
                    user_id_int,
                    tc_model=normalized_model,
                    model=normalized_model,
                )
            except Exception as e:
                logger.debug(f"[router_tc] Не удалось обновить provider/model в user_settings: {e}")

            # 2. Обновляем конфигурационный файл tc.json
            if req.save_to_config:
                _save_tc_config_ai(provider, normalized_model)

            return {
                "status": "success",
                "message": "Провайдер Test Computer успешно обновлен",
                "provider": provider,
                "model": normalized_model,
            }
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"[router_tc] Ошибка при установке провайдера TC: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    return router
