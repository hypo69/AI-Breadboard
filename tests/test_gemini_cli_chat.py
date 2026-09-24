# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Tests for Gemini CLI Provider and Chat Adapter
# =============================================================================
# Description:
#   Модульные тесты для GeminiCliProvider (4 режима, обнаружение, JSON, stream),
#   GeminiCliChatBase и интеграции с UnifiedChatModel и router_chat.
#
# File: test_gemini_cli_chat.py
# Project: ai-breadboard
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import json
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ai.gemini_cli_chat import (
    GeminiCliChatBase,
    GeminiCliProvider,
    GeminiCliResponse,
)
from src.ai.model_manager import (
    add_unsupported_model,
    get_available_models,
    load_unsupported_models,
)
from src.ai.orchestration.unified_chat import UnifiedChatModel
from src.api.router_chat import get_chat_model


# =============================================================================
# Тесты GeminiCliResponse
# =============================================================================

class TestGeminiCliResponse:
    """Тесты структуры ответа GeminiCliResponse."""

    def test_response_properties(self):
        """Проверка полей и свойства success."""
        resp_success = GeminiCliResponse(
            text="Hello world",
            return_code=0,
            stderr="",
            parsed_json={"status": "ok"},
            duration_seconds=1.23,
        )
        assert resp_success.success is True
        assert resp_success.text == "Hello world"
        assert resp_success.parsed_json == {"status": "ok"}
        assert resp_success.duration_seconds == 1.23

        resp_error = GeminiCliResponse(
            text="",
            return_code=1,
            stderr="Unknown option",
        )
        assert resp_error.success is False
        assert resp_error.return_code == 1
        assert resp_error.stderr == "Unknown option"


# =============================================================================
# Тесты GeminiCliProvider (4 режима)
# =============================================================================

