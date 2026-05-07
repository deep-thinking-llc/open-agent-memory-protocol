"""Knowledge entry and store types for OAMP v1.x."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class KnowledgeCategory(str, Enum):
    """Category of a knowledge entry."""

    fact = "fact"
    preference = "preference"
    pattern = "pattern"
    correction = "correction"


class KnowledgeSource(BaseModel):
    """Provenance information for a knowledge entry."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    agent_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("session_id")
    @classmethod
    def session_id_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("source.session_id must not be empty")
        return v


class KnowledgeDecay(BaseModel):
    """Temporal decay parameters for confidence.

    If half_life_days is None (or null), no decay is applied.
    """

    model_config = ConfigDict(extra="forbid")

    half_life_days: Optional[float] = None
    last_confirmed: Optional[datetime] = None

    @field_validator("half_life_days")
    @classmethod
    def half_life_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("half_life_days must be positive")
        return v


class GovernanceHandling(BaseModel):
    """Surface-specific handling hints for governed memory."""

    model_config = ConfigDict(extra="forbid")

    retrieval: Optional[Literal["governed", "ungoverned"]] = None
    export: Optional[Literal["governed", "ungoverned"]] = None
    stream: Optional[Literal["governed", "ungoverned"]] = None


class Governance(BaseModel):
    """Standard governed-memory metadata."""

    model_config = ConfigDict(extra="forbid")

    sensitivity_class: Literal["public", "internal", "confidential", "restricted"]
    labels: list[str] = Field(default_factory=list)
    handling: Optional[GovernanceHandling] = None


class ProvenanceSource(BaseModel):
    """Extended lineage record for multi-source provenance."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    timestamp: datetime
    agent_id: Optional[str] = None
    turn_id: Optional[str] = None

    @field_validator("session_id")
    @classmethod
    def session_id_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("provenance.sources[].session_id must not be empty")
        return v


class Provenance(BaseModel):
    """Extended provenance metadata for synthesized or multi-source memories."""

    model_config = ConfigDict(extra="forbid")

    sources: list[ProvenanceSource]
    derived: Optional[bool] = None

    @field_validator("sources")
    @classmethod
    def sources_not_empty(cls, v: list[ProvenanceSource]) -> list[ProvenanceSource]:
        if not v:
            raise ValueError("provenance.sources must not be empty")
        return v


class KnowledgeEntry(BaseModel):
    """A discrete piece of information an agent has learned about a user."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    oamp_version: str = "1.0.0"
    type: str = Field(default="knowledge_entry", alias="type")
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    category: KnowledgeCategory
    content: str
    confidence: float
    source: KnowledgeSource
    provenance: Optional[Provenance] = None
    governance: Optional[Governance] = None
    decay: Optional[KnowledgeDecay] = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("oamp_version")
    @classmethod
    def oamp_version_must_be_current(cls, v: str) -> str:
        if v not in {"1.0.0", "1.1.0", "1.2.0", "1.3.0"}:
            raise ValueError(f"oamp_version must be one of '1.0.0', '1.1.0', '1.2.0', or '1.3.0', got '{v}'")
        return v

    @field_validator("type")
    @classmethod
    def type_must_be_knowledge_entry(cls, v: str) -> str:
        if v != "knowledge_entry":
            raise ValueError(f"type must be 'knowledge_entry', got '{v}'")
        return v

    @field_validator("user_id")
    @classmethod
    def user_id_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("user_id must not be empty")
        return v

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("content must not be empty")
        return v

    @field_validator("confidence")
    @classmethod
    def confidence_in_range(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError(f"confidence must be 0.0-1.0, got {v}")
        return v


class KnowledgeStore(BaseModel):
    """A collection of knowledge entries for bulk export/import."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    oamp_version: str = "1.0.0"
    type: str = Field(default="knowledge_store", alias="type")
    user_id: str
    entries: list[KnowledgeEntry] = Field(default_factory=list)
    exported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    agent_id: Optional[str] = None

    @field_validator("oamp_version")
    @classmethod
    def oamp_version_must_be_current(cls, v: str) -> str:
        if v not in {"1.0.0", "1.1.0", "1.2.0", "1.3.0"}:
            raise ValueError(f"oamp_version must be one of '1.0.0', '1.1.0', '1.2.0', or '1.3.0', got '{v}'")
        return v

    @field_validator("type")
    @classmethod
    def type_must_be_knowledge_store(cls, v: str) -> str:
        if v != "knowledge_store":
            raise ValueError(f"type must be 'knowledge_store', got '{v}'")
        return v

    @field_validator("user_id")
    @classmethod
    def user_id_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("user_id must not be empty")
        return v
