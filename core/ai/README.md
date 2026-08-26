# `core.ai` Module — AI Model Integrations & Orchestration

## Purpose
The `core.ai` package encapsulates all interaction logic with neural network models, provider backends, and ReAct agent workflows.

---

## Subsystems & Components

| File / Subdirectory | Purpose | Key Classes / Functions |
|---|---|---|
| `unified_chat.py` | Single unified facade (`UnifiedChatModel`, `get_chat_model`) routing user prompts across all providers based on model prefixes. | `UnifiedChatModel`, `get_chat_model()` |
| `model_manager.py` | Centralized model pool manager; model discovery, availability caching, and auto-blacklisting of unsupported models. | `ModelManager`, `get_model_manager()` |
| `gemini/` | Direct Google Gemini SDK integration with automatic API key rotation, quota fallback, tool dispatching, and streaming. | `GoogleGenerativeAI`, `get_chat_model()` |
| `foundry_chat.py` | Microsoft AI Foundry client communicating over local OpenAI-compatible endpoints. | `FoundryChatBase` |
| `onnx_chat.py` | Microsoft ONNX Runtime / Olive local inference adapter supporting DirectML, CUDA, and CPU execution. | `ONNXChatBase` |
| `hf_chat.py` | Hugging Face Transformers local inference adapter. | `HFChatBase` |
| `openai_compat_chat.py` | Generic OpenAI-compatible client adapter for OpenAI, DeepSeek, Groq, and LM Studio. | `OpenAICompatChat` |
| `gemini_cli_chat.py` | Integration with Google Gemini CLI terminal agent via async subprocess execution. | `GeminiCliChatBase` |
| `agy_chat.py` | Integration with Google Antigravity AGY SDK over Gemini models. | `AgyChatBase` |
| `ollama_chat.py` | Local Ollama REST client for offline model execution. | `OllamaChatBase` |
| `langchain_agent.py` | LangChain ReAct agent orchestrator for tool calling and reasoning cycles. | `MediaAgent`, `create_media_agent()` |
| `langchain_tools.py` | Modular tool definitions exposed to LangChain and ReAct agents. | Tool decorators & functions |
| `langchain_prompts.py` | System prompt templates and chain configurations for autonomous agents. | Prompt builders |
| `mcp_client.py` | Model Context Protocol (MCP) client connecting to external tool servers. | `MCPClientManager` |
| `voice_pipeline.py` | End-to-end voice query processing and speech-driven playback control pipeline. | `VoicePipeline` |

---

## Model Routing Scheme

```
User Prompt → UnifiedChatModel._get_active_model(model_name)
    ├── "foundry:*"     → FoundryChatBase
    ├── "onnx:*"        → ONNXChatBase
    ├── "hf:*"          → HFChatBase
    ├── "openai:*"      → OpenAICompatChat
    ├── "deepseek:*"    → OpenAICompatChat
    ├── "gemini_cli:*"  → GeminiCliChatBase
    ├── "agy-*"         → AgyChatBase
    ├── "ollama:*"      → OllamaChatBase
    └── "gemini-*"      → GoogleGenerativeAI (GenAI SDK)
```

---

## Usage Example

```python
from core.ai.unified_chat import get_chat_model

chat_model = get_chat_model()

# Single prompt query
response = await chat_model.ask(
    q="Explain breadboard circuit tracing in 2 sentences.",
    model_name="gemini-2.5-flash"
)
print(response)

# Streaming response
async for chunk in chat_model.stream_chat(
    q="Compare DirectML vs CUDA for local ONNX inference.",
    model_name="foundry:qwen2.5-coder-7b"
):
    print(chunk, end="", flush=True)
```