class TestGeminiCliProvider:
    """Тесты низкоуровневого провайдера GeminiCliProvider."""

    def test_is_available_and_find_executable(self):
        """Проверка методов обнаружения исполняемого файла."""
        with patch("shutil.which", return_value="C:\\npm\\gemini.cmd"):
            provider = GeminiCliProvider()
            assert provider.is_available() is True
            assert provider.resolve_executable() == "C:\\npm\\gemini.cmd"

        with patch("shutil.which", return_value=None):
            with patch("os.path.exists", return_value=False):
                provider = GeminiCliProvider(executable="nonexistent_gemini_binary")
                assert provider.is_available() is False
                with pytest.raises(RuntimeError, match="Gemini CLI не найден"):
                    provider.resolve_executable()

    def test_get_version(self):
        """Проверка получения версии CLI."""
        provider = GeminiCliProvider()
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "0.4.1\n"

        with patch.object(provider, "resolve_executable", return_value="gemini"):
            with patch("subprocess.run", return_value=mock_res):
                assert provider.get_version() == "0.4.1"

    def test_clean_output(self):
        """Проверка фильтрации служебных баннеров YOLO и extensions."""
        provider = GeminiCliProvider()
        raw = "YOLO mode is enabled\nLoaded extension: gcloud\nActual AI response line 1\nLine 2"
        cleaned = provider._clean_output(raw)
        assert cleaned == "Actual AI response line 1\nLine 2"

    def test_extract_json_direct(self):
        """Проверка прямого парсинга JSON."""
        res = GeminiCliProvider._extract_json('{"key": "value", "count": 42}')
        assert res == {"key": "value", "count": 42}

    def test_extract_json_markdown_block(self):
        """Проверка извлечения JSON из markdown fenced блока."""
        text = "Вот ваш результат:\n```json\n{\n  \"items\": [1, 2, 3]\n}\n```\nСпасибо!"
        res = GeminiCliProvider._extract_json(text)
        assert res == {"items": [1, 2, 3]}

    def test_extract_json_invalid(self):
        """Проверка исключения при невалидном JSON."""
        with pytest.raises(ValueError, match="Не удалось распарсить JSON"):
            GeminiCliProvider._extract_json("Просто текст без json")

    def test_generate_sync_success(self):
        """Проверка синхронного метода generate() (Режим 1)."""
        provider = GeminiCliProvider()
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "YOLO mode is enabled\nСгенерированный ответ"
        mock_res.stderr = ""

        with patch.object(provider, "resolve_executable", return_value="gemini"):
            with patch("subprocess.run", return_value=mock_res) as mock_sub:
                response = provider.generate("Привет", model="gemini-3.1-flash-lite")
                assert response.success is True
                assert response.text == "Сгенерированный ответ"
                assert response.return_code == 0
                mock_sub.assert_called_once()

    def test_generate_sync_timeout(self):
        """Проверка обработки таймаута в generate()."""
        provider = GeminiCliProvider(timeout=5)
        with patch.object(provider, "resolve_executable", return_value="gemini"):
            with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="gemini", timeout=5)):
                with pytest.raises(TimeoutError, match="не завершился за 5 секунд"):
                    provider.generate("Долгий запрос")

    @pytest.mark.asyncio
    async def test_generate_async_success(self):
        """Проверка асинхронного метода generate_async()."""
        provider = GeminiCliProvider()
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"Async response", b""))

        with patch.object(provider, "resolve_executable", return_value="gemini"):
            with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_proc)):
                resp = await provider.generate_async("Запрос")
                assert resp.success is True
                assert resp.text == "Async response"

    def test_generate_json_success(self):
        """Проверка режима structured JSON (Режим 2)."""
        provider = GeminiCliProvider()
        mock_resp = GeminiCliResponse(
            text='```json\n{"name": "test", "active": true}\n```',
            return_code=0,
            stderr="",
        )
        with patch.object(provider, "generate", return_value=mock_resp):
            data = provider.generate_json("Верни JSON")
            assert data == {"name": "test", "active": True}

    def test_stream_sync(self):
        """Проверка синхронного генератора stream() (Режим 3)."""
        provider = GeminiCliProvider()
        mock_proc = MagicMock()
        mock_proc.stdout = ["YOLO mode is enabled\n", "Line 1\n", "Line 2\n"]
        mock_proc.poll.return_value = 0
        mock_proc.returncode = 0

        with patch.object(provider, "resolve_executable", return_value="gemini"):
            with patch("subprocess.Popen", return_value=mock_proc):
                chunks = list(provider.stream("Потоковый запрос"))
                assert chunks == ["Line 1\n", "Line 2\n"]

    @pytest.mark.asyncio
    async def test_stream_async(self):
        """Проверка асинхронного генератора stream_async() (Режим 3 - Async)."""
        provider = GeminiCliProvider()
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.wait = AsyncMock(return_value=0)
        mock_proc.stdout.readline = AsyncMock(side_effect=[b"Chunk A\n", b"Chunk B\n", b""])

        with patch.object(provider, "resolve_executable", return_value="gemini"):
            with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_proc)):
                chunks = []
                async for chunk in provider.stream_async("Асинхронный стрим"):
                    chunks.append(chunk)

                assert chunks == ["Chunk A\n", "Chunk B\n"]

    def test_run_agent(self):
        """Проверка режима агента в каталоге проекта (Режим 4)."""
        provider = GeminiCliProvider()
        mock_resp = GeminiCliResponse(text="Agent report", return_code=0, stderr="")

        with patch.object(provider, "generate", return_value=mock_resp) as mock_gen:
            target_dir = Path("c:/Users/onela/AppData/Local/AI-Breadboard")
            res = provider.run_agent("Задача агента", working_directory=target_dir)
            assert res.text == "Agent report"
            mock_gen.assert_called_once_with(
                prompt="Задача агента",
                model=None,
                working_directory=target_dir.resolve(),
                timeout=None,
                approval_mode="yolo",
            )


# =============================================================================
# Тесты GeminiCliChatBase
# =============================================================================

