# Orchestration Layer (`core/ai/orchestration`)

## Overview
The **Orchestration Layer** provides unified routing, hardware acceleration detection, and dynamic provider capability dispatch across local and cloud backends.

---

## Core Components

```
                    ┌─────────────────────────┐
                    │       AIRouter          │
                    └───────────┬─────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
┌──────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│ DiscoveryEngine  │  │CapabilityRegistry │  │   PolicyEngine    │
│ (Hardware & Port)│  │ (Chat/Vision/OCR) │  │(Privacy & Locality│
└──────────────────┘  └───────────────────┘  └───────────────────┘
```

1. **`hardware.py`**: Probes CPU, GPU (CUDA, DirectML), NPU, RAM/VRAM, and Windows Copilot+ hardware acceleration.
2. **`discovery.py`**: Probes local daemons (Foundry Local on `54837`, Ollama on `11434`), Windows AI components, and cloud API keys.
3. **`capability_registry.py`**: Maps models and providers to standardized `AICapability` categories (`chat`, `vision`, `ocr`, `embedding`, `code`, `image_generation`).
4. **`policy.py`**: Enforces privacy rules (`strict` vs `standard`) and execution locality (`local_only`, `prefer_local`, `cloud_only`).
5. **`router.py`**: Resolves `AIRequest` instances to compliant execution backends with seamless fallback.
6. **`unified_chat.py`**: High-level unified chat interface for FastAPI routes and CLI agents.

---

## Usage Example
```python
from core.ai.orchestration import AIRouter, AIRequest, AICapability, RoutingPolicy, PrivacyLevel

router = AIRouter()

# Request strictly local execution
req = AIRequest(
    prompt="Summarize the file locally.",
    capability=AICapability.CHAT,
    policy=RoutingPolicy(privacy=PrivacyLevel.STRICT),
)

candidates = await router.resolve_candidate_models(req)
print("Selected backend candidates:", [c.id for c in candidates])
```
