# -*- coding: utf-8 -*-
import pytest
import json
from src.ai.agents.system_logs_agent import SystemLogsAgent
from src.ai.agents.tools import system_logs_analyzer

class MockLLM:
    def __init__(self):
        self.last_prompt = ""

    async def ask(self, prompt: str) -> str:
        self.last_prompt = prompt
        return "Отчет SRE: Анализ критических ошибок завершен успешно."

def test_system_logs_agent_parse_days():
    agent = SystemLogsAgent()
    assert agent.parse_time_window_days("Покажи все критические ошибки в операционной системе за последние двадцать дней") == 20
    assert agent.parse_time_window_days("Ошибки в ОС за 5 дней") == 5
    assert agent.parse_time_window_days("Покажи сбои за 2 недели") == 14
    assert agent.parse_time_window_days("Покажи критические ошибки в системе") == 20

@pytest.mark.asyncio
async def test_system_logs_analyzer_tool_execution():
    result_str = await system_logs_analyzer.func(days=1, level="Critical,Error", limit=10)
    data = json.loads(result_str)
    assert "period_days" in data
    assert "channels" in data
    assert "top_incident_clusters" in data

@pytest.mark.asyncio
async def test_system_logs_agent_execution():
    mock_llm = MockLLM()
    agent = SystemLogsAgent(ai_model=mock_llm)
    query = "Покажи все критические ошибки в операционной системе за последние двадцать дней"
    report = await agent.run(query, active_llm=mock_llm)
    assert "Отчет SRE" in report
    assert "двадцать дней" in mock_llm.last_prompt or "20" in mock_llm.last_prompt
