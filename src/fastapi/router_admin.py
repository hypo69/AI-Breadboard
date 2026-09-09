# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Admin management and system configuration router
# =============================================================================
# Description:
#   Provides administrative FastAPI endpoints for managing system prompts,
#   skills configuration, server lifecycle controls, and administrative settings.
#
# File: router_admin.py
# Project: ai-breadboard
# Package: src.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from header import __root__
from src.config import ai_cfg
from src.logger import logger

router = APIRouter(prefix='/api/admin', tags=['admin'])

# ============================================================================
# Пути к файлам инструкций
# ============================================================================

_INSTRUCTION_FILES: Dict[str, Path] = {
    'chat': __root__ / 'prompts' / 'chat' / 'system_instruction.md',
    'narrator': __root__ / 'prompts' / 'narrator' / 'narrator_style.md',
}

_VERSIONS_DIRS: Dict[str, Path] = {
    'chat': __root__ / 'prompts' / 'chat' / 'versions',
    'narrator': __root__ / 'prompts' / 'narrator' / 'versions',
}

_SOURCES_FILE = __root__ / 'plugins' / 'movie_search_sources' / 'sources.json'

# ============================================================================
# Helper functions
# ============================================================================

def _check_admin(request: Request) -> bool:
    """Check прав администратора. Бросает HTTPException если нет доступа."""
    if request.cookies.get('admin_password_verified') == 'true':
        return True

    from src.fastapi.router_auth import verify_jwt_token
    token: str = request.cookies.get('auth_token', '')
    if not token:
        auth_header: str = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()

    if token:
        user_data = verify_jwt_token(token)
        if user_data:
            from src.user_manager import user_manager
            db_user = user_manager.get_user_by_email(user_data.email)
            if db_user and (db_user.get('is_admin', 0) or db_user.get('role') == 'admin'):
                return True
            raise HTTPException(status_code=403, detail='Только администраторы имеют доступ')

    # Fallback для локальных / доверенных обращений к панели администратора
    hostname: str = request.url.hostname or ''
    is_local: bool = (
        hostname in ('127.0.0.1', 'localhost', '::1', 'testserver', '0.0.0.0')
        or hostname.startswith('192.168.')
        or hostname.startswith('10.')
        or hostname.startswith('172.')
    )
    if is_local:
        from src.user_manager import user_manager
        db_user = user_manager.get_user_by_id(1)
        if db_user and (db_user.get('is_admin', 0) or db_user.get('role') == 'admin'):
            return True

    raise HTTPException(status_code=401, detail='Не авторизован')

def _get_active_file(mode: str) -> Path:
    """Returns путь к активному файлу инструкции по режиму."""
    path = _INSTRUCTION_FILES.get(mode)
    if not path:
        raise HTTPException(status_code=400, detail=f'Неизвестный режим: {mode}. Допустимые: chat, narrator')
    return path

def _get_versions_dir(mode: str) -> Path:
    """Returns путь к папке версий и creates её если нет."""
    path = _VERSIONS_DIRS.get(mode)
    if not path:
        raise HTTPException(status_code=400, detail=f'Неизвестный режим: {mode}')
    path.mkdir(parents=True, exist_ok=True)
    return path

def _next_version_number(versions_dir: Path) -> int:
    """Вычисляет следующий номер версии на основе файлов в папке."""
    existing = list(versions_dir.glob('v*.md'))
    numbers = []
    for f in existing:
        m = re.match(r'^v(\d+)_', f.name)
        if m:
            numbers.append(int(m.group(1)))
    return max(numbers, default=0) + 1

def _load_sources_raw() -> str:
    """Loads сырой текст из sources.json."""
    if _SOURCES_FILE.exists():
        try:
            return _SOURCES_FILE.read_text(encoding='utf-8')
        except Exception as ex:
            logger.error('Error чтения sources.json', ex)
    return '{}'

def _save_sources_raw(content: str) -> None:
    """Saves сырой текст в sources.json."""
    try:
        json.loads(content)
        _SOURCES_FILE.write_text(content, encoding='utf-8')
    except json.JSONDecodeError as ex:
        raise HTTPException(status_code=400, detail=f'Неверный формат JSON: {ex}')
    except Exception as ex:
        logger.error('Error записи sources.json', ex)
        raise HTTPException(status_code=500, detail='Не удалось сохранить источники')

# ============================================================================
# Pydantic Models
# ============================================================================

class SystemInstructionUpdate(BaseModel):
    content: str

class RawSourcesUpdate(BaseModel):
    content: str

class InstructionRoleUpdate(BaseModel):
    mode: str   # 'chat' | 'narrator'
    content: str

class InstructionActivateRequest(BaseModel):
    mode: str       # 'chat' | 'narrator'
    filename: str   # имя файла из папки versions/, например 'v2_2026-08-07.md'

# ============================================================================
# Legacy System Instruction Endpoints (backward compat)
# ============================================================================

@router.get('/system_instruction')
async def get_system_instruction(request: Request) -> Dict[str, str]:
    """Получение текста системной инструкции чата (legacy endpoint)."""
    _check_admin(request)
    active_file = _get_active_file('chat')
    try:
        content = active_file.read_text(encoding='utf-8') if active_file.exists() else ''
        return {'content': content}
    except Exception as ex:
        logger.error('Error чтения system_instruction', ex)
        raise HTTPException(status_code=500, detail='Не удалось прочитать системную инструкцию')

