from fastapi import APIRouter, Body
from typing import TYPE_CHECKING
from src.logger import logger

if TYPE_CHECKING:
    from src.app.state import AppState

def init_router(state: "AppState") -> APIRouter:
    """Инициализация роутера для приложения исследований и статистики."""
    router = APIRouter(prefix="/apps/research-statistic", tags=["research-statistic"])

    @router.post("/run-research")
    async def run_research(file_path: str = Body(..., embed=True)):
        """Запуск полного исследования данных по указанному пути."""
        try:
            from apps.research_and_statistic.engine import DataResearchEngine
            # Передаем state.chat_model и user_id=0 (системный пользователь)
            engine = DataResearchEngine(user_id=0, chat_model=state.chat_model)
            return await engine.run_full_research(file_path)

        except ImportError as e:
            logger.warning(f"Dependencies missing: {e}")
            return {"error": "Dependencies not installed"}

    @router.get("/health")
    async def health():
        return {"status": "ok"}

    logger.debug("Research and Statistic app router initialized.")
    return router
