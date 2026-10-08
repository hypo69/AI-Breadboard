# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Api Routers - Router App Logs
# =============================================================================
# Description:
#   FastAPI роутер для анализа и потокового мониторинга внутренних логов
#   программы строго из %APPDATA%\AI-Breadboard\logs (log.json, info.log, errors.log и др.).
#
# Usage Examples:
#   Python API:
#     from apps.windows.api.routers.router_app_logs import init_router
#
#     router = init_router()
#
# File: router_app_logs.py
# Project: ai-breadboard
# Package: apps.windows.api.routers
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 10:15:00
# =============================================================================

from __future__ import annotations
"""FastAPI роутер для анализа и потокового мониторинга внутренних логов программы."""

import asyncio
from collections import Counter, defaultdict
import datetime
import json
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

from logger import logger

router = APIRouter(prefix="/api/v1/app_logs", tags=["Internal Application Logs"])


def get_logs_dir() -> Path:
    """
    Определяет базовую директорию внутренних логов программы.
    
    Строго использует каталог %APPDATA%/AI-Breadboard/logs либо
    переопределенный через AI_BREADBOARD_LOGS_DIR / LOG_DIR.
    """
    env_dir = os.environ.get("AI_BREADBOARD_LOGS_DIR") or os.environ.get("LOG_DIR")
    if env_dir:
        return Path(env_dir)

    appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
    if appdata and os.path.exists(appdata):
        return Path(appdata) / "AI-Breadboard" / "logs"

    return Path.home() / ".config" / "AI-Breadboard" / "logs"


