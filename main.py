# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Assistant Web Server Startup
# =============================================================================
# Description:
#   FastAPI application initialization, router connection,
#   uvicorn server startup with Telegram bot support.
#
# File: main.py
# Project: ai-breadboard
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import asyncio
import os
import signal
import sys
from pathlib import Path

# Suppress Windows asyncio system noise (WinError 10054 on client connection resets)
if sys.platform == 'win32':
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport
        _orig_call_connection_lost = _ProactorBasePipeTransport._call_connection_lost

        def _silence_connection_lost(self, exc=None):
            try:
                _orig_call_connection_lost(self, exc)
            except (ConnectionResetError, ConnectionAbortedError, OSError) as e:
                if getattr(e, 'winerror', None) in (10054, 10053) or isinstance(e, (ConnectionResetError, ConnectionAbortedError)):
                    pass
                else:
                    raise

        _ProactorBasePipeTransport._call_connection_lost = _silence_connection_lost
    except Exception:
        pass


import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

import header
from header import __root__
from core.ai import GoogleGenerativeAI
from core.fastapi import (
    init_auth_router,
    init_chat_router,
    init_control_router,
    init_tts_router,
    init_logs_router,
    init_keys_router,
    init_admin_router,
    init_agents_router,
    router_openai,
)
from core.logger import logger
from core.utils.file import read_text_file
from core.utils.jjson import j_loads_ns
from core.utils.versioning import compare_versions as _compare_versions, choose_best_tag
import subprocess
import json
import urllib.request
import configparser
import re

load_dotenv(__root__ / '.env')
from core.config import server_cfg, ai_cfg, tts_cfg, logging_cfg

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# Auto login local user to user_id=1
@app.middleware("http")
async def auto_login_local_user(request: Request, call_next):
    hostname: str = request.url.hostname or ''
    is_local: bool = (
        hostname in ('127.0.0.1', 'localhost', '::1', 'testserver', '0.0.0.0')
        or hostname.startswith('192.168.')
        or hostname.startswith('10.')
        or hostname.startswith('172.')
    )
    if is_local:
        token: str = request.cookies.get('auth_token', '')
        from core.fastapi.router_auth import verify_jwt_token
        is_token_valid: bool = False
        if token:
            try:
                is_token_valid = bool(verify_jwt_token(token))
            except Exception:
                is_token_valid = False

        if not token or not is_token_valid:
            from core.user_manager import user_manager
            try:
                db_user = user_manager.get_user_by_id(1)
                if db_user:
                    from core.fastapi.router_auth import TokenData, create_jwt_token
                    token_data = TokenData(
                        email=db_user['email'],
                        name=db_user['name'],
                        picture=db_user.get('picture', ''),
                        id=db_user['id']
                    )
                    token = create_jwt_token(token_data)

                    # Forward cookie to current request headers for subsequent middleware and handlers
                    raw_headers = list(request.scope.get('headers', []))
                    cookie_bytes = f"auth_token={token}".encode('utf-8')
                    new_headers = []
                    found_cookie: bool = False
                    for k, v in raw_headers:
                        if k.lower() == b'cookie':
                            new_headers.append((k, v + b'; ' + cookie_bytes))
                            found_cookie = True
                        else:
                            new_headers.append((k, v))
                    if not found_cookie:
                        new_headers.append((b'cookie', cookie_bytes))
                    request.scope['headers'] = new_headers
                    if hasattr(request, '_cookies'):
                        delattr(request, '_cookies')

                    response = await call_next(request)
                    response.set_cookie(
                        'auth_token',
                        token,
                        httponly=True,
                        secure=False,
                        samesite='lax',
                        max_age=3600 * 24 * 30  # 30 days
                    )
                    return response
            except Exception as e:
                logger.error(f"Error in auto_login_local_user middleware: {e}")
    return await call_next(request)


