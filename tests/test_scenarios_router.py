# -*- coding: utf-8 -*-
"""Unit-тесты для FastAPI роутера сценариев (router_scenarios.py)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from src.api.router_scenarios import init_router, ScenarioQuestionsConfig


@pytest.fixture
def client():
    """Фикстура для создания изолированного тестового клиента FastAPI с роутером сценариев."""
    app = FastAPI()
    app.include_router(init_router())
    return TestClient(app)


def test_init_router_success():
    """Проверка корректности создания роутера и наличия всех зарегистрированных маршрутов."""
    router = init_router()
    routes = [r.path for r in router.routes]
    assert "/api/v1/scenarios" in routes
    assert "/api/v1/scenarios/run" in routes
    assert "/api/v1/scenarios/chat" in routes
    assert "/api/v1/scenarios/questions" in routes


def test_get_scenarios_list(client):
    """Проверка получения списка доступных сценариев через GET /api/v1/scenarios."""
    response = client.get("/api/v1/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(s["id"] == "quick_check" for s in data)


def test_get_questions_endpoint(client):
    """Проверка получения пула вопросов и быстрых кнопок из external questions.json."""
    response = client.get("/api/v1/scenarios/questions")
    assert response.status_code == 200
    data = response.json()
    assert "prompts" in data
    assert isinstance(data["prompts"], list)
    assert len(data["prompts"]) > 0
    assert "quick_buttons" in data
    assert isinstance(data["quick_buttons"], list)


def test_scenario_chat_and_save_skill(client, monkeypatch):
    """Проверка работы чата без автосохранения и ручного сохранения через /save-skill."""
    from apps.windows.core.dynamic_tool_engine import DynamicWindowsToolEngine

    # Отключаем вызовы внешних LLM
    async def mock_get_model(self):
        return None
    monkeypatch.setattr(DynamicWindowsToolEngine, "_get_model", mock_get_model)

    # 1. Запрос в чат без автосохранения
    chat_resp = client.post(
        "/api/v1/scenarios/chat",
        json={"message": "покажи список принтеров", "auto_create_skill": False},
    )
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert chat_data["status"] == "ok"
    assert chat_data["created_skill"] is None  # Навык не должен создаваться автоматически
    assert chat_data["tool_plan"] is not None  # План доступен для ручного сохранения
    assert chat_data["tool_plan"]["tool_name"] == "printers-inspector"

    # 2. Ручное подтверждение сохранения навыка через кнопку
    save_resp = client.post(
        "/api/v1/scenarios/save-skill",
        json={
            "tool_name": chat_data["tool_plan"]["tool_name"],
            "tool_title": chat_data["tool_plan"]["tool_title"],
            "description_ru": chat_data["tool_plan"]["description_ru"],
            "probe_type": chat_data["tool_plan"]["probe_type"],
            "probe_script": chat_data["tool_plan"]["probe_script"],
            "instructions": chat_data["tool_plan"]["instructions"],
            "command_executed": chat_data.get("command_executed"),
        },
    )
    assert save_resp.status_code == 200
    save_data = save_resp.json()
    assert save_data["name"] == "printers-inspector"
    assert "printers-inspector" in save_data["path"]


def test_scenario_chat_stream(client, monkeypatch):
    """Проверка потокового SSE эндпоинта /api/v1/scenarios/chat/stream."""
    from apps.windows.core.dynamic_tool_engine import DynamicWindowsToolEngine

    # Отключаем вызовы внешних LLM
    async def mock_get_model(self):
        return None
    monkeypatch.setattr(DynamicWindowsToolEngine, "_get_model", mock_get_model)

    response = client.post(
        "/api/v1/scenarios/chat/stream",
        json={"message": "покажи список принтеров", "auto_create_skill": False},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    # Проверяем наличие событий stage и done в потоке
    text = response.text
    assert "data:" in text
    assert '"type": "stage"' in text
    assert '"type": "done"' in text
    assert "printers-inspector" in text


def test_scenario_execute_fix_endpoint(client, monkeypatch):
    """Проверка работы эндпоинта /api/v1/scenarios/execute-fix."""
    from apps.windows.core.safe_executor import SafeExecutor
    from apps.windows.core.models import RemediationAction

    def mock_execute(self, action: RemediationAction, confirmed_by_user: bool = False):
        action.executed = True
        action.success = True
        return action

    monkeypatch.setattr(SafeExecutor, "execute", mock_execute)

    response = client.post(
        "/api/v1/scenarios/execute-fix",
        json={
            "action_id": "disable_orphaned_svc_test_service",
            "action_type": "disable_service",
            "title": "Отключить тестовую службу",
            "description": "Тестовое отключение",
            "target": "test_service",
            "risk": "caution",
            "execution_command": "Set-Service -Name 'test_service' -StartupType Disabled",
            "confirmed_by_user": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["action_id"] == "disable_orphaned_svc_test_service"
    assert data["success"] is True


def test_services_collector_resolve_binary_and_protection():
    """Проверка корректного разрешения путей и защиты системных служб."""
    from apps.windows.core.modules.services_collector import _resolve_service_binary, PROTECTED_SYSTEM_SERVICES

    # Проверка защиты системных служб
    assert "appxsvc" in PROTECTED_SYSTEM_SERVICES
    assert "bfe" in PROTECTED_SYSTEM_SERVICES
    assert "rpcss" in PROTECTED_SYSTEM_SERVICES

    # Проверка разрешения путей с параметрами
    resolved_svchost = _resolve_service_binary(r"%SystemRoot%\System32\svchost.exe -k wsappx")
    assert resolved_svchost.lower().endswith("svchost.exe")

    resolved_bare = _resolve_service_binary("svchost.exe -k LocalServiceNoNetworkFirewall")
    assert resolved_bare.lower().endswith("svchost.exe")


def test_dormant_software_audit_chat_and_metadata(client, monkeypatch):
    """Проверка правильного планирования и двухэтапного аудита давно не запускавшегося ПО с метаданными знаний и агентов."""
    from apps.windows.core.dynamic_tool_engine import DynamicWindowsToolEngine

    # Отключаем вызовы внешних LLM
    async def mock_get_model(self):
        return None
    monkeypatch.setattr(DynamicWindowsToolEngine, "_get_model", mock_get_model)

    response = client.post(
        "/api/v1/scenarios/chat",
        json={"message": "Найди давно не запускавшиеся программы", "auto_create_skill": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["tool_plan"] is not None
    assert data["tool_plan"]["tool_name"] == "dormant-software-auditor"

    # Проверяем наличие информации о задействованных агентах и знаниях
    assert "agents_used" in data
    assert isinstance(data["agents_used"], list)
    assert len(data["agents_used"]) >= 2
    assert any("DynamicWindowsToolEngine" in a["name"] for a in data["agents_used"])
    assert any("SoftwareAuditEngine" in a["name"] for a in data["agents_used"])

    assert "knowledge_used" in data
    assert isinstance(data["knowledge_used"], list)
    assert len(data["knowledge_used"]) >= 2
    assert any("UserAssist" in k["title"] for k in data["knowledge_used"])
    assert any("Prefetch" in k["title"] for k in data["knowledge_used"])

    # Проверяем, что в ответе отражена двухэтапная логика
    reply = data["reply"]
    assert "Этап 1: Инвентаризация установленного ПО" in reply
    assert "Этап 2: Аудит истории запусков" in reply


def test_extract_remediation_actions_structured_and_audit():
    """Тестирование извлечения структурированных действий SafeOps, auditpol и предложений аудита."""
    from apps.windows.core.dynamic_tool_engine import DynamicWindowsToolEngine

    engine = DynamicWindowsToolEngine()

    # 1. Структурированный блок ```action ... ```
    reply_with_block = r"""
