"""UI page handlers for the AI-Breadboard application."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, Response

from src.config import server_cfg
from src.logger import logger

__root__ = Path(__file__).resolve().parents[3]
webinterface_dir = Path(__file__).resolve().parents[2] / 'api' / 'webgui'


def register_pages(app: FastAPI) -> None:
    """Register all UI page handlers with the application.
    
    Args:
        app: FastAPI application instance to register pages with.
    """
    # Load HTML content helpers
    def read_text_file(path: Path) -> str:
        try:
            return path.read_text(encoding='utf-8')
        except Exception:
            return ''

    # Check admin auth
    def check_admin_auth(request: Request):
        from fastapi.responses import HTMLResponse, RedirectResponse

        # If authentication is globally disabled (e.g., tc.ps1 / ts.ps1 launcher)
        from src.api.router_auth import is_auth_disabled
        if is_auth_disabled():
            return None

        # 1. Check if user is authenticated via admin session password cookie
        if request.cookies.get('admin_password_verified') == 'true':
            return None

        # 2. Check if user is authenticated via OAuth / JWT token with admin role
        token = request.cookies.get('auth_token', '')
        if not token:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:].strip()
            elif auth_header.startswith('Token '):
                token = auth_header[6:].strip()

        if token:
            from src.api.router_auth import verify_jwt_token
            from src.user_manager import user_manager
            user_data = verify_jwt_token(token)
            if user_data and user_data.email:
                if user_data.email in ('admin@localhost', 'local@aibreadboard.local') or user_data.email.startswith('admin@'):
                    return None
                db_user = user_manager.get_user_by_email(user_data.email)
                if db_user and (db_user.get('is_admin', 0) or db_user.get('role') == 'admin'):
                    return None

        if request.url.path in ('/admin', '/admin/'):
            return HTMLResponse(content=ADMIN_LOGIN_HTML)

        return RedirectResponse(url='/admin', status_code=303)


    # Mount static directories on first registration
    from src.app import mount_static_files
    mount_static_files(app)
    
    # Setup favicon (now handled by mount_static_files)

    # === User Pages ===
    
    @app.get('/', response_class=HTMLResponse)
    async def root(request: Request) -> HTMLResponse:
        """Serving of main HTML page — authenticated user dashboard or login auth gate."""
        def is_authenticated_user(request: Request) -> bool:
            from src.api.router_auth import is_auth_disabled
            if is_auth_disabled():
                return True
            token = request.cookies.get('auth_token', '')
            if not token:
                auth_header = request.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:].strip()
                elif auth_header.startswith('Token '):
                    token = auth_header[6:].strip()
            if not token:
                return False
            from src.api.router_auth import verify_jwt_token
            return verify_jwt_token(token) is not None

        if is_authenticated_user(request):
            content = read_text_file(webinterface_dir / 'user' / 'index.html')
            if not content:
                raise HTTPException(status_code=500, detail='Failed to read user index page')
            return HTMLResponse(content=content)

        login_content = read_text_file(webinterface_dir / 'login.html')
        if not login_content:
            raise HTTPException(status_code=500, detail='Failed to read login page')
        return HTMLResponse(content=login_content)

    @app.get('/login', response_class=HTMLResponse)
    async def login_page(request: Request):
        """Serving of login & registration page."""
        from fastapi.responses import RedirectResponse
        def is_authenticated_user(request: Request) -> bool:
            from src.api.router_auth import is_auth_disabled
            if is_auth_disabled():
                return True
            token = request.cookies.get('auth_token', '')
            if not token:
                auth_header = request.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:].strip()
                elif auth_header.startswith('Token '):
                    token = auth_header[6:].strip()
            if not token:
                return False
            from src.api.router_auth import verify_jwt_token
            return verify_jwt_token(token) is not None

        if is_authenticated_user(request):
            return RedirectResponse(url='/', status_code=303)
        login_content = read_text_file(webinterface_dir / 'login.html')
        if not login_content:
            raise HTTPException(status_code=500, detail='Failed to read login page')
        return HTMLResponse(content=login_content)

    @app.get('/user')
    async def user_interface(request: Request) -> RedirectResponse:
        """Redirect User interface path to root /."""
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url='/', status_code=303)

    @app.get('/user/{full_path:path}', response_class=HTMLResponse)
    async def user_static(full_path: str) -> HTMLResponse:
        """Serving User static files."""
        content = read_text_file(webinterface_dir / 'user' / full_path)
        if not content:
            raise HTTPException(status_code=404, detail='File not found')
        return HTMLResponse(content=content)

    # === Telegram Mini App Pages ===
    
    @app.get('/tgmini', response_class=HTMLResponse)
    async def tgmini_interface() -> HTMLResponse:
        """Serving of Telegram Mini App HTML page."""
        content = read_text_file(webinterface_dir / 'tgmini' / 'index.html')
        if not content:
            raise HTTPException(status_code=500, detail='Failed to read Telegram Mini App index page')
        return HTMLResponse(content=content)

    @app.get('/tgmini/{full_path:path}', response_class=HTMLResponse)
    async def tgmini_static(full_path: str) -> HTMLResponse:
        """Serving Telegram Mini App static files."""
        content = read_text_file(webinterface_dir / 'tgmini' / full_path)
        if not content:
            raise HTTPException(status_code=404, detail='File not found')
        return HTMLResponse(content=content)

    # === Remote Control Pages ===
    
    @app.get('/rc', response_class=HTMLResponse)
    async def rc_interface() -> HTMLResponse:
        """Serving of Remote Control HTML page."""
        content = read_text_file(webinterface_dir / 'rc' / 'index.html')
        if not content:
            raise HTTPException(status_code=500, detail='Failed to read Remote Control page')
        return HTMLResponse(content=content)

    @app.get('/rc/{full_path:path}', response_class=HTMLResponse)
    async def rc_static(full_path: str) -> HTMLResponse:
        """Serving Remote Control static files."""
        content = read_text_file(webinterface_dir / 'rc' / full_path)
        if not content:
            raise HTTPException(status_code=404, detail='File not found')
        return HTMLResponse(content=content)

    # === Voice Remote Control Pages ===
    
    @app.get('/mic', response_class=HTMLResponse)
    @app.get('/remote_mic', response_class=HTMLResponse)
    async def remote_mic_interface() -> HTMLResponse:
        """Serve Voice Remote Control standalone HTML page."""
        content = read_text_file(webinterface_dir / 'remote_mic' / 'index.html')
        if not content:
            raise HTTPException(status_code=500, detail='Failed to read Voice Remote Control page')
        return HTMLResponse(content=content)

    @app.get('/mic/{full_path:path}', response_class=HTMLResponse)
    @app.get('/remote_mic/{full_path:path}', response_class=HTMLResponse)
    async def remote_mic_static(full_path: str) -> HTMLResponse:
        """Serve static asset files for Voice Remote Control application."""
        content = read_text_file(webinterface_dir / 'remote_mic' / full_path)
        if not content:
            raise HTTPException(status_code=404, detail='File not found')
        return HTMLResponse(content=content)

    # === User TTS Pages ===
    
    @app.get('/user_tts', response_class=HTMLResponse)
    async def user_tts_interface() -> HTMLResponse:
        """Serving of User TTS experimental page."""
        content = read_text_file(webinterface_dir / 'user_tts' / 'index.html')
        if not content:
            raise HTTPException(status_code=500, detail='Failed to read User TTS page')
        return HTMLResponse(content=content)

    @app.get('/user_tts/{full_path:path}', response_class=HTMLResponse)
    async def user_tts_static(full_path: str) -> HTMLResponse:
        """Serving User TTS static files."""
        content = read_text_file(webinterface_dir / 'user_tts' / full_path)
        if not content:
            raise HTTPException(status_code=404, detail='File not found')
        return HTMLResponse(content=content)

    # === Messenger Pages ===
    
    @app.get('/messenger', response_class=HTMLResponse)
    async def messenger_interface() -> HTMLResponse:
        """Serving of Real-Time Messenger and WebRTC meeting page."""
        content = read_text_file(webinterface_dir / 'messenger' / 'index.html')
        if not content:
            raise HTTPException(status_code=500, detail='Failed to read Messenger page')
        return HTMLResponse(content=content)

    @app.get('/messenger/{full_path:path}', response_class=HTMLResponse)
    async def messenger_static(full_path: str) -> HTMLResponse:
        """Serving Messenger static files."""
        content = read_text_file(webinterface_dir / 'messenger' / full_path)
        if not content:
            raise HTTPException(status_code=404, detail='File not found')
        return HTMLResponse(content=content)

    # === Helpdesk Pages ===
    
    @app.get('/helpdesk', response_class=HTMLResponse)
    async def helpdesk_interface() -> HTMLResponse:
        """Serving Helpdesk support management dashboard."""
        content = read_text_file(webinterface_dir / 'helpdesk' / 'index.html')
        if not content:
            raise HTTPException(status_code=500, detail='Failed to read Helpdesk page')
        return HTMLResponse(content=content)

    @app.get('/helpdesk/{full_path:path}', response_class=Response)
    async def helpdesk_static(full_path: str) -> Response:
        """Serving Helpdesk static files."""
        file_path = webinterface_dir / 'helpdesk' / full_path
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail='File not found')
        
        media_type = "text/plain"
        if full_path.endswith('.css'):
            media_type = "text/css"
        elif full_path.endswith('.js'):
            media_type = "application/javascript"
        elif full_path.endswith('.html'):
            media_type = "text/html"
        elif full_path.endswith('.json'):
            media_type = "application/json"
        
        return FileResponse(file_path, media_type=media_type)

    # === Applications Hub & Test Computer (/tc, /apps, /log_audit) ===

    @app.get('/tc', response_class=HTMLResponse)
    @app.get('/apps', response_class=HTMLResponse)
    @app.get('/log_audit', response_class=HTMLResponse)
    @app.get('/log-audit', response_class=HTMLResponse)
    async def apps_interface(request: Request) -> HTMLResponse:
        """Display the Applications Container / Test Computer page (/tc, /apps, /log_audit)."""
        content = read_text_file(webinterface_dir / 'apps' / 'index.html')
        if not content:
            raise HTTPException(status_code=500, detail='Failed to read apps index page')
        response = HTMLResponse(content=content)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    @app.get('/tc/{full_path:path}', response_class=HTMLResponse)
    @app.get('/apps/{full_path:path}', response_class=HTMLResponse)
    @app.get('/log_audit/{full_path:path}', response_class=HTMLResponse)
    @app.get('/log-audit/{full_path:path}', response_class=HTMLResponse)
    async def apps_static(full_path: str, request: Request):
        """Serving apps / test-computer portal static files."""
        file_path = webinterface_dir / 'apps' / full_path
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail='File not found')
        media_type = "text/plain"
        if full_path.endswith('.css'):
            media_type = "text/css"
        elif full_path.endswith('.js'):
            media_type = "application/javascript"
        elif full_path.endswith('.html'):
            media_type = "text/html"
        elif full_path.endswith('.json'):
            media_type = "application/json"
        return FileResponse(file_path, media_type=media_type)

    # === Admin Pages ===
    
    @app.get('/admin')
    async def admin_interface(request: Request):
        """Display the main admin panel page."""
        auth_response = check_admin_auth(request)
        if auth_response:
            return auth_response
        content = read_text_file(webinterface_dir / 'admin' / 'index.html')
        if not content:
            raise HTTPException(status_code=500, detail='Failed to read admin index page')
        return HTMLResponse(content=content)

    @app.post('/admin')
    async def admin_interface_post(request: Request):
        """Verify password and set admin authentication cookie."""
        from fastapi.responses import RedirectResponse
        from fastapi import Form
        form = await request.form()
        password = form.get('password')
        admin_password = os.getenv('ADMIN_PASSWORD')
        if not admin_password:
            logger.error("ADMIN_PASSWORD is not configured in .env")
            return RedirectResponse(url='/admin', status_code=303)

        if password and password == admin_password:
            response = RedirectResponse(url='/admin', status_code=303)
            response.set_cookie(
                key='admin_password_verified',
                value='true',
                max_age=86400 * 30,
                httponly=True,
                samesite='lax',
                path='/'
            )
            return response
        else:
            return RedirectResponse(url='/admin', status_code=303)

    @app.get('/admin/{full_path:path}')
    async def admin_static(full_path: str, request: Request):
        """Serving admin static files with security verification."""
        auth_response = check_admin_auth(request)
        if auth_response:
            return auth_response
        content = read_text_file(webinterface_dir / 'admin' / full_path)
        if not content:
            raise HTTPException(status_code=404, detail='File not found')
        return HTMLResponse(content=content)

    # === TV Player Pages ===
    
    @app.get('/tv', response_class=HTMLResponse)
    @app.get('/cosmicplayer', response_class=HTMLResponse)
    async def tv_interface() -> HTMLResponse:
        """Serving of TV Player HTML page."""
        tv_dir = webinterface_dir / 'tv'
        if not tv_dir.exists():
            tv_dir = webinterface_dir / 'cosmicplayer'
        content = read_text_file(tv_dir / 'index.html')
        if not content:
            raise HTTPException(status_code=500, detail='Failed to read TV index page')
        return HTMLResponse(content=content)

    @app.get('/tv/{full_path:path}', response_class=HTMLResponse)
    @app.get('/cosmicplayer/{full_path:path}', response_class=HTMLResponse)
    async def tv_static(full_path: str) -> HTMLResponse:
        """Serving TV static files."""
        tv_dir = webinterface_dir / 'tv'
        if not tv_dir.exists():
            tv_dir = webinterface_dir / 'cosmicplayer'
        content = read_text_file(tv_dir / full_path)
        if not content:
            raise HTTPException(status_code=404, detail='File not found')
        return HTMLResponse(content=content)

    @app.get('/logs')
    async def logs_interface(request: Request):
        """Redirect to admin dashboard logs tab."""
        from fastapi.responses import RedirectResponse
        auth_response = check_admin_auth(request)
        if auth_response:
            return auth_response
        return RedirectResponse(url='/admin#tab-logs', status_code=303)


# Admin login HTML (extracted from main.py)
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
            <p>Авторизуйтесь для доступа к панели администратора</p>
        </div>

        <!-- Google OAuth Primary Login -->
        <a href="/auth/google?next=/admin" class="btn-google" id="admin-google-auth-btn">
            <svg width="20" height="20" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/></svg>
            <span>Войти через Google (OAuth)</span>
        </a>

        <div class="divider">
            <span>или по паролю администратора</span>
        </div>

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

