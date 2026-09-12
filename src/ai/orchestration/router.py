# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI Capability and Request Router
# =============================================================================
# Description:
#   Dispatches user requests to the optimal AI provider based on capability,
#   system discovery, and policy rules.
#
# File: router.py
# Package: src.ai.orchestration
# Author: hypo69
# Copyright: (c) 2026 hypo69
# =============================================================================

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.logger import logger
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
    system_instruction: str = ""
    temperature: float = 0.0
    max_tokens: int = 0


class AIRouter:
    """Evaluates requests against capabilities and routes to active providers."""

    def __init__(
        self,
        registry: Optional[CapabilityRegistry] = None,
        discovery: Optional[DiscoveryEngine] = None,
    ):
        self.registry = registry or CapabilityRegistry()
        self.discovery = discovery or DiscoveryEngine()

    async def resolve_candidate_models(self, request: AIRequest) -> List[ModelDescriptor]:
        """Resolve ordered list of compliant model descriptors for the request."""
        # Direct override takes precedence
        if request.model_override:
            desc = self.registry.get_model(request.model_override)
            if desc and PolicyEngine.is_compliant(desc, request.policy):
                return [desc]

        candidates = self.registry.find_by_capability(request.capability)
        compliant = [c for c in candidates if PolicyEngine.is_compliant(c, request.policy)]

        # Order candidates: local first if prefer_local, cloud first if prefer_cloud
        if request.policy.locality in (LocalityPreference.PREFER_LOCAL, LocalityPreference.LOCAL_ONLY, LocalityPreference.AUTO):
            compliant.sort(key=lambda m: 0 if m.locality == Locality.LOCAL else 1)
        elif request.policy.locality in (LocalityPreference.PREFER_CLOUD, LocalityPreference.CLOUD_ONLY):
            compliant.sort(key=lambda m: 0 if m.locality == Locality.CLOUD else 1)

        return compliant
