# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Model Pool State Manager for AI Providers
# =============================================================================
# Description:
#   Manages model pools for multiple AI providers (gemini, gemini_cli, agy, foundry, ollama).
#   Tracks model status (active, exhausted, disabled) and handles 503 error recovery with
#   automatic failover to next available model after 5 retry attempts.
#
# File: model_pool_state.py
# Project: ai-breadboard
# Package: src.ai.orchestration
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from header import __root__
from logger.logger import logger

_SECRETS_DIR: Path = __root__ / 'src' / 'secrets'
_POOLS_FILE: Path = _SECRETS_DIR / 'model_pools.json'

# Default model pools for each provider
_DEFAULT_POOLS: Dict[str, List[str]] = {
    'gemini': [
        'gemini-flash-latest',
        'gemini-flash-lite-latest',
        'gemini-3.6-flash',
        'gemini-3.7-flash',
        'gemini-pro-latest',
    ],
    'gemini_cli': [
        'gemini-3.1-flash-lite',
        'gemini-2.5-flash',
        'gemini-2.5-pro',
        'gemini-3.1-pro-preview',
        'gemini-3.1-flash-lite-preview',
    ],
    'agy': [
        'agy-flash',
        'agy-pro',
    ],
    'ollama': [
        'llama3',
        'mistral',
        'codellama',
        'gemma',
        'phi3',
    ],
}

# Retry limits for exhausted models
_MAX_RETRY_ATTEMPTS: int = 5


def _ensure_secrets_dir() -> None:
    """Ensure that the secrets directory exists on the filesystem."""
    try:
        _SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as ex:
        logger.error(f'Failed to create secrets directory: {ex}')


def _now_iso() -> str:
    """Get current UTC timestamp in ISO 8601 string format.

    Returns:
        str: ISO formatted UTC datetime string.
    """
    return datetime.now(timezone.utc).isoformat()


def _now_ts() -> float:
    """Get current UTC timestamp as Unix epoch float.

    Returns:
        float: Unix timestamp in seconds.
    """
    return datetime.now(timezone.utc).timestamp()


def _iso_to_ts(iso_str: str) -> float:
    """Convert ISO formatted string into Unix timestamp.

    Args:
        iso_str (str): Datetime string in ISO 8601 format.

    Returns:
        float: Unix epoch timestamp or 0.0 on parsing error.
    """
    if not iso_str:
        return 0.0
    try:
        cleaned = iso_str.replace('Z', '+00:00')
        return datetime.fromisoformat(cleaned).timestamp()
    except Exception:
        return 0.0


def _load_pools_file() -> Dict[str, Dict[str, Any]]:
    """Load model pools data from JSON file.

    If file does not exist, initializes with default pools.

    Returns:
        Dict[str, Dict[str, Any]]: Model pools data structure.
    """
    if _POOLS_FILE.exists():
        try:
            content = _POOLS_FILE.read_text(encoding='utf-8').strip()
            if content:
                data = json.loads(content)
                if isinstance(data, dict):
                    return data
        except Exception as ex:
            logger.warning(f'Error reading {_POOLS_FILE}: {ex}')

    # Initialize with default pools if file does not exist
    return _initialize_default_pools()


def _initialize_default_pools() -> Dict[str, Dict[str, Any]]:
    """Initialize default model pools structure.

    Returns:
        Dict[str, Dict[str, Any]]: Default model pools data.
    """
    pools: Dict[str, Dict[str, Any]] = {}

    # Process each provider
    for provider in ['gemini', 'gemini_cli', 'agy', 'ollama']:
        models: Dict[str, Dict[str, Any]] = {}
        default_list = _DEFAULT_POOLS.get(provider, [])
        
        # For agy provider, generate agy- prefixed versions
        if provider == 'agy':
            gemini_pools = _DEFAULT_POOLS.get('gemini', [])
            for model in gemini_pools:
                if model.startswith('gemini-'):
                    agy_name = 'agy-' + model[len('gemini-'):]
                else:
                    agy_name = 'agy-' + model
                models[agy_name] = {
                    'status': 'active',
                    'exhausted_at': '',
                    'retry_count': 0,
                }
        else:
            for model in default_list:
                models[model] = {
                    'status': 'active',
                    'exhausted_at': '',
                    'retry_count': 0,
                }
        
        pools[provider] = {'models': models}

    # Handle foundry provider - load from config or fallback
    foundry_models = _get_foundry_models()
    if foundry_models:
        foundry_model_dict = {}
        for model in foundry_models:
            foundry_model_dict[model] = {
                'status': 'active',
                'exhausted_at': '',
                'retry_count': 0,
            }
        pools['foundry'] = {'models': foundry_model_dict}

    # Save initialized pools
    _save_pools_file(pools)

    return pools