# Mount static files
webinterface_dir = __root__ / 'webinterface'
webinterface_dir.mkdir(parents=True, exist_ok=True)
app.mount('/webinterface', StaticFiles(directory=webinterface_dir), name='webinterface')
app.mount('/html', StaticFiles(directory=webinterface_dir), name='html')
simple_assistant_dir = __root__ / 'SANDBOX' / 'AI Assistant' / 'Simple Assistant'
app.mount('/simple-assistant', StaticFiles(directory=simple_assistant_dir, html=True), name='simple-assistant')


def _parse_version(v: str) -> list[int]:
    """Legacy simple numeric parser kept for backward compatibility.
    Prefer using semver-aware functions below.
    """
    if not v:
        return [0, 0, 0]
    parts = re.findall(r"(\d+)", v)
    return [int(p) for p in parts]


def _cfg_get(key: str, default=None):
    try:
        vc = getattr(server_cfg, 'version_check', None)
        if vc is None:
            return default
        # support both attribute and dict-like access
        if isinstance(vc, dict):
            return vc.get(key, default)
        try:
            val = getattr(vc, key)
            return val
        except Exception:
            try:
                return vc.get(key, default)
            except Exception:
                return default
    except Exception:
        return default


def _cfg_get_bool(key: str, env_names: list[str], default: bool = False) -> bool:
    val = _cfg_get(key, None)
    if val is not None:
        return bool(val)
    for env in env_names:
        ev = os.getenv(env)
        if ev is not None:
            return str(ev).lower() in ('1', 'true', 'yes')
    return default


def get_local_version() -> str:
    """Try to read version from setup.cfg [metadata] section. Fallback to 0.0.0."""
    cfg = configparser.ConfigParser()
    try:
        setup_cfg = Path(__root__) / 'setup.cfg'
        if setup_cfg.exists():
            cfg.read(setup_cfg)
            if cfg.has_section('metadata') and cfg.has_option('metadata', 'version'):
                return cfg.get('metadata', 'version').strip()
    except Exception:
        pass
    return '0.0.0'


def _get_git_origin_remote() -> str | None:
    """Return origin remote URL or None."""
    try:
        out = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url'], cwd=str(__root__), stderr=subprocess.DEVNULL)
        url = out.decode().strip()
        return url
    except Exception:
        return None


def _parse_github_owner_repo(remote_url: str) -> tuple[str, str] | None:
    """Parse GitHub owner and repo from remote URL.
    Supports HTTPS and SSH forms.
    """
    if not remote_url:
        return None
    # https://github.com/owner/repo.git
    m = re.search(r'github.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)', remote_url)
    if m:
        return m.group('owner'), m.group('repo')
    return None


