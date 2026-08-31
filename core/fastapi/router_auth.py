# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: User authentication and OAuth router
# =============================================================================
# Description:
#   Provides FastAPI routing for user authentication, Google OAuth integration,
#   JWT token generation, and secure session state validation.
#
# File: router_auth.py
# Project: ai-breadboard
# Package: core.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import jwt
import requests
from dotenv import load_dotenv
from fastapi import APIRouter, Cookie, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from header import __root__
from core.logger import logger

load_dotenv()

router = APIRouter(prefix='/auth', tags=['auth'])

class TokenData:
    """Данные токена авторизации."""
    
    def __init__(self, email: str, name: Optional[str] = None, picture: Optional[str] = None, id: Optional[int] = None):
        self.email = email
        self.name = name
        self.picture = picture
        self.id = id

def load_google_oauth_config() -> dict:
    """Loading конфигурации Google OAuth из secrets файла или .env.
    
    Returns:
        dict: Configuration с client_id, client_secret, redirect_uri.
    """
    # Сначала пробуем загрузить из .env
    env_client_id = os.getenv('GOOGLE_CLIENT_ID')
    env_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    env_redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
    
    from core.config import server_cfg
    port = getattr(server_cfg, 'port', 8000)
    default_redirect = f'http://localhost:{port}/auth/google/callback'

    # Если в .env есть заглушки, пробуем загрузить из secrets файла
    if env_client_id and env_client_id.startswith('YOUR_'):
        secrets_file = __root__ / 'core' / 'secrets' / 'client_secret_*.json'
        try:
            for f in secrets_file.parent.glob(secrets_file.name):
                with open(f, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                    if 'web' in data:
                        web = data['web']
                        return {
                            'client_id': web.get('client_id', ''),
                            'client_secret': web.get('client_secret', ''),
                            'redirect_uri': env_redirect_uri or default_redirect
                        }
        except Exception as e:
            logger.warning('Failed to load Google OAuth from secrets file:', e, False)
    
    return {
        'client_id': env_client_id or '',
        'client_secret': env_client_secret or '',
        'redirect_uri': env_redirect_uri or default_redirect
    }

# Configuration JWT
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 часа

# Configuration Google OAuth (загружаем из .env или secrets)
_oauth_config = load_google_oauth_config()
GOOGLE_CLIENT_ID = _oauth_config['client_id']
GOOGLE_CLIENT_SECRET = _oauth_config['client_secret']
GOOGLE_REDIRECT_URI = _oauth_config['redirect_uri']

def create_jwt_token(data: TokenData) -> str:
    """Создание JWT токена.
    
    Args:
        data: Данные для включения в токен.
        
    Returns:
        str: Закодированный JWT токен.
    """
    to_encode = data.__dict__.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp': expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[TokenData]:
    """Check JWT токена.
    
    Args:
        token: JWT токен для проверки.
        
    Returns:
        Optional[TokenData]: Данные токена или None при ошибке.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return TokenData(
            email=payload.get('email', ''),
            name=payload.get('name'),
            picture=payload.get('picture'),
            id=payload.get('id')
        )
    except jwt.PyJWTError:
        return None

# Хранилище for OAuth state (in production use Redis or similar)
oauth_states: dict[str, datetime] = {}

def generate_state_token() -> str:
    """Генерация state token для защиты от CSRF атак."""
    state = secrets.token_urlsafe(32)
    oauth_states[state] = datetime.utcnow() + timedelta(minutes=10)
    return state

def validate_state_token(state: str) -> bool:
    """Validation state token."""
    if state not in oauth_states:
        return False
    # Clean up expired states
    now = datetime.utcnow()
    if oauth_states[state] < now:
        del oauth_states[state]
        return False
    return True

@router.get('/login')
async def login(request: Request) -> dict:
    """Check статуса авторизации пользователя.
    
    Args:
        request: FastAPI request object.
        
    Returns:
        dict: Status авторизации и данные пользователя.
    """
    token = request.cookies.get('auth_token')
    if not token:
        return {'authenticated': False}
    
    user_data = verify_jwt_token(token)
    if not user_data:
        return {'authenticated': False}
    
    return {
        'authenticated': True,
        'email': user_data.email,
        'name': user_data.name,
        'picture': user_data.picture
    }

GOOGLE_SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/contacts',
]

@router.get('/google')
async def google_login(request: Request, next: str = '/') -> RedirectResponse:
    """Перенаправление на Google OAuth страницу с расширенными правами.
    
    Returns:
        RedirectResponse: Перенаправление на Google OAuth.
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail='Google OAuth не настроен. Пожалуйста, свяжитесь с администратором.'
        )
    
    state = generate_state_token()
    
    # Determine redirect URI:
    # If GOOGLE_REDIRECT_URI is explicitly configured in .env, use it
    if GOOGLE_REDIRECT_URI and not GOOGLE_REDIRECT_URI.startswith('http://localhost:'):
        redirect_uri = GOOGLE_REDIRECT_URI
    else:
        # Fallback to dynamic request URL
        host = request.headers.get('x-forwarded-host') or request.headers.get('host') or request.url.netloc
        scheme = request.headers.get('x-forwarded-proto') or request.url.scheme
        redirect_uri = f'{scheme}://{host}/auth/google/callback'
    
    # Build Google OAuth URL with extended scopes & offline refresh token
    import urllib.parse
    scope_str = urllib.parse.quote(' '.join(GOOGLE_SCOPES))
    oauth_url = (
        'https://accounts.google.com/o/oauth2/v2/auth'
        f'?client_id={GOOGLE_CLIENT_ID}'
        f'&redirect_uri={redirect_uri}'
        f'&response_type=code'
        f'&scope={scope_str}'
        f'&access_type=offline'
        f'&prompt=consent'
        f'&include_granted_scopes=true'
        f'&state={state}'
    )
    
    response = RedirectResponse(url=oauth_url, status_code=302)
    # Store state and exact redirect_uri in cookies for validation on callback
    response.set_cookie('oauth_state', state, httponly=True, max_age=600)
    response.set_cookie('oauth_redirect_uri', redirect_uri, httponly=True, max_age=600)
    
    # Validate next parameter to prevent open redirects
    if not next.startswith('/'):
        next = '/'
    response.set_cookie('next_redirect', next, httponly=True, max_age=600)
    
    return response

