# Windows AI Provider (`core/ai/providers/windows_ai`)

## Overview
The `windows_ai` provider integrates **Windows AI APIs** and system-managed AI components (such as **Phi Silica**, **Windows OCR**, and **Imaging APIs**) directly into the AI-Breadboard orchestration framework.

---

## Architecture & Integration

Microsoft structures Windows AI into three distinct layers:
1. **Windows AI APIs**: Built-in system models managed and updated by Windows Update (e.g., Phi Silica on Copilot+ PCs with 40+ TOPS NPU).
2. **Foundry Local**: Local OpenAI-compatible REST server for open-weight models (Qwen, Phi-4, DeepSeek).
3. **Windows ML / ONNX Runtime**: Direct model execution on DirectML (GPU/NPU/CPU).

This provider encapsulates layer 1 (Windows AI APIs) with automatic host probing and graceful degradation.

---

## Capabilities
- **Chat / Reasoning**: `windows-ai:phi-silica` (NPU-accelerated local SLM)
- **OCR**: `windows-ai:ocr` (Native Windows text recognition)
- **Vision**: `windows-ai:vision` / `windows-ai:image-description`

---

## Graceful Fallback
If the host machine lacks preinstalled AI components (e.g. `Settings > System > AI components` reports no components installed), `WindowsAIChatBase.is_available()` returns `False`. The AI-Breadboard Router automatically degrades to **Foundry Local**, **Ollama**, **ONNX DirectML**, or **Cloud Gemini** without breaking application flow.

---

## Usage Example
```python
from core.ai.providers.windows_ai import WindowsAIChatBase, probe_windows_ai_components

# Probe host status
status = probe_windows_ai_components()
print("Windows AI Available:", status["available"])

# Initialize provider
provider = WindowsAIChatBase(model_id="phi-silica")
if provider.is_available():
    response = await provider.ask("Hello from AI Breadboard")
```
