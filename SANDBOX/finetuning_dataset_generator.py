# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Fine-Tuning Dataset Generator and Validator
# =============================================================================
# Description:
#   Educational utility script for generating and validating instruction datasets
#   in JSONL format for LoRA / QLoRA training on AI Breadboard.
#
# File: SANDBOX/finetuning_dataset_generator.py
# Project: aibreadboard
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
from pathlib import Path
from typing import Dict, List, Any
from src.logger import logger


def generate_sample_dataset(output_path: Path) -> int:
    """Generate golden reference dataset for instruction fine-tuning.

    Args:
        output_path (Path): Path to output JSONL file.

    Returns:
        int: Number of generated sample dialogues.
    """
    samples: List[Dict[str, Any]] = [
        {
            "messages": [
                {"role": "system", "content": "You are a precise AI Breadboard routing assistant."},
                {"role": "user", "content": "Route to DirectML ONNX model."},
                {"role": "assistant", "content": "Prefix target: onnx:qwen2.5-coder with DirectMLExecutionProvider."}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "You are an AI Breadboard RAG search specialist."},
                {"role": "user", "content": "What is the similarity threshold for high relevance in Gemini embeddings?"},
                {"role": "assistant", "content": "Cosine similarity score >= 0.60 indicates high topical relevance suitable for context injection."}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "You are a model optimization engineer."},
                {"role": "user", "content": "Explain constant folding in Microsoft Olive."},
                {"role": "assistant", "content": "Constant folding computes static operations at graph compilation time, eliminating runtime computation."}
            ]
        }
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for item in samples:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    logger.info(f"Dataset generated: {len(samples)} samples written to {output_path}")
    return len(samples)


def validate_dataset(dataset_path: Path) -> bool:
    """Validate JSONL dataset syntax and conversational role schemas.

    Args:
        dataset_path (Path): Path to dataset file.

    Returns:
        bool: True if dataset is valid, False otherwise.
    """
    if not dataset_path.exists():
        logger.error(f"Dataset file not found: {dataset_path}")
        return False

    valid_count: int = 0
    with open(dataset_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                data = json.loads(line_str)
            except Exception as e:
                logger.error(f"Line {idx}: JSON parse error: {e}")
                return False

            if "messages" not in data or not isinstance(data["messages"], list):
                logger.error(f"Line {idx}: Missing 'messages' list")
                return False

            roles = [msg.get("role", "") for msg in data["messages"] if isinstance(msg, dict)]
            if "user" not in roles or "assistant" not in roles:
                logger.error(f"Line {idx}: Must contain at least 'user' and 'assistant' roles")
                return False

            valid_count += 1

    logger.info(f"Validation successful: {valid_count} valid dialogues found in {dataset_path}")
    return True


if __name__ == "__main__":
    target_file = Path(__file__).parent / "sample_finetuning_dataset.jsonl"
    generate_sample_dataset(target_file)
    validate_dataset(target_file)
