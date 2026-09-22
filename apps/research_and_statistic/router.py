from fastapi import APIRouter, Body
from typing import TYPE_CHECKING
from logger import logger
from apps.common.csv_logger import AppCsvLogger

if TYPE_CHECKING:
    from src.app.state import AppState

def init_router(state: "AppState") -> APIRouter:
    """Инициализация роутера для приложения исследований и статистики."""
    router = APIRouter(prefix="/apps/research-statistic", tags=["research-statistic"])
    csv_logger = AppCsvLogger("research_and_statistic")

    @router.post("/run-research")
    async def run_research(file_path: str = Body(..., embed=True)):
        """Запуск полного исследования данных по указанному пути."""
        try:
            from apps.research_and_statistic.engine import DataResearchEngine
            # Передаем state.chat_model и user_id=0 (системный пользователь)
            engine = DataResearchEngine(user_id=0, chat_model=state.chat_model)
            res = await engine.run_full_research(file_path)
            csv_logger.log_event(
                event_type="research_run_completed",
                status="success",
                details=f"file_path={file_path}",
                filename="research_statistic_events.csv",
            )
            return res

        except ImportError as e:
            logger.warning(f"Dependencies missing: {e}")
            csv_logger.log_event(
                event_type="research_run_failed",
                status="missing_dependencies",
                details=f"file_path={file_path},error={e}",
                filename="research_statistic_events.csv",
            )
            return {"error": "Dependencies not installed"}
        except Exception as e:
            logger.error(f"Research run failed: {e}", exc_info=True)
            csv_logger.log_event(
                event_type="research_run_failed",
                status="error",
                details=f"file_path={file_path},error={e}",
                filename="research_statistic_events.csv",
            )
            return {"error": str(e)}

    @router.get("/health")
    async def health():
        csv_logger.log_poll(
            poll_type="health",
            metric_name="service_health",
            value="ok",
            unit="status",
            status="ok",
            filename="research_statistic_polls.csv",
        )
        return {"status": "ok"}

    logger.debug("Research and Statistic app router initialized.")
    return router
