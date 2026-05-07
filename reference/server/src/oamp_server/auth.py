"""Portable v1.3 grant parsing helpers for the reference server."""

from __future__ import annotations

from typing import Literal

import jwt
from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field

from .api.errors import unauthorized
from .config import Settings


class AgentGrantClaims(BaseModel):
    """Portable v1.3 grant claims carried in JWT or OAMP-Grant headers."""

    model_config = ConfigDict(extra="forbid")

    sub: str
    oamp_agent_id: str
    oamp_grant_id: str
    oamp_read_labels: list[str] = Field(default_factory=list)
    oamp_write_labels: list[str] = Field(default_factory=list)
    oamp_sensitivity_max: Literal["public", "internal", "confidential", "restricted"]
    oamp_export_full: bool = False
    exp: int | None = None


def decode_grant_token(token: str, settings: Settings) -> AgentGrantClaims:
    """Decode and validate a signed grant token."""
    try:
        payload = jwt.decode(
            token,
            settings.governance_grant_secret,
            algorithms=[settings.governance_grant_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise unauthorized(f"invalid grant token: {exc}") from exc
    return AgentGrantClaims.model_validate(payload)


def extract_grant(request: Request, settings: Settings) -> AgentGrantClaims | None:
    """Extract a v1.3 grant from Authorization or OAMP-Grant headers."""
    raw_grant = request.headers.get("OAMP-Grant")
    if raw_grant:
        return decode_grant_token(raw_grant, settings)

    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return decode_grant_token(auth.removeprefix("Bearer ").strip(), settings)

    return None
