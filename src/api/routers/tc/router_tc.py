# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard API - Router Tc Module
# =============================================================================
# Description:
#   router_tc.py
#
# Usage Examples:
#   Python API:
#     from src.api.routers.tc.router_tc import ModelInstructionRequest
#
#     service = ModelInstructionRequest()
#
# File: router_tc.py
# Project: ai-breadboard
# Package: src.api.routers.tc
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

from __future__ import annotations
"""router_tc.py

Реализация роутера Test Computer (TC). Содержит эндпоинты для управления системной инструкцией,
моделью и провайдером, а также прием телеметрических данных.

Updated: 2026-10-01 03:59:00"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from header import __root__

class ModelInstructionRequest(BaseModel):
    instruction: str = Field('', description='Текст системной инструкции')
    save_to_disk: bool = Field(False, description='Сохранить инструкцию в файл')

class ModelInstructionPutRequest(BaseModel):
    system_instruction: str = Field('', description='Текст системной инструкции (PUT)')
    save_to_disk: bool = Field(False, description='Сохранить инструкцию в файл')

class ModelRequest(BaseModel):
    model: str = Field('', description='Имя модели')
    provider: str = Field('', description='Имя провайдера')
    save_to_config: bool = Field(False, description='Сохранить в tc.json')

class ModelPutRequest(BaseModel):
    model: str = Field('', description='Имя модели')
    provider: str = Field('', description='Имя провайдера')
    save_to_config: bool = Field(False, description='Сохранить в tc.json')

class ModelProviderRequest(BaseModel):
    provider: str = Field('', description='Имя провайдера')
    model: Optional[str] = Field(None, description='Имя модели (опционально)')
    save_to_config: bool = Field(False, description='Сохранить в tc.json')

class TelemetryReading(BaseModel):
    id: str
    hardware_name: str
    hardware_type: str
    sensor_category: str
    sensor_name: str
    unit: str
    value: Any

class TelemetryPayload(BaseModel):
    source: str
    readings: List[TelemetryReading]

def _instruction_path() -> Path:
    return __root__ / 'prompts' / 'tc' / 'system_instruction.md'

def _config_path() -> Path:
    return __root__ / 'start_scenarios_config' / 'tc.json'

def _load_config() -> Dict[str, Any]:
    cfg_path = _config_path()
    if cfg_path.is_file():
        try:
            import json
            return json.loads(cfg_path.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}

def _save_config(data: Dict[str, Any]) -> None:
    cfg_path = _config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    import json
    cfg_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def _find_tc_config_path() -> Path:
    """Возвращает путь к файлу tc.json.
    Используется в тестах через monkey‑patch. Если файл не найден – бросает FileNotFoundError.
    """
    cfg_path = _config_path()
    if cfg_path.is_file():
        return cfg_path
    raise FileNotFoundError(f'TC config file not found at {cfg_path}')
router = APIRouter(prefix='/api/v1/tc', tags=['tc'])

@router.get('/model-instruction')
def get_tc_model_instruction(request: Request) -> Dict[str, Any]:
    """Возвращает текущую системную инструкцию. Если файл существует – читаем, иначе пустая строка."""
    instr_path = _instruction_path()
    instruction = instr_path.read_text(encoding='utf-8') if instr_path.is_file() else ''
    cfg = _load_config()
    provider = cfg.get('ai', {}).get('provider', '')
    model = cfg.get('ai', {}).get(provider, {}).get('model', '')
    return {'status': 'success', 'instruction': instruction, 'system_instruction': instruction, 'model': provider, 'provider': provider.upper() if provider else ''}

@router.post('/model-instruction')
def post_tc_model_instruction(payload: ModelInstructionRequest, request: Request) -> Dict[str, Any]:
    if not payload.instruction:
        raise HTTPException(status_code=400, detail='Инструкция не может быть пустой')
    if payload.save_to_disk:
        path = _instruction_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload.instruction, encoding='utf-8')
    return {'status': 'success', 'instruction': payload.instruction}

@router.put('/model-instruction')
def put_tc_model_instruction(payload: ModelInstructionPutRequest, request: Request) -> Dict[str, Any]:
    if not payload.system_instruction:
        raise HTTPException(status_code=400, detail='Инструкция не может быть пустой')
    if payload.save_to_disk:
        path = _instruction_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload.system_instruction, encoding='utf-8')
    return {'status': 'success', 'instruction': payload.system_instruction}

@router.get('/model')
def get_tc_model(request: Request) -> Dict[str, Any]:
    cfg = _load_config()
    provider = cfg.get('ai', {}).get('provider', '')
    model = cfg.get('ai', {}).get(provider, {}).get('model', '')
    return {'status': 'success', 'model': model, 'provider': provider.upper(), 'display': model}

@router.post('/model')
def post_tc_model(payload: ModelRequest, request: Request) -> Dict[str, Any]:
    if not payload.model:
        raise HTTPException(status_code=400, detail='Имя модели не может быть пустым')
    if not payload.provider:
        raise HTTPException(status_code=400, detail='Имя провайдера не может быть пустым')
    if payload.save_to_config:
        cfg_path = _find_tc_config_path()
        import json
        data = json.loads(cfg_path.read_text(encoding='utf-8')) if cfg_path.is_file() else {}
        provider_key = payload.provider.lower()
        data.setdefault('ai', {})['provider'] = provider_key
        data['ai'].setdefault(provider_key, {})['model'] = payload.model
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'status': 'success', 'model': payload.model, 'provider': payload.provider.upper()}

@router.put('/model')
def put_tc_model(payload: ModelPutRequest, request: Request) -> Dict[str, Any]:
    if not payload.model:
        raise HTTPException(status_code=400, detail='Имя модели не может быть пустым')
    if not payload.provider:
        raise HTTPException(status_code=400, detail='Имя провайдера не может быть пустым')
    if payload.save_to_config:
        cfg_path = _find_tc_config_path()
        import json
        data = json.loads(cfg_path.read_text(encoding='utf-8')) if cfg_path.is_file() else {}
        provider_key = payload.provider.lower()
        data.setdefault('ai', {})['provider'] = provider_key
        data['ai'].setdefault(provider_key, {})['model'] = payload.model
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'status': 'success', 'model': payload.model, 'provider': payload.provider.upper()}

@router.get('/provider')
def get_tc_model_provider(request: Request) -> Dict[str, Any]:
    cfg = _load_config()
    provider = cfg.get('ai', {}).get('provider', '')
    model = cfg.get('ai', {}).get(provider, {}).get('model', '')
    return {'status': 'success', 'provider': provider.upper(), 'model': model}

@router.post('/provider')
def post_tc_model_provider(payload: ModelProviderRequest, request: Request) -> Dict[str, Any]:
    if not payload.provider:
        raise HTTPException(status_code=400, detail='Имя провайдера не может быть пустым')
    if payload.save_to_config:
        cfg_path = _find_tc_config_path()
        import json
        data = json.loads(cfg_path.read_text(encoding='utf-8')) if cfg_path.is_file() else {}
        provider_key = payload.provider.lower()
        data.setdefault('ai', {})['provider'] = provider_key
        if payload.model:
            data['ai'].setdefault(provider_key, {})['model'] = payload.model
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'status': 'success', 'provider': payload.provider.upper(), 'model': payload.model or ''}

@router.post('/telemetry')
def post_tc_telemetry(payload: TelemetryPayload, request: Request) -> Dict[str, Any]:
    try:
        from apps.windows.telemetry.sqlite import TelemetryStorage
    except ImportError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    storage = TelemetryStorage.get_instance()
    saved_count = storage.save_sensor_polls(payload.source, payload.readings)
    return {'status': 'success', 'saved_count': saved_count, 'source': payload.source}

def init_router() -> APIRouter:
    """Экспортировать роутер TC."""
    return router
__all__ = ['init_router', 'router', '_find_tc_config_path']