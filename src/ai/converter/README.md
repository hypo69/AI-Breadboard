# `core.ai.converter` — Model Conversion & Optimization

## Overview

The `core.ai.converter` module provides utilities for converting language models into the ONNX (Open Neural Network Exchange) format and performing graph optimization passes for accelerated local inference.

It acts as a bridge between standard Hugging Face/local model checkpoints and runtime execution engines (such as ONNX Runtime with DirectML or CUDA).

---

## Architecture & Components

```
core/ai/converter/
├── __init__.py           # Exports public API (GGUFConverter, ConversionResult, gguf_converter)
├── gguf_to_onnx.py       # Core conversion, Optimum export & ONNX Runtime graph optimization
└── README.md             # Package documentation
```

### Key Components

- **`GGUFConverter`** (`gguf_to_onnx.py`):
  Primary converter class that orchestrates asynchronous export and optimization workflows.
  - `convert()`: Main asynchronous entry point that delegates heavy model compilation to thread pool executors.
  - `_export()`: Synchronously loads tokenizers and exports causal language models via Optimum (`ORTModelForCausalLM`).
  - `_optimize()`: Optimizes computational graphs (operator fusion, attention optimizations) using `onnxruntime.transformers.optimizer`.
  - `is_available()`: Utility method checking whether optional dependencies (`optimum`, `onnxruntime`) are installed.

- **`ConversionResult`** (`gguf_to_onnx.py`):
  Dataclass representing the result of a conversion process:
  - `success` (`bool`): Whether export and optimization completed successfully.
  - `output_dir` (`str`): Target directory containing saved ONNX artifacts and tokenizer configs.
  - `optimized_path` (`str`): Absolute path to the optimized ONNX model file (if optimization was enabled).
  - `error` (`str`): Error message in case of failure.
  - `chunks_info` (`dict`): Metadata including generated ONNX filenames and total file size in MB.

- **`gguf_converter`** (`gguf_to_onnx.py` / `__init__.py`):
  Pre-instantiated singleton instance of `GGUFConverter` for immediate use across the application.

---

## Installation & Prerequisites

Model conversion and optimization require optional Hugging Face and ONNX Runtime dependencies:

```bash
pip install optimum[onnxruntime] transformers onnxruntime
```

---

## Usage Examples

### 1. Checking Tool Availability

```python
from core.ai.converter import gguf_converter

status = gguf_converter.is_available()
print(status)
# Output: {'converter': True, 'optimizer': True}
```

### 2. Asynchronous Model Conversion & Optimization

```python
import asyncio
from core.ai.converter import gguf_converter

async def main():
    result = await gguf_converter.convert(
        model_path="gpt2",
        output_dir="./models/onnx/gpt2",
        model_type="gpt2",
        opset=17,
        optimize=True,
    )

    if result.success:
        print(f"Model exported to: {result.output_dir}")
        print(f"Optimized model: {result.optimized_path}")
        print(f"Files: {result.chunks_info.get('onnx_files')}")
        print(f"Total size: {result.chunks_info.get('total_size_mb')} MB")
    else:
        print(f"Conversion failed: {result.error}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Related Modules

- [`core.ai`](../README.md) — Main AI integrations and UnifiedChatModel routing.
- [`core.ai.providers`](../providers/README.md) — Backend model providers and ONNX execution runtime.
- [`DOCUMENTATION_INDEX.md`](../../../DOCUMENTATION_INDEX.md) — Master documentation index.
