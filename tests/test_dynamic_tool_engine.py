# -*- coding: utf-8 -*-
import pytest
from apps.windows.core.dynamic_tool_engine import DynamicWindowsToolEngine

@pytest.fixture(autouse=True)
def disable_external_llm(monkeypatch):
    """Отключение внешних сетевых/CLI вызовов LLM для детерминированных быстрых тестов."""
    async def mock_get_model(self):
        return None
    monkeypatch.setattr(DynamicWindowsToolEngine, "_get_model", mock_get_model)


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