def get_remote_latest_version() -> str | None:
    """Query GitHub API for the latest version.

    Flow:
    - Try /releases/latest and use tag_name/name if available.
    - Fallback to /tags and pick the highest semantic version-like tag.
    Authenticated requests are used when GITHUB_TOKEN or GH_TOKEN env var is present.
    """
    def _headers() -> dict:
        headers = {'User-Agent': 'ai-breadboard-version-check'}
        token = _cfg_get('github_token', None) or os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN') or os.getenv('GITHUB_API_TOKEN')
        if token:
            headers['Authorization'] = f'token {token}'
        return headers

    try:
        remote = _get_git_origin_remote()
        if not remote:
            return None
        parsed = _parse_github_owner_repo(remote)
        if not parsed:
            return None
        owner, repo = parsed

        # Try releases/latest first
        try:
            url = f'https://api.github.com/repos/{owner}/{repo}/releases/latest'
            req = urllib.request.Request(url, headers=_headers())
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.load(resp)
                tag = data.get('tag_name') or data.get('name')
                if tag:
                    return tag
        except Exception:
            # fallthrough to tags
            pass

        # Fallback: get tags and pick the highest semver-like tag
        try:
                # Optionally fetch tags from remote to ensure local tag refs are up-to-date
                fetch_tags_enabled = _cfg_get_bool('fetch_tags', ['FETCH_TAGS', 'ai-breadboard_FETCH_TAGS', 'FETCH_REMOTE_TAGS'], False)
                if fetch_tags_enabled:
                    try:
                        logger.info('Fetching remote tags (git fetch --tags origin)')
                        subprocess.check_call(['git', 'fetch', '--tags', 'origin'], cwd=str(__root__))
                    except Exception as e:
                        logger.debug(f'Failed to fetch tags: {e}')

                url = f'https://api.github.com/repos/{owner}/{repo}/tags'
                req = urllib.request.Request(url, headers=_headers())
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.load(resp)
                    tags = [t.get('name') for t in data if t.get('name')]
                    if not tags:
                        return None

                    # Logging of the remote tag list when debug enabled
                    debug_enabled = _cfg_get('debug', None)
                    if debug_enabled is None:
                        debug_enabled = os.getenv('VERSION_CHECK_DEBUG') == '1' or (hasattr(logger, 'isEnabledFor') and logger.isEnabledFor(10))
                    if debug_enabled:
                        logger.debug(f'Remote tags from API: {tags}')

                    # Prefer stable releases unless prerelease is explicitly allowed
                    allow_prerelease = _cfg_get('allow_prerelease', None)
                    if allow_prerelease is None:
                        allow_prerelease = str(os.getenv('ALLOW_PRERELEASE') or os.getenv('ai-breadboard_ALLOW_PRERELEASE') or '').lower() in ('1', 'true', 'yes')

                    best = choose_best_tag(tags, allow_prerelease=bool(allow_prerelease), debug=bool(debug_enabled))
                    if debug_enabled:
                        logger.debug(f'Selected tag: {best} (allow_prerelease={allow_prerelease})')
                    return best
        except Exception:
            # Try using git ls-remote --tags origin as a last-resort fallback
            try:
                out = subprocess.check_output(['git', 'ls-remote', '--tags', 'origin'], cwd=str(__root__), stderr=subprocess.DEVNULL)
                lines = out.decode().splitlines()
                tags = []
                for line in lines:
                    parts = line.split('\t')
                    if len(parts) < 2:
                        continue
                    ref = parts[1]
                    if ref.startswith('refs/tags/'):
                        tag = ref[len('refs/tags/'):]
                        # annotated tags may have ^{} suffix: refs/tags/v1.0.0^{}
                        tag = tag.replace('^{}', '')
                        tags.append(tag)
                if not tags:
                    return None

                debug_enabled = _cfg_get('debug', None)
                if debug_enabled is None:
                    debug_enabled = os.getenv('VERSION_CHECK_DEBUG') == '1' or (hasattr(logger, 'isEnabledFor') and logger.isEnabledFor(10))
                if debug_enabled:
                    logger.debug(f'Remote tags from ls-remote: {tags}')

                allow_prerelease = _cfg_get('allow_prerelease', None)
                if allow_prerelease is None:
                    allow_prerelease = str(os.getenv('ALLOW_PRERELEASE') or os.getenv('ai-breadboard_ALLOW_PRERELEASE') or '').lower() in ('1', 'true', 'yes')

                best = choose_best_tag(tags, allow_prerelease=bool(allow_prerelease), debug=bool(debug_enabled))
                if debug_enabled:
                    logger.debug(f'Selected tag from ls-remote: {best} (allow_prerelease={allow_prerelease})')
                return best
            except Exception:
                return None
    except Exception:
        return None


