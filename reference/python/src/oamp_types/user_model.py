"""User model types for OAMP v1."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExpertiseLevel(str, Enum):
    """Level of expertise in a domain."""

    novice = "novice"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"


class CommunicationProfile(BaseModel):
    """How the user prefers to interact with agents."""

    model_config = ConfigDict(extra="forbid")

    verbosity: float = 0.0
    formality: float = 0.0
    prefers_examples: bool = True
    prefers_explanations: bool = True
    languages: list[str] = Field(default_factory=lambda: ["en"])

    @field_validator("verbosity")
    @classmethod
    def verbosity_in_range(cls, v: float) -> float:
        if v < -1.0 or v > 1.0:
            raise ValueError(f"verbosity must be -1.0 to 1.0, got {v}")
        return v

    @field_validator("formality")
    @classmethod
    def formality_in_range(cls, v: float) -> float:
        if v < -1.0 or v > 1.0:
            raise ValueError(f"formality must be -1.0 to 1.0, got {v}")
        return v


class ExpertiseDomain(BaseModel):
    """The user's demonstrated knowledge in a domain."""

    model_config = ConfigDict(extra="forbid")

    domain: str
    level: ExpertiseLevel
    confidence: float
    evidence_sessions: list[str] = Field(default_factory=list)
    last_observed: Optional[datetime] = None

    @field_validator("domain")
    @classmethod
    def domain_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("domain must not be empty")
        return v

    @field_validator("confidence")
    @classmethod
    def confidence_in_range(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError(f"confidence must be 0.0-1.0, got {v}")
        return v


class Correction(BaseModel):
    """A record of the user correcting the agent's behavior."""

    model_config = ConfigDict(extra="forbid")

    what_agent_did: str
    what_user_wanted: str
    context: Optional[str] = None
    session_id: str
    timestamp: datetime

    @field_validator("what_agent_did")
    @classmethod
    def what_agent_did_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("what_agent_did must not be empty")
        return v

    @field_validator("what_user_wanted")
    @classmethod
    def what_user_wanted_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("what_user_wanted must not be empty")
        return v

    @field_validator("session_id")
    @classmethod
    def session_id_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("session_id must not be empty")
        return v


class StatedPreference(BaseModel):
    """A preference the user has explicitly declared."""

    model_config = ConfigDict(extra="forbid")

    key: str
    value: str
    timestamp: datetime

    @field_validator("key")
    @classmethod
    def key_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("key must not be empty")
        return v


class UserModel(BaseModel):
    """An agent's evolving structured understanding of a user."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    oamp_version: str = "1.0.0"
    type: str = Field(default="user_model", alias="type")
    user_id: str
    model_version: int = Field(default=1, ge=1)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    communication: Optional[CommunicationProfile] = None
    expertise: list[ExpertiseDomain] = Field(default_factory=list)
    corrections: list[Correction] = Field(default_factory=list)
    stated_preferences: list[StatedPreference] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("oamp_version")
    @classmethod
    def oamp_version_must_be_current(cls, v: str) -> str:
        if v != "1.0.0":
            raise ValueError(f"oamp_version must be '1.0.0', got '{v}'")
        return v

    @field_validator("type")
    @classmethod
    def type_must_be_user_model(cls, v: str) -> str:
        if v != "user_model":
            raise ValueError(f"type must be 'user_model', got '{v}'")
        return v

    @field_validator("user_id")
    @classmethod
    def user_id_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("user_id must not be empty")
        return v