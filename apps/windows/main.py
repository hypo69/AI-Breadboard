# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows - Main
# =============================================================================
# Description:
#   Главная точка входа для приложения AI Windows Diagnostic & Administration Center.
#
# Usage Examples:
#   CLI:
#     python -m apps.windows.main
#   Python API:
#     from apps.windows.main import load_tc_config
#
#     res = load_tc_config()
#
# Updated: 2026-10-08 01:30:00
# =============================================================================

from __future__ import annotations
"""Главная точка входа для приложения AI Windows Diagnostic & Administration Center."""

# Updated: 2026-10-01 07:03:00
# =============================================================================
"""
Главная точка входа для приложения AI Windows Diagnostic & Administration Center.

Запускает автономный оптимизированный FastAPI сервер для среды Test Computer (/tc)
и системных инструментов Windows без избыточных внешних зависимостей.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Исправление для Proactor на Windows при сбросе соединений
if sys.platform == 'win32':
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport
        _orig_call_connection_lost = _ProactorBasePipeTransport._call_connection_lost

        def _patched_call_connection_lost(self, exc=None):
            try:
                _orig_call_connection_lost(self, exc)
            except ConnectionResetError:
                pass
            except OSError as err:
                if getattr(err, 'winerror', None) != 10054:
                    raise
        _ProactorBasePipeTransport._call_connection_lost = _patched_call_connection_lost
    except Exception:
        pass

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / '.env')

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from logger import logger
from src.app.cors import build_cors_config
from src.app.metrics import create_metrics
from src.app.state import AppState
from src.app.ws_hub import WSHub

_WEBGUI_DIR = _PROJECT_ROOT / 'src' / 'api' / 'webgui'


def load_tc_config(config_path_override: Optional[str] = None) -> Dict[str, Any]:
    """Загрузка конфигурации для Test Computer / Windows App.

    Args:
        config_path_override: Пользовательский путь к файлу конфигурации.

    Returns:
        Словарь с параметрами конфигурации.
    """
    candidates: List[Path] = []
    if config_path_override:
        p = Path(config_path_override)
        candidates.append(p if p.is_absolute() else _PROJECT_ROOT / p)

    env_cfg = os.getenv('AIBREADBOARD_CONFIG') or os.getenv('CONFIG_FILE')
    if env_cfg:
        p = Path(env_cfg)
        candidates.append(p if p.is_absolute() else _PROJECT_ROOT / p)
        candidates.append(_PROJECT_ROOT / 'start_scenarios_config' / p.name)

    candidates.extend([
        _PROJECT_ROOT / 'start_scenarios_config' / 'tc.json',
        _PROJECT_ROOT / 'config' / 'tc.json',
        _PROJECT_ROOT / 'config_tc.json',
        _PROJECT_ROOT / 'apps' / 'windows' / 'config.json',
        _PROJECT_ROOT / 'config.json',
    ])

    for cand in candidates:
        if cand.exists() and cand.is_file():
            try:
                with open(cand, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception as exc:
                logger.warning(f'Не удалось прочитать конфигурацию из {cand}: {exc}')

    return {}


from contextlib import asynccontextmanager

def create_windows_app(config: Optional[Dict[str, Any]] = None) -> FastAPI:
    """Создание и сборка экземпляра FastAPI для Windows Diagnostic Center.

    Args:
        config: Словарь настроек или None для автоматической загрузки.

    Returns:
        Сконфигурированный экземпляр FastAPI.
    """
    app_config = config if config is not None else load_tc_config()
    server_section = app_config.get('server', {})
    cors_config = build_cors_config(server_section)

    state = AppState()
    state.metrics = create_metrics(started_at=state.started_at)
    state.ws_hub = WSHub()

    @asynccontextmanager
    async def lifespan(app_: FastAPI):
        if state.ws_hub:
            await state.ws_hub.start_heartbeat()

        # Фоновый сервис сбора телеметрии
        telemetry_svc = None
        try:
            from apps.windows.telemetry.service import TelemetryLoggerService
            telemetry_svc = TelemetryLoggerService.get_instance()
            telemetry_svc.start()
            logger.info("[MainApp] Фоновый сервис телеметрии запущен.")
        except Exception as tel_err:
            logger.warning(f"[MainApp] Ошибка запуска фонового сервиса телеметрии: {tel_err}")

        # Проверка критических аудитов при запуске
        try:
            from apps.windows.telemetry.audit_startup_checker import run_startup_audit
            startup_audit = run_startup_audit(
                check_integrity=True,
                check_performance=True,
                check_drivers=False,
                check_eventlog=False
            )
            if not startup_audit.is_healthy:
                logger.error(
                    f"🚨 STARTUP AUDIT: Критические проблемы! "
                    f"Critical: {startup_audit.critical_count}, Warnings: {startup_audit.warning_count}"
                )
                for finding in startup_audit.findings:
                    logger.warning(f"  - [{finding['severity'].upper()}] {finding['domain']}: {finding['title']}")
            elif startup_audit.warning_count > 0:
                logger.warning(f"⚠️ STARTUP AUDIT: Предупреждения: {startup_audit.warning_count}")
            else:
                logger.info(f"✅ STARTUP AUDIT: Проверки пройдены ({startup_audit.duration_ms}ms)")
        except Exception as audit_err:
            logger.debug(f"Startup audit: {audit_err}")

        yield

        if telemetry_svc:
            try:
                telemetry_svc.stop()
                logger.info("[MainApp] Фоновый сервис телеметрии остановлен.")
            except Exception:
                pass

        if state.ws_hub:
            await state.ws_hub.stop()

    app = FastAPI(
        title='AI Windows Diagnostic & Administration Center',
        description='Выделенный сервер диагностики, аудита и администрирования Windows',
        version='2.0.0',
        docs_url='/docs',
        redoc_url='/redoc',
        openapi_url='/openapi.json',
        lifespan=lifespan,
    )

    app.add_middleware(CORSMiddleware, **cors_config)

    # Middleware против кэширования статики интерфейса
    @app.middleware('http')
    async def add_no_cache_headers(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.startswith('/html/') or path.startswith('/webinterface/') or path.startswith('/tc'):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

    app.state.app_state = state
    app.state.metrics = state.metrics
    app.state.ws_hub = state.ws_hub

    # Инициализация легковесной модели ИИ только если она включена
    ai_cfg = app_config.get('ai', {})
    try:
        from src.ai import UnifiedChatModel
        state.chat_model = UnifiedChatModel()
        state.narrator_model = UnifiedChatModel() if ai_cfg.get('enable_narrator', False) else None
    except Exception as exc:
        logger.debug(f'AI модель не инициализирована: {exc}')
        state.chat_model = None
        state.narrator_model = None
    app.state.chat_model = state.chat_model
    app.state.narrator_model = state.narrator_model

    # Монтирование статических файлов веб-интерфейса
    if _WEBGUI_DIR.exists():
        app.mount('/webinterface', StaticFiles(directory=str(_WEBGUI_DIR)), name='webinterface')

    def _read_web_file(rel_path: str) -> str:
        target = _WEBGUI_DIR / rel_path
        if target.exists() and target.is_file():
            return target.read_text(encoding='utf-8')
        return ''

    # Основные веб-страницы Test Computer (/tc, /apps, /su, /log_audit)
    @app.get('/', response_class=HTMLResponse)
    @app.get('/tc', response_class=HTMLResponse)
    @app.get('/apps', response_class=HTMLResponse)
    @app.get('/su', response_class=HTMLResponse)
    @app.get('/log_audit', response_class=HTMLResponse)
    async def tc_interface(request: Request) -> HTMLResponse:
        """Главный интерфейс Test Computer / Windows Diagnostics."""
        content = _read_web_file('apps/index.html')
        if not content:
            raise HTTPException(status_code=500, detail='Не удалось загрузить apps/index.html')
        resp = HTMLResponse(content=content)
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        return resp

    # Статические ассеты для приложений и меню
    @app.get('/tc/{full_path:path}')
    @app.get('/apps/{full_path:path}')
    @app.get('/su/{full_path:path}')
    @app.get('/log_audit/{full_path:path}')
    async def tc_static(full_path: str) -> Response:
        """Отдача статических файлов приложений портала TC."""
        file_path = _WEBGUI_DIR / 'apps' / full_path
        if not file_path.exists() or not file_path.is_file():
            # Поиск в общем каталоге webinterface
            alt_path = _WEBGUI_DIR / full_path
            if alt_path.exists() and alt_path.is_file():
                file_path = alt_path
            else:
                raise HTTPException(status_code=404, detail=f'Файл не найден: {full_path}')

        media_type = 'text/plain'
        if full_path.endswith('.css'):
            media_type = 'text/css'
        elif full_path.endswith('.js'):
            media_type = 'application/javascript'
        elif full_path.endswith('.html'):
            media_type = 'text/html'
        elif full_path.endswith('.json'):
            media_type = 'application/json'
        return FileResponse(file_path, media_type=media_type)

    @app.get('/html/{full_path:path}')
    async def html_static_fallback(full_path: str) -> Response:
        """Совместимость с путями /html/... к меню и ресурсам."""
        file_path = _WEBGUI_DIR / full_path
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail=f'Файл не найден: /html/{full_path}')
        media_type = 'text/plain'
        if full_path.endswith('.css'):
            media_type = 'text/css'
        elif full_path.endswith('.js'):
            media_type = 'application/javascript'
        elif full_path.endswith('.html'):
            media_type = 'text/html'
        elif full_path.endswith('.json'):
            media_type = 'application/json'
        elif full_path.endswith('.png'):
            media_type = 'image/png'
        elif full_path.endswith('.svg'):
            media_type = 'image/svg+xml'
        return FileResponse(file_path, media_type=media_type)

    # -------------------------------------------------------------------------
    # Регистрация только необходимых роутеров Windows & TC
    # -------------------------------------------------------------------------
    # 1. Основной диагностический роутер Windows
    try:
        from apps.windows.router import init_router as init_windows_router
        app.include_router(init_windows_router(app, state))
    except Exception as exc:
        logger.warning(f'Ошибка регистрации apps.windows.router: {exc}')

    # 2. Windows Sysadmin (AD, аудит файлов и безопасности)
    try:
        from apps.windows.modules.sysadmin.router import init_router as init_sysadmin_router
        app.include_router(init_sysadmin_router())
    except Exception as exc:
        logger.debug(f'Роутер sysadmin не зарегистрирован: {exc}')

    # 3. Сетевой терминал
    try:
        from apps.windows.modules.network.router import init_router as init_network_router
        app.include_router(init_network_router())
    except Exception as exc:
        logger.debug(f'Роутер network не зарегистрирован: {exc}')

    # 4. Центр управления системой
    try:
        from apps.windows.modules.system_control_center.router import init_router as init_scc_router
        app.include_router(init_scc_router())
    except Exception as exc:
        logger.debug(f'Роутер system_control_center не зарегистрирован: {exc}')

    # 5. Панели оборудования (/api/v1/panel/*, /api/v1/about-system)

    try:
        from apps.windows.api.routers.router_hardware_sensors import init_router as init_hardware_sensors_router
        app.include_router(init_hardware_sensors_router())
    except Exception as exc:
        logger.debug(f'Роутер router_hardware_sensors не зарегистрирован: {exc}')

    try:
        from apps.windows.api.routers.router_cpu_load import init_router as init_cpu_load_router
        app.include_router(init_cpu_load_router())
    except Exception as exc:
        logger.debug(f'Роутер router_cpu_load не зарегистрирован: {exc}')

    try:
        from apps.windows.api.routers.router_gpu_load import init_router as init_gpu_load_router
        app.include_router(init_gpu_load_router())
    except Exception as exc:
        logger.debug(f'Роутер router_gpu_load не зарегистрирован: {exc}')

    try:
        from apps.windows.api.routers.router_storage_load import init_router as init_storage_load_router
        app.include_router(init_storage_load_router())
    except Exception as exc:
        logger.debug(f'Роутер router_storage_load не зарегистрирован: {exc}')

    try:
        from apps.windows.api.routers.router_memory_io import init_router as init_memory_io_router
        app.include_router(init_memory_io_router())
    except Exception as exc:
        logger.debug(f'Роутер router_memory_io не зарегистрирован: {exc}')

    try:
        from apps.windows.api.routers.router_network_load import init_router as init_network_load_router
        app.include_router(init_network_load_router())
    except Exception as exc:
        logger.debug(f'Роутер router_network_load не зарегистрирован: {exc}')

    try:
        from apps.windows.api.routers.router_telemetry_config import init_router as init_telemetry_config_router
        app.include_router(init_telemetry_config_router())
    except Exception as exc:
        logger.debug(f'Роутер router_telemetry_config не зарегистрирован: {exc}')

    try:
        from apps.windows.api.routers.router_about_system import init_router as init_about_system_router
        app.include_router(init_about_system_router())
    except Exception as exc:
        logger.debug(f'Роутер router_about_system не зарегистрирован: {exc}')

    try:
        from src.api.routers.core.router_system import init_router as init_system_diagnostics_router
        app.include_router(init_system_diagnostics_router(chat_model=state.chat_model))
    except Exception as exc:
        logger.debug(f'Роутер router_system не зарегистрирован: {exc}')

    try:
        from apps.windows.api.routers.router_windows_admin import init_router as init_win_admin_router
        app.include_router(init_win_admin_router())
    except Exception as exc:
        logger.debug(f'Роутер router_windows_admin не зарегистрирован: {exc}')

    try:
        from apps.windows.api.routers.router_diagnostics import init_router as init_apps_diag_router
        app.include_router(init_apps_diag_router())
    except Exception as exc:
        logger.debug(f'Роутер router_diagnostics не зарегистрирован: {exc}')

    try:
        from apps.windows.api.routers.router_chat import init_router as init_apps_chat_router
        app.include_router(init_apps_chat_router(chat_model=state.chat_model, narrator_model=state.narrator_model))
    except Exception as exc:
        logger.debug(f'Роутер router_chat не зарегистрирован: {exc}')

    try:
        from apps.windows.api.routers.router_admin import init_router as init_apps_admin_router, init_skills_router, init_plugins_router, init_apps_router
        app.include_router(init_apps_admin_router())
        app.include_router(init_skills_router())
        app.include_router(init_plugins_router())
        app.include_router(init_apps_router())
    except Exception as exc:
        logger.debug(f'Роутер router_admin не зарегистрирован: {exc}')

    # 6. Аудитор автозагрузки
    try:
        from apps.windows.modules.startup.router import init_router as init_startup_router
        app.include_router(init_startup_router())
    except Exception as exc:
        logger.debug(f'Роутер startup не зарегистрирован: {exc}')

    # 7. Диспетчер резервного копирования
    try:
        from apps.windows.modules.backup_manager.router import init_router as init_backup_router
        app.include_router(init_backup_router())
    except Exception as exc:
        logger.debug(f'Роутер backup_manager не зарегистрирован: {exc}')

    # 8. Защитник Windows
    try:
        from apps.windows.modules.defender.router import init_router as init_defender_router
        app.include_router(init_defender_router())
    except Exception as exc:
        logger.debug(f'Роутер defender не зарегистрирован: {exc}')

    # 8.1. Управление хранилищем (Storage Manager)
    try:
        from apps.windows.modules.storage_manager.router import init_router as init_storage_mgr_router
        app.include_router(init_storage_mgr_router())
    except Exception as exc:
        logger.debug(f'Роутер storage_manager не зарегистрирован: {exc}')

    # 8.2. Загрузка и восстановление (Boot & Recovery)
    try:
        from apps.windows.modules.boot_recovery.router import init_router as init_boot_router
        app.include_router(init_boot_router())
    except Exception as exc:
        logger.debug(f'Роутер boot_recovery не зарегистрирован: {exc}')

    # 8.3. Целостность системных файлов (Servicing & Integrity)
    try:
        from apps.windows.modules.servicing_integrity.router import init_router as init_servicing_router
        app.include_router(init_servicing_router())
    except Exception as exc:
        logger.debug(f'Роутер servicing_integrity не зарегистрирован: {exc}')

    # 8.4. Системные службы (Services Manager)
    try:
        from apps.windows.modules.services_manager.router import init_router as init_services_mgr_router
        app.include_router(init_services_mgr_router())
    except Exception as exc:
        logger.debug(f'Роутер services_manager не зарегистрирован: {exc}')

    # 8.5. Планировщик заданий (Task Scheduler)
    try:
        from apps.windows.modules.task_scheduler.router import init_router as init_sched_router
        app.include_router(init_sched_router())
    except Exception as exc:
        logger.debug(f'Роутер task_scheduler не зарегистрирован: {exc}')

    # 8.6. Управление процессами (Process Manager)
    try:
        from apps.windows.modules.process_manager.router import init_router as init_proc_router
        app.include_router(init_proc_router())
    except Exception as exc:
        logger.debug(f'Роутер process_manager не зарегистрирован: {exc}')

    # 8.7. Брандмауэр Windows (Firewall Manager)
    try:
        from apps.windows.modules.firewall_manager.router import init_router as init_firewall_router
        app.include_router(init_firewall_router())
    except Exception as exc:
        logger.debug(f'Роутер firewall_manager не зарегистрирован: {exc}')

    # 8.8. Безопасность и ACL (Security & ACL)
    try:
        from apps.windows.modules.security_acl.router import init_router as init_sec_acl_router
        app.include_router(init_sec_acl_router())
    except Exception as exc:
        logger.debug(f'Роутер security_acl не зарегистрирован: {exc}')

    # 8.9. Производительность и трассировка (Performance & Tracing)
    try:
        from apps.windows.modules.performance_tracing.router import init_router as init_perf_tracing_router
        app.include_router(init_perf_tracing_router())
    except Exception as exc:
        logger.debug(f'Роутер performance_tracing не зарегистрирован: {exc}')

    # 8.10. Журналы событий (Event Logs)
    try:
        from apps.windows.modules.event_logs.router import init_router as init_event_logs_router
        app.include_router(init_event_logs_router())
    except Exception as exc:
        logger.debug(f'Роутер event_logs не зарегистрирован: {exc}')

    # 8.11. Управление ПО и пакетами (Software Manager)
    try:
        from apps.windows.modules.software_manager.router import init_router as init_sw_mgr_router
        app.include_router(init_sw_mgr_router())
    except Exception as exc:
        logger.debug(f'Роутер software_manager не зарегистрирован: {exc}')

    # 10. Каталог атомарных возможностей Windows CLI и API (/api/v1/capabilities)
    try:
        from apps.windows.api.router_capabilities import init_router as init_capabilities_router
        app.include_router(init_capabilities_router())
    except Exception as exc:
        logger.debug(f'Роутер capabilities не зарегистрирован: {exc}')

    # 10.1. Windows Window Management Control Plane (/api/v1/window-management)
    try:
        from apps.windows.modules.window_control_plane.router import init_router as init_wcp_router
        app.include_router(init_wcp_router())
    except Exception as exc:
        logger.debug(f'Роутер window_control_plane не зарегистрирован: {exc}')

    # 10.2. Windows Personalization & Appearance (/api/v1/windows/personalization)
    try:
        from apps.windows.modules.personalization.router import init_router as init_personalization_router
        app.include_router(init_personalization_router())
    except Exception as exc:
        logger.debug(f'Роутер personalization не зарегистрирован: {exc}')

    # 10.3. Progressive Knowledge Base WikiLLM (/api/windows/wikillm)
    try:
        from apps.windows.wikillm.router import init_router as init_wikillm_router
        app.include_router(init_wikillm_router())
    except Exception as exc:
        logger.debug(f'Роутер wikillm не зарегистрирован: {exc}')

    # 11. Роутер Test Computer (/tc/model, /tc/model_instruction, /tc/telemetry)
    try:
        from src.api.routers.tc.router_tc import init_router as init_tc_router
        app.include_router(init_tc_router())
    except Exception as exc:
        logger.warning(f'Роутер TC не зарегистрирован: {exc}')

    # 12. Вспомогательные роутеры меню и утилит
    try:
        from src.api.routers.core.router_menu import init_router as init_menu_router
        app.include_router(init_menu_router())
    except Exception:
        pass

    try:
        from src.api.routers.core.router_recovery import init_router as init_recovery_router
        app.include_router(init_recovery_router())
    except Exception:
        pass

    try:
        from src.api.routers.core.router_ninite import init_router as init_ninite_router
        app.include_router(init_ninite_router())
    except Exception:
        pass

    try:
        from src.api.routers.core.router_registry_viewer import init_router as init_reg_router
        app.include_router(init_reg_router())
    except Exception:
        pass

    try:
        from src.api.routers.core.router_system_logs import init_router as init_sys_logs_router
        app.include_router(init_sys_logs_router())
    except Exception:
        pass

    try:
        from src.api.routers.core.router_scenarios import init_router as init_scenarios_router
        app.include_router(init_scenarios_router())
    except Exception:
        pass

    @app.get('/favicon.ico', include_in_schema=False)
    async def favicon() -> Response:
        """Отдача иконки favicon.ico."""
        fav = _WEBGUI_DIR / 'favicon.ico'
        if not fav.exists():
            fav = _WEBGUI_DIR / 'assets' / 'favicon.ico'
        if fav.exists():
            return FileResponse(fav)
        return Response(status_code=204)

    # -------------------------------------------------------------------------
    # Эндпоинты статусов приложений и настроек ИИ по стандарту /api/v1/*
    # -------------------------------------------------------------------------
    @app.get('/api/v1/apps/status')
    @app.get('/api/apps/status')
    async def get_apps_status(profile: Optional[str] = None) -> Dict[str, Any]:
        """Возвращает статус доступности приложений для формирования меню."""
        cfg = load_tc_config(profile)
        apps_sec = cfg.get('apps', {})
        enabled_list = apps_sec.get('enabled', []) if isinstance(apps_sec, dict) else []
        disabled_list = apps_sec.get('disabled', []) if isinstance(apps_sec, dict) else []

        apps_map: Dict[str, Dict[str, Any]] = {}
        for item in enabled_list:
            apps_map[item] = {'enabled': True, 'name': item}
        for item in disabled_list:
            apps_map[item] = {'enabled': False, 'name': item}

        return {
            'status': 'ok',
            'apps': apps_map,
            'ai': cfg.get('ai', {}),
        }

    @app.get('/auth/settings')
    @app.get('/api/v1/auth/settings')
    async def get_user_settings() -> Dict[str, Any]:
        """Чтение активных настроек пользователя и модели."""
        cfg = load_tc_config()
        ai_sec = cfg.get('ai', {})
        prov = ai_sec.get('provider', 'gemini')
        model = ai_sec.get(prov, {}).get('model', '')
        return {'status': 'ok', 'model': f'{prov}:{model}' if model else prov, 'favorite_models': {}}

    @app.post('/auth/settings')
    @app.post('/api/v1/auth/settings')
    async def update_user_settings(request: Request) -> Dict[str, Any]:
        """Сохранение активной модели пользователя."""
        try:
            body = await request.json()
            return {'status': 'ok', 'saved': body}
        except Exception:
            return {'status': 'ok'}

    @app.get('/api/v1/chat/active-model')
    async def get_chat_active_model() -> Dict[str, Any]:
        """Возвращает активную модель ИИ."""
        cfg = load_tc_config()
        ai_sec = cfg.get('ai', {})
        prov = ai_sec.get('provider', 'gemini')
        model = ai_sec.get(prov, {}).get('model', '')
        return {'status': 'ok', 'provider': prov, 'model': model, 'config_file': 'tc.json'}

    @app.get('/api/v1/chat/models')
    async def get_available_chat_models() -> Dict[str, Any]:
        """Список доступных моделей ИИ для дропдауна."""
        return {
            'models': {
                'gemini': ['gemini-3.1-flash-lite', 'gemini-2.5-flash'],
                'gemini_cli': ['gemini:gemini-3.1-flash-lite'],
                'agy': ['agy-gemini-3.6-flash'],
            }
        }

    return app


# Экземпляр приложения по умолчанию
app = create_windows_app()


def run_standalone_server(
    host: str = '127.0.0.1',
    port: int = 8000,
    use_ssl: bool = False,
    reload: bool = False,
    workers: int = 1,
) -> None:
    """Запуск сервера через uvicorn с поддержкой параметров.

    Args:
        host: IP адрес для привязки.
        port: TCP порт сервера.
        use_ssl: Флаг использования SSL сертификатов.
        reload: Режим автоперезагрузки при изменении кода.
        workers: Количество рабочих процессов.
    """
    import uvicorn

    ssl_certfile = None
    ssl_keyfile = None

    if use_ssl:
        certs_dir = Path.home() / '.certs'
        cert_cand = certs_dir / 'localhost+2.pem'
        key_cand = certs_dir / 'localhost+2-key.pem'
        if cert_cand.exists() and key_cand.exists():
            ssl_certfile = str(cert_cand)
            ssl_keyfile = str(key_cand)
        else:
            logger.warning('SSL сертификаты не найдены в ~/.certs, запуск по HTTP')
            use_ssl = False

    proto = 'https' if use_ssl else 'http'
    print('\n' + '=' * 70)
    print('  AI WINDOWS DIAGNOSTIC & ADMINISTRATION CENTER (TEST COMPUTER)')
    print('=' * 70)
    print(f'  Адрес:     {proto}://{host}:{port}/tc')
    print(f'  API Docs:  {proto}://{host}:{port}/docs')
    print(f'  SSL:       {"ВКЛ" if use_ssl else "ВЫКЛ"}')
    print(f'  Reload:    {"ВКЛ" if reload else "ВЫКЛ"}')
    print('=' * 70 + '\n')

    import copy
    import uvicorn.config

    log_config = copy.deepcopy(uvicorn.config.LOGGING_CONFIG)
    log_config['formatters']['default']['fmt'] = '%(asctime)s %(levelprefix)s %(message)s'
    log_config['formatters']['default']['datefmt'] = '%Y-%m-%d %H:%M:%S'
    log_config['formatters']['access']['fmt'] = (
        '%(asctime)s %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
    )
    log_config['formatters']['access']['datefmt'] = '%Y-%m-%d %H:%M:%S'

    uvicorn.run(
        'apps.windows.main:app' if reload else app,
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,
        ssl_certfile=ssl_certfile,
        ssl_keyfile=ssl_keyfile,
        log_level='info',
        log_config=log_config,
    )


def main() -> None:
    """Парсинг аргументов командной строки и запуск сервера."""
    cfg = load_tc_config()
    server_sec = cfg.get('server', {})

    default_host = server_sec.get('host', '127.0.0.1')
    default_port = int(server_sec.get('port', 8000))
    protocol = server_sec.get('protocol', 'https' if server_sec.get('use_ssl', True) else 'http')
    default_ssl = protocol.lower() == 'https' or bool(server_sec.get('use_ssl', False))

    parser = argparse.ArgumentParser(description='AI Windows Diagnostic Center & Test Computer')
    parser.add_argument('--host', type=str, default=default_host, help='IP адрес привязки (по умолчанию из конфига)')
    parser.add_argument('--port', '-p', type=int, default=default_port, help='Порт сервера (по умолчанию из конфига)')
    parser.add_argument('--ssl', action='store_true', default=default_ssl, help='Использовать SSL')
    parser.add_argument('--no-ssl', action='store_false', dest='ssl', help='Отключить SSL')
    parser.add_argument('--reload', action='store_true', help='Включить автоперезагрузку')
    parser.add_argument('--workers', type=int, default=1, help='Количество воркеров uvicorn')
    args = parser.parse_args()

    run_standalone_server(
        host=args.host,
        port=args.port,
        use_ssl=args.ssl,
        reload=args.reload,
        workers=args.workers,
    )


if __name__ == '__main__':
    main()