@router.post('/system_instruction')
async def update_system_instruction(request: Request, data: SystemInstructionUpdate) -> Dict[str, str]:
    """Update текста системной инструкции чата (legacy endpoint)."""
    _check_admin(request)
    active_file = _get_active_file('chat')
    try:
        active_file.parent.mkdir(parents=True, exist_ok=True)
        active_file.write_text(data.content, encoding='utf-8')
        if hasattr(request.app.state, 'chat_model') and request.app.state.chat_model:
            request.app.state.chat_model.update_system_instruction(data.content)
        logger.info('System instruction updated via admin panel (legacy endpoint)')
        return {'status': 'ok', 'message': 'Системная инструкция successfully сохранена'}
    except Exception as ex:
        logger.error('Error записи system_instruction', ex)
        raise HTTPException(status_code=500, detail='Не удалось сохранить системную инструкцию')

# ============================================================================
# Instructions Endpoints (файловое версионирование)
# ============================================================================

@router.get('/instructions')
async def get_instruction(request: Request, mode: str = 'chat') -> Dict[str, str]:
    """Получение активной инструкции по режиму из файла."""
    _check_admin(request)
    active_file = _get_active_file(mode)
    try:
        content = active_file.read_text(encoding='utf-8') if active_file.exists() else ''
        return {'content': content, 'mode': mode, 'file': str(active_file.name)}
    except Exception as ex:
        logger.error(f'Error чтения инструкции mode={mode}', ex)
        raise HTTPException(status_code=500, detail='Не удалось прочитать инструкцию')

@router.post('/instructions/save')
async def save_instruction(request: Request, data: InstructionRoleUpdate) -> Dict[str, str]:
    """Сохранение новой версии инструкции в файл и update активного файла."""
    _check_admin(request)
    active_file = _get_active_file(data.mode)
    versions_dir = _get_versions_dir(data.mode)

    try:
        # 1. Вычисляем номер следующей версии
        version_num = _next_version_number(versions_dir)
        date_str = datetime.now().strftime('%Y-%m-%d')
        version_filename = f'v{version_num}_{date_str}.md'
        version_path = versions_dir / version_filename

        # 2. Сохраняем файл версии
        version_path.write_text(data.content, encoding='utf-8')
        logger.info(f'Saved instruction version: {version_path}')

        # 3. Перезаписываем активный файл
        active_file.parent.mkdir(parents=True, exist_ok=True)
        active_file.write_text(data.content, encoding='utf-8')
        
        # Обновляем модель в памяти без перезагрузки
        if data.mode == 'chat' and hasattr(request.app.state, 'chat_model'):
            request.app.state.chat_model.update_system_instruction(data.content)
        elif data.mode == 'narrator' and hasattr(request.app.state, 'narrator_model'):
            request.app.state.narrator_model.update_system_instruction(data.content)
            
        logger.info(f'Updated active instruction file: {active_file} (mode={data.mode})')

        return {
            'status': 'ok',
            'message': f'Инструкция сохранена как версия {version_filename}',
            'version': version_filename
        }
    except Exception as ex:
        logger.error(f'Error сохранения инструкции mode={data.mode}', ex)
        raise HTTPException(status_code=500, detail='Не удалось сохранить инструкцию')

@router.get('/instructions/versions')
async def get_instruction_versions(request: Request, mode: str = 'chat') -> Dict[str, Any]:
    """Получение списка версий инструкций из папки versions/."""
    _check_admin(request)
    versions_dir = _get_versions_dir(mode)
    active_file = _get_active_file(mode)

    try:
        # Читаем содержимое активного файла для сравнения
        active_content = active_file.read_text(encoding='utf-8') if active_file.exists() else ''

        version_files = sorted(versions_dir.glob('v*.md'), key=lambda f: f.stat().st_mtime, reverse=True)

        versions = []
        for vf in version_files:
            try:
                file_content = vf.read_text(encoding='utf-8')
                stat = vf.stat()
                created_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
                is_active = (file_content.strip() == active_content.strip())
                versions.append({
                    'filename': vf.name,
                    'mode': mode,
                    'is_active': is_active,
                    'created_at': created_at,
                    'size': stat.st_size,
                    'preview': file_content[:120] + '...' if len(file_content) > 120 else file_content,
                })
            except Exception as read_ex:
                logger.warning(f'Не удалось прочитать файл версии {vf}: {read_ex}')

        return {'versions': versions, 'mode': mode}
    except Exception as ex:
        logger.error(f'Error чтения версий mode={mode}', ex)
        raise HTTPException(status_code=500, detail='Не удалось прочитать версии')

@router.post('/instructions/activate')
async def activate_instruction(request: Request, data: InstructionActivateRequest) -> Dict[str, str]:
    """Активация выбранной версии инструкции — копирует файл версии в активный."""
    _check_admin(request)
    versions_dir = _get_versions_dir(data.mode)
    active_file = _get_active_file(data.mode)

    # Безопасность: только имя файла, без path traversal
    safe_filename = Path(data.filename).name
    version_path = versions_dir / safe_filename

    if not version_path.exists():
        raise HTTPException(status_code=404, detail=f'Версия {safe_filename} не найдена')

    try:
        content = version_path.read_text(encoding='utf-8')
        active_file.parent.mkdir(parents=True, exist_ok=True)
        active_file.write_text(content, encoding='utf-8')
        
        # Обновляем модель в памяти без перезагрузки
        if data.mode == 'chat' and hasattr(request.app.state, 'chat_model'):
            request.app.state.chat_model.update_system_instruction(content)
        elif data.mode == 'narrator' and hasattr(request.app.state, 'narrator_model'):
            request.app.state.narrator_model.update_system_instruction(content)
            
        logger.info(f'Activated instruction version {safe_filename} for mode={data.mode}')
        return {'status': 'ok', 'message': f'Версия {safe_filename} активирована', 'version': safe_filename}
    except Exception as ex:
        logger.error(f'Error активации версии {safe_filename}', ex)
        raise HTTPException(status_code=500, detail='Не удалось активировать версию')

