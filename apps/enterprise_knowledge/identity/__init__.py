"""Управление идентичностью сотрудников."""

from apps.enterprise_knowledge.identity.registry import IdentityRegistry
from apps.enterprise_knowledge.identity.resolution import IdentityResolver
from apps.enterprise_knowledge.identity.aliases import AliasManager
from apps.enterprise_knowledge.identity.verification import IdentityVerifier

__all__ = ["IdentityRegistry", "IdentityResolver", "AliasManager", "IdentityVerifier"]
