# -*- coding: utf-8 -*-
import pytest
from apps.windows.core.dynamic_tool_engine import DynamicWindowsToolEngine

from apps.windows.core.tools.registry import ToolRegistry
from apps.windows.core.tools.dynamic_factory import DynamicToolFactory, CreateCustomToolMetaTool
from apps.windows.core.tools.system_tools import WindowsCollectorTool, SafePowerShellProbeTool
from apps.windows.core.agent_loop import WindowsAgentLoop

@pytest.fixture(autouse=True)
def disable_external_llm(monkeypatch):
    """Отключение внешних сетевых/CLI вызовов LLM для детерминированных быстрых тестов."""
    async def mock_get_model(self):
        return None
    monkeypatch.setattr(DynamicWindowsToolEngine, "_get_model", mock_get_model)


@pytest.mark.asyncio
async def test_tool_registry_and_meta_tool():
    """Тест регистрации инструментов и динамического создания инструмента через мета-инструмент."""
    registry = ToolRegistry()
    factory = DynamicToolFactory(registry)
    meta_tool = CreateCustomToolMetaTool(factory)
    registry.register(meta_tool)

    # Проверка схемы Function Calling
    defs = registry.get_definitions()
    assert len(defs) == 1
    assert defs[0]["name"] == "create_custom_tool"

    # Вызов мета-инструмента
    result = await registry.execute(
        "create_custom_tool",
        tool_name="wifi-adapter-probe",
        tool_title="Зонд Wi-Fi адаптеров",
        description_ru="Сбор данных о беспроводных интерфейсах",
        probe_script="Get-NetAdapter | ConvertTo-Json",
        instructions="Опрос сетевых беспроводных адаптеров",
    )
    assert result.status == "ok"
    assert registry.has("wifi-adapter-probe")

    created_tool = registry.get("wifi-adapter-probe")
    assert created_tool.title == "Зонд Wi-Fi адаптеров"
    assert "Get-NetAdapter" in created_tool.probe_script


@pytest.mark.asyncio
async def test_safe_powershell_probe_security():
    """Тест блокировки деструктивных команд в SafePowerShellProbeTool."""
    probe_tool = SafePowerShellProbeTool()
    
    # Попытка вызвать опасную команду
    res = await probe_tool.execute("Remove-Item -Recurse -Force C:\\Windows")
    assert res.status == "error"
    assert "отклонена политикой безопасности SafeOps" in res.message


@pytest.mark.asyncio
async def test_dynamic_tool_engine_mouse_query():
    engine = DynamicWindowsToolEngine()
    plan = await engine.plan_tool("Какие мыши были подключены к этому компьютеру?")
    assert plan.tool_name == "mouse-history-inspector"
    assert plan.probe_type == "powershell"

    res = await engine.process_query("Какие мыши были подключены к этому компьютеру?", auto_create_skill=True)
    assert res["status"] == "ok"
    assert "мышей" in res["reply"] or "манипуляторов" in res["reply"] or "мышь" in res["reply"].lower()
    assert res["created_skill"] is not None
    assert res["created_skill"]["name"] == "mouse-history-inspector"


@pytest.mark.asyncio
async def test_dynamic_tool_engine_usb_query():
    engine = DynamicWindowsToolEngine()
    plan = await engine.plan_tool("А все устройства, которые использовали usb?")
    assert plan.tool_name == "usb-device-auditor"
    assert plan.probe_type == "powershell"

    res = await engine.process_query("А все устройства, которые использовали usb?", auto_create_skill=True)
    assert res["status"] == "ok"
    assert "USB" in res["reply"]
    assert res["created_skill"] is not None
    assert res["created_skill"]["name"] == "usb-device-auditor"


@pytest.mark.asyncio
async def test_dynamic_tool_engine_network_collector():
    engine = DynamicWindowsToolEngine()
    plan = await engine.plan_tool("Покажи список открытых сетевых портов и соединений")
    assert plan.collector_name == "network" or "port" in plan.tool_name


@pytest.mark.asyncio
async def test_dynamic_tool_engine_printer_query():
    """Тест распознавания запроса о принтерах и генерации инструмента printers-inspector."""
    engine = DynamicWindowsToolEngine()
    plan = await engine.plan_tool("покажи список принтеров")
    assert plan.tool_name == "printers-inspector"
    assert plan.probe_type == "powershell"

    res = await engine.process_query("покажи список принтеров", auto_create_skill=True)
    assert res["status"] == "ok"
    assert "принтер" in res["reply"].lower() or "print" in res["reply"].lower()
    assert res["created_skill"] is not None
    assert res["created_skill"]["name"] == "printers-inspector"