@router.get('/google/callback')
async def google_callback(request: Request, code: str, state: str) -> RedirectResponse:
    """Обработка callback от Google OAuth с сохранением токенов доступа.
    
    Args:
        request: FastAPI request object.
        code: Authorization code from Google.
        state: State token for CSRF protection.
        
    Returns:
        RedirectResponse: Перенаправление на главную страницу или сохраненный next.
    """
    # Validate state
    cookie_state = request.cookies.get('oauth_state')
    if not cookie_state or cookie_state != state:
        logger.warning('Invalid state token in Google OAuth callback')
        raise HTTPException(status_code=400, detail='Неверный state токен')
    
    if not validate_state_token(state):
        raise HTTPException(status_code=400, detail='Срок действия state токена истек')
    
    # Exchange code for tokens with Google
    redirect_uri = request.cookies.get('oauth_redirect_uri', '')
    if not redirect_uri:
        if GOOGLE_REDIRECT_URI and not GOOGLE_REDIRECT_URI.startswith('http://localhost:'):
            redirect_uri = GOOGLE_REDIRECT_URI
        else:
            host = request.headers.get('x-forwarded-host') or request.headers.get('host') or request.url.netloc
            scheme = request.headers.get('x-forwarded-proto') or request.url.scheme
            redirect_uri = f'{scheme}://{host}/auth/google/callback'

    token_url = 'https://oauth2.googleapis.com/token'
    token_data = {
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }
    
    try:
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_json = token_response.json()
        
        access_token = token_json.get('access_token', '')
        refresh_token = token_json.get('refresh_token', '')
        expires_in = token_json.get('expires_in', 3600)
        granted_scope = token_json.get('scope', '')

        if not access_token:
            logger.error('Failed to get access token from Google:', token_json)
            raise HTTPException(status_code=500, detail='Не удалось получить токен доступа от Google')
        
        # Get user info from Google
        userinfo_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        userinfo_headers = {'Authorization': f'Bearer {access_token}'}
        userinfo_response = requests.get(userinfo_url, headers=userinfo_headers)
        userinfo_response.raise_for_status()
        userinfo = userinfo_response.json()
        
        user_email = userinfo.get('email', '')
        user_name = userinfo.get('name', '')
        user_picture = userinfo.get('picture', '')
        
        if not user_email:
            logger.error('Failed to get email from Google userinfo:', userinfo)
            raise HTTPException(status_code=500, detail='Не удалось получить email от Google')
        
        # Integration с UserManager
        from core.user_manager import user_manager
        db_user = user_manager.get_user_by_email(user_email)
        if not db_user:
            user_id = user_manager.add_user(email=user_email, name=user_name, picture=user_picture, role='admin')
        else:
            user_id = db_user['id']
            user_manager.update_user(user_id, name=user_name, picture=user_picture, last_login=datetime.utcnow().isoformat())
        
        # Сохранение Google OAuth токенов для доступа к Google Docs / Calendar / Contacts
        user_manager.save_google_tokens(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(expires_in),
            scope=granted_scope
        )

        # Создаем JWT токен с ID пользователя
        token = create_jwt_token(TokenData(email=user_email, name=user_name, picture=user_picture, id=user_id))
        
        next_redirect = request.cookies.get('next_redirect') or '/'
        if not next_redirect.startswith('/'):
            next_redirect = '/'
            
        response = RedirectResponse(url=next_redirect, status_code=302)
        response.set_cookie(
            'auth_token', 
            token, 
            httponly=True, 
            secure=False,  # Set to True in production with HTTPS
            samesite='lax',
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        response.delete_cookie('next_redirect')
        
        return response
        
    except requests.exceptions.RequestException as e:
        logger.error('Google OAuth request failed:', e, False)
        raise HTTPException(status_code=500, detail='Error связи с Google OAuth')

@router.get('/google/status')
async def google_auth_status(request: Request) -> dict:
    """Check наличия и валидности токенов Google OAuth у текущего пользователя."""
    token = request.cookies.get('auth_token', '')
    if not token:
        return {'connected': False, 'reason': 'unauthorized'}
    user_data = verify_jwt_token(token)
    if not user_data:
        return {'connected': False, 'reason': 'invalid_token'}
    from core.user_manager import user_manager
    tokens = user_manager.get_google_tokens(user_data.id) if user_data.id else {}
    if not tokens or not tokens.get('access_token'):
        return {'connected': False, 'email': user_data.email}
    return {
        'connected': True,
        'email': user_data.email,
        'has_refresh_token': bool(tokens.get('refresh_token')),
        'scope': tokens.get('scope', ''),
        'expires_at': tokens.get('expires_at', '')
    }

@router.post('/logout')
async def logout(response: Response) -> dict:
    """Выход пользователя из системы.
    
    Args:
        response: FastAPI response object.
        
    Returns:
        dict: Результат операции.
    """
    response.delete_cookie('auth_token')
    response.delete_cookie('oauth_state')
    return {'message': 'Успешный выход'}

@router.get('/check')
async def check_auth(request: Request) -> dict:
    """Check текущей авторизации.
    
    Args:
        request: FastAPI request object.
        
    Returns:
        dict: Status авторизации.
    """
    token = request.cookies.get('auth_token', '')
    if not token:
        return {'authenticated': False}
    
    user_data = verify_jwt_token(token)
    if not user_data:
        return {'authenticated': False}
    
    db_user = user_manager.get_user_by_email(user_data.email) if user_data.email else {}
    role = db_user.get('role', 'user') if db_user else 'user'
    is_admin = bool(db_user.get('is_admin', 0)) if db_user else False
    user_id = db_user.get('id', 0) if db_user else 0
    google_tokens = user_manager.get_google_tokens(user_id) if user_id else {}
    has_google = bool(google_tokens.get('refresh_token') or google_tokens.get('access_token'))
    
    return {
        'authenticated': True,
        'id': user_id,
        'email': user_data.email,
        'name': user_data.name,
        'picture': user_data.picture,
        'role': role,
        'is_admin': is_admin,
        'has_google': has_google
    }

from pydantic import BaseModel

class EmailRegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class EmailVerifyRequest(BaseModel):
    email: str
    code: str

class EmailLoginRequest(BaseModel):
    email: str
    password: str

def send_verification_email(email: str, code: str):
    import smtplib
    from email.mime.text import MIMEText
    
    subject = "Код подтверждения AI Assistant"
    body = f"Ваш код подтверждения: {code}\n\nКод действителен 15 минут."
    
    # Всегда пишем в логи
    logger.info(f"==========================================")
    logger.info(f"EMAIL VERIFICATION FOR {email}: {code}")
    logger.info(f"==========================================")
    
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    
    if smtp_host and smtp_port and smtp_user and smtp_pass:
        try:
            msg = MIMEText(body, 'plain', 'utf-8')
            msg['Subject'] = subject
            msg['From'] = smtp_user
            msg['To'] = email
            
            with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            logger.info(f"Verification email successfully sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send email to {email}:", e, False)

@router.post('/register')
async def register(data: EmailRegisterRequest):
    from core.user_manager import user_manager
    email = data.email.lower().strip()
    
    db_user = user_manager.get_user_by_email(email)
    if db_user and db_user.get('is_email_verified', 0) == 1 and db_user.get('password_hash'):
         raise HTTPException(status_code=400, detail='Пользователь с такой почтой уже зарегистрирован')
         
    user_id = user_manager.register_email_user(email, data.password, data.name)
    if not user_id:
        raise HTTPException(status_code=500, detail='Не удалось зарегистрировать пользователя')
        
    code = user_manager.create_email_verification(email)
    send_verification_email(email, code)
    
    return {'message': 'Код подтверждения отправлен на почту', 'email': email}

@router.post('/verify')
async def verify(data: EmailVerifyRequest):
    from core.user_manager import user_manager
    email = data.email.lower().strip()
    success = user_manager.verify_email_code(email, data.code)
    if not success:
        raise HTTPException(status_code=400, detail='Неверный или истекший код подтверждения')
    return {'message': 'Почта successfully подтверждена'}

@router.post('/login/email')
async def login_email(data: EmailLoginRequest, response: Response):
    from core.user_manager import user_manager
    email = data.email.lower().strip()
    db_user = user_manager.get_user_by_email(email)
    if not db_user:
        raise HTTPException(status_code=401, detail='Неверный email или пароль')
        
    if not db_user.get('password_hash'):
        raise HTTPException(status_code=400, detail='Для данного аккаунта не задан пароль. Войдите через Google или зарегистрируйтесь.')
        
    if not user_manager.verify_password(data.password, db_user['password_hash']):
        raise HTTPException(status_code=401, detail='Неверный email или пароль')
        
    if db_user.get('is_email_verified', 0) == 0:
        code = user_manager.create_email_verification(email)
        send_verification_email(email, code)
        raise HTTPException(status_code=403, detail='Почта не подтверждена. Новый код подтверждения отправлен на ваш email.')
        
    token = create_jwt_token(TokenData(email=db_user['email'], name=db_user['name'], picture=db_user['picture'], id=db_user['id']))
    response.set_cookie(
        'auth_token', 
        token, 
        httponly=True, 
        secure=False,
        samesite='lax',
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return {'message': 'Успешный вход', 'user': {'email': db_user['email'], 'name': db_user['name']}}

@router.get('/telegram/callback')
async def telegram_callback(
    request: Request,
    id: int,
    first_name: str,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
    photo_url: Optional[str] = None,
    auth_date: int = 0,
    hash: str = ""
):
    import hashlib
    import hmac
    import time
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise HTTPException(status_code=500, detail="Telegram Bot Token не настроен на сервере")
        
    if time.time() - auth_date > 86400:
        raise HTTPException(status_code=400, detail="Срок действия авторизации Telegram истек")
        
    params = {
        'id': str(id),
        'first_name': first_name,
        'auth_date': str(auth_date)
    }
    if last_name:
        params['last_name'] = last_name
    if username:
        params['username'] = username
    if photo_url:
        params['photo_url'] = photo_url
        
    sorted_params = sorted(params.items())
    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted_params])
    
    secret_key = hashlib.sha256(bot_token.encode('utf-8')).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()
    
    if calculated_hash != hash:
        logger.warning(f"Invalid Telegram auth hash: {hash} vs {calculated_hash}")
        raise HTTPException(status_code=400, detail="Неверная подпись данных Telegram")
        
    from core.user_manager import user_manager
    db_user = user_manager.get_user_by_telegram_id(id)
    
    if not db_user:
        temp_email = f"tg_{id}@telegram.bot"
        db_user = user_manager.get_user_by_email(temp_email)
        if not db_user:
            name = first_name
            if last_name:
                name += f" {last_name}"
            user_id = user_manager.add_user(
                email=temp_email,
                name=name,
                picture=photo_url or "",
                role="user"
            )
            user_manager.update_user(user_id, telegram_id=id, telegram_username=username)
            db_user = user_manager.get_user_by_id(user_id)
            
    token = create_jwt_token(TokenData(email=db_user['email'], name=db_user['name'], picture=db_user['picture'], id=db_user['id']))
    
    response = RedirectResponse(url='/', status_code=302)
    response.set_cookie(
        'auth_token', 
        token, 
        httponly=True, 
        secure=False,
        samesite='lax',
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return response

class SettingsUpdateRequest(BaseModel):
    theme: Optional[str] = ""
    language: Optional[str] = ""
    tts_enabled: Optional[int] = 0
    system_instruction: Optional[str] = ""
    model: Optional[str] = ""
    tts_system: Optional[str] = ""
    tts_voice: Optional[str] = ""
    search_engine: Optional[str] = ""

# ===========================================
# Admin User Management API
# ===========================================

class UserCreateRequest(BaseModel):
    email: str
    name: str
    role: Optional[str] = 'user'
    is_active: Optional[int] = 1

class UserUpdateRequest(BaseModel):
    name: Optional[str] = ""
    email: Optional[str] = ""
    role: Optional[str] = ""
    is_active: Optional[int] = 0

@router.get('/admin/users')
async def list_users(request: Request):
    """Получение списка всех пользователей (только для администраторов)."""
    token = request.cookies.get('auth_token')
    if not token:
        raise HTTPException(status_code=401, detail='Не авторизован')
    
    user_data = verify_jwt_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail='Неверный сессионный токен')
    
    from core.user_manager import user_manager
    db_user = user_manager.get_user_by_email(user_data.email)
    
    # Check прав администратора
    if not db_user or not db_user.get('is_admin', 0):
        raise HTTPException(status_code=403, detail='Только администраторы могут просматривать list пользователей')
    
    users = user_manager.get_all_users(active_only=False)
    return {'users': users}

