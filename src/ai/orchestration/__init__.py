# -*- coding: utf-8 -*-
from .hardware import HardwareProfile, probe_hardware
from .capability_registry import AICapability, CapabilityRegistry, ModelDescriptor, Locality
from .policy import PolicyEngine, RoutingPolicy, PrivacyLevel, LocalityPreference
from .discovery import DiscoveryEngine
from .router import AIRouter, AIRequest
from .unified_chat import UnifiedChatModel
from .model_manager import (
    load_unsupported_models,
    normalize_model_name,
    get_available_models,
    actualize_all_models,
    add_unsupported_model,
    is_model_supported,
)

from .model_error_hub import (
    ModelErrorCategory,
    ModelErrorEvent,
    ModelErrorHub,
    classify_model_error,
    get_error_hub,
    get_model_errors,
    get_model_health_summary,
    record_model_error,
)

__all__ = [
    "HardwareProfile",
    "probe_hardware",
    "AICapability",
    "CapabilityRegistry",
    "ModelDescriptor",
    "Locality",
    "PolicyEngine",
    "RoutingPolicy",
    "PrivacyLevel",
    "LocalityPreference",
    "DiscoveryEngine",
    "AIRouter",
    "AIRequest",
    "UnifiedChatModel",
    "load_unsupported_models",
    "normalize_model_name",
    "get_available_models",
    "actualize_all_models",
    "add_unsupported_model",
    "is_model_supported",
    "ModelErrorCategory",
    "ModelErrorEvent",
    "ModelErrorHub",
    "classify_model_error",
    "get_error_hub",
    "record_model_error",
    "get_model_errors",
    "get_model_health_summary",
]