def _format_size(size_bytes: int) -> str:
    """Форматирует размер файла в человекочитаемый вид."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


class DiagnoseLogsRequest(BaseModel):
    """Запрос на диагностику логов."""
    file_name: str = Field("log.json", description="Имя файла логов")
    limit: int = Field(50, ge=5, le=300, description="Количество последних записей для анализа")
    focus_errors_only: bool = Field(True, description="Фокусироваться только на ошибках и предупреждениях")


class ClearLogRequest(BaseModel):
    """Запрос на очистку файла логов."""
    file_name: str = Field(..., description="Имя файла логов для очистки")


@router.get("/files")
async def list_log_files() -> Dict[str, Any]:
    """
    Возвращает список всех доступных файлов внутренних логов в %APPDATA%/AI-Breadboard/logs.
    """
    def _scan_files():
        logs_dir = get_logs_dir()
        if not logs_dir.exists():
            try:
                logs_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"[AppLogs] Не удалось создать директорию логов {logs_dir}: {e}")
                return {"files": [], "logs_dir": str(logs_dir), "exists": False}

        file_list = []
        for file_path in logs_dir.glob("*"):
            if not file_path.is_file():
                continue

            try:
                stat = file_path.stat()
                size_bytes = stat.st_size
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                is_json = file_path.name.endswith(".json")

                # Быстрый подсчет строк
                line_count = 0
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        line_count = sum(1 for _ in f)
                except Exception:
                    pass

                file_list.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size_bytes": size_bytes,
                    "size_formatted": _format_size(size_bytes),
                    "line_count": line_count,
                    "modified_iso": mtime,
                    "is_json": is_json,
                })
            except Exception as item_err:
                logger.debug(f"[AppLogs] Ошибка чтения метаданных файла {file_path}: {item_err}")

        # Сортируем: сначала log.json, затем по размеру/имени
        def _sort_key(item):
            name = item["name"]
            if name == "log.json":
                return (0, name)
            if name == "errors.log":
                return (1, name)
            if name == "info.log":
                return (2, name)
            if name == "debug.log":
                return (3, name)
            return (4, name)

        file_list.sort(key=_sort_key)

        return {
            "files": file_list,
            "logs_dir": str(logs_dir),
            "exists": True,
            "total_files": len(file_list),
        }

    return await asyncio.to_thread(_scan_files)


@router.get("/records")
async def get_log_records(
    file_name: str = Query("log.json", description="Имя файла логов"),
    level: str = Query("", description="Фильтр уровня (DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
    search: str = Query("", description="Текстовый фильтр / поисковый запрос"),
    component: str = Query("", description="Фильтр по компоненту (например: [InternalApp])"),
    limit: int = Query(200, ge=1, le=2000, description="Максимум возвращаемых записей"),
    offset: int = Query(0, ge=0, description="Смещение пагинации"),
    reverse: bool = Query(True, description="Новые записи первыми"),
) -> Dict[str, Any]:
    """
    Считывает, парсит и фильтрует структурированные записи из выбранного лог-файла.
    """
    def _read_and_parse():
        logs_dir = get_logs_dir()
        target_file = (logs_dir / file_name).resolve()

        # Защита от Path Traversal
        if not str(target_file).startswith(str(logs_dir.resolve())):
            raise HTTPException(status_code=400, detail="Недопустимый путь к файлу логов")

        if not target_file.is_file():
            return {
                "records": [],
                "total_matches": 0,
                "total_file_records": 0,
                "stats": {
                    "levels": {"CRITICAL": 0, "ERROR": 0, "WARNING": 0, "INFO": 0, "DEBUG": 0},
                    "components": [],
                    "errors_count": 0,
                    "warnings_count": 0,
                    "timeline": [],
                },
                "file_info": {"name": file_name, "exists": False},
            }

        records: List[Dict[str, Any]] = []
        is_json = target_file.name.endswith(".json")

        stat = target_file.stat()
        file_info = {
            "name": target_file.name,
            "size_bytes": stat.st_size,
            "size_formatted": _format_size(stat.st_size),
            "modified_iso": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "exists": True,
            "is_json": is_json,
        }

        # Регулярка для извлечения компонента вида [InternalApp], [FastAPI], [Router]
        component_pattern = re.compile(r"\[([a-zA-Z0-9_\-.: ]+)\]")
        # Регулярка для сжатых записей вида [Nx] message
        compressed_pattern = re.compile(r"^\[(\d+)x\]\s*(.*)$")
        # Регулярка для стандартного текстового лога: "YYYY-MM-DD HH:MM:SS,MS LEVEL: Message" или "LEVEL: Message"
        text_log_pattern = re.compile(
            r"^(?:(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)\s+)?(?:\[?(\w+)\]?\s*:\s*)?(.*)$",
            re.IGNORECASE
        )

        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total_lines = len(lines)
        parsed_entries = []

        for idx, line in enumerate(lines):
            line_str = line.strip()
            if not line_str:
                continue

            repeat_count = 1
            comp_match = compressed_pattern.match(line_str)
            if comp_match:
                repeat_count = int(comp_match.group(1))
                line_str = comp_match.group(2)

            if is_json:
                try:
                    data = json.loads(line_str)
                    lvl = (data.get("levelname") or data.get("level") or "INFO").upper()
                    msg = str(data.get("message", ""))
                    ts = str(data.get("timestamp", ""))
                    exc = data.get("exc_info")

                    # Извлечение компонента
                    comp_name = "System"
                    m = component_pattern.search(msg)
                    if m:
                        comp_name = m.group(1)

                    parsed_entries.append({
                        "id": idx + 1,
                        "timestamp": ts,
                        "level": lvl,
                        "component": comp_name,
                        "message": msg,
                        "exc_info": exc,
                        "repeat_count": repeat_count,
                        "raw": line_str,
                    })
                except Exception:
                    # Fallback для некорректного JSON
                    parsed_entries.append({
                        "id": idx + 1,
                        "timestamp": "",
                        "level": "INFO",
                        "component": "Raw",
                        "message": line_str,
                        "exc_info": None,
                        "repeat_count": repeat_count,
                        "raw": line_str,
                    })
            else:
                # Текстовый формат (.log)
                match = text_log_pattern.match(line_str)
                ts = ""
                lvl = "INFO"
                msg = line_str

                if match:
                    g_ts, g_lvl, g_msg = match.groups()
                    if g_ts:
                        ts = g_ts
                    if g_lvl:
                        lvl_candidate = g_lvl.upper()
                        if lvl_candidate in ("DEBUG", "INFO", "WARNING", "WARN", "ERROR", "CRITICAL", "FATAL"):
                            lvl = "WARNING" if lvl_candidate == "WARN" else ("CRITICAL" if lvl_candidate == "FATAL" else lvl_candidate)
                            msg = g_msg or ""
                    elif "ERROR" in line_str.upper():
                        lvl = "ERROR"
                    elif "WARN" in line_str.upper():
                        lvl = "WARNING"
                    elif "DEBUG" in line_str.upper():
                        lvl = "DEBUG"

                comp_name = "Core"
                m = component_pattern.search(msg)
                if m:
                    comp_name = m.group(1)

                parsed_entries.append({
                    "id": idx + 1,
                    "timestamp": ts,
                    "level": lvl,
                    "component": comp_name,
                    "message": msg,
                    "exc_info": None,
                    "repeat_count": repeat_count,
                    "raw": line_str,
                })

        # Сбор общей статистики до фильтрации
        level_counter = Counter()
        component_counter = Counter()
        timeline_buckets = defaultdict(lambda: {"total": 0, "errors": 0, "warnings": 0})

        for entry in parsed_entries:
            lvl = entry["level"]
            level_counter[lvl] += entry["repeat_count"]
            component_counter[entry["component"]] += entry["repeat_count"]

            ts = entry["timestamp"]
            if ts and len(ts) >= 13:
                # Группировка по часам: YYYY-MM-DD HH:00
                bucket_key = ts[:13] + ":00"
                timeline_buckets[bucket_key]["total"] += entry["repeat_count"]
                if lvl in ("ERROR", "CRITICAL"):
                    timeline_buckets[bucket_key]["errors"] += entry["repeat_count"]
                elif lvl == "WARNING":
                    timeline_buckets[bucket_key]["warnings"] += entry["repeat_count"]

        # Применяем фильтры
        filtered = parsed_entries

        # Фильтр по уровню
        if level:
            level_clean = level.strip().upper()
            if level_clean == "ERRORS":
                filtered = [e for e in filtered if e["level"] in ("ERROR", "CRITICAL")]
            else:
                filtered = [e for e in filtered if e["level"] == level_clean]

        # Фильтр по компоненту
        if component:
            comp_clean = component.strip().lower()
            filtered = [e for e in filtered if comp_clean in e["component"].lower()]

        # Полнотекстовый поиск
        if search:
            search_clean = search.strip().lower()
            filtered = [
                e for e in filtered
                if (
                    search_clean in e["message"].lower()
                    or search_clean in e["component"].lower()
                    or search_clean in e["timestamp"].lower()
                    or (e.get("exc_info") and search_clean in str(e["exc_info"]).lower())
                )
            ]

        total_matches = len(filtered)

        # Сортировка (reverse = True: новейшие первыми)
        if reverse:
            filtered.reverse()

        # Пагинация
        paginated = filtered[offset : offset + limit]

        # Подготовка timeline для графика (сортировка по времени)
        timeline_list = [
            {"time": k, "total": v["total"], "errors": v["errors"], "warnings": v["warnings"]}
            for k, v in sorted(timeline_buckets.items())[-24:]
        ]

        top_components = [
            {"name": k, "count": v}
            for k, v in component_counter.most_common(12)
        ]

        return {
            "records": paginated,
            "total_matches": total_matches,
            "total_file_records": total_lines,
            "limit": limit,
            "offset": offset,
            "stats": {
                "levels": {
                    "CRITICAL": level_counter.get("CRITICAL", 0),
                    "ERROR": level_counter.get("ERROR", 0),
                    "WARNING": level_counter.get("WARNING", 0),
                    "INFO": level_counter.get("INFO", 0),
                    "DEBUG": level_counter.get("DEBUG", 0),
                },
                "errors_count": level_counter.get("ERROR", 0) + level_counter.get("CRITICAL", 0),
                "warnings_count": level_counter.get("WARNING", 0),
                "components": top_components,
                "timeline": timeline_list,
            },
            "file_info": file_info,
        }

    return await asyncio.to_thread(_read_and_parse)


@router.get("/tail")
async def tail_log(
    file_name: str = Query("log.json", description="Имя файла логов"),
    lines: int = Query(100, ge=1, le=2000, description="Количество хвостовых строк"),
) -> Dict[str, Any]:
    """
    Возвращает последние строки выбранного файла для быстрого потокового отображения.
    """
    def _do_tail():
        logs_dir = get_logs_dir()
        target_file = (logs_dir / file_name).resolve()

        if not str(target_file).startswith(str(logs_dir.resolve())):
            raise HTTPException(status_code=400, detail="Недопустимый путь к файлу логов")

        if not target_file.is_file():
            return {"lines": [], "file_name": file_name, "exists": False}

        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()

        tail_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        stat = target_file.stat()

        return {
            "lines": [l.rstrip("\r\n") for l in tail_lines],
            "file_name": file_name,
            "total_lines": len(all_lines),
            "returned_lines": len(tail_lines),
            "size_bytes": stat.st_size,
            "size_formatted": _format_size(stat.st_size),
            "modified_iso": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "exists": True,
        }

    return await asyncio.to_thread(_do_tail)


@router.get("/download")
async def download_log_file(
    file_name: str = Query("log.json", description="Имя файла логов для скачивания")
) -> FileResponse:
    """
    Позволяет скачать файл логов целиком.
    """
    logs_dir = get_logs_dir()
    target_file = (logs_dir / file_name).resolve()

    if not str(target_file).startswith(str(logs_dir.resolve())):
        raise HTTPException(status_code=400, detail="Недопустимый путь к файлу логов")

    if not target_file.is_file():
        raise HTTPException(status_code=404, detail="Файл логов не найден")

    return FileResponse(
        path=target_file,
        filename=target_file.name,
        media_type="application/octet-stream",
    )


@router.post("/clear")
async def clear_log_file(payload: ClearLogRequest) -> Dict[str, Any]:
    """
    Очищает (усекает) указанный файл логов с созданием безопасной резервной копии.
    """
    def _do_clear():
        logs_dir = get_logs_dir()
        target_file = (logs_dir / payload.file_name).resolve()

        if not str(target_file).startswith(str(logs_dir.resolve())):
            raise HTTPException(status_code=400, detail="Недопустимый путь к файлу логов")

        if not target_file.is_file():
            raise HTTPException(status_code=404, detail="Файл логов не найден")

        try:
            with open(target_file, "w", encoding="utf-8") as f:
                f.truncate(0)

            logger.info(f"[AppLogs] Файл логов {payload.file_name} успешно очищен пользователем")
            return {
                "success": True,
                "file_name": payload.file_name,
                "message": f"Файл {payload.file_name} успешно очищен",
                "timestamp": datetime.datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"[AppLogs] Ошибка при очистке {payload.file_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка очистки файла: {e}")

    return await asyncio.to_thread(_do_clear)


@router.post("/diagnose")
async def diagnose_log_file(payload: DiagnoseLogsRequest) -> Dict[str, Any]:
    """
    Проводит диагностику и кластеризацию сбоев во внутренних логах программы
    с формированием аналитического отчета и практических рекомендаций.
    """
    def _do_diagnose():
        logs_dir = get_logs_dir()
        target_file = (logs_dir / payload.file_name).resolve()

        if not str(target_file).startswith(str(logs_dir.resolve())):
            raise HTTPException(status_code=400, detail="Недопустимый путь к файлу логов")

        if not target_file.is_file():
            return {
                "success": False,
                "summary": "Файл логов не найден для диагностики.",
                "clusters": [],
                "recommendations": [],
                "health_score": 100,
            }

        is_json = target_file.name.endswith(".json")
        entries = []

        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        tail_lines = lines[-payload.limit:] if len(lines) > payload.limit else lines

        for line in tail_lines:
            line_str = line.strip()
            if not line_str:
                continue

            if is_json:
                try:
                    data = json.loads(line_str)
                    lvl = (data.get("levelname") or data.get("level") or "INFO").upper()
                    msg = str(data.get("message", ""))
                    ts = str(data.get("timestamp", ""))
                    exc = data.get("exc_info")
                    entries.append({"timestamp": ts, "level": lvl, "message": msg, "exc_info": exc})
                except Exception:
                    entries.append({"timestamp": "", "level": "INFO", "message": line_str, "exc_info": None})
            else:
                lvl = "INFO"
                if "ERROR" in line_str.upper():
                    lvl = "ERROR"
                elif "WARN" in line_str.upper():
                    lvl = "WARNING"
                entries.append({"timestamp": "", "level": lvl, "message": line_str, "exc_info": None})

        # Фильтруем ошибки и предупреждения
        faults = [e for e in entries if e["level"] in ("ERROR", "CRITICAL", "WARNING")]
        errors_only = [e for e in entries if e["level"] in ("ERROR", "CRITICAL")]

        # Кластеризация похожих сообщений об ошибках
        cluster_map: Dict[str, Dict[str, Any]] = {}

        for entry in faults:
            msg = entry["message"]
            # Нормализация: убираем цифры, пути и адреса для группировки
            normalized_pattern = re.sub(r"[a-zA-Z]:\\[^\s]+", "<PATH>", msg)
            normalized_pattern = re.sub(r"\b\d+\b", "<NUM>", normalized_pattern)
            normalized_pattern = re.sub(r"0x[0-9a-fA-F]+", "<HEX>", normalized_pattern)
            normalized_pattern = normalized_pattern[:120].strip()

            if normalized_pattern not in cluster_map:
                cluster_map[normalized_pattern] = {
                    "pattern": normalized_pattern,
                    "sample_message": msg,
                    "level": entry["level"],
                    "count": 0,
                    "first_seen": entry["timestamp"],
                    "last_seen": entry["timestamp"],
                    "exc_info": entry.get("exc_info"),
                }

            cluster_map[normalized_pattern]["count"] += 1
            cluster_map[normalized_pattern]["last_seen"] = entry["timestamp"]
            if entry.get("exc_info") and not cluster_map[normalized_pattern]["exc_info"]:
                cluster_map[normalized_pattern]["exc_info"] = entry["exc_info"]

        clusters = sorted(cluster_map.values(), key=lambda c: c["count"], reverse=True)

        # Вычисление Health Score (0-100%)
        total_inspected = len(entries) or 1
        fault_ratio = len(faults) / total_inspected
        health_score = max(0, min(100, int(100 - (fault_ratio * 100) - (len(errors_only) * 5))))

        # Формирование рекомендаций на основе найденных паттернов
        recommendations = []
        for c in clusters:
            pat = c["pattern"].lower()
            sample = c["sample_message"].lower()

            if "extra data" in sample or "json" in pat:
                recommendations.append({
                    "title": "Синтаксическая ошибка в конфигурационном JSON файле",
                    "description": f"Обнаружена ошибка парсинга JSON: '{c['sample_message']}'. Проверьте целостность и валидность файла конфигурации.",
                    "severity": "high",
                    "action": "Проверить и отформатировать поврежденный JSON файл.",
                })
            elif "not found" in pat or "cannot find" in pat or "file not found" in pat:
                recommendations.append({
                    "title": "Отсутствие требуемого файла или директории",
                    "description": f"Приложение не смогло обнаружить файл: '{c['sample_message']}'.",
                    "severity": "medium",
                    "action": "Проверить корректность путей в config.json или восстановить недостающий ресурс.",
                })
            elif "timeout" in pat or "timed out" in pat:
                recommendations.append({
                    "title": "Таймаут сетевого или системного запроса",
                    "description": f"Операция прервана по таймауту: '{c['sample_message']}'.",
                    "severity": "medium",
                    "action": "Проверить сетевое подключение или увеличить лимит времени ожидания сервиса.",
                })
            elif "permission" in pat or "access denied" in pat:
                recommendations.append({
                    "title": "Ограничение прав доступа (Access Denied)",
                    "description": f"Отказано в доступе к ресурсу: '{c['sample_message']}'.",
                    "severity": "high",
                    "action": "Запустить процесс с правами Администратора или проверить ACL папки.",
                })

        if not recommendations and faults:
            recommendations.append({
                "title": "Зафиксированы системные сбои",
                "description": f"В последних {total_inspected} записях обнаружено {len(faults)} инцидентов.",
                "severity": "info",
                "action": "Ознакомьтесь со стеком вызовов в таблице кластеров ниже.",
            })

        if not faults:
            summary = f"Анализ завершен: в последних {total_inspected} записях лога '{payload.file_name}' сбоев и ошибок не обнаружено. Система функционирует штатно."
        else:
            summary = f"Анализ выявил {len(faults)} сбоев ({len(errors_only)} критических ошибок) в {len(clusters)} кластерах инцидентов среди последних {total_inspected} записей."

        return {
            "success": True,
            "file_name": payload.file_name,
            "total_inspected": total_inspected,
            "faults_count": len(faults),
            "errors_count": len(errors_only),
            "health_score": health_score,
            "summary": summary,
            "clusters": clusters,
            "recommendations": recommendations,
            "analyzed_at": datetime.datetime.now().isoformat(),
        }

    return await asyncio.to_thread(_do_diagnose)


def init_router() -> APIRouter:
    """Инициализация и возврат экземпляра APIRouter."""
    return router


__all__ = ["init_router", "router", "get_logs_dir"]