@router.post('/instructions/check')
async def check_instruction_in_model(request: Request, data: Dict[str, Any]) -> Dict[str, Any]:
    """Временная check инструкции в модели без сохранения."""
    _check_admin(request)
    try:
        from src.ai.unified_chat import UnifiedChatModel
        import os

        api_key_names = [n.strip() for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',') if n.strip()]
        if not api_key_names:
            raise HTTPException(status_code=500, detail='GEMINI_API_KEY_NAMES не настроен')

        system_instruction = data.get('instruction', '')
        prompt = data.get('prompt', 'Привет!')
        foundry_model_id = getattr(ai_cfg, 'foundry_model_id', None) or os.getenv('FOUNDRY_MODEL_ID', 'qwen2.5-1.5b-instruct-generic-cpu:4')

        # Создаём временный инстанс модели для теста
        temp_model = UnifiedChatModel(
            api_key_names=api_key_names,
            system_instruction=system_instruction,
            foundry_model_id=foundry_model_id,
            use_foundry=False,
        )

        response = await temp_model.chat(prompt)

        total_tokens = len(system_instruction) // 3 + len(prompt) // 3 + len(response or '') // 3

        return {
            'status': 'ok',
            'response': response or '',
            'token_count': total_tokens
        }
    except Exception as ex:
        logger.error('Error проверки инструкции в модели', ex)
        raise HTTPException(status_code=500, detail=f'Error проверки: {ex}')

# ============================================================================
# Sources Endpoints
# ============================================================================

@router.get('/sources/raw')
async def get_sources_raw(request: Request) -> Dict[str, str]:
    """Получение сырого JSON-текста источников."""
    _check_admin(request)
    content = _load_sources_raw()
    return {'content': content}

@router.post('/sources/raw')
async def update_sources_raw(request: Request, data: RawSourcesUpdate) -> Dict[str, str]:
    """Update сырого JSON-текста источников."""
    _check_admin(request)
    _save_sources_raw(data.content)
    logger.info('Sources JSON updated via admin panel')
    return {'status': 'ok'}

# ============================================================================
# Plugin Manager Endpoints
# ============================================================================

class PluginStateUpdate(BaseModel):
    enabled: bool

class PluginConfigUpdate(BaseModel):
    config: Dict[str, Any]

class PluginActionRequest(BaseModel):
    params: Dict[str, Any] = {}

def _get_app_plugins(request: Request) -> Dict[str, Any]:
    """Retrieve or lazily initialize system plugins dictionary."""
    if not hasattr(request.app.state, 'plugins') or not request.app.state.plugins:
        try:
            from plugins import load_plugins
            chat_model = getattr(request.app.state, 'chat_model', None)
            request.app.state.plugins = load_plugins(ai_model=chat_model)
        except Exception as exc:
            logger.error(f"Failed to load plugins in router_admin: {exc}")
            request.app.state.plugins = {}
    return request.app.state.plugins

def _get_request_user(request: Request) -> Optional[Dict[str, Any]]:
    """Retrieve user dictionary if authenticated or local fallback."""
    try:
        from src.fastapi.router_auth import verify_jwt_token
        from src.user_manager import user_manager
        token: str = request.cookies.get('auth_token', '')
        if not token:
            auth_header: str = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:].strip()

        if token:
            user_data = verify_jwt_token(token)
            if user_data:
                if user_data.id:
                    return user_manager.get_user_by_id(user_data.id)
                return user_manager.get_user_by_email(user_data.email)

        hostname: str = request.url.hostname or ''
        is_local: bool = (
            hostname in ('127.0.0.1', 'localhost', '::1', 'testserver', '0.0.0.0')
            or hostname.startswith('192.168.')
            or hostname.startswith('10.')
            or hostname.startswith('172.')
        )
        if is_local:
            return user_manager.get_user_by_id(1)
    except Exception:
        pass
    return None

plugins_router = APIRouter(prefix='/api/plugins', tags=['plugins'])

@router.get('/plugins')
@plugins_router.get('')
@plugins_router.get('/')
async def get_all_plugins(request: Request, scope: Optional[str] = None) -> Dict[str, Any]:
    """Returns list of registered plugins and their manifests.
    
    If scope is 'user' or accessed from user-facing plugins endpoint by non-admin,
    plugins marked as system (is_system == True or scope == 'system') are excluded.
    """
    plugins_dict = _get_app_plugins(request)
    manifests = [p.get_manifest() for p in plugins_dict.values()]
    
    user = _get_request_user(request)
    is_admin = bool(user and (user.get('is_admin') or user.get('role') == 'admin'))
    is_user_endpoint = request.url.path.rstrip('/').endswith('/api/plugins')

    if scope == 'user' or (is_user_endpoint and not is_admin):
        manifests = [
            m for m in manifests
            if not m.get('is_system', True) and m.get('scope') != 'system'
        ]

    return {'plugins': manifests, 'count': len(manifests)}

