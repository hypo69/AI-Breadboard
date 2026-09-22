"""AI provider configuration endpoints."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.config import ai_cfg
from logger import logger

__root__ = Path(__file__).parent.parent.parent


class FoundryConfigRequest(BaseModel):
    enabled: bool
    url: str = "http://localhost:54837"
    key: str = ""
    model: str = "qwen2.5-1.5b"
    remember: bool = True


class OllamaConfigRequest(BaseModel):
    enabled: bool
    url: str = "http://localhost:11434"
    model: str = "llama3.1"
    remember: bool = True


class AgyConfigRequest(BaseModel):
    enabled: bool
    key: str = ""
    model: str = "agy-flash"
    remember: bool = True


class OnnxConfigRequest(BaseModel):
    enabled: bool = True
    models_dir: str = "models/onnx"
    execution_provider: str = "DirectMLExecutionProvider"
    default_model: str = "phi-3.5-mini-instruct-onnx"
    olive_precision: str = "int4"
    remember: bool = True


def get_foundry_config() -> dict:
    """Get Foundry config in new format (providers.foundry)."""
    from src.config import ai_cfg
    providers = getattr(ai_cfg, "providers", {}) if ai_cfg else {}
    foundry_cfg = providers.get("foundry", {}) if isinstance(providers, dict) else {}
    return {
        "enabled": foundry_cfg.get("enabled", False),
        "url": foundry_cfg.get("base_url", "http://localhost:54837"),
        "key": os.getenv("FOUNDRY_API_KEY", ""),
        "model": foundry_cfg.get("model", "qwen2.5-1.5b")
    }


def save_foundry_config(data: FoundryConfigRequest) -> dict:
    from dotenv import set_key
    
    # Secret goes to .env
    if data.key:
        env_path = str(__root__ / '.env')
        set_key(env_path, "FOUNDRY_API_KEY", data.key)
        os.environ["FOUNDRY_API_KEY"] = data.key
    
    # Save to config.json in new format (providers-based)
    if data.remember:
        config_path = __root__ / 'config.json'
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg_data = json.load(f)
        except Exception:
            cfg_data = {}
            
        if "ai" not in cfg_data:
            cfg_data["ai"] = {}
        
        if "providers" not in cfg_data["ai"]:
            cfg_data["ai"]["providers"] = {}
        
        # New format: providers.foundry with enabled/base_url/model/unsupported_models
        cfg_data["ai"]["providers"]["foundry"] = {
            "enabled": data.enabled,
            "base_url": data.url,
            "model": data.model,
            "unsupported_models": []
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(cfg_data, f, indent=2, ensure_ascii=False)
        
    # Update in-memory config
    if ai_cfg:
        if not hasattr(ai_cfg, 'providers') or not isinstance(getattr(ai_cfg, 'providers', None), dict):
            ai_cfg.providers = {}
        if not isinstance(ai_cfg.providers, dict):
            ai_cfg.providers = {}
        ai_cfg.providers["foundry"] = type('obj', (object,), {
            'enabled': data.enabled,
            'base_url': data.url,
            'model': data.model,
            'unsupported_models': []
        })()
    
    return {"status": "ok"}


def get_ollama_config() -> dict:
    """Get Ollama config in new format (providers.ollama)."""
    from src.config import ai_cfg
    providers = getattr(ai_cfg, "providers", {}) if ai_cfg else {}
    ollama_cfg = providers.get("ollama", {}) if isinstance(providers, dict) else {}
    return {
        "enabled": ollama_cfg.get("enabled", False),
        "url": ollama_cfg.get("base_url", "http://localhost:11434"),
        "model": ollama_cfg.get("model", "llama3.1")
    }


def save_ollama_config(data: OllamaConfigRequest) -> dict:
    config_path = __root__ / 'config.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg_data = json.load(f)
    except Exception:
        cfg_data = {}
        
    if "ai" not in cfg_data:
        cfg_data["ai"] = {}
    
    if "providers" not in cfg_data["ai"]:
        cfg_data["ai"]["providers"] = {}
    
    # New format: providers.ollama with enabled/base_url/model/unsupported_models
    cfg_data["ai"]["providers"]["ollama"] = {
        "enabled": data.enabled,
        "base_url": data.url,
        "model": data.model,
        "unsupported_models": []
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(cfg_data, f, indent=2, ensure_ascii=False)
    
    # Update in-memory config
    if ai_cfg:
        if not hasattr(ai_cfg, 'providers') or not isinstance(getattr(ai_cfg, 'providers', None), dict):
            ai_cfg.providers = {}
        if not isinstance(ai_cfg.providers, dict):
            ai_cfg.providers = {}
        ai_cfg.providers["ollama"] = type('obj', (object,), {
            'enabled': data.enabled,
            'base_url': data.url,
            'model': data.model,
            'unsupported_models': []
        })()
    
    return {"status": "ok"}


def get_agy_config() -> dict:
    """Get AGY config in new format (providers.agy)."""
    from src.config import ai_cfg
    providers = getattr(ai_cfg, "providers", {}) if ai_cfg else {}
    agy_cfg = providers.get("agy", {}) if isinstance(providers, dict) else {}
    return {
        "enabled": agy_cfg.get("enabled", False),
        "key": os.getenv("AGY_API_KEY", "") or os.getenv("GEMINI_ANTIGRAVITY_API_KEY", ""),
        "model": agy_cfg.get("model", "agy-flash"),
        "effort": agy_cfg.get("effort", "medium"),
    }


def save_agy_config(data: AgyConfigRequest) -> dict:
    from dotenv import set_key
    
    # Secret goes to .env
    if data.key:
        env_path = str(__root__ / '.env')
        set_key(env_path, "AGY_API_KEY", data.key)
        os.environ["AGY_API_KEY"] = data.key
    
    if data.remember:
        config_path = __root__ / 'config.json'
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg_data = json.load(f)
        except Exception:
            cfg_data = {}
            
        if "ai" not in cfg_data:
            cfg_data["ai"] = {}
        
        if "providers" not in cfg_data["ai"]:
            cfg_data["ai"]["providers"] = {}
        
        # New format: providers.agy with enabled/model/effort/unsupported_models
        cfg_data["ai"]["providers"]["agy"] = {
            "enabled": data.enabled,
            "model": data.model,
            "unsupported_models": []
        }
        if hasattr(data, 'effort') and data.effort:
            cfg_data["ai"]["providers"]["agy"]["effort"] = data.effort
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(cfg_data, f, indent=2, ensure_ascii=False)
        
    # Update in-memory config
    if ai_cfg:
        if not hasattr(ai_cfg, 'providers') or not isinstance(getattr(ai_cfg, 'providers', None), dict):
            ai_cfg.providers = {}
        if not isinstance(ai_cfg.providers, dict):
            ai_cfg.providers = {}
        agy_obj = type('obj', (object,), {
            'enabled': data.enabled,
            'model': data.model,
            'unsupported_models': []
        })()
        if hasattr(data, 'effort') and data.effort:
            agy_obj.effort = data.effort
        ai_cfg.providers["agy"] = agy_obj
    
    return {"status": "ok"}


def get_onnx_config() -> dict:
    config_path = __root__ / 'config.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg_data = json.load(f)
    except Exception:
        cfg_data = {}
    onnx_data = cfg_data.get("onnx", {}) if isinstance(cfg_data, dict) else {}
    return {
        "enabled": onnx_data.get("enabled", True),
        "models_dir": onnx_data.get("models_dir", "models/onnx"),
        "execution_provider": onnx_data.get("execution_provider", "DirectMLExecutionProvider"),
        "default_model": onnx_data.get("default_model", "phi-3.5-mini-instruct-onnx"),
        "olive_precision": onnx_data.get("olive_precision", "int4"),
    }


def save_onnx_config(data: OnnxConfigRequest) -> dict:
    config_path = __root__ / 'config.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg_data = json.load(f)
    except Exception:
        cfg_data = {}

    if "onnx" not in cfg_data:
        cfg_data["onnx"] = {}

    cfg_data["onnx"]["enabled"] = data.enabled
    cfg_data["onnx"]["models_dir"] = data.models_dir
    cfg_data["onnx"]["execution_provider"] = data.execution_provider
    cfg_data["onnx"]["default_model"] = data.default_model
    cfg_data["onnx"]["olive_precision"] = data.olive_precision

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(cfg_data, f, indent=2, ensure_ascii=False)

    return {"status": "ok"}


def get_onnx_providers() -> dict:
    from src.ai.providers.onnx.olive_optimizer import get_available_execution_providers, check_olive_available
    available = get_available_execution_providers()
    return {
        "providers": available,
        "olive_available": check_olive_available(),
    }


def setup_config_endpoints(app: FastAPI) -> None:
    """Setup AI provider configuration endpoints.
    
    Args:
        app: FastAPI application instance to register endpoints with.
    """
    import json
    
    @app.get('/api/foundry/config')
    async def _get_foundry_config():
        return get_foundry_config()

    @app.post('/api/foundry/config')
    async def _save_foundry_config(data: FoundryConfigRequest):
        return save_foundry_config(data)

    @app.get('/api/ollama/config')
    async def _get_ollama_config():
        return get_ollama_config()

    @app.post('/api/ollama/config')
    async def _save_ollama_config(data: OllamaConfigRequest):
        return save_ollama_config(data)

    @app.get('/api/agy/config')
    async def _get_agy_config():
        return get_agy_config()

    @app.post('/api/agy/config')
    async def _save_agy_config(data: AgyConfigRequest):
        return save_agy_config(data)

    @app.get('/api/onnx/config')
    async def _get_onnx_config():
        return get_onnx_config()

    @app.post('/api/onnx/config')
    async def _save_onnx_config(data: OnnxConfigRequest):
        return save_onnx_config(data)

    @app.get('/api/onnx/providers')
    async def _get_onnx_providers():
        return get_onnx_providers()
