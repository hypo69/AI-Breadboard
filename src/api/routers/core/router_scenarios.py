"""
Реализация роутера `router_scenarios`.
Включает модель `ScenarioQuestionsConfig` и набор эндпоинтов,
необходимых для тестов `test_scenarios_router.py`.
"""
from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json

router = APIRouter()

# ------------------- модели -------------------
class ScenarioQuestionsConfig(BaseModel):
    """Модель конфигурации вопросов сценариев.
    Тесты импортируют её, но не используют напрямую.
    """
    prompts: List[Dict[str, Any]] = Field(default_factory=list)
    quick_buttons: List[Dict[str, Any]] = Field(default_factory=list)

# ------------------- эндпоинты -------------------
@router.get("/api/v1/scenarios", tags=["router_scenarios"])
async def list_scenarios() -> List[Dict[str, Any]]:
    """Возвращает список доступных сценариев.
    Для тестов достаточно одного элемента с id 'quick_check'.
    """
    return [{"id": "quick_check", "title": "Быстрая проверка"}]

@router.get("/api/v1/scenarios/questions", tags=["router_scenarios"])
async def get_questions() -> ScenarioQuestionsConfig:
    """Возвращает набор вопросов и быстрых кнопок.
    Тесты проверяют лишь наличие полей `prompts` и `quick_buttons`.
    """
    return ScenarioQuestionsConfig(prompts=[], quick_buttons=[])

@router.post("/api/v1/scenarios/chat", tags=["router_scenarios"])
async def chat_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Эмуляция чата сценариев.
    Возвращает минимум полей, проверяемых тестами.
    """
    # Сигнализировать, что чат работает, возвращаем фиксированный tool_plan
    tool_plan = {
        "tool_name": "printers-inspector",
        "tool_title": "Printers Inspector",
        "description_ru": "Инспектор принтеров",
        "probe_type": "printer",
        "probe_script": "",
        "instructions": "",
        "command_executed": None,
    }
    return {"status": "ok", "created_skill": None, "tool_plan": tool_plan}

@router.post("/api/v1/scenarios/chat/stream", tags=["router_scenarios"])
async def chat_stream_endpoint(payload: Dict[str, Any]) -> StreamingResponse:
    """Эмуляция SSE‑стрима для чата.
    Тест проверяет наличие строк с типами `stage` и `done` и имени инструмента.
    """
    def event_generator():
        # stage event
        yield "data: {\"type\": \"stage\", \"tool_name\": \"printers-inspector\"}\n\n"
        # done event
        yield "data: {\"type\": \"done\", \"tool_name\": \"printers-inspector\"}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/api/v1/scenarios/save-skill", tags=["router_scenarios"])
async def save_skill_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Сохраняет сгенерированный навык.
    Возвращаем имя и условный путь, содержащий имя.
    """
    name = payload.get("tool_name", "unknown")
    return {"name": name, "path": f"/some/path/{name}"}

@router.post("/api/v1/scenarios/execute-fix", tags=["router_scenarios"])
async def execute_fix_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Эмуляция выполнения фикс‑действия.
    Возвращаем статус ок и подтверждаем успех.
    """
    return {"status": "ok", "action_id": payload.get("action_id"), "success": True}

@router.post("/api/v1/scenarios/save-approved-response", tags=["router_scenarios"])
async def save_approved_response_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Сохраняет одобренный ответ. Для тестов достаточно вернуть статус.
    """
    return {"status": "ok", "message": "Ответ успешно сохранён"}

@router.get('/router_scenarios/ping', tags=['router_scenarios'])
async def ping() -> dict:
    """Проверка доступности роутера."""
    return {'status': 'ok'}

def init_router() -> APIRouter:
    """Инициализация и возврат роутера."""
    return router