def _is_interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def prompt_and_perform_update(branch: str = 'main') -> None:
    """If a newer remote version exists, prompt the user and, on consent, run git pull --ff-only.
    This function is conservative and skips the check in non-interactive environments.
    """
    try:
        auto_update = _cfg_get('auto_update', None)
        if auto_update is None:
            auto_update_env = os.getenv('AUTO_UPDATE') or os.getenv('ai-breadboard_AUTO_UPDATE')
            auto_update = str(auto_update_env or '').lower() in ('1', 'true', 'yes')
        else:
            auto_update = bool(auto_update)

        if not _is_interactive() and not auto_update:
            logger.debug('Non-interactive shell and AUTO_UPDATE not enabled: skipping version check')
            return

        local_v = get_local_version()
        remote_v = get_remote_latest_version()
        if not remote_v:
            logger.debug('Could not determine remote version')
            return

        cmp = _compare_versions(local_v, remote_v)
        if cmp >= 0:
            logger.info(f'Local version {local_v} is up-to-date (remote {remote_v})')
            return

        logger.info(f'A newer version is available: {remote_v} (local: {local_v}).')

        do_update = auto_update
        if not do_update:
            # interactive prompt
            try:
                resp = input('Do you want to update the code from origin and restart? [y/N]: ').strip().lower()
                do_update = resp in ('y', 'yes')
            except Exception:
                do_update = False

        if not do_update:
            logger.info('User declined update or update not approved')
            return

        # run git fetch + merge --ff-only origin/<branch>
        try:
            logger.info(f'Pulling latest changes from origin/{branch}...')
            subprocess.check_call(['git', 'fetch', 'origin', branch], cwd=str(__root__))
            subprocess.check_call(['git', 'merge', '--ff-only', f'origin/{branch}'], cwd=str(__root__))
            logger.info('Update pulled successfully. You should restart the process to apply changes.')
            print('Update pulled successfully. Please restart the application to apply changes.')
        except subprocess.CalledProcessError as e:
            logger.error(f'Failed to update repository: {e}')
            print('Failed to update repository. See logs for details.')
    except Exception as e:
        logger.error(f'Error during version check/update: {e}')


_api_key_names: list[str] = [n.strip() for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',') if n.strip()]

use_foundry = getattr(ai_cfg, 'use_foundry', False) if ai_cfg else False
foundry_model_id = getattr(ai_cfg, 'foundry_model_id', 'qwen2.5-1.5b') if ai_cfg else 'qwen2.5-1.5b'

use_ollama = getattr(ai_cfg, 'use_ollama', False) if ai_cfg else False
ollama_model_id = getattr(ai_cfg, 'ollama_model_id', 'llama3.1') if ai_cfg else 'llama3.1'
ollama_base_url = getattr(ai_cfg, 'ollama_base_url', 'http://localhost:11434') if ai_cfg else 'http://localhost:11434'

from core.ai import UnifiedChatModel

# --- Chat model instance ---
_system_instruction_chat: str = read_text_file(__root__ / 'prompts' / 'chat' / 'system_instruction.md') or ''
chat_model = UnifiedChatModel(
    api_key_names=_api_key_names,
    system_instruction=_system_instruction_chat,
    foundry_model_id=foundry_model_id,
    use_foundry=use_foundry,
    use_ollama=use_ollama,
    ollama_model_id=ollama_model_id,
    ollama_base_url=ollama_base_url,
)

# --- Narrator model instance ---
_system_instruction_narrator: str = read_text_file(__root__ / 'prompts' / 'narrator' / 'narrator_style.md') or ''
narrator_model = UnifiedChatModel(
    api_key_names=_api_key_names,
    system_instruction=_system_instruction_narrator,
    foundry_model_id=foundry_model_id,
    use_foundry=use_foundry,
    use_ollama=use_ollama,
    ollama_model_id=ollama_model_id,
    ollama_base_url=ollama_base_url,
)
logger.info('Chat and Narrator model instances initialized')

app.include_router(init_chat_router(chat_model, narrator_model))
app.include_router(init_auth_router())
app.include_router(init_control_router())
app.include_router(init_tts_router())
app.include_router(init_logs_router())
app.include_router(init_keys_router())
app.include_router(init_admin_router())
app.include_router(init_agents_router())
app.include_router(router_openai)


@app.on_event("startup")
async def startup_event():
    # Store model instances in app.state for access from routers
    app.state.chat_model = chat_model
    app.state.narrator_model = narrator_model

    # One-time actualization and caching of all provider models
    from core.ai.model_manager import actualize_all_models
    await actualize_all_models()

    # Log analyzer is disabled — run manually if needed
    # from core.logger.log_analyzer import start_log_analyzer
    # start_log_analyzer()
    
    if ai_cfg and getattr(ai_cfg, 'preload_silero', False):
        from core.tts.silero import get_silero_model
        logger.info("Pre-loading Silero TTS model...")
        try:
            get_silero_model()
            logger.info("Silero TTS model pre-loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to pre-load Silero TTS model: {e}")