@pytest.mark.asyncio
async def test_dynamic_tool_engine_audio_and_display():
    """Тест распознавания аудиоустройств и мониторов."""
    engine = DynamicWindowsToolEngine()
    plan_display = await engine.plan_tool("какие мониторы и видеокарты подключены?")
    assert plan_display.tool_name == "display-monitor-inspector"

    plan_audio = await engine.plan_tool("проверь звуковые устройства и микрофоны")
    assert plan_audio.tool_name == "audio-devices-inspector"


def test_slug_and_json_extraction():
    """Тест транслитерации слагов и парсинга JSON блоков."""
    from apps.windows.core.dynamic_tool_engine import to_ascii_slug, extract_json_block

    assert to_ascii_slug("Покажи список принтеров") == "pokazhi-spisok-printerov"
    assert to_ascii_slug("Mouse History Inspector") == "mouse-history-inspector"

    # Парсинг блока Markdown
    raw_md = "Вот план:\n```json\n{\"tool_name\": \"test-tool\", \"intent\": \"test\"}\n```\n"
    parsed = extract_json_block(raw_md)
    assert parsed is not None
    assert parsed["tool_name"] == "test-tool"


def test_resolve_model_info_dynamic(monkeypatch):
    """Проверка динамического извлечения модели и провайдера из конфигурации без хардкода."""
    from types import SimpleNamespace
    import src.config as config_module
    from apps.windows.core.dynamic_tool_engine import DynamicWindowsToolEngine

    engine = DynamicWindowsToolEngine()

    # Сценарий 1: Профиль с явным provider/model (например, config_tc.json)
    monkeypatch.setattr(config_module, "ai_cfg", SimpleNamespace(
        provider="gemini",
        model="gemini-2.5-flash",
    ))
    provider, model_id, display = engine._resolve_model_info()
    assert provider == "GEMINI"
    assert model_id == "gemini-2.5-flash"
    assert display == "GEMINI: gemini-2.5-flash"

    # Сценарий 2: Провайдер Ollama
    monkeypatch.setattr(config_module, "ai_cfg", SimpleNamespace(
        provider="",
        model="",
        use_ollama=True,
        ollama_model_id="llama3.2:latest",
    ))
    provider, model_id, display = engine._resolve_model_info()
    assert provider == "OLLAMA"
    assert model_id == "llama3.2:latest"
    assert display == "Ollama: llama3.2:latest"

    # Сценарий 3: Проверка формирования агентов в get_execution_metadata
    from apps.windows.core.dynamic_tool_engine import DynamicToolPlan
    plan = DynamicToolPlan(
        intent="test",
        tool_name="test_tool",
        tool_title="Test Tool",
        description_ru="Описание",
        probe_type="powershell",
    )
    agents, _ = engine.get_execution_metadata(plan, {})
    llm_agent = next(a for a in agents if a.get("type") == "llm")
    assert llm_agent["name"] == "Ollama: llama3.2:latest"


@pytest.mark.asyncio
async def test_dynamic_tool_engine_prompt_generation():
    """Тест формирования и возврата точного промпта, отправляемого языковой модели."""
    from apps.windows.core.dynamic_tool_engine import DynamicToolPlan

    engine = DynamicWindowsToolEngine()
    plan = DynamicToolPlan(
        intent="Инспекция сетевых соединений",
        tool_name="network-inspector",
        tool_title="Инспектор сети",
        description_ru="Анализ соединений",
        probe_type="collector",
        collector_name="network",
    )

    probe_data = [{"LocalAddress": "127.0.0.1", "Port": 8000, "State": "Listen"}]
    prompt = engine.build_synthesis_prompt(
        query="Какие порты открыты?",
        plan=plan,
        probe_data=probe_data,
        conversation_id="test-session-123",
    )

    assert "Пользователь задал вопрос о системе Windows: «Какие порты открыты?»" in prompt
    assert "Инструмент: Инспектор сети" in prompt
    assert "127.0.0.1" in prompt
    assert "```action" in prompt

    # Проверка вызова через process_query
    res = await engine.process_query("Какие порты открыты?")
    assert "generated_prompt" in res
    assert isinstance(res["generated_prompt"], str)
    assert len(res["generated_prompt"]) > 0
    assert "Какие порты открыты?" in res["generated_prompt"]


