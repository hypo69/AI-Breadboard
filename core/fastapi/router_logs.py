# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: FastAPI-роутер панели управления логами
# =============================================================================
# Описание:
#   API-эндпоинты для просмотра, чтения, очистки и AI-анализа лог-файлов.
#   Маршруты: GET /api/logs/files, GET /api/logs/read, DELETE /api/logs/clear,
#             POST /api/logs/analyze, GET /api/logs/reports
#
# File: src/fastapi/router_logs.py
# Project: ai-assistant
# Package: src.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import datetime
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from header import __root__
from core.logger import logger

LOG_DIR = __root__ / 'tmp' / 'logs'
REPORTS_DIR = __root__ / 'tmp' / 'reports'

# Список разрешённых имён файлов (whitelist)
_ALLOWED_EXTENSIONS = {'.log', '.json', '.md', '.txt'}


def _safe_log_path(filename: str) -> Path:
    """Возвращает путь к файлу логов после проверки безопасности."""
    path = (LOG_DIR / filename).resolve()
    if not str(path).startswith(str(LOG_DIR.resolve())):
        raise HTTPException(status_code=400, detail='Недопустимый путь к файлу')
    if path.suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail='Недопустимое расширение файла')
    return path


def _safe_report_path(filename: str) -> Path:
    """Возвращает путь к файлу отчёта после проверки безопасности."""
    path = (REPORTS_DIR / filename).resolve()
    if not str(path).startswith(str(REPORTS_DIR.resolve())):
        raise HTTPException(status_code=400, detail='Недопустимый путь к файлу')
    if path.suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail='Недопустимое расширение файла')
    return path


def _file_info(p: Path) -> dict:
    """Возвращает метаданные файла."""
    stat = p.stat()
    return {
        'name': p.name,
        'size': stat.st_size,
        'size_kb': round(stat.st_size / 1024, 1),
        'modified': datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
    }


class AnalyzeRequest(BaseModel):
    filename: str


def init_router(prefix: str = '/api/logs') -> APIRouter:
    router = APIRouter(prefix=prefix, tags=['logs'])

    # ------------------------------------------------------------------
    # GET /api/logs/files — список лог-файлов
    # ------------------------------------------------------------------
    @router.get('/files')
    async def list_log_files() -> dict:
        """Возвращает список доступных лог-файлов с их метаданными."""
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        files = []
        for p in sorted(LOG_DIR.iterdir()):
            if p.is_file() and p.suffix in _ALLOWED_EXTENSIONS:
                files.append(_file_info(p))
        return {'files': files, 'count': len(files)}

    # ------------------------------------------------------------------
    # GET /api/logs/read?filename=info.log&tail=200 — чтение файла
    # ------------------------------------------------------------------
    @router.get('/read')
    async def read_log_file(filename: str, tail: int = 500) -> dict:
        """Возвращает последние `tail` строк лог-файла."""
        path = _safe_log_path(filename)
        if not path.exists():
            raise HTTPException(status_code=404, detail=f'Файл не найден: {filename}')

        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'Ошибка чтения файла: {e}')

        total = len(lines)
        sliced = lines[-tail:] if tail > 0 else lines
        return {
            'filename': filename,
            'total_lines': total,
            'returned_lines': len(sliced),
            'content': ''.join(sliced),
        }

    # ------------------------------------------------------------------
    # DELETE /api/logs/clear?filename=info.log — очистка файла
    # ------------------------------------------------------------------
    @router.delete('/clear')
    async def clear_log_file(filename: str) -> dict:
        """Очищает содержимое лог-файла (обнуляет, не удаляет)."""
        path = _safe_log_path(filename)
        if not path.exists():
            raise HTTPException(status_code=404, detail=f'Файл не найден: {filename}')

        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.truncate(0)
            logger.info(f'Лог-файл очищен вручную: {filename}')
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'Ошибка при очистке: {e}')

        return {'status': 'ok', 'message': f'Файл {filename} очищен'}

    # ------------------------------------------------------------------
    # POST /api/logs/analyze — запуск AI-анализа
    # ------------------------------------------------------------------
    @router.post('/analyze')
    async def analyze_log(body: AnalyzeRequest) -> dict:
        """Запускает AI-анализ лог-файла через Gemini."""
        path = _safe_log_path(body.filename)
        if not path.exists():
            raise HTTPException(status_code=404, detail=f'Файл не найден: {body.filename}')

        try:
            from core.logger.log_analyzer import analyze_log_file
            from core.ai import GoogleGenerativeAI

            api_key_names = [
                n.strip()
                for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',')
                if n.strip()
            ]
            ai_model = GoogleGenerativeAI(
                api_key_names=api_key_names,
                system_instruction=(
                    'Вы — профессиональный аналитик системных логов. '
                    'Исследуйте логи, выявляйте ошибки, проблемы, тренды '
                    'и давайте рекомендации по устранению.'
                ),
            )

            import asyncio
            asyncio.create_task(analyze_log_file(path, ai_model))
            return {'status': 'started', 'message': f'Анализ файла {body.filename} запущен в фоне'}

        except Exception as e:
            logger.error(f'Ошибка запуска AI-анализа для {body.filename}', e)
            raise HTTPException(status_code=500, detail=f'Ошибка: {e}')

    # ------------------------------------------------------------------
    # GET /api/logs/reports — список AI-отчётов
    # ------------------------------------------------------------------
    @router.get('/reports')
    async def list_reports() -> dict:
        """Возвращает список AI-отчётов из папки logs/reports/."""
        if not REPORTS_DIR.exists():
            return {'reports': [], 'count': 0}

        reports = []
        for p in sorted(REPORTS_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if p.is_file() and p.suffix in _ALLOWED_EXTENSIONS:
                reports.append(_file_info(p))
        return {'reports': reports, 'count': len(reports)}

    # ------------------------------------------------------------------
    # GET /api/logs/report?filename=master_journal.md — чтение отчёта
    # ------------------------------------------------------------------
    @router.get('/report')
    async def read_report(filename: str) -> dict:
        """Возвращает содержимое AI-отчёта."""
        path = _safe_report_path(filename)
        if not path.exists():
            raise HTTPException(status_code=404, detail=f'Отчёт не найден: {filename}')

        try:
            content = path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'Ошибка чтения отчёта: {e}')

        return {
            'filename': filename,
            'content': content,
            'size': len(content),
        }

    # ------------------------------------------------------------------
    # GET /api/logs/stats — сводная статистика
    # ------------------------------------------------------------------
    @router.get('/stats')
    async def log_stats() -> dict:
        """Возвращает сводную статистику по лог-файлам."""
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        stats = {
            'total_size_bytes': 0,
            'file_count': 0,
            'report_count': 0,
            'files': [],
        }

        for p in LOG_DIR.iterdir():
            if p.is_file() and p.suffix in _ALLOWED_EXTENSIONS:
                sz = p.stat().st_size
                stats['total_size_bytes'] += sz
                stats['file_count'] += 1
                stats['files'].append({'name': p.name, 'size': sz})

        if REPORTS_DIR.exists():
            stats['report_count'] = sum(
                1 for p in REPORTS_DIR.iterdir()
                if p.is_file() and p.suffix in _ALLOWED_EXTENSIONS
            )

        stats['total_size_kb'] = round(stats['total_size_bytes'] / 1024, 1)
        stats['total_size_mb'] = round(stats['total_size_bytes'] / (1024 * 1024), 2)
        return stats

    return router