Все проверено. Для включения аудита используйте кнопку ниже.
```action
{
  "action_id": "custom_audit_fix",
  "action_type": "custom_command",
  "title": "Включить аудит процессов",
  "description": "Включает аудит создания процессов",
  "target": "Audit",
  "risk": "caution",
  "execution_command": "auditpol /set /subcategory:\"Process Creation\" /success:enable /failure:enable"
}
```
"""
    actions = engine.extract_remediation_actions({}, reply_with_block)
    assert len(actions) == 1
    assert actions[0]["action_id"] == "custom_audit_fix"
    assert actions[0]["title"] == "Включить аудит процессов"
    assert "Process Creation" in actions[0]["execution_command"]

    # 2. Разговорное предложение включить аудит процессов
    conv_reply = """
Состояние стабильное. Если вам требуется принудительное включение расширенного аудита процессов, подтвердите необходимость в чате.
"""
    actions2 = engine.extract_remediation_actions({}, conv_reply)
    assert len(actions2) == 1
    assert actions2[0]["action_id"] == "enable_process_creation_audit"
    assert actions2[0]["title"] == "Включить расширенный аудит создания процессов"
    assert "auditpol" in actions2[0]["execution_command"]

    # 3. Извлечение Set-Service команды
    svc_reply = "Рекомендуется отключить проблемную службу: `Set-Service -Name 'DiagTrack' -StartupType Disabled`"
    actions3 = engine.extract_remediation_actions({}, svc_reply)
    assert len(actions3) == 1
    assert actions3[0]["action_id"] == "disable_service_diagtrack"
    assert actions3[0]["action_type"] == "disable_service"


def test_scenario_chat_with_use_rag(client, monkeypatch):
    """Проверка передачи флага use_rag в эндпоинты чата."""
    from apps.windows.core.dynamic_tool_engine import DynamicWindowsToolEngine

    async def mock_get_model(self):
        return None
    monkeypatch.setattr(DynamicWindowsToolEngine, "_get_model", mock_get_model)

    # 1. Запрос со включенным RAG
    resp_rag = client.post(
        "/api/v1/scenarios/chat",
        json={"message": "покажи список принтеров", "use_rag": True},
    )
    assert resp_rag.status_code == 200
    data_rag = resp_rag.json()
    knowledge_types = [k.get("type") for k in data_rag.get("knowledge_used", [])]
    assert "rag" in knowledge_types

    # 2. Потоковый запрос со включенным RAG
    resp_stream = client.post(
        "/api/v1/scenarios/chat/stream",
        json={"message": "покажи список принтеров", "use_rag": True},
    )
    assert resp_stream.status_code == 200
    assert '"stage": "rag"' in resp_stream.text






