# Windows ML / ONNX Runtime Provider (`core/ai/providers/onnx`)

## Overview
The `onnx` provider executes ONNX models with hardware acceleration via Microsoft ONNX Runtime (DirectML, CPU, CUDA, and QNN Execution Providers).

## Architecture
- **Windows ML & DirectML**: Runs on AMD, Intel, and NVIDIA GPUs and NPUs natively on Windows.
- **Olive Optimization**: Direct integration with quantized and pruned models.

## Usage
```python
from core.ai.providers.onnx import ONNXChatBase

provider = ONNXChatBase(model_path="models/phi-3-mini.onnx")
response = await provider.ask("Generate code snippet.")
```
