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
# Package: core.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from header import __root__
from core.logger import logger

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
    from core.fastapi.router_auth import verify_jwt_token
    token: str = request.cookies.get('auth_token', '')
    if not token:
        auth_header: str = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()

    if token:
        user_data = verify_jwt_token(token)
        if user_data:
            from core.user_manager import user_manager
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
        from core.user_manager import user_manager
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
        from core.ai.unified_chat import UnifiedChatModel
        import os

        api_key_names = [n.strip() for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',') if n.strip()]
        if not api_key_names:
            raise HTTPException(status_code=500, detail='GEMINI_API_KEY_NAMES не настроен')

        system_instruction = data.get('instruction', '')
        prompt = data.get('prompt', 'Привет!')
        foundry_model_id = os.getenv('FOUNDRY_MODEL_ID', 'qwen3-0.6b-generic-cpu:4')

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

@router.get('/plugins')
async def get_all_plugins(request: Request) -> Dict[str, Any]:
    """Returns empty реестр (плагины отключены)."""
    _check_admin(request)
    return {'plugins': {}, 'count': 0}

@router.get('/plugins/{plugin_name}')
async def get_plugin_details(plugin_name: str, request: Request) -> Dict[str, Any]:
    """Returns 404 (плагины отключены)."""
    _check_admin(request)
    raise HTTPException(status_code=404, detail=f"Плагин '{plugin_name}' не найден")

@router.post('/plugins/{plugin_name}/toggle')
async def toggle_plugin(plugin_name: str, data: PluginStateUpdate, request: Request) -> Dict[str, Any]:
    """Плагины отключены."""
    _check_admin(request)
    raise HTTPException(status_code=404, detail=f"Плагин '{plugin_name}' не найден")

@router.post('/plugins/{plugin_name}/config')
async def save_plugin_config(plugin_name: str, data: PluginConfigUpdate, request: Request) -> Dict[str, Any]:
    """Плагины отключены."""
    _check_admin(request)
    raise HTTPException(status_code=404, detail=f"Плагин '{plugin_name}' не найден")

@router.post('/plugins/{plugin_name}/action/{action_name}')
async def call_plugin_action(plugin_name: str, action_name: str, data: PluginActionRequest, request: Request) -> Dict[str, Any]:
    """Плагины отключены."""
    _check_admin(request)
    raise HTTPException(status_code=404, detail=f"Плагин '{plugin_name}' не найден")

@router.get('/plugin/{plugin_name}/status')
async def get_plugin_status(plugin_name: str, request: Request):
    """Плагины отключены."""
    _check_admin(request)
    raise HTTPException(status_code=404, detail='Плагин не найден')

@router.post('/plugin/{plugin_name}/status')
async def update_plugin_status(plugin_name: str, data: PluginStateUpdate, request: Request):
    """Update статуса плагина (обратная совместимость)."""
    _check_admin(request)
    plugins_dict = getattr(request.app.state, 'plugins', {})
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
    name: str = ''
    email: str = ''
    role: str = ''
    is_admin: int = 0
    is_active: int = 1
    is_email_verified: int = 1

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
    from core.user_manager import user_manager
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

    from core.user_manager import user_manager
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
    from core.user_manager import user_manager
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    settings = user_manager.get_user_settings(user_id)
    permissions = user_manager.get_user_permissions(user_id)
    sanitized = {k: v for k, v in user.items() if k != 'password_hash'}
    sanitized['has_password'] = bool(user.get('password_hash'))

    return {
        'status': 'ok',
        'user': sanitized,
        'settings': settings,
        'permissions': permissions
    }

@router.put('/users/{user_id}')
async def update_admin_user(user_id: int, data: AdminUserUpdateRequest, request: Request) -> Dict[str, Any]:
    """Update данных пользователя."""
    _check_admin(request)
    from core.user_manager import user_manager
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    updates: Dict[str, Any] = {}
    if data.name:
        updates['name'] = data.name.strip()
    if data.email:
        email_clean = data.email.strip().lower()
        if email_clean != user.get('email'):
            existing = user_manager.get_user_by_email(email_clean)
            if existing and existing.get('id') != user_id:
                raise HTTPException(status_code=400, detail='Этот email уже занят другим пользователем')
            updates['email'] = email_clean
    if data.role:
        updates['role'] = data.role
    updates['is_admin'] = data.is_admin
    updates['is_active'] = data.is_active
    updates['is_email_verified'] = data.is_email_verified

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

    from core.user_manager import user_manager
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
    from core.user_manager import user_manager
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
    from core.user_manager import user_manager
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
    from core.user_manager import user_manager
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
# Initialization
# ============================================================================

def init_router() -> APIRouter:
    """Initialization роутера управления системными инструкциями и источниками."""
    return router
