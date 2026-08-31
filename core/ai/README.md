# `core.ai` Module — AI Model Integrations & Orchestration

## Purpose
The `core.ai` package encapsulates all interaction logic with neural network models, provider backends, and ReAct agent workflows.

---

## Subsystems & Architecture

```text
core/ai/
├── providers/                 # Modular AI backends & transports
│   ├── base.py                # BaseChatProvider interface
│   ├── gemini/                # Google Gemini GenAI SDK, RAG & key rotation
│   ├── ollama/                # Ollama Chat adapter & HTTP Client
│   ├── foundry/               # Microsoft AI Foundry Chat & Client
│   ├── onnx/                  # ONNX Runtime DirectML/CUDA
│   ├── huggingface/           # Hugging Face Transformers
│   ├── openai/                # OpenAI-compatible transport (DeepSeek, Groq, LM Studio)
│   ├── gemini_cli/            # Google Gemini CLI terminal agent
│   └── agy/                   # Google Antigravity AGY SDK
│
├── orchestration/             # Routing & Model pool management
│   ├── model_manager.py       # Model discovery, health caching & blacklist
│   └── unified_chat.py        # Single UnifiedChatModel routing facade
│
├── agents/                    # Autonomous ReAct agents, tools & MCP
│   ├── agent.py               # MediaSearchAgent orchestrator
│   ├── prompts.py             # System prompt templates
│   ├── tools.py               # Agent tools
│   └── mcp_client.py          # Model Context Protocol client manager
│
└── voice/                     # Speech & Voice pipelines
    ├── pipeline.py            # Voiceover chunking & TTS generation pipeline
    └── converters/            # GGUF / ONNX audio model converters
```

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
from core.ai import UnifiedChatModel

chat_model = UnifiedChatModel(
    api_key_names=["GEMINI_API_KEY"],
    system_instruction="You are a helpful assistant.",
    foundry_model_id="qwen2.5-coder-7b",
)

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
