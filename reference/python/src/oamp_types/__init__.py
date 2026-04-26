"""Open Agent Memory Protocol (OAMP) types for Python."""

from .knowledge import (
    KnowledgeCategory,
    KnowledgeSource,
    KnowledgeDecay,
    KnowledgeEntry,
    KnowledgeStore,
)
from .user_model import (
    ExpertiseLevel,
    CommunicationProfile,
    ExpertiseDomain,
    Correction,
    StatedPreference,
    UserModel,
)
from .validate import (
    validate_knowledge_entry,
    validate_knowledge_store,
    validate_user_model,
)

OAMP_VERSION = "1.0.0"

__all__ = [
    "OAMP_VERSION",
    "KnowledgeCategory",
    "KnowledgeSource",
    "KnowledgeDecay",
    "KnowledgeEntry",
    "KnowledgeStore",
    "ExpertiseLevel",
    "CommunicationProfile",
    "ExpertiseDomain",
    "Correction",
    "StatedPreference",
    "UserModel",
    "validate_knowledge_entry",
    "validate_knowledge_store",
    "validate_user_model",
]