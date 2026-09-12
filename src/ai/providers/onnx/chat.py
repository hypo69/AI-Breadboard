# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: ONNX Runtime and Olive Chat Engine
# =============================================================================
# Description:
#   Direct inference execution for ONNX models and Olive-optimized models with
#   support for DirectML, QNN NPU, CUDA, and CPU execution providers.
#
# File: chat.py
# Project: ai-breadboard
# Package: src.ai.providers.onnx
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from header import __root__
from src.logger.logger import logger

_loaded_onnx_models: Dict[str, Dict[str, Any]] = {}


def _check_onnx_runtime() -> bool:
    """Check for optimum and onnxruntime availability.

    Returns:
        bool: True if required packages are installed, False otherwise.
    """
    try:
        import onnxruntime  # noqa: F401
        from optimum.onnxruntime import ORTModelForCausalLM  # noqa: F401
        from transformers import AutoTokenizer  # noqa: F401
        return True
    except ImportError:
        return False


def _resolve_model_path(model_path_or_name: str) -> str:
    """Resolve model path to local models/onnx directory or return input identifier.

    Args:
        model_path_or_name (str): Relative or absolute path, or model folder name.

    Returns:
        str: Absolute or normalized model path string.
    """
    clean_name = model_path_or_name.strip()
    if clean_name.startswith("onnx:"):
        clean_name = clean_name.split(":", 1)[-1].lstrip(":")

    candidate_local = __root__ / "models" / "onnx" / clean_name
    if candidate_local.exists():
        return str(candidate_local)

    candidate_direct = Path(clean_name)
    if candidate_direct.exists():
        return str(candidate_direct)

    return clean_name


class ONNXClient:
    """Local inference client for ONNX and Microsoft Olive optimized models."""

    def load_model(
        self,
        model_path: str,
        execution_provider: str = "DirectMLExecutionProvider",
    ) -> Dict[str, Any]:
        """Load ONNX model into memory with chosen execution provider.

        Args:
            model_path (str): Path or identifier for ONNX model.
            execution_provider (str): Execution provider name. Defaults to 'DirectMLExecutionProvider'.

        Returns:
            Dict[str, Any]: Load result status dictionary.
        """
        if not _check_onnx_runtime():
            return {
                "success": False,
                "error": "optimum[onnxruntime] or onnxruntime not installed in environment",
            }

        resolved_path = _resolve_model_path(model_path)
        if resolved_path in _loaded_onnx_models:
            return {"success": True, "model_path": resolved_path, "status": "already_loaded"}

        try:
            from optimum.onnxruntime import ORTModelForCausalLM
            from transformers import AutoTokenizer

            logger.info(f"[ONNXClient] Loading ONNX model from {resolved_path} using {execution_provider}")

            try:
                model = ORTModelForCausalLM.from_pretrained(
                    resolved_path,
                    provider=execution_provider,
                )
                active_provider = execution_provider
            except Exception as ep_err:
                logger.warning(
                    f"[ONNXClient] Provider {execution_provider} failed ({ep_err}). Falling back to CPUExecutionProvider"
                )
                model = ORTModelForCausalLM.from_pretrained(
                    resolved_path,
                    provider="CPUExecutionProvider",
                )
                active_provider = "CPUExecutionProvider"

            tokenizer = AutoTokenizer.from_pretrained(resolved_path)

            _loaded_onnx_models[resolved_path] = {
                "model": model,
                "tokenizer": tokenizer,
                "provider": active_provider,
            }
            logger.info(f"[ONNXClient] ONNX model {resolved_path} successfully loaded on {active_provider}")
            return {"success": True, "model_path": resolved_path, "provider": active_provider}

        except Exception as e:
            logger.error(f"[ONNXClient] Failed loading ONNX model {model_path}: {e}")
            return {"success": False, "error": str(e)}

    def unload_model(self, model_path: str) -> Dict[str, Any]:
        """Unload ONNX model from memory.

        Args:
            model_path (str): Model path to unload.

        Returns:
            Dict[str, Any]: Status dictionary.
        """
        resolved_path = _resolve_model_path(model_path)
        if resolved_path not in _loaded_onnx_models:
            return {"success": False, "error": f"Model {model_path} is not loaded"}
        try:
            import gc
            del _loaded_onnx_models[resolved_path]
            gc.collect()
            logger.info(f"[ONNXClient] ONNX model {resolved_path} unloaded")
            return {"success": True, "model_path": resolved_path}
        except Exception as e:
            logger.error(f"[ONNXClient] Error unloading ONNX model {resolved_path}: {e}")
            return {"success": False, "error": str(e)}

    async def generate(
        self,
        prompt: str,
        model_path: str,
        system_prompt: str = "",
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        execution_provider: str = "DirectMLExecutionProvider",
    ) -> Dict[str, Any]:
        """Generate response via ONNX Runtime in thread pool.

        Args:
            prompt (str): User prompt text.
            model_path (str): Model path or name.
            system_prompt (str): System instruction prompt.
            max_new_tokens (int): Maximum new tokens to generate.
            temperature (float): Sampling temperature.
            execution_provider (str): Requested execution provider.

        Returns:
            Dict[str, Any]: Response payload dictionary with content.
        """
        resolved_path = _resolve_model_path(model_path)
        if resolved_path not in _loaded_onnx_models:
            loop = asyncio.get_running_loop()
            load_res = await loop.run_in_executor(None, self.load_model, resolved_path, execution_provider)
            if not load_res.get("success"):
                return {"success": False, "error": f"Failed to load ONNX model: {load_res.get('error', '')}"}

        try:
            data = _loaded_onnx_models[resolved_path]
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
            logger.error(f"[ONNXClient] ONNX inference error for {model_path}: {e}")
            return {"success": False, "error": str(e)}

    def list_loaded(self) -> List[Dict[str, Any]]:
        """List currently loaded ONNX models in memory.

        Returns:
            List[Dict[str, Any]]: Model entries with path and provider.
        """
        return [{"id": k, "provider": v.get("provider", "")} for k, v in _loaded_onnx_models.items()]


onnx_client = ONNXClient()


class ONNXChatBase:
    """High-level chat wrapper for ONNX and Microsoft Olive models."""

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
        """Generate full response synchronously or asynchronously."""
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
        """Generate response as an asynchronous stream."""
        content = await self.generate_content(prompt, temperature=temperature, max_tokens=max_tokens)
        if content:
            yield content

