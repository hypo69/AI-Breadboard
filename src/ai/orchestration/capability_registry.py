# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Capability Registry and Metadata Store
# =============================================================================
# Description:
#   Maintains the unified mapping between AI capabilities (chat, vision,
#   ocr, embedding, code) and registered provider models.
#
# File: capability_registry.py
# Package: src.ai.orchestration
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================

from enum import StrEnum
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field


class AICapability(StrEnum):
    """Standard capability identifiers for AI workloads."""
    CHAT = "chat"
    VISION = "vision"
    OCR = "ocr"
    EMBEDDING = "embedding"
    CODE = "code"
    IMAGE_GENERATION = "image_generation"
    AUDIO_TTS = "audio_tts"
    AUDIO_STT = "audio_stt"


class Locality(StrEnum):
    """Execution locality of an AI model."""
    LOCAL = "local"
    CLOUD = "cloud"
    HYBRID = "hybrid"


@dataclass
class ModelDescriptor:
    """Metadata descriptor for a registered model."""
    id: str
    provider: str
    capabilities: Set[AICapability] = field(default_factory=set)
    locality: Locality = Locality.LOCAL
    latency_tier: str = "normal"  # "low", "normal", "high"
    requires_api_key: bool = False
    context_window: int = 8192
    hardware_target: str = "cpu"  # "cpu", "gpu", "npu"


class CapabilityRegistry:
    """Central registry mapping AI capabilities to registered models."""

    def __init__(self):
        """Initialize empty capability registry."""
        self._models: Dict[str, ModelDescriptor] = {}
        self._seed_default_descriptors()

    def _seed_default_descriptors(self) -> None:
        """Seed registry with known model descriptors across providers."""
        # Windows AI
        self.register_model(ModelDescriptor(
            id="windows-ai:phi-silica",
            provider="windows_ai",
            capabilities={AICapability.CHAT, AICapability.CODE},
            locality=Locality.LOCAL,
            latency_tier="low",
            hardware_target="npu",
        ))
        self.register_model(ModelDescriptor(
            id="windows-ai:ocr",
            provider="windows_ai",
            capabilities={AICapability.OCR},
            locality=Locality.LOCAL,
            latency_tier="low",
            hardware_target="npu",
        ))

        # Foundry Local
        self.register_model(ModelDescriptor(
            id="foundry:phi-4",
            provider="foundry",
            capabilities={AICapability.CHAT, AICapability.CODE},
            locality=Locality.LOCAL,
            latency_tier="low",
            hardware_target="gpu",
        ))
        self.register_model(ModelDescriptor(
            id="foundry:qwen2.5-7b",
            provider="foundry",
            capabilities={AICapability.CHAT, AICapability.CODE},
            locality=Locality.LOCAL,
            latency_tier="normal",
            hardware_target="gpu",
        ))

        # Ollama
        self.register_model(ModelDescriptor(
            id="ollama:llama3.1",
            provider="ollama",
            capabilities={AICapability.CHAT, AICapability.CODE},
            locality=Locality.LOCAL,
            latency_tier="normal",
            hardware_target="gpu",
        ))

        # Gemini Cloud
        self.register_model(ModelDescriptor(
            id="gemini:gemini-3.7-flash",
            provider="gemini",
            capabilities={AICapability.CHAT, AICapability.VISION, AICapability.CODE},
            locality=Locality.CLOUD,
            latency_tier="low",
            requires_api_key=True,
        ))
        self.register_model(ModelDescriptor(
            id="gemini:gemini-2.5-pro",
            provider="gemini",
            capabilities={AICapability.CHAT, AICapability.VISION, AICapability.CODE},
            locality=Locality.CLOUD,
            latency_tier="normal",
            requires_api_key=True,
        ))

    def register_model(self, descriptor: ModelDescriptor) -> None:
        """Register a model descriptor into the capability registry."""
        self._models[descriptor.id] = descriptor

    def get_model(self, model_id: str) -> Optional[ModelDescriptor]:
        """Retrieve model descriptor by ID."""
        return self._models.get(model_id)

    def find_by_capability(
        self,
        capability: AICapability,
        locality: Optional[Locality] = None,
    ) -> List[ModelDescriptor]:
        """Find models supporting a specific capability with optional locality filter."""
        matches = []
        for model in self._models.values():
            if capability in model.capabilities:
                if locality is None or model.locality == locality:
                    matches.append(model)
        return matches

    def list_all(self) -> List[ModelDescriptor]:
        """List all registered model descriptors."""
        return list(self._models.values())
