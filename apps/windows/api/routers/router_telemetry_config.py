# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router Telemetry Config
# =============================================================================
# Description:
#   FastAPI REST эндпоинты для чтения, редактирования, валидации и сохранения
#   файла конфигурации телеметрии (%APPDATA%\AI-Breadboard\apps\windows\telemetry\config.json)
#   с мгновенным применением изменений на лету.
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_telemetry_config import init_router
#
#     router = init_router()
#
# File: router_telemetry_config.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 03:20:00
# =============================================================================

from __future__ import annotations
"""FastAPI REST эндпоинты для управления конфигурацией телеметрии."""

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from logger import logger
from apps.windows.telemetry.telemetry_config import TelemetryConfigManager, get_default_telemetry_config_path


class TelemetryConfigUpdateRequest(BaseModel):
    """Модель запроса на обновление структурированной конфигурации телеметрии."""
    config: Dict[str, Any] = Field(..., description="Новые параметры конфигурации JSON")


class TelemetryRawConfigUpdateRequest(BaseModel):
    """Модель запроса на сохранение сырого JSON текста конфигурации."""
    raw_json: str = Field(..., description="Сырой текст JSON конфигурации")


def init_router() -> APIRouter:
    """Инициализирует и возвращает роутер API управления конфигурацией телеметрии.

    Returns:
        APIRouter: Сконфигурированный FastAPI роутер.
    """
    router = APIRouter(prefix="/api/windows/telemetry/config", tags=["windows-telemetry-config"])

    @router.get("")
    async def get_telemetry_config() -> Dict[str, Any]:
        """Получает текущую активную конфигурацию телеметрии из %APPDATA%.

        Returns:
            Dict[str, Any]: Словарь с конфигурацией, путем к файлу и временем изменения.
        """
        cfg_mgr = TelemetryConfigManager()
        cfg_mgr.check_and_reload()
        cfg_path = Path(cfg_mgr.config_path)
        
        last_modified = ""
        if cfg_path.is_file():
            try:
                mtime = cfg_path.stat().st_mtime
                last_modified = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
            except Exception:
                pass

        return {
            "success": True,
            "config_path": str(cfg_path),
            "last_modified": last_modified,
            "config": cfg_mgr.get_config(),
            "intervals": cfg_mgr.get_all_intervals(),
        }

    @router.get("/raw")
    async def get_raw_telemetry_config() -> Dict[str, Any]:
        """Возвращает сырой текст файла конфигурации JSON.

        Returns:
            Dict[str, Any]: Сырой текст JSON и метаданные.
        """
        cfg_path = get_default_telemetry_config_path()
        if not cfg_path.is_file():
            # Попытка инициализировать файл из шаблона
            bundled_template = Path(__file__).resolve().parents[2] / "telemetry" / "config.json"
            if bundled_template.is_file():
                try:
                    cfg_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(bundled_template, cfg_path)
                except Exception as e:
                    logger.warning(f"Не удалось скопировать шаблон конфигурации: {e}")
                    cfg_path = bundled_template

        try:
            content = cfg_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Ошибка чтения файла конфигурации телеметрии {cfg_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Не удалось прочитать файл конфигурации: {e}")

        return {
            "success": True,
            "config_path": str(cfg_path),
            "raw_json": content,
        }

    @router.post("")
    @router.put("")
    async def save_telemetry_config(payload: TelemetryConfigUpdateRequest) -> Dict[str, Any]:
        """Сохраняет структурированную конфигурацию в файл %APPDATA% и инициирует горячую перезагрузку.

        Args:
            payload: Данные новой конфигурации.

        Returns:
            Dict[str, Any]: Результат операции и обновленные интервалы.
        """
        cfg_mgr = TelemetryConfigManager()
        saved = cfg_mgr.save_config(payload.config)
        if not saved:
            raise HTTPException(status_code=500, detail="Не удалось сохранить файл конфигурации")

        cfg_mgr.reload()
        logger.info(f"✅ Конфигурация телеметрии успешно обновлена через веб-интерфейс: {cfg_mgr.config_path}")

        return {
            "success": True,
            "message": "Конфигурация успешно сохранена и применена на лету",
            "config_path": cfg_mgr.config_path,
            "config": cfg_mgr.get_config(),
            "intervals": cfg_mgr.get_all_intervals(),
        }

    @router.post("/raw")
    async def save_raw_telemetry_config(payload: TelemetryRawConfigUpdateRequest) -> Dict[str, Any]:
        """Валидирует и сохраняет сырой текст JSON конфигурации в %APPDATA%.

        Args:
            payload: Сырой текст JSON.

        Returns:
            Dict[str, Any]: Результат валидации и сохранения.
        """
        try:
            parsed_data = json.loads(payload.raw_json)
        except json.JSONDecodeError as err:
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка синтаксиса JSON: строка {err.lineno}, колонка {err.colno}: {err.msg}",
            )

        if not isinstance(parsed_data, dict):
            raise HTTPException(status_code=400, detail="Конфигурация верхнего уровня должна быть JSON-объектом")

        cfg_mgr = TelemetryConfigManager()
        target_path = Path(cfg_mgr.config_path)
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(
                json.dumps(parsed_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"Ошибка записи сырой конфигурации в {target_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка сохранения на диск: {e}")

        cfg_mgr.reload()
        logger.info(f"✅ Сырой JSON конфигурации телеметрии успешно сохранен и применен: {target_path}")

        return {
            "success": True,
            "message": "Сырой JSON валидирован, сохранен и применен на лету",
            "config_path": str(target_path),
            "config": cfg_mgr.get_config(),
        }

    @router.post("/reset")
    async def reset_telemetry_config_to_default() -> Dict[str, Any]:
        """Сбрасывает конфигурацию телеметрии к значениям по умолчанию из исходного шаблона.

        Returns:
            Dict[str, Any]: Результат сброса.
        """
        bundled_template = Path(__file__).resolve().parents[2] / "telemetry" / "config.json"
        if not bundled_template.is_file():
            raise HTTPException(status_code=404, detail="Исходный шаблон config.json не найден в пакете модуля")

        target_path = get_default_telemetry_config_path()
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(bundled_template, target_path)
        except Exception as e:
            logger.error(f"Не удалось сбросить конфигурацию телеметрии: {e}")
            raise HTTPException(status_code=500, detail=f"Не удалось скопировать шаблон: {e}")

        cfg_mgr = TelemetryConfigManager(config_path=str(target_path))
        cfg_mgr.reload()
        logger.info(f"↺ Конфигурация телеметрии сброшена к исходному шаблону: {target_path}")

        return {
            "success": True,
            "message": "Конфигурация телеметрии успешно сброшена к значениям по умолчанию",
            "config_path": str(target_path),
            "config": cfg_mgr.get_config(),
            "intervals": cfg_mgr.get_all_intervals(),
        }

    return router
