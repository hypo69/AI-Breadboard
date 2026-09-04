# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: GGUF to ONNX model conversion and optimization
# =============================================================================
# Description:
#   Module for converting local models to ONNX format with optional graph optimization.
#
# File: gguf_to_onnx.py
# Project: ai-breadboard
# Package: src.ai.converter
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

"""GGUF to ONNX model converter with optimization support.

Converts HuggingFace models to ONNX format and optionally optimizes the computational graph."""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from src.logger.logger import logger

CONVERTER_AVAILABLE = False
OPTIMIZER_AVAILABLE = False

try:
    from transformers import AutoTokenizer  # noqa: F401
    from optimum.onnxruntime import ORTModelForCausalLM  # noqa: F401
    CONVERTER_AVAILABLE = True
except ImportError:
    pass

try:
    from onnxruntime.transformers import optimizer as ort_optimizer  # noqa: F401
    OPTIMIZER_AVAILABLE = True
except ImportError:
    pass

@dataclass
class ConversionResult:
    """Model conversion and optimization result.
    
    Attributes:
        success (bool): Whether conversion succeeded.
        output_dir (str): Directory where ONNX artifacts saved.
        optimized_path (str): Path to optimized model (if optimization ran).
        error (str): Error message if conversion failed.
        chunks_info (Dict): Metadata about exported files.
    """
    success: bool
    output_dir: str = ""
    optimized_path: str = ""
    error: str = ""
    chunks_info: Dict[str, Any] = field(default_factory=dict)

class GGUFConverter:
    """Converter for models to ONNX format with optional optimization.
    
    Converts HuggingFace or local models to ONNX and optionally runs
    graph optimization passes for inference performance.
    """

    async def convert(
        self,
        model_path: str,
        output_dir: str,
        model_type: str = "gpt2",
        opset: int = 17,
        optimize: bool = True,
    ) -> ConversionResult:
        """Convert model to ONNX format.

        Args:
            model_path (str): HuggingFace model ID or path to local model directory.
            output_dir (str): Directory to save ONNX artifacts.
            model_type (str): Architecture type for optimizer ('gpt2', 'bert', 'bart'). Default 'gpt2'.
            opset (int): ONNX opset version. Default 17.
            optimize (bool): Run graph optimization passes. Default True.

        Returns:
            ConversionResult: Export result and file paths.
        """
        if not CONVERTER_AVAILABLE:
            return ConversionResult(
                success=False,
                error="optimum[onnxruntime] not installed. Run: pip install optimum[onnxruntime]",
            )

        src = Path(model_path)
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        logger.info(f"[GGUFConverter] Starting conversion: {model_path} -> {out}")

        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, self._export, model_path, str(out), opset
            )
            if not result.success:
                return result

            if optimize and OPTIMIZER_AVAILABLE:
                onnx_file = out / "model.onnx"
                if onnx_file.exists():
                    opt_path = await loop.run_in_executor(
                        None, self._optimize, str(onnx_file), model_type
                    )
                    result.optimized_path = opt_path

            logger.info(f"[GGUFConverter] Conversion completed successfully: {out}")
            return result

        except Exception as e:
            logger.error(f"[GGUFConverter] Error converting {model_path}: {e}")
            return ConversionResult(success=False, error=str(e))

    def _export(self, model_path: str, output_dir: str, opset: int) -> ConversionResult:
        """Synchronous model export via optimum.
        
        Args:
            model_path (str): Model path or identifier.
            output_dir (str): Output directory for ONNX files.
            opset (int): ONNX opset version.
            
        Returns:
            ConversionResult: Export result with file information.
        """
        try:
            from transformers import AutoTokenizer
            from optimum.onnxruntime import ORTModelForCausalLM

            logger.info(f"[GGUFConverter] Loading tokenizer from {model_path}")
            tokenizer = AutoTokenizer.from_pretrained(model_path)

            logger.info("[GGUFConverter] Exporting to ONNX via ORTModelForCausalLM...")
            model = ORTModelForCausalLM.from_pretrained(
                model_path,
                export=True,
                opset=opset,
            )

            model.save_pretrained(output_dir)
            tokenizer.save_pretrained(output_dir)

            out = Path(output_dir)
            onnx_files = list(out.glob("*.onnx"))
            chunks_info = {
                "onnx_files": [f.name for f in onnx_files],
                "total_size_mb": round(
                    sum(f.stat().st_size for f in onnx_files) / 1024 / 1024, 2
                ),
            }

            return ConversionResult(
                success=True,
                output_dir=output_dir,
                chunks_info=chunks_info,
            )

        except Exception as e:
            logger.error(f"[GGUFConverter] Error exporting {model_path}: {e}")
            return ConversionResult(success=False, error=str(e))

    def _optimize(self, onnx_path: str, model_type: str) -> str:
        """Synchronous ONNX graph optimization.
        
        Args:
            onnx_path (str): Path to ONNX model file.
            model_type (str): Model architecture type.
            
        Returns:
            str: Path to optimized model, or empty string on error.
        """
        try:
            from onnxruntime.transformers import optimizer as ort_optimizer
            logger.info(f"[GGUFConverter] Optimizing ONNX graph: {onnx_path}")
            opt_model = ort_optimizer.optimize_model(onnx_path, model_type=model_type)
            output_path = onnx_path.replace(".onnx", "_optimized.onnx")
            opt_model.save_model_to_file(output_path)
            logger.info(f"[GGUFConverter] Optimized model saved: {output_path}")
            return output_path
        except Exception as e:
            logger.warning(f"[GGUFConverter] Optimization skipped due to error: {e}")
            return ""

    @staticmethod
    def is_available() -> Dict[str, bool]:
        """Check availability of conversion tools.
        
        Returns:
            Dict[str, bool]: Availability of converter and optimizer.
        """
        return {
            "converter": CONVERTER_AVAILABLE,
            "optimizer": OPTIMIZER_AVAILABLE,
        }

gguf_converter = GGUFConverter()