@app.get('/', response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    """Serving of main HTML page — admin interface."""
    auth_response = check_admin_auth(request)
    if auth_response:
        return auth_response
    content = read_text_file(__root__ / 'webinterface' / 'admin' / 'index.html')
    if not content:
        raise HTTPException(status_code=500, detail='Failed to read admin index page')
    return HTMLResponse(content=content)


@app.get('/tgmini', response_class=HTMLResponse)
async def tgmini_interface() -> HTMLResponse:
    """Serving of Telegram Mini App HTML page."""
    content = read_text_file(__root__ / 'webinterface' / 'tgmini' / 'index.html')
    if not content:
        raise HTTPException(status_code=500, detail='Failed to read Telegram Mini App index page')
    return HTMLResponse(content=content)


@app.get('/tgmini/{full_path:path}', response_class=HTMLResponse)
async def tgmini_static(full_path: str) -> HTMLResponse:
    """Serving Telegram Mini App static files."""
    content = read_text_file(__root__ / 'webinterface' / 'tgmini' / full_path)
    if not content:
        raise HTTPException(status_code=404, detail='File not found')
    return HTMLResponse(content=content)


@app.get('/rc', response_class=HTMLResponse)
async def rc_interface() -> HTMLResponse:
    """Serving of Remote Control HTML page."""
    content = read_text_file(__root__ / 'webinterface' / 'rc' / 'index.html')
    if not content:
        raise HTTPException(status_code=500, detail='Failed to read Remote Control page')
    return HTMLResponse(content=content)


@app.get('/rc/{full_path:path}', response_class=HTMLResponse)
async def rc_static(full_path: str) -> HTMLResponse:
    """Serving Remote Control static files."""
    content = read_text_file(__root__ / 'webinterface' / 'rc' / full_path)
    if not content:
        raise HTTPException(status_code=404, detail='File not found')
    return HTMLResponse(content=content)


@app.get('/user_tts', response_class=HTMLResponse)
async def user_tts_interface() -> HTMLResponse:
    """Serving of User TTS experimental page."""
    content = read_text_file(__root__ / 'webinterface' / 'user_tts' / 'index.html')
    if not content:
        raise HTTPException(status_code=500, detail='Failed to read User TTS page')
    return HTMLResponse(content=content)


@app.get('/user_tts/{full_path:path}', response_class=HTMLResponse)
async def user_tts_static(full_path: str) -> HTMLResponse:
    """Serving User TTS static files."""
    content = read_text_file(__root__ / 'webinterface' / 'user_tts' / full_path)
    if not content:
        raise HTTPException(status_code=404, detail='File not found')
    return HTMLResponse(content=content)



ADMIN_LOGIN_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Вход в панель управления</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&family=Plus+Jakarta+Sans:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: rgba(255, 255, 255, 0.03);
            --card-border: rgba(255, 255, 255, 0.08);
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.4);
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Plus Jakarta Sans', 'Outfit', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            position: relative;
        }

        body::before {
            content: '';
            position: absolute;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, var(--primary-glow) 0%, transparent 70%);
            top: 20%;
            left: 30%;
            z-index: 0;
            filter: blur(40px);
            animation: float-slow 12s infinite alternate ease-in-out;
        }
        body::after {
            content: '';
            position: absolute;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(168, 85, 247, 0.2) 0%, transparent 70%);
            bottom: 15%;
            right: 25%;
            z-index: 0;
            filter: blur(50px);
            animation: float-slow 15s infinite alternate-reverse ease-in-out;
        }

        @keyframes float-slow {
            0% { transform: translate(0, 0) scale(1); }
            100% { transform: translate(50px, 30px) scale(1.1); }
        }

        .login-container {
            position: relative;
            z-index: 10;
            width: 100%;
            max-width: 420px;
            padding: 40px;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 24px;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
            animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1);
            text-align: center;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .logo {
            margin-bottom: 28px;
        }

        .logo h1 {
            font-size: 26px;
            font-weight: 600;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #fff 0%, var(--text-muted) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .logo p {
            font-size: 14px;
            color: var(--text-muted);
            margin-top: 8px;
            line-height: 1.4;
        }

        .btn-google {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            width: 100%;
            padding: 14px 20px;
            background: #ffffff;
            color: #1f2937;
            font-size: 15px;
            font-weight: 600;
            border-radius: 12px;
            text-decoration: none;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(255, 255, 255, 0.15);
            margin-bottom: 20px;
        }

        .btn-google:hover {
            background: #f3f4f6;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 255, 255, 0.25);
        }

        .divider {
            display: flex;
            align-items: center;
            text-align: center;
            margin: 20px 0;
            color: var(--text-muted);
            font-size: 13px;
        }

        .divider::before, .divider::after {
            content: '';
            flex: 1;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .divider span {
            padding: 0 10px;
        }

        .input-group {
            position: relative;
            margin-bottom: 18px;
        }

        .input-group input {
            width: 100%;
            padding: 14px 18px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: #fff;
            font-size: 15px;
            outline: none;
            transition: all 0.3s ease;
            font-family: inherit;
        }

        .input-group input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 4px var(--primary-glow);
            background: rgba(255, 255, 255, 0.08);
        }

        .btn-submit {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, var(--primary) 0%, #4f46e5 100%);
            border: none;
            border-radius: 12px;
            color: #fff;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px var(--primary-glow);
            font-family: inherit;
        }

        .btn-submit:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px var(--primary-glow);
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>Панель управления</h1>
            <p>Авторизуйтесь через Google для доступа к функциям AI Assistant, Google Документам, Календарю и Контактам</p>
        </div>

        <a href="/auth/google?next=/admin" class="btn-google">
            <svg width="20" height="20" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
            </svg>
            Войти через Google
        </a>

        <div class="divider"><span>или локальный вход</span></div>

        <form method="POST" action="/admin">
            <div class="input-group">
                <input type="password" name="password" placeholder="Пароль администратора" required autocomplete="current-password">
            </div>
            <button type="submit" class="btn-submit">Войти по паролю</button>
        </form>
    </div>
