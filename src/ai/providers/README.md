# AI Providers (`core/ai/providers`)

## Overview
This directory contains modular provider packages for all supported local and cloud AI runtimes:

| Provider Package | Runtime / Service | Type | Capabilities |
| :--- | :--- | :--- | :--- |
| `windows_ai` | Windows AI APIs (Phi Silica, OCR, Imaging) | Local / System | Chat, OCR, Vision |
| `foundry` | Microsoft Foundry Local (`localhost:54837`) | Local REST | Chat, Code |
| `ollama` | Ollama Daemon (`localhost:11434`) | Local REST | Chat, Code, Embeddings |
| `onnx` | Windows ML / ONNX Runtime (DirectML) | In-process HW | Chat, Vision, Embeddings |
| `gemini` | Google Generative AI API | Cloud | Chat, Vision, Tools, Embeddings |
| `gemini_cli` | Gemini Command Line Interface | Local CLI | Chat, Tools |
| `agy` | Antigravity Subprocess / Sidecar | Local CLI | Chat, Agentic Tools |
| `huggingface` | Hugging Face Transformers | In-process / API | Chat, Embeddings |
| `openai` | OpenAI / OpenAI-Compatible Endpoints | Local / Cloud | Chat, Code |