def _get_foundry_models() -> List[str]:
    """Get Foundry models from config or fallback list.

    Returns:
        List[str]: List of Foundry model identifiers.
    """
    try:
        from src.config import ai_cfg
        models = getattr(ai_cfg, 'foundry_models', None)
        if models and isinstance(models, list):
            return models
    except Exception as ex:
        logger.warning(f'Could not load Foundry models from config: {ex}')

    # Fallback models
    return [
        'llama-3-70b-instruct',
        'mistral-large',
        'codellama-34b-instruct',
        'gemma-2-9b-instruct',
        'phi-3-medium-128k',
    ]


def _save_pools_file(data: Dict[str, Dict[str, Any]]) -> bool:
    """Write model pools data to JSON file safely.

    Args:
        data (Dict[str, Dict[str, Any]]): Pools data to serialize.

    Returns:
        bool: True on success, False on failure.
    """
    try:
        _ensure_secrets_dir()
        _POOLS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _POOLS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        return True
    except Exception as ex:
        logger.error(f'Failed to save pools to {_POOLS_FILE}: {ex}')
        return False


def load_model_pool(provider: str) -> List[Dict[str, Any]]:
    """Load model pool for specified provider.

    Args:
        provider (str): Provider name (gemini, gemini_cli, agy, foundry, ollama).

    Returns:
        List[Dict[str, Any]]: List of model information dictionaries.
    """
    _ensure_secrets_dir()
    pools = _load_pools_file()

    if provider not in pools:
        # Initialize provider pool if not exists
        models = _DEFAULT_POOLS.get(provider, [])
        if provider == 'agy':
            gemini_models = _DEFAULT_POOLS.get('gemini', [])
            models = ['agy-' + m[len('gemini-'):] for m in gemini_models if m.startswith('gemini-')]
        pools[provider] = {'models': {m: {'status': 'active', 'exhausted_at': '', 'retry_count': 0} for m in models}}
        _save_pools_file(pools)

    provider_data = pools.get(provider, {})
    models_data = provider_data.get('models', {})

    result = []
    for model_name, model_info in models_data.items():
        result.append({
            'model_name': model_name,
            'status': model_info.get('status', 'active'),
            'exhausted_at': model_info.get('exhausted_at', ''),
            'retry_count': model_info.get('retry_count', 0),
        })

    return result


def mark_model_exhausted(provider: str, model_name: str) -> None:
    """Mark a model as exhausted due to 503 error.

    Args:
        provider (str): Provider name.
        model_name (str): Model identifier to mark as exhausted.
    """
    pools = _load_pools_file()

    if provider not in pools:
        load_model_pool(provider)
        pools = _load_pools_file()

    provider_data = pools.get(provider, {})
    models = provider_data.get('models', {})

    if model_name not in models:
        models[model_name] = {
            'status': 'active',
            'exhausted_at': '',
            'retry_count': 0,
        }

    model_info = models[model_name]
    retry_count = model_info.get('retry_count', 0) + 1
    model_info['retry_count'] = retry_count

    if retry_count >= _MAX_RETRY_ATTEMPTS:
        # Exhausted after max retries - mark as exhausted
        model_info['status'] = 'exhausted'
        model_info['exhausted_at'] = _now_iso()
        model_info['retry_count'] = 0
        logger.warning(f'Model "{model_name}" for provider "{provider}" marked as exhausted after {retry_count} attempts.')
    else:
        # Still retrying, keep active
        model_info['status'] = 'active'
        logger.info(f'Model "{model_name}" retry {retry_count}/{_MAX_RETRY_ATTEMPTS} for provider "{provider}".')

    pools[provider]['models'] = models
    _save_pools_file(pools)


def get_available_models(provider: str) -> List[Dict[str, Any]]:
    """Get list of available (non-exhausted, non-disabled) models for provider.

    Args:
        provider (str): Provider name.

    Returns:
        List[Dict[str, Any]]: List of available model information.
    """
    models = load_model_pool(provider)
    return [m for m in models if m['status'] in ('active', 'exhausted')]