@router.put('/admin/users/{user_id}')
async def update_user(user_id: int, data: UserUpdateRequest, request: Request):
    """Update данных пользователя (только для администраторов)."""
    token = request.cookies.get('auth_token')
    if not token:
        raise HTTPException(status_code=401, detail='Не авторизован')
    
    user_data = verify_jwt_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail='Неверный сессионный токен')
    
    from core.user_manager import user_manager
    db_user = user_manager.get_user_by_email(user_data.email)
    
    # Check прав администратора
    if not db_user or not db_user.get('is_admin', 0):
        raise HTTPException(status_code=403, detail='Только администраторы могут редактировать пользователей')
    
    # Update пользователя
    updates = {}
    if data.name is not None:
        updates['name'] = data.name
    if data.email is not None:
        updates['email'] = data.email
    if data.role is not None:
        updates['role'] = data.role
    if data.is_active is not None:
        updates['is_active'] = data.is_active
    
    if updates:
        success = user_manager.update_user(user_id, **updates)
        if not success:
            raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    return {'status': 'ok', 'user_id': user_id}

@router.delete('/admin/users/{user_id}')
async def delete_user(user_id: int, request: Request):
    """Удаление пользователя (только для администраторов)."""
    token = request.cookies.get('auth_token')
    if not token:
        raise HTTPException(status_code=401, detail='Не авторизован')
    
    user_data = verify_jwt_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail='Неверный сессионный токен')
    
    from core.user_manager import user_manager
    db_user = user_manager.get_user_by_email(user_data.email)
    
    # Check прав администратора
    if not db_user or not db_user.get('is_admin', 0):
        raise HTTPException(status_code=403, detail='Только администраторы могут удалять пользователей')
    
    # Нельзя удалить самого себя
    if db_user['id'] == user_id:
        raise HTTPException(status_code=400, detail='Нельзя удалить самого себя')
    
    success = user_manager.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    
    return {'status': 'ok', 'message': 'Пользователь удалён'}

