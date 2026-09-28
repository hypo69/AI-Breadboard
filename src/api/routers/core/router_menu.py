"""
Минимальная реализация роутера router_menu.
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from typing import Any, Dict

# Путь к конфигурационному JSON файлу меню
TC_MENU_CONFIG_PATH = Path(__file__).resolve().parents[2] / "tc_menu_config.json"

router = APIRouter(prefix="/api/menu", tags=["router_menu"])

@router.get("/config", tags=["router_menu"])
async def get_menu_config(target: str | None = None) -> Dict[str, Any]:
    """Возвращает содержимое конфигурации меню.
    Если указан параметр `target=su`, из меню удаляются элементы, не нужны для сценария superuser.
    """
    if not TC_MENU_CONFIG_PATH.exists():
        raise HTTPException(status_code=404, detail="Файл конфигурации не найден")
    with open(TC_MENU_CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    # Фильтрация для суперпользователя (SU)
    if target == "su":
        # Удаляем элементы с id 'about_system'
        config = {
            "menu": {
                "topButtons": [item for item in config.get("menu", {}).get("topButtons", []) if item.get("id") != "about_system"],
                "sidebarItems": [item for item in config.get("menu", {}).get("sidebarItems", []) if item.get("id") != "about_system"],
            },
            **{k: v for k, v in config.items() if k != "menu"},
        }
    return config

@router.post("/config", tags=["router_menu"])
async def post_menu_config(payload: Dict[str, Any]) -> Dict[str, str]:
    """Сохраняет новую конфигурацию меню в файл.
    Возвращает статус.
    """
    if "menu" not in payload:
        raise HTTPException(status_code=400, detail="Отсутствует обязательный раздел 'menu'")
    with open(TC_MENU_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return {"status": "ok"}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера для FastAPI приложения."""
    return router

__all__ = ["init_router", "router", "TC_MENU_CONFIG_PATH"]