</body>
</html>
"""


def check_admin_auth(request: Request):
    """Проверка прав доступа к панели администратора с Google OAuth."""
    from fastapi.responses import RedirectResponse, HTMLResponse
    from core.fastapi.router_auth import verify_jwt_token
    from core.user_manager import user_manager

    token = request.cookies.get('auth_token', '')
    if not token:
        if request.url.path in ('/admin', '/'):
            return HTMLResponse(content=ADMIN_LOGIN_HTML)
        return RedirectResponse(url='/auth/google?next=' + request.url.path, status_code=303)

    user_data = verify_jwt_token(token)
    if not user_data:
        if request.url.path in ('/admin', '/'):
            return HTMLResponse(content=ADMIN_LOGIN_HTML)
        return RedirectResponse(url='/auth/google?next=' + request.url.path, status_code=303)

    db_user = user_manager.get_user_by_email(user_data.email)
    if not db_user:
        if request.url.path in ('/admin', '/'):
            return HTMLResponse(content=ADMIN_LOGIN_HTML)
        return RedirectResponse(url='/auth/google?next=' + request.url.path, status_code=303)

    # Check if user has Google OAuth tokens for working with Google services
    has_google = user_manager.has_google_auth(db_user['id'])
    is_admin_user = bool(db_user.get('is_admin', 0) or db_user.get('role') == 'admin')

    # If user is logged in via Google and is admin — grant access
    if has_google and is_admin_user:
        return False

    # If administrator verified password locally
    if request.cookies.get('admin_password_verified') == 'true' and is_admin_user:
        return False

    if request.url.path in ('/admin', '/'):
        return HTMLResponse(content=ADMIN_LOGIN_HTML)

    return RedirectResponse(url='/auth/google?next=' + request.url.path, status_code=303)


@app.get('/admin')
async def admin_interface(request: Request):
    """Display the main admin panel page."""
    auth_response = check_admin_auth(request)
    if auth_response:
        return auth_response
    content = read_text_file(__root__ / 'webinterface' / 'admin' / 'index.html')
    if not content:
        raise HTTPException(status_code=500, detail='Failed to read admin index page')
    return HTMLResponse(content=content)


@app.post('/admin')
async def admin_interface_post(request: Request):
    """Verify password and set admin authentication cookie."""
    from fastapi.responses import RedirectResponse
    form = await request.form()
    password = form.get('password')
    if password == 'onela':
        response = RedirectResponse(url='/admin', status_code=303)
        response.set_cookie(key='admin_password_verified', value='true', max_age=86400 * 30, httponly=True)
        return response
    else:
        return RedirectResponse(url='/admin', status_code=303)




@app.get('/admin/{full_path:path}')
async def admin_static(full_path: str, request: Request):
    """Serving admin static files with security verification."""
    auth_response = check_admin_auth(request)
    if auth_response:
        return auth_response
    content = read_text_file(__root__ / 'webinterface' / 'admin' / full_path)
    if not content:
        raise HTTPException(status_code=404, detail='File not found')
    return HTMLResponse(content=content)


@app.get('/tv', response_class=HTMLResponse)
async def tv_interface() -> HTMLResponse:
    """Serving of TV Player HTML page."""
    content = read_text_file(__root__ / 'webinterface' / 'tv' / 'index.html')
    if not content:
        raise HTTPException(status_code=500, detail='Failed to read TV index page')
    return HTMLResponse(content=content)


@app.get('/tv/{full_path:path}', response_class=HTMLResponse)
async def tv_static(full_path: str) -> HTMLResponse:
    """Serving TV static files."""
    content = read_text_file(__root__ / 'webinterface' / 'tv' / full_path)
    if not content:
        raise HTTPException(status_code=404, detail='File not found')
    return HTMLResponse(content=content)


@app.get('/logs')
async def logs_interface():
    """Redirect to admin dashboard logs tab."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url='/admin#tab-logs', status_code=303)