@router.get('/cabinet')
async def get_cabinet(request: Request) -> dict:
    """Получение данных личного кабинета пользователя."""
    token = request.cookies.get('auth_token')
    if not token:
        raise HTTPException(status_code=401, detail='Не авторизован')
    user_data = verify_jwt_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail='Неверный сессионный токен')
    
    from core.user_manager import user_manager
    db_user = user_manager.get_user_by_email(user_data.email)
    if not db_user:
        raise HTTPException(status_code=404, detail='Пользователь не найден в БД')
        
    return {
        'id': db_user['id'],
        'email': db_user['email'],
        'name': db_user['name'],
        'picture': db_user['picture'],
        'created_at': db_user['created_at'],
        'telegram_username': db_user.get('telegram_username'),
        'role': db_user['role'],
        'is_admin': db_user['is_admin']
    }

@router.post('/link-token')
async def get_link_token(request: Request) -> dict:
    """Генерация временного токена для привязки Telegram-аккаунта."""
    token = request.cookies.get('auth_token')
    if not token:
        raise HTTPException(status_code=401, detail='Не авторизован')
    user_data = verify_jwt_token(token)
    if not user_data or not user_data.email:
        raise HTTPException(status_code=401, detail='Неверный сессионный токен')
    
    from core.user_manager import user_manager
    db_user = user_manager.get_user_by_email(user_data.email)
    if not db_user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
        
    link_token = user_manager.generate_link_token(db_user['id'])
    return {'token': link_token}

