# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Microsoft Olive Optimization and Model Preparation Engine
# =============================================================================
# Description:
#   Provides utilities for optimizing, quantizing, and compiling AI models using
#   Microsoft Olive toolkit for ONNX Runtime (DirectML, QNN NPU, CUDA, CPU).
#
# File: olive_optimizer.py
# Project: ai-breadboard
# Package: src.ai.providers.onnx
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import os
import sys
import shutil
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from header import __root__
from src.logger.logger import logger


def check_olive_available() -> bool:
    """Check if Microsoft Olive package is installed in the current environment.

    Returns:
        bool: True if olive is importable, False otherwise.
    """
    try:
        import olive  # noqa: F401
        return True
    except ImportError:
        return False


def get_available_execution_providers() -> List[str]:
    """Discover available ONNX Runtime Execution Providers on the current host.

    Returns:
        List[str]: List of supported provider strings (e.g. 'DirectMLExecutionProvider', 'CPUExecutionProvider').
    """
    try:
        import onnxruntime as ort
        return list(ort.get_available_providers())
    except ImportError:
        return ["CPUExecutionProvider"]


def generate_olive_config(
    model_name_or_path: str,
    output_dir: str,
    precision: str = "int4",
    target_provider: str = "DirectMLExecutionProvider",
) -> Dict[str, Any]:
    """Generate a standard Microsoft Olive configuration dictionary for quantization/optimization.

    Args:
        model_name_or_path (str): HuggingFace model repo ID or local path.
        output_dir (str): Destination folder for optimized ONNX artifacts.
        precision (str): Target precision ('int4', 'int8', 'fp16'). Defaults to 'int4'.
        target_provider (str): ONNX Runtime execution provider name. Defaults to 'DirectMLExecutionProvider'.

    Returns:
        Dict[str, Any]: Olive configuration dictionary.
    """
    return {
        "input_model": {
            "type": "HfModel",
            "model_path": model_name_or_path,
        },
        "systems": {
            "local_system": {
                "type": "LocalSystem",
                "accelerators": [
                    {
                        "device": "gpu" if "DirectML" in target_provider or "CUDA" in target_provider else "cpu",
                        "execution_providers": [target_provider],
                    }
                ],
            }
        },
        "evaluators": {},
        "passes": {
            "onnx_conversion": {
                "type": "OnnxConversion",
                "target_opset": 17,
            },
            "onnx_quantization": {
                "type": "OnnxMatMul4Quantizer" if precision == "int4" else "OnnxQuantization",
                "precision": precision,
            },
        },
        "engine": {
            "output_dir": output_dir,
            "target": "local_system",
            "execution_providers": [target_provider],
        },
    }


async def optimize_model_with_olive(
    model_name_or_path: str,
    output_dir: Optional[str] = None,
    precision: str = "int4",
    target_provider: str = "DirectMLExecutionProvider",
) -> Dict[str, Any]:
    """Run Microsoft Olive optimization pipeline asynchronously.

    Args:
        model_name_or_path (str): Source model ID or path.
        output_dir (Optional[str]): Destination folder for ONNX weights.
        precision (str): Quantization precision ('int4', 'int8', 'fp16').
        target_provider (str): Target execution provider.

    Returns:
        Dict[str, Any]: Status dictionary containing success status, output path, or error details.
    """
    if not output_dir:
        safe_name = model_name_or_path.replace("/", "_").replace("\\", "_")
        output_dir = str(__root__ / "models" / "onnx" / f"{safe_name}-{precision}")

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    logger.info(
        f"[OliveOptimizer] Starting optimization for {model_name_or_path} "
        f"(Precision: {precision}, Target: {target_provider}) -> {out_path}"
    )

    if not check_olive_available():
        msg = (
            "Microsoft Olive (olive-ai) is not installed in the environment. "
            "Install it via `pip install olive-ai[directml]` or `pip install olive-ai[cpu]`."
        )
        logger.warning(f"[OliveOptimizer] {msg}")
        return {
            "success": False,
            "error": msg,
            "output_dir": str(out_path),
        }

    try:
        # Run Olive optimization workflow
        loop = asyncio.get_running_loop()

        def _run_olive() -> Dict[str, Any]:
            import olive.workflows.run as olive_run
            cfg = generate_olive_config(
                model_name_or_path=model_name_or_path,
                output_dir=str(out_path),
                precision=precision,
                target_provider=target_provider,
            )
            res = olive_run.run(cfg)
            return {"success": True, "result": str(res), "output_dir": str(out_path)}

        result = await loop.run_in_executor(None, _run_olive)
        logger.info(f"[OliveOptimizer] Optimization completed successfully for {model_name_or_path}")
        return result

    except Exception as ex:
        logger.error(f"[OliveOptimizer] Olive optimization failed for {model_name_or_path}: {ex}", ex)
        return {
            "success": False,
            "error": str(ex),
            "output_dir": str(out_path),
        }
