"""
Роутер восстановления файлов (R‑Studio) для FastAPI.
Требования:
- Константа RSTUDIO_EXE указывает путь к исполняемому файлу R‑Studio.
- Функция _check_rstudio_exists() проверяет наличие файла.
- GET /api/recovery/status возвращает информацию о наличии утилиты.
- POST /api/recovery/launch запускает R‑Studio через subprocess.Popen.
- Экспортируются init_router и RSTUDIO_EXE.
"""

import subprocess
from pathlib import Path
from fastapi import APIRouter, HTTPException

# Путь к R‑Studio (можно переопределить через переменную окружения, но для тестов фиксируем)
RSTUDIO_EXE = Path(r"C:\\Program Files\\RStudio\\bin\\RStudio.exe")

router = APIRouter(prefix="/api/recovery", tags=["recovery"])


def _check_rstudio_exists() -> bool:
    """Проверить, существует ли исполняемый файл R‑Studio.

    Возвращает True, если файл существует, иначе False.
    """
    return RSTUDIO_EXE.exists()


@router.get("/status")
async def get_status() -> dict:
    """Возврат информации о доступности утилиты восстановления.

    Returns
    -------
    dict
        {"success": True, "tool": {"name": "R‑Studio", "path": str(RSTUDIO_EXE), "exists": bool}}
    """
    return {
        "success": True,
        "tool": {
            "name": "R‑Studio",
            "path": str(RSTUDIO_EXE),
            "exists": _check_rstudio_exists(),
        },
    }


@router.post("/launch")
async def launch_recovery() -> dict:
    """Запустить R‑Studio.

    Returns
    -------
    dict
        При успехе: {"success": True, "pid": <pid>, "message": "Успешно запущена"}
        При отсутствии файла: HTTPException 404.
        При ошибке Popen: HTTPException 500.
    """
    if not _check_rstudio_exists():
        raise HTTPException(status_code=404, detail="R‑Studio executable not found")
    try:
        proc = subprocess.Popen([str(RSTUDIO_EXE)])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Не удалось запустить R‑Studio: {exc}")
    return {"success": True, "pid": proc.pid, "message": "Успешно запущена"}


def init_router() -> APIRouter:
    """Инициализация и возврат роутера восстановления файлов."""
    return router

__all__ = ["init_router", "RSTUDIO_EXE"]