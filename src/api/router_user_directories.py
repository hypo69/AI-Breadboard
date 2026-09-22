# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: User Directories and Workspace Storage Router
# =============================================================================
# Description:
#   FastAPI REST API роутер для управления и мониторинга пользовательских директорий,
#   аудита дискового пространства, дерева файлов, предпросмотра, скачивания,
#   удаления файлов и пакетной очистки осиротевших каталогов.
#
# File: router_user_directories.py
# Project: AI-Breadboard
# Package: src.api
# Module: router_user_directories
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import base64
import mimetypes
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from logger import logger
from src.user_manager import user_manager

router = APIRouter(prefix="/api/admin/user-directories", tags=["user-directories"])


# =============================================================================
# Pydantic Модели
# =============================================================================

class OrphanedCleanRequest(BaseModel):
    """Модель запроса для очистки осиротевших каталогов."""
    dirs: Optional[List[str]] = Field(
        default=None,
        description="Список конкретных имен директорий для удаления. Если не передан — удаляются все."
    )


# =============================================================================
# Вспомогательные функции
# =============================================================================

def _format_size(size_bytes: int) -> str:
    """Форматирование размера в байтах в человекочитаемый вид."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def _format_timestamp(ts: float) -> str:
    """Форматирование временной метки в строку ISO/локальное время."""
    try:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "-"


def _check_admin_or_local_auth(request: Request) -> bool:
    """Проверка прав доступа: администратор, локальный хост или отключенная авторизация."""
    from src.api.router_auth import is_auth_disabled
    if is_auth_disabled():
        return True

    # 1. Проверка сессионной куки администратора
    if request.cookies.get("admin_password_verified") == "true":
        return True

    # 2. Проверка JWT токена
    token: str = request.cookies.get("auth_token", "")
    if not token:
        auth_header: str = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if token:
        from src.api.router_auth import verify_jwt_token
        user_data = verify_jwt_token(token)
        if user_data:
            if user_data.email in ("admin@localhost", "local@aibreadboard.local") or user_data.email.startswith("admin@"):
                return True
            db_user = user_manager.get_user_by_email(user_data.email)
            if db_user and (db_user.get("is_admin", 0) or db_user.get("role") == "admin"):
                return True

    # 3. Локальный хост (Test Computer / dev environment)
    hostname = request.url.hostname or ""
    if hostname in ("127.0.0.1", "localhost", "::1", "testserver", "0.0.0.0"):
        return True

    raise HTTPException(status_code=403, detail="Доступ разрешен только администраторам")


def _get_safe_user_path(user_id: int, relative_path: str = "") -> Path:
    """Безопасное получение пути внутри пользовательской директории с защитой от traversal."""
    user_root = user_manager.get_user_directory(user_id, create=True).resolve()
    if not relative_path:
        return user_root

    clean_rel = relative_path.replace("\\", "/").strip("/")
    target_path = (user_root / clean_rel).resolve()

    try:
        target_path.relative_to(user_root)
    except ValueError:
        raise HTTPException(status_code=400, detail="Недопустимый путь (выход за пределы директории пользователя)")

    return target_path


# =============================================================================
# Эндпоинты API
# =============================================================================

@router.get("/summary")
async def get_storage_summary(request: Request) -> Dict[str, Any]:
    """Получение сводной статистики хранилища всех пользователей.

    Args:
        request (Request): HTTP-запрос FastAPI.

    Returns:
        Dict[str, Any]: Агрегированная статистика хранилища.
    """
    _check_admin_or_local_auth(request)

    base_dir = user_manager.users_dir
    users = user_manager.get_all_users(active_only=False)

    total_storage_bytes = 0
    total_files_count = 0
    total_dirs_count = 0
    extension_counts: Dict[str, Dict[str, Any]] = {}

    user_ids_in_db = {u.get("id") for u in users if u.get("id")}
    orphaned_count = 0
    orphaned_bytes = 0

    # Сканирование реальных каталогов
    if base_dir.exists():
        for entry in base_dir.iterdir():
            if entry.is_dir():
                is_numeric_id = False
                try:
                    uid = int(entry.name)
                    is_numeric_id = True
                except ValueError:
                    uid = None

                is_orphaned = (not is_numeric_id) or (uid not in user_ids_in_db)

                dir_size = 0
                dir_files = 0
                for f in entry.rglob("*"):
                    if f.is_file():
                        dir_files += 1
                        try:
                            f_size = f.stat().st_size
                            dir_size += f_size
                            ext = f.suffix.lower().lstrip(".") or "no_ext"
                            if ext not in extension_counts:
                                extension_counts[ext] = {"count": 0, "size_bytes": 0}
                            extension_counts[ext]["count"] += 1
                            extension_counts[ext]["size_bytes"] += f_size
                        except Exception:
                            pass

                total_storage_bytes += dir_size
                total_files_count += dir_files
                total_dirs_count += 1

                if is_orphaned:
                    orphaned_count += 1
                    orphaned_bytes += dir_size

    # Сортировка расширений по размеру
    top_extensions = sorted(
        [
            {
                "extension": ext,
                "count": data["count"],
                "size_bytes": data["size_bytes"],
                "size_formatted": _format_size(data["size_bytes"]),
            }
            for ext, data in extension_counts.items()
        ],
        key=lambda x: x["size_bytes"],
        reverse=True,
    )

    return {
        "status": "ok",
        "summary": {
            "total_users": len(users),
            "total_storage_bytes": total_storage_bytes,
            "total_storage_formatted": _format_size(total_storage_bytes),
            "total_files_count": total_files_count,
            "total_directories_count": total_dirs_count,
            "orphaned_count": orphaned_count,
            "orphaned_bytes": orphaned_bytes,
            "orphaned_formatted": _format_size(orphaned_bytes),
            "top_extensions": top_extensions[:10],
        },
    }


@router.get("/users")
async def get_users_directories_list(request: Request) -> Dict[str, Any]:
    """Получение списка пользователей с детализацией их хранилищ и подпапок.

    Args:
        request (Request): HTTP-запрос FastAPI.

    Returns:
        Dict[str, Any]: Список пользователей с метриками хранилища.
    """
    _check_admin_or_local_auth(request)

    users = user_manager.get_all_users(active_only=False)
    results: List[Dict[str, Any]] = []

    for u in users:
        uid = u.get("id")
        if not uid:
            continue

        stats = user_manager.get_user_storage_stats(uid)
        user_dir = user_manager.get_user_directory(uid, create=False)
        exists = user_dir.exists()

        # Сканирование подпапок
        subfolders_info: Dict[str, Dict[str, Any]] = {}
        standard_subfolders = ["files", "rag", "profile", "temp"]

        if exists:
            for sub in standard_subfolders:
                sub_path = user_dir / sub
                if sub_path.exists() and sub_path.is_dir():
                    s_size = sum(f.stat().st_size for f in sub_path.rglob("*") if f.is_file())
                    s_files = sum(1 for f in sub_path.rglob("*") if f.is_file())
                    subfolders_info[sub] = {
                        "exists": True,
                        "files_count": s_files,
                        "size_bytes": s_size,
                        "size_formatted": _format_size(s_size),
                    }
                else:
                    subfolders_info[sub] = {
                        "exists": False,
                        "files_count": 0,
                        "size_bytes": 0,
                        "size_formatted": "0 B",
                    }
        else:
            for sub in standard_subfolders:
                subfolders_info[sub] = {
                    "exists": False,
                    "files_count": 0,
                    "size_bytes": 0,
                    "size_formatted": "0 B",
                }

        quota_bytes = stats.get("quota_bytes", 1073741824)  # По умолчанию 1 GB
        used_bytes = stats.get("total_bytes", 0)
        quota_percent = min(100.0, round((used_bytes / quota_bytes) * 100, 1)) if quota_bytes > 0 else 0.0

        results.append({
            "id": uid,
            "name": u.get("name", f"User {uid}"),
            "email": u.get("email", ""),
            "role": u.get("role", "user"),
            "is_admin": bool(u.get("is_admin", 0)),
            "is_active": bool(u.get("is_active", 1)),
            "last_login": u.get("last_login") or "-",
            "created_at": u.get("created_at") or "-",
            "exists_on_disk": exists,
            "dir_path": str(user_dir),
            "size_bytes": used_bytes,
            "size_formatted": _format_size(used_bytes),
            "files_count": stats.get("files_count", 0),
            "quota_bytes": quota_bytes,
            "quota_formatted": _format_size(quota_bytes),
            "quota_percent": quota_percent,
            "subfolders": subfolders_info,
        })

    # Сортировка: сначала пользователи с наибольшим объемом данных
    results.sort(key=lambda x: x["size_bytes"], reverse=True)

    return {"status": "ok", "users": results, "total": len(results)}


@router.get("/users/{user_id}/tree")
async def get_user_file_tree(
    user_id: int,
    request: Request,
    subfolder: Optional[str] = Query(None, description="Подпапка для выборки (files, rag, profile, temp)"),
    q: Optional[str] = Query(None, description="Поисковый запрос по имени файла"),
    extension: Optional[str] = Query(None, description="Фильтр по расширению файла"),
) -> Dict[str, Any]:
    """Получение дерева/списка файлов и папок внутри хранилища пользователя.

    Args:
        user_id (int): Идентификатор пользователя.
        request (Request): HTTP-запрос FastAPI.
        subfolder (Optional[str]): Ограничение по подпапке.
        q (Optional[str]): Строка поиска.
        extension (Optional[str]): Фильтр по расширению.

    Returns:
        Dict[str, Any]: Список файлов и директорий с метаданными.
    """
    _check_admin_or_local_auth(request)

    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    user_root = user_manager.get_user_directory(user_id, create=True)
    target_dir = user_root
    if subfolder:
        clean_sub = subfolder.replace("\\", "/").strip("/")
        target_dir = (user_root / clean_sub).resolve()
        try:
            target_dir.relative_to(user_root)
        except ValueError:
            raise HTTPException(status_code=400, detail="Недопустимая подпапка")

    if not target_dir.exists():
        return {
            "status": "ok",
            "user_id": user_id,
            "user_name": user.get("name"),
            "subfolder": subfolder or "root",
            "items": [],
            "total_items": 0,
            "total_size_bytes": 0,
            "total_size_formatted": "0 B",
        }

    items: List[Dict[str, Any]] = []
    total_size = 0

    search_query = q.lower().strip() if q else ""
    ext_filter = extension.lower().strip().lstrip(".") if extension else ""

    for path in sorted(target_dir.rglob("*")):
        try:
            rel_to_user = str(path.relative_to(user_root)).replace("\\", "/")
            stat = path.stat()
            is_file = path.is_file()
            f_size = stat.st_size if is_file else 0
            ext = path.suffix.lower().lstrip(".") if is_file else ""

            # Фильтрация по поисковому запросу
            if search_query and (search_query not in path.name.lower() and search_query not in rel_to_user.lower()):
                continue

            # Фильтрация по расширению
            if ext_filter and ext != ext_filter:
                continue

            if is_file:
                total_size += f_size

            mime, _ = mimetypes.guess_type(str(path))

            items.append({
                "name": path.name,
                "relative_path": rel_to_user,
                "subfolder": rel_to_user.split("/")[0] if "/" in rel_to_user else "root",
                "is_dir": path.is_dir(),
                "size_bytes": f_size,
                "size_formatted": _format_size(f_size) if is_file else "-",
                "extension": ext if is_file else "folder",
                "mime_type": mime or ("directory" if path.is_dir() else "application/octet-stream"),
                "modified_at": stat.st_mtime,
                "modified_formatted": _format_timestamp(stat.st_mtime),
            })
        except Exception as ex:
            logger.warning(f"Ошибка чтения метаданных файла {path}: {ex}")

    return {
        "status": "ok",
        "user_id": user_id,
        "user_name": user.get("name"),
        "subfolder": subfolder or "root",
        "items": items,
        "total_items": len(items),
        "total_size_bytes": total_size,
        "total_size_formatted": _format_size(total_size),
    }


@router.get("/users/{user_id}/file/preview")
async def preview_user_file(
    user_id: int,
    path: str = Query(..., description="Относительный путь к файлу внутри директории пользователя"),
    request: Request = None,
) -> Dict[str, Any]:
    """Безопасный предпросмотр содержимого текстового или графического файла пользователя.

    Args:
        user_id (int): Идентификатор пользователя.
        path (str): Относительный путь к файлу.
        request (Request): HTTP-запрос FastAPI.

    Returns:
        Dict[str, Any]: Содержимое и метаданные файла для предпросмотра.
    """
    _check_admin_or_local_auth(request)

    file_path = _get_safe_user_path(user_id, path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Файл не найден")

    stat = file_path.stat()
    mime, _ = mimetypes.guess_type(str(file_path))
    ext = file_path.suffix.lower().lstrip(".")

    text_extensions = {
        "txt", "md", "json", "csv", "tsv", "log", "py", "js", "html", "css",
        "xml", "yaml", "yml", "ini", "cfg", "env", "sql", "sh", "ps1", "bat"
    }
    image_extensions = {"png", "jpg", "jpeg", "webp", "gif", "svg", "bmp", "ico"}

    is_text = ext in text_extensions or (mime and mime.startswith("text/"))
    is_image = ext in image_extensions or (mime and mime.startswith("image/"))

    content: str = ""
    is_truncated: bool = False

    if is_text:
        # Чтение до 2 МБ текста
        max_bytes = 2 * 1024 * 1024
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(max_bytes)
                if file_path.stat().st_size > max_bytes:
                    is_truncated = True
        except Exception as ex:
            content = f"Ошибка чтения текстового файла: {ex}"
    elif is_image:
        try:
            # Картинки до 10 МБ кодируем в base64 data URI
            if stat.st_size <= 10 * 1024 * 1024:
                raw = file_path.read_bytes()
                b64 = base64.b64encode(raw).decode("utf-8")
                mime_str = mime or "image/png"
                content = f"data:{mime_str};base64,{b64}"
            else:
                content = "Изображение слишком большое для предварительного просмотра в браузере (> 10 MB)."
        except Exception as ex:
            content = f"Ошибка чтения изображения: {ex}"
    else:
        content = f"Бинарный файл ({mime or 'application/octet-stream'}). Предварительный просмотр недоступен. Воспользуйтесь скачиванием."

    return {
        "status": "ok",
        "filename": file_path.name,
        "relative_path": path.replace("\\", "/"),
        "size_bytes": stat.st_size,
        "size_formatted": _format_size(stat.st_size),
        "extension": ext,
        "mime_type": mime or "application/octet-stream",
        "modified_at": stat.st_mtime,
        "modified_formatted": _format_timestamp(stat.st_mtime),
        "is_text": is_text,
        "is_image": is_image,
        "is_truncated": is_truncated,
        "content": content,
    }


@router.get("/users/{user_id}/file/download")
async def download_user_file(
    user_id: int,
    path: str = Query(..., description="Относительный путь к файлу"),
    request: Request = None,
) -> FileResponse:
    """Скачивание файла из хранилища пользователя.

    Args:
        user_id (int): Идентификатор пользователя.
        path (str): Относительный путь к файлу.
        request (Request): HTTP-запрос FastAPI.

    Returns:
        FileResponse: Ответ с файлом для скачивания.
    """
    _check_admin_or_local_auth(request)

    file_path = _get_safe_user_path(user_id, path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Файл не найден")

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream",
    )


@router.delete("/users/{user_id}/file")
async def delete_user_file(
    user_id: int,
    path: str = Query(..., description="Относительный путь к файлу или папке"),
    request: Request = None,
) -> Dict[str, Any]:
    """Удаление файла или директории из хранилища пользователя.

    Args:
        user_id (int): Идентификатор пользователя.
        path (str): Относительный путь к файлу/папке.
        request (Request): HTTP-запрос FastAPI.

    Returns:
        Dict[str, Any]: Результат удаления.
    """
    _check_admin_or_local_auth(request)

    file_path = _get_safe_user_path(user_id, path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл или папка не найдена")

    # Защита от удаления корневой папки пользователя через этот метод
    user_root = user_manager.get_user_directory(user_id, create=False).resolve()
    if file_path == user_root:
        raise HTTPException(status_code=400, detail="Нельзя удалить корневую директорию пользователя")

    try:
        if file_path.is_dir():
            shutil.rmtree(file_path)
            action_type = "directory_deleted"
        else:
            file_path.unlink()
            action_type = "file_deleted"

        logger.info(f"Удален объект хранилища пользователя {user_id}: {path}")
        return {
            "status": "ok",
            "message": f"Успешно удалено: {file_path.name}",
            "action": action_type,
            "path": path,
        }
    except Exception as ex:
        logger.error(f"Ошибка удаления объекта {file_path}:", ex, False)
        raise HTTPException(status_code=500, detail=f"Ошибка удаления: {ex}")


@router.get("/orphaned")
async def get_orphaned_directories(request: Request) -> Dict[str, Any]:
    """Получение списка осиротевших каталогов пользователей.

    Args:
        request (Request): HTTP-запрос FastAPI.

    Returns:
        Dict[str, Any]: Список осиротевших директорий и их метаданные.
    """
    _check_admin_or_local_auth(request)

    orphaned = user_manager.get_orphaned_user_directories()
    total_size = sum(item["size_bytes"] for item in orphaned)
    total_files = sum(item["files_count"] for item in orphaned)

    return {
        "status": "ok",
        "total": len(orphaned),
        "total_size_bytes": total_size,
        "total_size_formatted": _format_size(total_size),
        "total_files": total_files,
        "orphaned_dirs": [
            {
                **d,
                "size_formatted": _format_size(d["size_bytes"]),
                "modified_formatted": _format_timestamp(d.get("modified_at", 0)),
            }
            for d in orphaned
        ],
    }


@router.post("/orphaned/clean")
async def clean_orphaned_directories(
    request: Request,
    payload: Optional[OrphanedCleanRequest] = None,
) -> Dict[str, Any]:
    """Очистка осиротевших каталогов пользователей.

    Args:
        request (Request): HTTP-запрос FastAPI.
        payload (Optional[OrphanedCleanRequest]): Список конкретных директорий или None для всех.

    Returns:
        Dict[str, Any]: Результат очистки каталогов.
    """
    _check_admin_or_local_auth(request)

    dirs_to_clean = payload.dirs if payload else None
    res = user_manager.cleanup_orphaned_user_directories(dir_names=dirs_to_clean)

    return {
        "status": "ok",
        "deleted_count": res.get("deleted_count", 0),
        "freed_bytes": res.get("freed_bytes", 0),
        "freed_formatted": _format_size(res.get("freed_bytes", 0)),
        "errors": res.get("errors", []),
    }


def init_router() -> APIRouter:
    """Инициализация и экспорт роутера пользовательских директорий."""
    return router


__all__ = ["router", "init_router"]
