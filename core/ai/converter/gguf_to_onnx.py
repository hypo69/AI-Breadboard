# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Конвертация GGUF / HF моделей в ONNX и оптимизация
# =============================================================================
# Описание:
#   Модуль конвертации локальных моделей в формат ONNX
#   с последующей оптимизацией через onnxruntime-tools / Microsoft Olive passes.
#   Использует optimum[onnxruntime] для экспорта через HuggingFace Transformers.
#
# File: core/ai/converter/gguf_to_onnx.py
# Project: ai-assistant
# Package: core.ai.converter
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from core.logger.logger import logger

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
    """Результат конвертации и оптимизации модели."""
    success: bool
    output_dir: str = ""
    optimized_path: str = ""
    error: str = ""
    chunks_info: Dict[str, Any] = field(default_factory=dict)


class GGUFConverter:
    """Конвертер моделей в формат ONNX с опциональной оптимизацией."""

    async def convert(
        self,
        model_path: str,
        output_dir: str,
        model_type: str = "gpt2",
        opset: int = 17,
        optimize: bool = True,
    ) -> ConversionResult:
        """Конвертация модели в формат ONNX.

        Args:
            model_path: HF model ID или путь к локальной директории модели.
            output_dir: Директория для сохранения ONNX артефактов.
            model_type: Архитектурный тип для оптимизатора ('gpt2', 'bert', 'bart').
            opset: Версия ONNX opset.
            optimize: Запуск проходов оптимизации графа.

        Returns:
            ConversionResult: Результат экспорта и пути к файлам.
        """
        if not CONVERTER_AVAILABLE:
            return ConversionResult(
                success=False,
                error="optimum[onnxruntime] не установлен. Выполните: pip install optimum[onnxruntime]",
            )

        src = Path(model_path)
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        logger.info(f"[GGUFConverter] Начало конвертации: {model_path} -> {out}")

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

            logger.info(f"[GGUFConverter] Конвертация завершена успешно: {out}")
            return result

        except Exception as e:
            logger.error(f"[GGUFConverter] Ошибка конвертации {model_path}: {e}")
            return ConversionResult(success=False, error=str(e))

    def _export(self, model_path: str, output_dir: str, opset: int) -> ConversionResult:
        """Синхронный экспорт модели через optimum."""
        try:
            from transformers import AutoTokenizer
            from optimum.onnxruntime import ORTModelForCausalLM

            logger.info(f"[GGUFConverter] Загрузка токенизатора из {model_path}")
            tokenizer = AutoTokenizer.from_pretrained(model_path)

            logger.info("[GGUFConverter] Экспорт в ONNX через ORTModelForCausalLM...")
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
            logger.error(f"[GGUFConverter] Ошибка экспорта {model_path}: {e}")
            return ConversionResult(success=False, error=str(e))

    def _optimize(self, onnx_path: str, model_type: str) -> str:
        """Синхронная оптимизация графа ONNX модели."""
        try:
            from onnxruntime.transformers import optimizer as ort_optimizer
            logger.info(f"[GGUFConverter] Оптимизация ONNX графа: {onnx_path}")
            opt_model = ort_optimizer.optimize_model(onnx_path, model_type=model_type)
            output_path = onnx_path.replace(".onnx", "_optimized.onnx")
            opt_model.save_model_to_file(output_path)
            logger.info(f"[GGUFConverter] Оптимизированная модель сохранена: {output_path}")
            return output_path
        except Exception as e:
            logger.warning(f"[GGUFConverter] Оптимизация пропущена из-за ошибки: {e}")
            return ""

    @staticmethod
    def is_available() -> Dict[str, bool]:
        """Проверка доступности инструментов конвертации."""
        return {
            "converter": CONVERTER_AVAILABLE,
            "optimizer": OPTIMIZER_AVAILABLE,
        }


gguf_converter = GGUFConverter()