class TestGeminiCliChat:
    """Тесты класса GeminiCliChatBase."""

    def test_normalize_model_id_defaults(self):
        """Проверка нормализации идентификаторов моделей."""
        assert GeminiCliChatBase.normalize_model_id("") == "gemini-3.1-flash-lite"
        assert GeminiCliChatBase.normalize_model_id("gemini_cli:gemini-3.1-flash-lite") == "gemini-3.1-flash-lite"
        assert GeminiCliChatBase.normalize_model_id("gemini-cli-gemini-2.5-flash") == "gemini-2.5-flash"
        assert GeminiCliChatBase.normalize_model_id("models/gemini-2.5-pro") == "gemini-2.5-pro"

    def test_capabilities_and_availability(self):
        """Проверка get_capabilities() и is_available()."""
        assert "chat" in GeminiCliChatBase.get_capabilities()
        assert "stream" in GeminiCliChatBase.get_capabilities()
        with patch("shutil.which", return_value="gemini"):
            assert GeminiCliChatBase.is_available() is True

    @pytest.mark.asyncio
    async def test_ask_mock(self):
        """Тест метода ask()."""
        chat = GeminiCliChatBase(model_id="gemini-3.1-flash-lite", system_prompt="Test sys prompt")
        mock_resp = GeminiCliResponse(text="Test CLI answer", return_code=0, stderr="")

        with patch.object(chat.provider, "generate_async", AsyncMock(return_value=mock_resp)):
            res = await chat.ask("Hello CLI")
            assert res == "Test CLI answer"

    @pytest.mark.asyncio
    async def test_chat_saves_history(self):
        """Тест метода chat() с сохранением истории диалога."""
        chat = GeminiCliChatBase(model_id="gemini-3.1-flash-lite")
        mock_resp = GeminiCliResponse(text="Response 1", return_code=0, stderr="")

        with patch.object(chat.provider, "generate_async", AsyncMock(return_value=mock_resp)):
            res = await chat.chat("Hi")
            assert res == "Response 1"
            assert len(chat.history) == 2
            assert chat.history[0] == {"role": "user", "content": "Hi"}
            assert chat.history[1] == {"role": "model", "content": "Response 1"}

    @pytest.mark.asyncio
    async def test_chat_stream(self):
        """Тест потокового вывода через chat_stream."""
        chat = GeminiCliChatBase(model_id="gemini-3.1-flash-lite")

        async def _mock_stream(*args, **kwargs):
            yield "Chunk 1\n"
            yield "Chunk 2\n"

        with patch.object(chat.provider, "stream_async", side_effect=_mock_stream):
            chunks = []
            async for c in chat.chat_stream("Stream prompt"):
                chunks.append(c)

            assert len(chunks) == 2
            assert chunks[0] == "Chunk 1\n"
            assert chunks[1] == "Chunk 2\n"


# =============================================================================
# Тесты ModelManager и Маршрутизации
# =============================================================================

class TestModelManagerGeminiCli:
    """Тесты управления моделями Gemini CLI в model_manager."""

    def test_get_available_models_gemini_cli(self):
        """Проверка получения списка моделей Gemini CLI."""
        models = get_available_models(provider="gemini_cli", force_refresh=True)
        assert isinstance(models, list)
        assert len(models) > 0
        assert "gemini-3.1-flash-lite" in models
        assert models[0] == "gemini-3.1-flash-lite"

    def test_unsupported_models_filter(self):
        """Проверка списка неподдерживаемых моделей."""
        unsupported = load_unsupported_models("gemini_cli")
        assert isinstance(unsupported, set)


class TestRouterChatGeminiCliIntegration:
    """Тесты фабрики get_chat_model в router_chat."""

    def test_get_chat_model_gemini_cli(self):
        """Проверка создания экземпляра GeminiCliChatBase через get_chat_model."""
        model = get_chat_model("gemini_cli:gemini-3.1-flash-lite", system_instruction="Test")
        assert isinstance(model, GeminiCliChatBase)
        assert model.model_id == "gemini-3.1-flash-lite"
        assert model.system_instruction == "Test"


class TestUnifiedChatGeminiCliIntegration:
    """Тесты маршрутизации в UnifiedChatModel."""

    @pytest.mark.asyncio
    async def test_unified_chat_gemini_cli_dispatch(self):
        """Проверка перенаправления запросов в Gemini CLI через UnifiedChatModel."""
        unified = UnifiedChatModel(
            api_key_names=[],
            system_instruction="Default system",
        )

        active_model, active_name = unified._get_active_model("gemini_cli:gemini-3.1-flash-lite")
        assert isinstance(active_model, GeminiCliChatBase)
        assert active_name == "gemini_cli:gemini-3.1-flash-lite"