from pydantic import BaseModel

class FoundryConfigRequest(BaseModel):
    enabled: bool
    url: str
    key: str
    model: str

class OllamaConfigRequest(BaseModel):
    enabled: bool
    url: str
    model: str

@app.get('/api/foundry/config')
async def get_foundry_config():
    import os
    return {
        "enabled": getattr(ai_cfg, "use_foundry", False) if ai_cfg else False,
        "url": getattr(ai_cfg, "foundry_base_url", "http://localhost:54837") if ai_cfg else "http://localhost:54837",
        "key": os.getenv("FOUNDRY_API_KEY", ""),
        "model": getattr(ai_cfg, "foundry_model_id", "qwen2.5-1.5b") if ai_cfg else "qwen2.5-1.5b"
    }

@app.post('/api/foundry/config')
async def save_foundry_config(data: FoundryConfigRequest):
    from dotenv import set_key
    import os
    import json
    
    # Secret goes to .env
    env_path = str(__root__ / '.env')
    set_key(env_path, "FOUNDRY_API_KEY", data.key)
    os.environ["FOUNDRY_API_KEY"] = data.key
    
    # Non-secrets go to config.json
    config_path = __root__ / 'config.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg_data = json.load(f)
    except Exception:
        cfg_data = {}
        
    if "ai" not in cfg_data:
        cfg_data["ai"] = {}
        
    cfg_data["ai"]["use_foundry"] = data.enabled
    cfg_data["ai"]["foundry_base_url"] = data.url
    cfg_data["ai"]["foundry_model_id"] = data.model
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(cfg_data, f, indent=2, ensure_ascii=False)
        
    # Update in-memory config
    if ai_cfg:
        ai_cfg.use_foundry = data.enabled
        ai_cfg.foundry_base_url = data.url
        ai_cfg.foundry_model_id = data.model
    
    return {"status": "ok"}


@app.get('/api/ollama/config')
async def get_ollama_config():
    return {
        "enabled": getattr(ai_cfg, "use_ollama", False) if ai_cfg else False,
        "url": getattr(ai_cfg, "ollama_base_url", "http://localhost:11434") if ai_cfg else "http://localhost:11434",
        "model": getattr(ai_cfg, "ollama_model_id", "llama3.1") if ai_cfg else "llama3.1"
    }

