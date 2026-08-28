# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Microsoft Olive / ONNX Runtime Client & Chat Wrapper
# =============================================================================
# Описание:
#   Прямой запуск оптимизированных моделей ONNX с поддержкой DirectML / CPU / CUDA.
#   Использует optimum.onnxruntime для инференса и токенизации без внешних сервисов.
#
# File: core/ai/onnx_chat.py
# Project: ai-breadboard
# Package: core.ai
# Module: ONNXChat
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List

from core.logger.logger import logger

_loaded_onnx_models: Dict[str, Dict[str, Any]] = {}


def _check_onnx_runtime() -> bool:
    """Проверка наличия optimum и onnxruntime."""
    try:
        import onnxruntime  # noqa: F401
        from optimum.onnxruntime import ORTModelForCausalLM  # noqa: F401
        from transformers import AutoTokenizer  # noqa: F401
        return True
    except ImportError:
        return False


class ONNXClient:
    """Клиент локального инференса моделей ONNX."""

    def load_model(
        self,
        model_path: str,
        execution_provider: str = "DirectMLExecutionProvider",
    ) -> Dict[str, Any]:
        """Загрузка ONNX модели в память с выбранным провайдером исполнения."""
        if not _check_onnx_runtime():
            return {
                "success": False,
                "error": "optimum[onnxruntime] или onnxruntime не установлены",
            }

        if model_path in _loaded_onnx_models:
            return {"success": True, "model_path": model_path, "status": "already_loaded"}

        try:
            from optimum.onnxruntime import ORTModelForCausalLM
            from transformers import AutoTokenizer

            logger.info(f"[ONNXClient] Загрузка ONNX модели из {model_path} с {execution_provider}")

            providers: List[str] = [execution_provider, "CPUExecutionProvider"]
            model = ORTModelForCausalLM.from_pretrained(
                model_path,
                provider=execution_provider,
            )
            tokenizer = AutoTokenizer.from_pretrained(model_path)

            _loaded_onnx_models[model_path] = {
                "model": model,
                "tokenizer": tokenizer,
                "provider": execution_provider,
            }
            logger.info(f"[ONNXClient] ONNX модель {model_path} успешно загружена")
            return {"success": True, "model_path": model_path, "provider": execution_provider}

        except Exception as e:
            logger.error(f"[ONNXClient] Ошибка при загрузке ONNX модели {model_path}: {e}")
            return {"success": False, "error": str(e)}

    def unload_model(self, model_path: str) -> Dict[str, Any]:
        """Выгрузка ONNX модели из памяти."""
        if model_path not in _loaded_onnx_models:
            return {"success": False, "error": f"Модель {model_path} не загружена"}
        try:
            import gc
            del _loaded_onnx_models[model_path]
            gc.collect()
            logger.info(f"[ONNXClient] ONNX модель {model_path} выгружена")
            return {"success": True, "model_path": model_path}
        except Exception as e:
            logger.error(f"[ONNXClient] Ошибка выгрузки ONNX модели {model_path}: {e}")
            return {"success": False, "error": str(e)}

    async def generate(
        self,
        prompt: str,
        model_path: str,
        system_prompt: str = "",
        max_new_tokens: int = 512,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Генерация ответа через ONNX Runtime в отдельном пуле потоков."""
        if model_path not in _loaded_onnx_models:
            loop = asyncio.get_running_loop()
            load_res = await loop.run_in_executor(None, self.load_model, model_path)
            if not load_res.get("success"):
                return {"success": False, "error": f"Не удалось загрузить ONNX модель: {load_res.get('error', '')}"}

        try:
            data = _loaded_onnx_models[model_path]
            model = data["model"]
            tokenizer = data["tokenizer"]

            if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template:
                messages: List[Dict[str, str]] = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                inputs_text = tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            else:
                inputs_text = f"{system_prompt}\n\n{prompt}".strip() if system_prompt else prompt

            def _infer() -> str:
                inputs = tokenizer(inputs_text, return_tensors="pt")
                do_sample: bool = temperature > 0.0
                gen_kwargs: Dict[str, Any] = {
                    "max_new_tokens": max_new_tokens,
                    "do_sample": do_sample,
                    "pad_token_id": tokenizer.eos_token_id,
                }
                if do_sample:
                    gen_kwargs["temperature"] = temperature
                outputs = model.generate(**inputs, **gen_kwargs)
                input_len = inputs["input_ids"].shape[-1]
                generated_tokens = outputs[0][input_len:]
                return tokenizer.decode(generated_tokens, skip_special_tokens=True)

            loop = asyncio.get_running_loop()
            content = await loop.run_in_executor(None, _infer)
            return {"success": True, "content": content, "model": model_path}

        except Exception as e:
            logger.error(f"[ONNXClient] Ошибка инференса ONNX {model_path}: {e}")
            return {"success": False, "error": str(e)}

    def list_loaded(self) -> List[Dict[str, Any]]:
        """Список загруженных ONNX моделей."""
        return [{"id": k, "provider": v.get("provider", "")} for k, v in _loaded_onnx_models.items()]


onnx_client = ONNXClient()


class ONNXChatBase:
    """Обертка чата для ONNX моделей."""

    def __init__(self, model_id: str, system_prompt: str = ""):
        self.model_id = model_id
        self.system_prompt = system_prompt
        self.client = onnx_client

    async def generate_content(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> str:
        """Синхронно-асинхронная генерация единого ответа."""
        res = await self.client.generate(
            prompt=prompt,
            model_path=self.model_id,
            system_prompt=self.system_prompt,
            max_new_tokens=max_tokens,
            temperature=temperature,
        )
        if res.get("success"):
            return res.get("content", "")
        raise RuntimeError(f"ONNX error: {res.get('error', 'Unknown generation error')}")

    async def generate_content_stream(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Стриминговая генерация контента."""
        content = await self.generate_content(prompt, temperature=temperature, max_tokens=max_tokens)
        if content:
            yield content
