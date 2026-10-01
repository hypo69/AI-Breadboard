# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI - Policy Module
# =============================================================================
# Description:
#   Data privacy constraints for AI requests.
#
# Usage Examples:
#   Python API:
#     from src.ai.orchestration.policy import PrivacyLevel
#
#     service = PrivacyLevel()
#
# File: policy.py
# Project: ai-breadboard
# Package: src.ai.orchestration
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Data privacy constraints for AI requests."""

from enum import StrEnum
from dataclasses import dataclass
from typing import Optional
from .capability_registry import Locality, ModelDescriptor

class PrivacyLevel(StrEnum):
    """Data privacy constraints for AI requests."""
    STRICT = 'strict'
    STANDARD = 'standard'

class LocalityPreference(StrEnum):
    """Locality preference for dispatch."""
    LOCAL_ONLY = 'local_only'
    PREFER_LOCAL = 'prefer_local'
    CLOUD_ONLY = 'cloud_only'
    PREFER_CLOUD = 'prefer_cloud'
    AUTO = 'auto'

@dataclass
class RoutingPolicy:
    """Routing policy configuration for an AI request."""
    locality: LocalityPreference = LocalityPreference.AUTO
    privacy: PrivacyLevel = PrivacyLevel.STANDARD
    max_latency_tier: str = 'high'
    allow_fallback: bool = True

class PolicyEngine:
    """Validates and filters model candidates against request policy constraints."""

    @staticmethod
    def is_compliant(descriptor: ModelDescriptor, policy: RoutingPolicy) -> bool:
        """Check if model descriptor satisfies the routing policy.

        Args:
            descriptor (ModelDescriptor): Model descriptor to validate.
            policy (RoutingPolicy): Routing policy.

        Returns:
            bool: True if compliant, False otherwise.
        """
        if policy.privacy == PrivacyLevel.STRICT and descriptor.locality != Locality.LOCAL:
            return False
        if policy.locality == LocalityPreference.LOCAL_ONLY and descriptor.locality != Locality.LOCAL:
            return False
        if policy.locality == LocalityPreference.CLOUD_ONLY and descriptor.locality != Locality.CLOUD:
            return False
        return True