def switch_model(provider: str, current_model: str) -> Optional[str]:
    """Switch to next available model for provider.

    Args:
        provider (str): Provider name.
        current_model (str): Current model identifier.

    Returns:
        Optional[str]: New model identifier, or None if no available models.
    """
    pools = _load_pools_file()

    if provider not in pools:
        return None

    provider_data = pools.get(provider, {})
    models = provider_data.get('models', {})

    # Get all models and their status
    model_list = list(models.keys())

    if not model_list:
        return None

    # Find next available model starting after current
    try:
        current_idx = model_list.index(current_model)
    except ValueError:
        current_idx = -1

    # Try to find next active model
    start_idx = (current_idx + 1) % len(model_list)
    for i in range(len(model_list)):
        idx = (start_idx + i) % len(model_list)
        model_name = model_list[idx]
        model_info = models.get(model_name, {})
        status = model_info.get('status', 'active')

        if status == 'active':
            return model_name

    # If no active models, try exhausted (maybe 24h cooldown passed)
    for i in range(len(model_list)):
        idx = (start_idx + i) % len(model_list)
        model_name = model_list[idx]
        model_info = models.get(model_name, {})
        status = model_info.get('status', 'active')

        if status == 'exhausted':
            return model_name

    # No available models
    logger.warning(f'No available models for provider "{provider}"')
    return None


def get_model_status(provider: str, model_name: str) -> Optional[str]:
    """Get status of specific model.

    Args:
        provider (str): Provider name.
        model_name (str): Model identifier.

    Returns:
        Optional[str]: Model status (active, exhausted, disabled), or None if not found.
    """
    pools = _load_pools_file()

    if provider not in pools:
        return None

    provider_data = pools.get(provider, {})
    models = provider_data.get('models', {})

    if model_name not in models:
        return None

    return models[model_name].get('status', 'active')


def save_model_pool(provider: str, models: List[Dict[str, Any]]) -> bool:
    """Save model pool for provider.

    Args:
        provider (str): Provider name.
        models (List[Dict[str, Any]]): List of model information dictionaries.

    Returns:
        bool: True on success.
    """
    pools = _load_pools_file()

    if provider not in pools:
        pools[provider] = {'models': {}}

    provider_data = pools[provider]
    models_dict: Dict[str, Dict[str, Any]] = {}

    for model_info in models:
        model_name = model_info.get('model_name', '')
        if model_name:
            models_dict[model_name] = {
                'status': model_info.get('status', 'active'),
                'exhausted_at': model_info.get('exhausted_at', ''),
                'retry_count': model_info.get('retry_count', 0),
            }

    provider_data['models'] = models_dict
    pools[provider] = provider_data

    success = _save_pools_file(pools)
    if success:
        logger.info(f'Model pool for provider "{provider}" saved.')
    return success


def reset_model_exhausted(provider: str, model_name: str) -> bool:
    """Reset exhausted model status to active.

    Args:
        provider (str): Provider name.
        model_name (str): Model identifier to reset.

    Returns:
        bool: True if model was reset.
    """
    pools = _load_pools_file()

    if provider not in pools:
        return False

    provider_data = pools.get(provider, {})
    models = provider_data.get('models', {})

    if model_name not in models:
        return False

    models[model_name]['status'] = 'active'
    models[model_name]['exhausted_at'] = ''
    models[model_name]['retry_count'] = 0

    pools[provider]['models'] = models
    success = _save_pools_file(pools)

    if success:
        logger.info(f'Model "{model_name}" for provider "{provider}" reset to active.')

    return success


def get_pool_status(provider: str) -> Dict[str, Any]:
    """Get overall status of model pool for provider.

    Args:
        provider (str): Provider name.

    Returns:
        Dict[str, Any]: Pool status information.
    """
    pools = _load_pools_file()

    if provider not in pools:
        load_model_pool(provider)
        pools = _load_pools_file()

    provider_data = pools.get(provider, {})
    models = provider_data.get('models', {})

    status_counts = {'active': 0, 'exhausted': 0, 'disabled': 0}
    model_statuses = []

    for model_name, model_info in models.items():
        status = model_info.get('status', 'active')
        status_counts[status] = status_counts.get(status, 0) + 1

        model_statuses.append({
            'model_name': model_name,
            'status': status,
            'exhausted_at': model_info.get('exhausted_at', ''),
            'retry_count': model_info.get('retry_count', 0),
        })

    total = len(models)
    active = status_counts.get('active', 0)

    return {
        'provider': provider,
        'total_models': total,
        'active_models': active,
        'exhausted_models': status_counts.get('exhausted', 0),
        'disabled_models': status_counts.get('disabled', 0),
        'available_for_use': active > 0,
        'models': model_statuses,
    }
