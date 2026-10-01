# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Router Module
# =============================================================================
# Description:
#   Represents a unified AI capability request.
#
# Usage Examples:
#   Python API:
#     from src.ai.orchestration.router import AIRequest
#
#     service = AIRequest()
#
# File: router.py
# Project: ai-breadboard
# Package: src.ai.orchestration
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Represents a unified AI capability request."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from logger import logger
from .capability_registry import AICapability, CapabilityRegistry, ModelDescriptor, Locality
from .policy import PolicyEngine, RoutingPolicy, LocalityPreference, PrivacyLevel
from .discovery import DiscoveryEngine

@dataclass
class AIRequest:
    """Represents a unified AI capability request."""
    prompt: str
    capability: AICapability = AICapability.CHAT
    policy: RoutingPolicy = field(default_factory=RoutingPolicy)
    model_override: Optional[str] = None
    system_instruction: str = ''
    temperature: float = 0.0
    max_tokens: int = 0

class AIRouter:
    """Evaluates requests against capabilities and routes to active providers."""

    def __init__(self, registry: Optional[CapabilityRegistry]=None, discovery: Optional[DiscoveryEngine]=None):
        self.registry = registry or CapabilityRegistry()
        self.discovery = discovery or DiscoveryEngine()

    async def resolve_candidate_models(self, request: AIRequest) -> List[ModelDescriptor]:
        """Resolve ordered list of compliant model descriptors for the request."""
        if request.model_override:
            desc = self.registry.get_model(request.model_override)
            if desc and PolicyEngine.is_compliant(desc, request.policy):
                return [desc]
        candidates = self.registry.find_by_capability(request.capability)
        compliant = [c for c in candidates if PolicyEngine.is_compliant(c, request.policy)]
        if request.policy.locality in (LocalityPreference.PREFER_LOCAL, LocalityPreference.LOCAL_ONLY, LocalityPreference.AUTO):
            compliant.sort(key=lambda m: 0 if m.locality == Locality.LOCAL else 1)
        elif request.policy.locality in (LocalityPreference.PREFER_CLOUD, LocalityPreference.CLOUD_ONLY):
            compliant.sort(key=lambda m: 0 if m.locality == Locality.CLOUD else 1)
        return compliant