@app.post('/api/ollama/config')
async def save_ollama_config(data: OllamaConfigRequest):
    import json
    
    config_path = __root__ / 'config.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg_data = json.load(f)
    except Exception:
        cfg_data = {}
        
    if "ai" not in cfg_data:
        cfg_data["ai"] = {}
        
    cfg_data["ai"]["use_ollama"] = data.enabled
    cfg_data["ai"]["ollama_base_url"] = data.url
    cfg_data["ai"]["ollama_model_id"] = data.model
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(cfg_data, f, indent=2, ensure_ascii=False)
        
    # Update in-memory config
    if ai_cfg:
        ai_cfg.use_ollama = data.enabled
        ai_cfg.ollama_base_url = data.url
        ai_cfg.ollama_model_id = data.model
    
    return {"status": "ok"}


class AgyConfigRequest(BaseModel):
    enabled: bool
    key: str = ""
    model: str = "agy-flash"

@app.get('/api/agy/config')
async def get_agy_config():
    import os
    return {
        "enabled": getattr(ai_cfg, "use_agy", True) if ai_cfg else True,
        "key": os.getenv("AGY_API_KEY", ""),
        "model": getattr(ai_cfg, "agy_model_id", "agy-flash") if ai_cfg else "agy-flash"
    }

@app.post('/api/agy/config')
async def save_agy_config(data: AgyConfigRequest):
    from dotenv import set_key
    import os
    import json
    
    # Secret goes to .env
    env_path = str(__root__ / '.env')
    set_key(env_path, "AGY_API_KEY", data.key)
    os.environ["AGY_API_KEY"] = data.key
    
    # Non-secrets go to config.json
    config_path = __root__ / 'config.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg_data = json.load(f)
    except Exception:
        cfg_data = {}
        
    if "ai" not in cfg_data:
        cfg_data["ai"] = {}
        
    cfg_data["ai"]["use_agy"] = data.enabled
    cfg_data["ai"]["agy_model_id"] = data.model
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(cfg_data, f, indent=2, ensure_ascii=False)
        
    # Update in-memory config
    if ai_cfg:
        ai_cfg.use_agy = data.enabled
        ai_cfg.agy_model_id = data.model
    
    return {"status": "ok"}




if __name__ == '__main__':
    try:
        args = sys.argv[1:]
        branch = str(os.getenv('GIT_BRANCH', 'main'))
        if '--check-update' in args:
            prompt_and_perform_update(branch=branch)
            sys.exit(0)
        if '--check-update-and-run' in args:
            prompt_and_perform_update(branch=branch)
        else:
            # Default startup behavior: perform version check according to config
            try:
                prompt_and_perform_update(branch=branch)
            except Exception:
                pass
    except Exception:
        # Non-fatal if version check fails
        pass
    # For development: single-process launch without --workers
    # In production use Run-Unicorn.ps1, which launches:
    #   uvicorn main:app --workers N  (without Telegram bot)
    #   python bot_runner.py           (Telegram bot separately)
    port: int = int(getattr(server_cfg, "port", 8000))
    if not port:
        logger.error('Port not configured')
        sys.exit(1)

    cert_file = Path(r'C:\Users\onela\.certs\localhost+2.pem')
    key_file = Path(r'C:\Users\onela\.certs\localhost+2-key.pem')

    ssl_kwargs = {}
    use_ssl = getattr(server_cfg, "use_ssl", True)
    host = getattr(server_cfg, "host", "0.0.0.0")
    reload = bool(getattr(server_cfg, "reload", True))

    if use_ssl and cert_file.exists() and key_file.exists():
        ssl_kwargs = {'ssl_certfile': str(cert_file), 'ssl_keyfile': str(key_file)}
        logger.info(f'Server starting https://{host}:{port} (SSL enabled)')
    else:
        logger.warning('Starting without HTTPS (SSL disabled or certificates not found)')
        logger.info(f'Запуск сервера http://{host}:{port}')

    logger.info(f"Uvicorn autoreload: {'ON' if reload else 'OFF'}")
    uvicorn.run('main:app', host=host, port=port, reload=reload, **ssl_kwargs)
