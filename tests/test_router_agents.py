# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тестирование роутера управления и создания агентов ИИ
# =============================================================================

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from core.fastapi.router_agents import _get_agents_list, _save_agents_list

client = TestClient(app)


class TestAgentsRouter:
    """Тестирование CRUD и вспомогательных эндпоинтов /api/agents."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Сохранение и восстановление состояния списка агентов."""
        self.original_agents = _get_agents_list()
        yield
        _save_agents_list(self.original_agents)

    def test_list_agents(self):
        """Проверка получения списка всех агентов."""
        response = client.get("/api/agents")
        assert response.status_code == 200
        agents = response.json()
        assert isinstance(agents, list)
        assert len(agents) > 0
        # Проверяем наличие ключевых системных агентов
        ids = [a.get("id") for a in agents]
        assert "web_search_gemini" in ids
        assert "web_search_gemini_cli" in ids

    def test_list_tools(self):
        """Проверка получения каталога инструментов."""
        response = client.get("/api/agents/tools")
        assert response.status_code == 200
        tools = response.json()
        assert isinstance(tools, list)
        tool_ids = [t.get("id") for t in tools]
        assert "web_search" in tool_ids
        assert "rag_search" in tool_ids
        assert "python_eval" in tool_ids

    def test_list_providers(self):
        """Проверка получения списка провайдеров и моделей из пула."""
        response = client.get("/api/agents/providers")
        assert response.status_code == 200
        providers = response.json()
        assert "gemini" in providers
        assert "agy" in providers
        assert "foundry" in providers
        assert "ollama" in providers
        assert len(providers["gemini"]["models"]) > 0

    def test_create_and_delete_custom_agent(self):
        """Тест создания и последующего удаления кастомного агента."""
        new_agent = {
            "id": "test_research_agent",
            "name": "Research Assistant",
            "description": "Тестовый агент для поиска информации",
            "is_system": False,
            "enabled": True,
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "temperature": 0.2,
            "max_steps": 10,
            "timeout_seconds": 45,
            "tools": ["web_search", "rag_search"],
            "system_prompt": "Ты тестовый агент-исследователь."
        }

        # 1. Создание
        create_res = client.post("/api/agents", json=new_agent)
        assert create_res.status_code == 200
        data = create_res.json()
        assert data.get("status") == "ok"
        assert data.get("agent", {}).get("id") == "test_research_agent"
        assert data.get("agent", {}).get("is_system") is False

        # 2. Проверка в списке
        list_res = client.get("/api/agents")
        agent_ids = [a.get("id") for a in list_res.json()]
        assert "test_research_agent" in agent_ids

        # 3. Обновление
        updated_agent = dict(new_agent)
        updated_agent["name"] = "Updated Research Assistant"
        updated_agent["enabled"] = False
        update_res = client.put("/api/agents/test_research_agent", json=updated_agent)
        assert update_res.status_code == 200
        assert update_res.json().get("agent", {}).get("name") == "Updated Research Assistant"
        assert update_res.json().get("agent", {}).get("enabled") is False

        # 4. Удаление
        del_res = client.delete("/api/agents/test_research_agent")
        assert del_res.status_code == 200
        assert del_res.json().get("deleted_id") == "test_research_agent"

        # 5. Проверка отсутствия
        list_after = client.get("/api/agents")
        agent_ids_after = [a.get("id") for a in list_after.json()]
        assert "test_research_agent" not in agent_ids_after

    def test_prevent_delete_system_agent(self):
        """Проверка запрета удаления системных агентов."""
        del_res = client.delete("/api/agents/web_search_gemini")
        assert del_res.status_code == 403
        assert "Системных агентов нельзя удалять" in del_res.json().get("detail", "")

    def test_prevent_duplicate_agent_id(self):
        """Проверка ошибки при создании дублирующегося ID."""
        dup_agent = {
            "id": "web_search_gemini",  # Уже существует
            "name": "Duplicate Agent",
            "description": "...",
            "enabled": True,
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "temperature": 0.2,
            "max_steps": 10,
            "timeout_seconds": 30,
            "tools": [],
            "system_prompt": ""
        }
        res = client.post("/api/agents", json=dup_agent)
        assert res.status_code == 400
        assert "уже существует" in res.json().get("detail", "")

    @patch("core.fastapi.router_chat.get_chat_model")
    def test_generate_prompt_ai(self, mock_get_chat_model):
        """Тест генерации системного промпта через AI-модель."""
        mock_llm = MagicMock()
        mock_llm.ask = AsyncMock(return_value=json.dumps({
            "name": "Аналитик данных",
            "description": "Анализирует данные и выполняет расчеты",
            "system_prompt": "Ты аналитик данных.",
            "recommended_tools": ["python_eval", "web_search"],
            "temperature": 0.4,
            "max_steps": 12
        }))
        mock_get_chat_model.return_value = mock_llm

        req_payload = {
            "task_description": "Создай агента-аналитика для расчетов",
            "provider": "gemini",
            "model": "gemini-2.5-flash"
        }
        response = client.post("/api/agents/generate-prompt", json=req_payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        spec = data.get("data", {})
        assert spec.get("name") == "Аналитик данных"
        assert "python_eval" in spec.get("recommended_tools", [])

    @patch("core.fastapi.router_chat.get_chat_model")
    def test_sandbox_execution(self, mock_get_chat_model):
        """Тест выполнения тестового запроса в песочнице."""
        mock_llm = MagicMock()
        mock_llm.ask = AsyncMock(return_value="Тестовый ответ агента в песочнице.")
        mock_get_chat_model.return_value = mock_llm

        test_payload = {
            "agent_id": "web_search_gemini",
            "test_message": "Какая сегодня погода?"
        }
        response = client.post("/api/agents/test", json=test_payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert "Тестовый ответ" in data.get("response", "")
        assert len(data.get("steps", [])) > 0
        assert data.get("duration_ms") >= 0