@router.get('/settings')
async def get_settings(request: Request) -> dict:
    """Получение настроек текущего пользователя."""
    token = request.cookies.get('auth_token')
    if not token:
        raise HTTPException(status_code=401, detail='Не авторизован')
    user_data = verify_jwt_token(token)
    if not user_data or not user_data.email:
        raise HTTPException(status_code=401, detail='Неверный сессионный токен')
        
    from core.user_manager import user_manager
    db_user = user_manager.get_user_by_email(user_data.email)
    if not db_user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
        
    settings = user_manager.get_user_settings(db_user['id'])
    
    # Добавляем актуальный поисковый движок из config.json
    try:
        cfg_path = __root__ / 'config.json'
        if cfg_path.exists():
            with open(cfg_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                settings['search_engine'] = cfg.get('web_search', {}).get('engine', 'gemini_cli')
        else:
            settings['search_engine'] = 'gemini_cli'
    except Exception as e:
        logger.warning(f'Не удалось прочитать search_engine из config.json: {e}')
        settings['search_engine'] = 'gemini_cli'

    return settings

@router.post('/settings')
async def update_settings(request: Request, data: SettingsUpdateRequest) -> dict:
    """Update настроек текущего пользователя."""
    token = request.cookies.get('auth_token')
    if not token:
        raise HTTPException(status_code=401, detail='Не авторизован')
    user_data = verify_jwt_token(token)
    if not user_data or not user_data.email:
        raise HTTPException(status_code=401, detail='Неверный сессионный токен')
        
    from core.user_manager import user_manager
    db_user = user_manager.get_user_by_email(user_data.email)
    if not db_user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
        
    success = user_manager.update_user_settings(
        db_user['id'],
        theme=data.theme,
        language=data.language,
        tts_enabled=data.tts_enabled,
        system_instruction=data.system_instruction,
        model=data.model,
        tts_system=data.tts_system,
        tts_voice=data.tts_voice
    )
    if not success:
        raise HTTPException(status_code=500, detail='Не удалось сохранить настройки')
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Initialization роутера авторизации.

    Returns:
        APIRouter: Настроенный роутер FastAPI.
    """
    return router