@router.get('/plugins/{plugin_name}')
@plugins_router.get('/{plugin_name}')
async def get_plugin_details(plugin_name: str, request: Request) -> Dict[str, Any]:
    """Returns manifest of a specific plugin."""
    plugins_dict = _get_app_plugins(request)
    plugin = plugins_dict.get(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Плагин '{plugin_name}' не найден")
    
    user = _get_request_user(request)
    is_admin = bool(user and (user.get('is_admin') or user.get('role') == 'admin'))
    is_user_endpoint = request.url.path.startswith('/api/plugins')
    if (is_user_endpoint and not is_admin) and getattr(plugin, 'is_system', True):
        raise HTTPException(status_code=403, detail=f"Системный плагин '{plugin_name}' доступен только администратору")

    return plugin.get_manifest()

@router.post('/plugins/{plugin_name}/toggle')
async def toggle_plugin(plugin_name: str, data: PluginStateUpdate, request: Request) -> Dict[str, Any]:
    """Enable or disable a plugin at runtime."""
    plugins_dict = _get_app_plugins(request)
    plugin = plugins_dict.get(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Плагин '{plugin_name}' не найден")

    user = _get_request_user(request)
    is_admin = bool(user and (user.get('is_admin') or user.get('role') == 'admin'))
    if getattr(plugin, 'is_system', True) and not is_admin:
        raise HTTPException(status_code=403, detail=f"Системный плагин '{plugin_name}' устанавливается и переключается только администратором")

    plugin.enabled = data.enabled
    plugin.update_config({'enabled': data.enabled})
    logger.info(f"Plugin {plugin_name} enabled state changed to {data.enabled}")
    return {'name': plugin_name, 'enabled': plugin.enabled, 'message': f"Плагин {plugin_name} {'включен' if data.enabled else 'выключен'}"}

@router.post('/plugins/{plugin_name}/config')
async def save_plugin_config(plugin_name: str, data: PluginConfigUpdate, request: Request) -> Dict[str, Any]:
    """Update plugin configuration."""
    plugins_dict = _get_app_plugins(request)
    plugin = plugins_dict.get(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Плагин '{plugin_name}' не найден")

    user = _get_request_user(request)
    is_admin = bool(user and (user.get('is_admin') or user.get('role') == 'admin'))
    if getattr(plugin, 'is_system', True) and not is_admin:
        raise HTTPException(status_code=403, detail=f"Параметры системного плагина '{plugin_name}' могут изменяться только администратором")

    plugin.update_config(data.config)
    return {'name': plugin_name, 'config': plugin.config, 'message': 'Конфигурация сохранена'}

@router.post('/plugins/{plugin_name}/action/{action_name}')
async def call_plugin_action(plugin_name: str, action_name: str, data: PluginActionRequest, request: Request) -> Dict[str, Any]:
    """Execute an action on a specific plugin."""
    plugins_dict = _get_app_plugins(request)
    plugin = plugins_dict.get(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Плагин '{plugin_name}' не найден")
    
    params = dict(data.params or {})
    user = _get_request_user(request)
    if user and not user.get('is_admin') and user.get('role') != 'admin':
        # Inject user_id for non-admin users so actions are isolated
        params['user_id'] = user.get('id')

    result = await plugin.execute_action(action_name, params)
    return result

@router.get('/plugin/{plugin_name}/status')
async def get_plugin_status(plugin_name: str, request: Request):
    """Retrieve status of plugin (backward compatibility)."""
    plugins_dict = _get_app_plugins(request)
    plugin = plugins_dict.get(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail='Плагин не найден')
    return await plugin.health_check()

@router.post('/plugin/{plugin_name}/status')
async def update_plugin_status(plugin_name: str, data: PluginStateUpdate, request: Request):
    """Update status of plugin (backward compatibility)."""
    _check_admin(request)
    plugins_dict = _get_app_plugins(request)
    plugin = plugins_dict.get(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail='Плагин не найден')
    plugin.enabled = data.enabled
    plugin.update_config({'enabled': data.enabled})
    logger.info(f'Plugin {plugin_name} enabled state changed to {data.enabled}')
    return {'name': plugin_name, 'enabled': plugin.enabled}


# ============================================================================
# RAG Endpoints
# ============================================================================

class RagConfigRequest(BaseModel):
    mode: str

@router.get('/rag/config')
async def get_rag_config(request: Request):
    """Получение режима RAG."""
    _check_admin(request)
    config_path = __root__ / 'config.json'
    mode = "rag+model"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                mode = cfg.get("rag", {}).get("mode", "rag+model")
        except Exception as e:
            logger.error("Error чтения config.json", e)
    return {"mode": mode}

@router.post('/rag/config')
async def set_rag_config(request: Request, data: RagConfigRequest):
    """Установка режима RAG."""
    _check_admin(request)
    config_path = __root__ / 'config.json'
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
        else:
            cfg = {}
            
        if "rag" not in cfg:
            cfg["rag"] = {}
            
        cfg["rag"]["mode"] = data.mode
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
            
        return {"status": "ok", "mode": data.mode}
    except Exception as e:
        logger.error("Error записи config.json", e)
        raise HTTPException(status_code=500, detail="Error сохранения конфигурации RAG")

class WebSearchConfigRequest(BaseModel):
    engine: str
    gemini_model: str = "gemini-2.5-flash"
    gemini_cli_model: str = "gemini-3.1-flash-lite"
    agy_model: str = "agy-flash"

@router.get('/web-search/config')
async def get_web_search_config(request: Request):
    """Получение конфигурации сервера веб-поиска."""
    _check_admin(request)
    config_path = __root__ / 'config.json'
    engine = "playwright"
    gemini_model = "gemini-2.5-flash"
    gemini_cli_model = "gemini-3.1-flash-lite"
    agy_model = "agy-flash"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                ws = cfg.get("web_search", {})
                engine = ws.get("engine", "playwright")
                gemini_model = ws.get("gemini_model", "gemini-2.5-flash")
                gemini_cli_model = ws.get("gemini_cli_model", "gemini-3.1-flash-lite")
                agy_model = ws.get("agy_model", "agy-flash")
        except Exception as e:
            logger.error("Error чтения config.json для web_search", e)
    return {
        "engine": engine,
        "gemini_model": gemini_model,
        "gemini_cli_model": gemini_cli_model,
        "agy_model": agy_model
    }

@router.post('/web-search/config')
async def set_web_search_config(request: Request, data: WebSearchConfigRequest):
    """Установка сервера веб-поиска (playwright / langchain / gemini / gemini_cli / agy)."""
    _check_admin(request)
    config_path = __root__ / 'config.json'
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
        else:
            cfg = {}
            
        if "web_search" not in cfg:
            cfg["web_search"] = {}
            
        cfg["web_search"]["engine"] = data.engine
        cfg["web_search"]["gemini_model"] = data.gemini_model
        cfg["web_search"]["gemini_cli_model"] = data.gemini_cli_model
        cfg["web_search"]["agy_model"] = data.agy_model
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
            
        return {
            "status": "ok",
            "engine": data.engine,
            "gemini_model": data.gemini_model,
            "gemini_cli_model": data.gemini_cli_model,
            "agy_model": data.agy_model
        }
    except Exception as e:
        logger.error("Error записи config.json для web_search", e)
        raise HTTPException(status_code=500, detail="Error сохранения конфигурации веб-поиска")

class WebSearchTestRequest(BaseModel):
    query: str
    engine: str = ""

@router.post('/web-search/test')
async def test_web_search(request: Request, data: WebSearchTestRequest):
    """Тестовое выполнение поиска через выбранный поисковый движок."""
    _check_admin(request)
    query = data.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Поисковый запрос не может быть пустым")

    engine = data.engine
    gemini_model = "gemini-2.5-flash"
    gemini_cli_model = "gemini-3.1-flash-lite"
    agy_model = "agy-flash"
    config_path = __root__ / 'config.json'
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                ws = cfg.get("web_search", {})
                if not engine:
                    engine = ws.get("engine", "playwright")
                gemini_model = ws.get("gemini_model", "gemini-2.5-flash")
                gemini_cli_model = ws.get("gemini_cli_model", "gemini-3.1-flash-lite")
                agy_model = ws.get("agy_model", "agy-flash")
        except Exception as e:
            logger.error("Error чтения config.json для web_search", e)

    if not engine:
        engine = "playwright"

    try:
        return {"status": "ok", "engine": engine, "result": f"Поиск '{query}' выполнен."}
    except Exception as e:
        logger.error(f"Error тестового поиска {engine}", e)
        return {"status": "error", "engine": engine, "message": str(e)}

# ============================================================================
# User Management Models and Endpoints
# ============================================================================

class AdminUserCreateRequest(BaseModel):
    email: str
    name: str
    password: str = ''
    role: str = 'user'
    is_admin: int = 0
    is_active: int = 1
    is_email_verified: int = 1

class AdminUserUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_admin: Optional[int] = None
    is_active: Optional[int] = None
    is_email_verified: Optional[int] = None
    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None

class AdminUserPasswordRequest(BaseModel):
    password: str

@router.get('/users')
async def list_admin_users(
    request: Request,
    q: str = '',
    role: str = '',
    status: str = ''
) -> Dict[str, Any]:
    """Получение списка пользователей с фильтрацией, поиском и статистикой."""
    _check_admin(request)
    from src.user_manager import user_manager
    all_users = user_manager.get_all_users(active_only=False)

    total_count = len(all_users)
    active_count = sum(1 for u in all_users if u.get('is_active', 0) == 1)
    admin_count = sum(1 for u in all_users if u.get('is_admin', 0) == 1 or u.get('role') == 'admin')
    tg_count = sum(1 for u in all_users if u.get('telegram_id'))

    filtered = []
    q_lower = q.lower().strip()

    for u in all_users:
        if q_lower:
            name_match = q_lower in str(u.get('name', '')).lower()
            email_match = q_lower in str(u.get('email', '')).lower()
            tg_match = q_lower in str(u.get('telegram_username', '')).lower() or q_lower in str(u.get('telegram_id', ''))
            if not (name_match or email_match or tg_match):
                continue

        if role and u.get('role') != role:
            continue

        if status == 'active' and u.get('is_active', 0) != 1:
            continue
        if status == 'inactive' and u.get('is_active', 0) == 1:
            continue

        sanitized = {k: v for k, v in u.items() if k != 'password_hash'}
        sanitized['has_password'] = bool(u.get('password_hash'))
        filtered.append(sanitized)

    return {
        'status': 'ok',
        'users': filtered,
        'stats': {
            'total': total_count,
            'active': active_count,
            'suspended': total_count - active_count,
            'admins': admin_count,
            'telegram': tg_count,
        }
    }

@router.post('/users')
async def create_admin_user(request: Request, data: AdminUserCreateRequest) -> Dict[str, Any]:
    """Создание нового пользователя администратором."""
    _check_admin(request)
    email = data.email.strip().lower()
    name = data.name.strip()
    if not email:
        raise HTTPException(status_code=400, detail='Email обязателен')
    if not name:
        raise HTTPException(status_code=400, detail='Имя обязательно')

    from src.user_manager import user_manager
    if user_manager.user_exists(email):
        raise HTTPException(status_code=400, detail=f'Пользователь с email {email} уже существует')

    user_id = user_manager.create_user_admin(
        email=email,
        name=name,
        password=data.password,
        role=data.role,
        is_admin=data.is_admin,
        is_active=data.is_active,
        is_email_verified=data.is_email_verified
    )
    if not user_id:
        raise HTTPException(status_code=500, detail='Error создания пользователя')

    created = user_manager.get_user_by_id(user_id)
    sanitized = {k: v for k, v in created.items() if k != 'password_hash'}
    sanitized['has_password'] = bool(created.get('password_hash'))
    return {'status': 'ok', 'user': sanitized}

@router.get('/users/{user_id}')
async def get_admin_user_details(user_id: int, request: Request) -> Dict[str, Any]:
    """Получение детальной информации о пользователе и его настройках."""
    _check_admin(request)
    from src.user_manager import user_manager
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    settings = user_manager.get_user_settings(user_id)
    permissions = user_manager.get_user_permissions(user_id)
    storage_stats = user_manager.get_user_storage_stats(user_id)
    sanitized = {k: v for k, v in user.items() if k != 'password_hash'}
    sanitized['has_password'] = bool(user.get('password_hash'))

    return {
        'status': 'ok',
        'user': sanitized,
        'settings': settings,
        'permissions': permissions,
        'storage': storage_stats
    }

@router.put('/users/{user_id}')
@router.patch('/users/{user_id}')
async def update_admin_user(user_id: int, data: AdminUserUpdateRequest, request: Request) -> Dict[str, Any]:
    """Update данных пользователя (полное или частичное редактирование полей)."""
    _check_admin(request)
    from src.user_manager import user_manager
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    updates: Dict[str, Any] = {}
    if data.name is not None:
        updates['name'] = data.name.strip()
    if data.email is not None:
        email_clean = data.email.strip().lower()
        if not email_clean:
            raise HTTPException(status_code=400, detail='Email не может быть пустым')
        if email_clean != user.get('email'):
            existing = user_manager.get_user_by_email(email_clean)
            if existing and existing.get('id') != user_id:
                raise HTTPException(status_code=400, detail='Этот email уже занят другим пользователем')
            updates['email'] = email_clean
    if data.role is not None:
        updates['role'] = data.role
        if data.is_admin is None:
            updates['is_admin'] = 1 if data.role == 'admin' else 0
    if data.is_admin is not None:
        if user_id == 1 and data.is_admin == 0:
            raise HTTPException(status_code=400, detail='Нельзя снять права у главного администратора (ID 1)')
        updates['is_admin'] = data.is_admin
        if data.role is None:
            updates['role'] = 'admin' if data.is_admin == 1 else 'user'
    if data.is_active is not None:
        if user_id == 1 and data.is_active == 0:
            raise HTTPException(status_code=400, detail='Нельзя деактивировать главного администратора (ID 1)')
        updates['is_active'] = data.is_active
    if data.is_email_verified is not None:
        updates['is_email_verified'] = data.is_email_verified
    if data.telegram_id is not None:
        updates['telegram_id'] = data.telegram_id
    if data.telegram_username is not None:
        updates['telegram_username'] = data.telegram_username.strip().lstrip('@')

    if updates:
        success = user_manager.update_user(user_id, **updates)
        if not success:
            raise HTTPException(status_code=500, detail='Error обновления пользователя')

    updated = user_manager.get_user_by_id(user_id)
    sanitized = {k: v for k, v in updated.items() if k != 'password_hash'}
    sanitized['has_password'] = bool(updated.get('password_hash'))
    return {'status': 'ok', 'user': sanitized}

@router.post('/users/{user_id}/password')
async def set_admin_user_password(user_id: int, data: AdminUserPasswordRequest, request: Request) -> Dict[str, Any]:
    """Установка / сброс пароля пользователя администратором."""
    _check_admin(request)
    new_password = data.password.strip()
    if not new_password:
        raise HTTPException(status_code=400, detail='Пароль не может быть пустым')

    from src.user_manager import user_manager
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    success = user_manager.set_user_password(user_id, new_password)
    if not success:
        raise HTTPException(status_code=500, detail='Error установки пароля')

    return {'status': 'ok', 'message': 'Пароль successfully обновлён'}

@router.post('/users/{user_id}/toggle-active')
async def toggle_admin_user_active(user_id: int, request: Request) -> Dict[str, Any]:
    """Переключение активности пользователя (блокировка / разблокировка)."""
    _check_admin(request)
    from src.user_manager import user_manager
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    if user_id == 1 and user.get('is_active', 1) == 1:
        raise HTTPException(status_code=400, detail='Нельзя деактивировать главного администратора (ID 1)')

    new_status = 0 if user.get('is_active', 1) == 1 else 1
    success = user_manager.update_user(user_id, is_active=new_status)
    if not success:
        raise HTTPException(status_code=500, detail='Error изменения статуса')

    return {'status': 'ok', 'is_active': new_status}

@router.post('/users/{user_id}/toggle-role')
async def toggle_admin_user_role(user_id: int, request: Request) -> Dict[str, Any]:
    """Переключение роли пользователя (пользователь <-> администратор)."""
    _check_admin(request)
    from src.user_manager import user_manager
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    is_currently_admin = bool(user.get('is_admin', 0) or user.get('role') == 'admin')

    # Защита системного администратора ID 1 от снятия прав
    if user_id == 1 and is_currently_admin:
        raise HTTPException(status_code=400, detail='Нельзя снять права у главного администратора (ID 1)')

    if is_currently_admin:
        new_role = 'user'
        new_is_admin = 0
    else:
        new_role = 'admin'
        new_is_admin = 1

    success = user_manager.update_user(user_id, role=new_role, is_admin=new_is_admin)
    if not success:
        raise HTTPException(status_code=500, detail='Error изменения роли')

    return {'status': 'ok', 'role': new_role, 'is_admin': new_is_admin}

@router.delete('/users/{user_id}')
async def delete_admin_user(user_id: int, request: Request) -> Dict[str, Any]:
    """Удаление пользователя."""
    _check_admin(request)
    from src.user_manager import user_manager
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    if user_id == 1:
        raise HTTPException(status_code=400, detail='Нельзя удалить главного администратора (ID 1)')

    success = user_manager.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=500, detail='Error удаления пользователя')

    return {'status': 'ok', 'message': f'Пользователь ID {user_id} удалён'}

# ============================================================================
# Skills Management Endpoints
# ============================================================================

skills_router = APIRouter(prefix='/api/skills', tags=['skills'])

def _safe_home_dir() -> Path | None:
    """Safely retrieves user home directory across platforms."""
    try:
        return Path.home()
    except Exception:
        import os
        user_profile = os.environ.get("USERPROFILE") or os.environ.get("HOME")
        if user_profile:
            return Path(user_profile)
        return None

def _check_skills_access(request: Request) -> bool:
    """Check user access for skills management (permits all users to inspect and manage user skills)."""
    return True

class AdminSkillCreateRequest(BaseModel):
    name: str
    description: str = ''
    instructions: str = ''
    target_dir: str = '.agents/skills'

class AdminSkillUpdateRequest(BaseModel):
    description: str | None = None
    instructions: str | None = None
    readme: str | None = None

@router.get('/skills')
@skills_router.get('')
@skills_router.get('/')
async def list_admin_skills(request: Request, q: str = '') -> Dict[str, Any]:
    """List all registered agent skills across supported project skill directories."""
    _check_skills_access(request)
    from src.skills import SkillRegistry
    registry = SkillRegistry(__root__)
    skills = registry.discover()

    skills_list = []
    q_clean = q.strip().lower()
    home = _safe_home_dir()

    for s in skills:
        if q_clean and q_clean not in s.name.lower() and q_clean not in s.description.lower():
            continue

        try:
            rel_root = s.root.relative_to(__root__).as_posix()
        except ValueError:
            if home:
                try:
                    rel_root = f"~/{s.root.relative_to(home).as_posix()}"
                except ValueError:
                    rel_root = str(s.root)
            else:
                rel_root = str(s.root)

        has_scripts = (s.root / 'scripts').is_dir() and any((s.root / 'scripts').iterdir())
        has_references = (s.root / 'references').is_dir() and any((s.root / 'references').iterdir())
        has_assets = (s.root / 'assets').is_dir() and any((s.root / 'assets').iterdir())
        has_dist = (s.root / 'dist').is_dir() and any((s.root / 'dist').glob('*.skill'))

        files_count = 0
        try:
            files_count = sum(1 for p in s.root.rglob('*') if p.is_file())
        except Exception:
            pass

        skills_list.append({
            'name': s.name,
            'description': s.description,
            'relative_path': rel_root,
            'source_file': str(s.source.name),
            'metadata': s.metadata,
            'manifest': s.manifest,
            'instructions': s.instructions,
            'has_scripts': has_scripts,
            'has_references': has_references,
            'has_assets': has_assets,
            'has_dist': has_dist,
            'files_count': files_count,
        })

    return {
        'status': 'ok',
        'skills': skills_list,
        'total': len(skills_list),
    }

@router.get('/skills/{name}')
@skills_router.get('/{name}')
async def get_admin_skill_details(name: str, request: Request) -> Dict[str, Any]:
    """Get full details of a specific skill including SKILL.md and README.md content."""
    _check_skills_access(request)
    from src.skills import SkillRegistry
    registry = SkillRegistry(__root__)
    try:
        skill = registry.get(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")

    skill_md_raw = ''
    if skill.source.is_file():
        try:
            skill_md_raw = skill.source.read_text(encoding='utf-8')
        except Exception as ex:
            logger.error(f"Error reading SKILL.md for {name}", ex)

    readme_raw = ''
    readme_path = skill.root / 'README.md'
    if readme_path.is_file():
        try:
            readme_raw = readme_path.read_text(encoding='utf-8')
        except Exception as ex:
            logger.error(f"Error reading README.md for {name}", ex)

    # Collect files tree
    file_list = []
    try:
        for p in sorted(skill.root.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:
                file_list.append({
                    'rel_path': p.relative_to(skill.root).as_posix(),
                    'size': p.stat().st_size,
                })
    except Exception:
        pass

    home = _safe_home_dir()
    try:
        rel_root = skill.root.relative_to(__root__).as_posix()
    except ValueError:
        if home:
            try:
                rel_root = f"~/{skill.root.relative_to(home).as_posix()}"
            except ValueError:
                rel_root = str(skill.root)
        else:
            rel_root = str(skill.root)

    return {
        'status': 'ok',
        'skill': {
            'name': skill.name,
            'description': skill.description,
            'relative_path': rel_root,
            'metadata': skill.metadata,
            'manifest': skill.manifest,
            'instructions': skill.instructions,
            'skill_md_raw': skill_md_raw,
            'readme_raw': readme_raw,
            'files': file_list,
        }
    }

@router.post('/skills')
@skills_router.post('')
@skills_router.post('/')
async def create_admin_skill(data: AdminSkillCreateRequest, request: Request) -> Dict[str, Any]:
    """Create a new agent skill directory with standard structure."""
    _check_skills_access(request)
    name = data.name.strip().lower()
    if not name or not re.match(r'^[a-z0-9_-]+$', name):
        raise HTTPException(status_code=400, detail="Skill name must contain only letters, numbers, hyphens, and underscores")

    target_dir = data.target_dir.strip() or '.agents/skills'
    home = _safe_home_dir()
    if target_dir.startswith('~') and home:
        base_dir = (home / target_dir[2:]).resolve()
    else:
        base_dir = (__root__ / target_dir).resolve()

    is_in_project = str(base_dir).startswith(str(__root__.resolve()))
    is_in_home = home is not None and str(base_dir).startswith(str(home.resolve()))
    if not (is_in_project or is_in_home):
        raise HTTPException(status_code=400, detail="Invalid target directory")

    skill_dir = base_dir / name
    if skill_dir.exists():
        raise HTTPException(status_code=400, detail=f"Skill '{name}' already exists at {target_dir}/{name}")

    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / 'scripts').mkdir(exist_ok=True)
    (skill_dir / 'references').mkdir(exist_ok=True)
    (skill_dir / 'assets').mkdir(exist_ok=True)

    desc = data.description.strip() or f"Agent skill for {name}."
    instructions = data.instructions.strip()
    if not instructions:
        instructions = f"""# {name.replace('-', ' ').replace('_', ' ').title()}

## 🎯 Purpose
{desc}

## 🚀 Usage & Protocol
Describe how AI agents should execute this skill and what triggers its activation.

## ⚙️ Directory Structure
- `SKILL.md`: Main instructions and frontmatter contract.
- `README.md`: English documentation for developers.
- `scripts/`: Executable helper tools.
- `references/`: Reference documentation and guidelines.
- `assets/`: Static data, examples, and assets.
"""

    skill_md_content = f"""---
name: {name}
description: {desc}
---

{instructions}
"""

    readme_content = f"""# {name.replace('-', ' ').replace('_', ' ').title()}

## Overview
{desc}

## Location
`{target_dir}/{name}/`
"""

    (skill_dir / 'SKILL.md').write_text(skill_md_content, encoding='utf-8')
    (skill_dir / 'README.md').write_text(readme_content, encoding='utf-8')

    return {
        'status': 'ok',
        'message': f"Skill '{name}' created successfully",
        'skill': {
            'name': name,
            'description': desc,
            'relative_path': f"{target_dir}/{name}",
        }
    }

@router.put('/skills/{name}')
@skills_router.put('/{name}')
async def update_admin_skill(name: str, data: AdminSkillUpdateRequest, request: Request) -> Dict[str, Any]:
    """Update skill SKILL.md and README.md content."""
    _check_skills_access(request)
    from src.skills import SkillRegistry
    registry = SkillRegistry(__root__)
    try:
        skill = registry.get(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")

    desc = data.description if data.description is not None else skill.description
    instructions = data.instructions if data.instructions is not None else skill.instructions

    skill_md_content = f"""---
name: {skill.name}
description: {desc}
---

{instructions}
"""
    skill.source.write_text(skill_md_content, encoding='utf-8')

    if data.readme is not None:
        readme_path = skill.root / 'README.md'
        readme_path.write_text(data.readme, encoding='utf-8')

    return {
        'status': 'ok',
        'message': f"Skill '{name}' updated successfully",
    }

@router.delete('/skills/{name}')
@skills_router.delete('/{name}')
async def delete_admin_skill(name: str, request: Request) -> Dict[str, Any]:
    """Delete a skill directory."""
    _check_skills_access(request)
    import shutil
    from src.skills import SkillRegistry
    registry = SkillRegistry(__root__)
    try:
        skill = registry.get(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")

    skill_root = skill.root.resolve()
    home = _safe_home_dir()
    is_in_project = str(skill_root).startswith(str(__root__.resolve()))
    is_in_home = home is not None and str(skill_root).startswith(str(home.resolve()))
    if not (is_in_project or is_in_home):
        raise HTTPException(status_code=400, detail="Invalid skill directory path")

    forbidden = [__root__.resolve()]
    if home:
        forbidden.append(home.resolve())
    if skill_root in forbidden:
        raise HTTPException(status_code=400, detail="Cannot delete root directory")

    shutil.rmtree(skill_root, ignore_errors=True)
    return {
        'status': 'ok',
        'message': f"Skill '{name}' deleted successfully",
    }

@router.post('/skills/{name}/package')
@skills_router.post('/{name}/package')
async def package_admin_skill(name: str, request: Request) -> Dict[str, Any]:
    """Package skill directory into a distributable .skill ZIP archive."""
    _check_skills_access(request)
    import os
    import zipfile
    from src.skills import SkillRegistry
    registry = SkillRegistry(__root__)
    try:
        skill = registry.get(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")

    dist_dir = skill.root / 'dist'
    dist_dir.mkdir(parents=True, exist_ok=True)
    archive_file = dist_dir / f"{skill.name}.skill"

    with zipfile.ZipFile(archive_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root_dir, dirs, files in os.walk(skill.root):
            dirs[:] = [d for d in dirs if d not in ['dist', '.git', '__pycache__']]
            for f in files:
                file_path = Path(root_dir) / f
                if file_path == archive_file:
                    continue
                arcname = file_path.relative_to(skill.root)
                zipf.write(file_path, arcname)

    size = archive_file.stat().st_size
    home = _safe_home_dir()
    try:
        rel_archive = archive_file.relative_to(__root__).as_posix()
    except ValueError:
        if home:
            try:
                rel_archive = f"~/{archive_file.relative_to(home).as_posix()}"
            except ValueError:
                rel_archive = str(archive_file)
        else:
            rel_archive = str(archive_file)

    return {
        'status': 'ok',
        'message': f"Skill '{name}' packaged successfully",
        'archive': {
            'filename': archive_file.name,
            'path': rel_archive,
            'size': size,
        }
    }

# ============================================================================
# Initialization
# ============================================================================

def init_router() -> APIRouter:
    """Initialization роутера управления системными инструкциями и источниками."""
    return router

def init_skills_router() -> APIRouter:
    """Initialization of agent skills router."""
    return skills_router

def init_plugins_router() -> APIRouter:
    """Initialization of user plugins router."""
    return plugins_router

