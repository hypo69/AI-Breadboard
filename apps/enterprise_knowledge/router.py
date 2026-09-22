"""FastAPI API платформы корпоративных знаний."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from apps.enterprise_knowledge.engine import EnterpriseKnowledgeEngine


router = APIRouter(prefix="/api/v1/enterprise-knowledge", tags=["Enterprise Knowledge"])
engine = EnterpriseKnowledgeEngine()
templates = Jinja2Templates(directory="apps/enterprise_knowledge/templates")


class EmployeeRequest(BaseModel):
    employee_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    department: str | None = None
    email: str | None = None
    aliases: list[str] = Field(default_factory=list)
    verified: bool = False
    confidence: float = Field(1.0, ge=0, le=1)


class IngestRequest(BaseModel):
    event_id: str = Field(..., min_length=1)
    source: dict[str, Any] = Field(default_factory=dict)
    event_type: str = "knowledge_received"
    occurred_at: str | None = None
    participants: list[dict[str, Any]] = Field(default_factory=list)
    content: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    facts: list[dict[str, Any]] = Field(default_factory=list)


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    employee_id: str | None = None
    status: str | None = None
    limit: int = Field(20, ge=1, le=100)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/employees")
async def register_employee(body: EmployeeRequest) -> dict[str, Any]:
    return engine.register_employee(body.model_dump())


@router.get("/employees/{employee_id}")
async def get_employee(employee_id: str) -> dict[str, Any]:
    result = engine.employee(employee_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return result


@router.post("/ingest")
async def ingest(body: IngestRequest) -> dict[str, Any]:
    return engine.ingest(body.model_dump(exclude_none=True))


@router.post("/query")
async def query(body: QueryRequest) -> dict[str, Any]:
    return engine.query(**body.model_dump())


@router.get("/helpdesk", response_class=HTMLResponse)
async def helpdesk_page(request: Request) -> HTMLResponse:
    """Main helpdesk page for Enterprise Knowledge Platform."""
    return templates.TemplateResponse("helpdesk.html", {"request": request})


def init_router() -> APIRouter:
    """Инициализация и экспорт FastAPI роутера Enterprise Knowledge Platform.

    Returns:
        APIRouter: Сконфигурированный экземпляр роутера.
    """
    return router


__all__ = [
    "init_router",
    "router",
    "engine",
]
