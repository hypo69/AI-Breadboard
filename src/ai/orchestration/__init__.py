# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard AI -   Init   Module
# =============================================================================
# Description:
#   Модуль основной системы (`__init__`).
#
# Usage Examples:
#
#
# File: __init__.py
# Project: ai-breadboard
# Package: src.ai.orchestration
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-01 13:13:56
# =============================================================================

"""Модуль основной системы (`__init__`)."""

from .hardware import HardwareProfile, probe_hardware
from .capability_registry import AICapability, CapabilityRegistry, ModelDescriptor, Locality
from .policy import PolicyEngine, RoutingPolicy, PrivacyLevel, LocalityPreference
from .discovery import DiscoveryEngine
from .router import AIRouter, AIRequest
from .unified_chat import UnifiedChatModel
from .model_manager import load_unsupported_models, normalize_model_name, get_available_models, actualize_all_models, add_unsupported_model, is_model_supported
from .model_error_hub import ModelErrorCategory, ModelErrorEvent, ModelErrorHub, classify_model_error, get_error_hub, get_model_errors, get_model_health_summary, record_model_error
__all__ = ['HardwareProfile', 'probe_hardware', 'AICapability', 'CapabilityRegistry', 'ModelDescriptor', 'Locality', 'PolicyEngine', 'RoutingPolicy', 'PrivacyLevel', 'LocalityPreference', 'DiscoveryEngine', 'AIRouter', 'AIRequest', 'UnifiedChatModel', 'load_unsupported_models', 'normalize_model_name', 'get_available_models', 'actualize_all_models', 'add_unsupported_model', 'is_model_supported', 'ModelErrorCategory', 'ModelErrorEvent', 'ModelErrorHub', 'classify_model_error', 'get_error_hub', 'record_model_error', 'get_model_errors', 'get_model_health_summary']