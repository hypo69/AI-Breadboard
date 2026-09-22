"""Накопительная платформа корпоративных знаний."""

from apps.enterprise_knowledge.engine import EnterpriseKnowledgeEngine
from apps.enterprise_knowledge.storage import KnowledgeStore

__all__ = ["EnterpriseKnowledgeEngine", "KnowledgeStore"]
