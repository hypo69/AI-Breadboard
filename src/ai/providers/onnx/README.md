# Microsoft ONNX Runtime & Olive Provider (`src/ai/providers/onnx`)

## Overview
The `onnx` provider executes ONNX models with hardware acceleration via Microsoft ONNX Runtime across multiple execution backends (DirectML GPU, Qualcomm QNN NPU, NVIDIA CUDA, and CPU). It integrates directly with Microsoft Olive for quantization and model optimization.

## Architecture & Features
- **DirectML & Windows ML**: Native acceleration across AMD, Intel, and NVIDIA GPUs on Windows.
- **Qualcomm QNN NPU**: Hardware-accelerated NPU execution for Windows on ARM / Copilot+ PC devices.
- **Olive Optimization Engine**: Generation of Olive quantization configs (INT4 / INT8 / FP16) and direct compilation of models.
- **Automatic Fallback**: Automatic graceful fallback to CPU Execution Provider if specialized GPU/NPU providers are unavailable.

## Configuration (`config.json`)
```json
{
  "onnx": {
    "enabled": true,
    "models_dir": "models/onnx",
    "execution_provider": "DirectMLExecutionProvider",
    "default_model": "phi-3.5-mini-instruct-onnx",
    "olive_precision": "int4"
  }
}
```

## Python Usage
```python
from src.ai.providers.onnx.chat import ONNXChatBase
from src.ai.providers.onnx.olive_optimizer import optimize_model_with_olive

# Inference
provider = ONNXChatBase(model_id="phi-3.5-mini-instruct-onnx")
response = await provider.generate_content("Hello from ONNX Runtime!")

# Optimization via Olive
res = await optimize_model_with_olive(
    model_name_or_path="microsoft/Phi-3.5-mini-instruct",
    precision="int4",
    target_provider="DirectMLExecutionProvider"
)
```

