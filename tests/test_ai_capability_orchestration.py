# -*- coding: utf-8 -*-
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from core.ai.orchestration import (
    HardwareProfile,
    probe_hardware,
    AICapability,
    CapabilityRegistry,
    ModelDescriptor,
    Locality,
    PolicyEngine,
    RoutingPolicy,
    PrivacyLevel,
    LocalityPreference,
    DiscoveryEngine,
    AIRouter,
    AIRequest,
)
from core.ai.providers.windows_ai import WindowsAIChatBase, probe_windows_ai_components
from core.ai.providers.gemini import GeminiChatBase


def test_hardware_probe():
    """Verify hardware profile structure and fallback values."""
    profile = probe_hardware()
    assert isinstance(profile, HardwareProfile)
    assert profile.cpu_cores >= 1
    assert isinstance(profile.has_cuda, bool)
    assert isinstance(profile.has_directml, bool)
    data = profile.to_dict()
    assert "cpu_cores" in data
    assert "ram_gb" in data


def test_capability_registry():
    """Verify capability registry registration and capability query."""
    registry = CapabilityRegistry()
    chat_models = registry.find_by_capability(AICapability.CHAT)
    assert len(chat_models) > 0

    ocr_models = registry.find_by_capability(AICapability.OCR)
    assert any("ocr" in m.id for m in ocr_models)

    local_chat = registry.find_by_capability(AICapability.CHAT, locality=Locality.LOCAL)
    assert all(m.locality == Locality.LOCAL for m in local_chat)


def test_policy_engine_privacy_strict():
    """Verify PolicyEngine forbids cloud models when privacy is STRICT."""
    cloud_model = ModelDescriptor(
        id="gemini:test",
        provider="gemini",
        capabilities={AICapability.CHAT},
        locality=Locality.CLOUD,
    )
    local_model = ModelDescriptor(
        id="foundry:test",
        provider="foundry",
        capabilities={AICapability.CHAT},
        locality=Locality.LOCAL,
    )

    strict_policy = RoutingPolicy(privacy=PrivacyLevel.STRICT)
    assert PolicyEngine.is_compliant(cloud_model, strict_policy) is False
    assert PolicyEngine.is_compliant(local_model, strict_policy) is True


def test_policy_engine_locality():
    """Verify PolicyEngine enforces local_only and cloud_only constraints."""
    local_model = ModelDescriptor(
        id="ollama:test",
        provider="ollama",
        capabilities={AICapability.CHAT},
        locality=Locality.LOCAL,
    )
    cloud_model = ModelDescriptor(
        id="gemini:test",
        provider="gemini",
        capabilities={AICapability.CHAT},
        locality=Locality.CLOUD,
    )

    local_policy = RoutingPolicy(locality=LocalityPreference.LOCAL_ONLY)
    assert PolicyEngine.is_compliant(local_model, local_policy) is True
    assert PolicyEngine.is_compliant(cloud_model, local_policy) is False

    cloud_policy = RoutingPolicy(locality=LocalityPreference.CLOUD_ONLY)
    assert PolicyEngine.is_compliant(local_model, cloud_policy) is False
    assert PolicyEngine.is_compliant(cloud_model, cloud_policy) is True


@pytest.mark.asyncio
async def test_ai_router_resolution():
    """Verify AIRouter resolves compliant candidate models."""
    router = AIRouter()

    # Request with strict privacy
    req = AIRequest(
        prompt="Classify this document locally",
        capability=AICapability.CHAT,
        policy=RoutingPolicy(privacy=PrivacyLevel.STRICT),
    )
    candidates = await router.resolve_candidate_models(req)
    assert len(candidates) > 0
    assert all(c.locality == Locality.LOCAL for c in candidates)


def test_windows_ai_probe_structure():
    """Verify Windows AI probe returns structured result without raising errors."""
    res = probe_windows_ai_components()
    assert isinstance(res, dict)
    assert "available" in res
    assert "components" in res
    assert isinstance(res["components"], list)


@pytest.mark.asyncio
async def test_windows_ai_chat_graceful_fallback():
    """Verify WindowsAIChatBase provides graceful fallback when uninstalled."""
    provider = WindowsAIChatBase(model_id="phi-silica")
    with patch.object(WindowsAIChatBase, "is_available", return_value=False):
        response = await provider.ask("Hello")
        assert "Windows AI Components are not installed" in response
