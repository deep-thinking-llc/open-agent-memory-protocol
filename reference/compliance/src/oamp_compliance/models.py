"""Test data models and factories for the compliance test suite."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


def make_knowledge_entry(
    user_id: str = "compliance-test-user",
    category: str = "fact",
    content: str = "Compliance test knowledge entry",
    confidence: float = 0.8,
    session_id: str = "compliance-session",
    tags: list[str] | None = None,
    decay: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    entry_id: str | None = None,
) -> dict[str, Any]:
    """Create a valid KnowledgeEntry dict for testing."""
    entry: dict[str, Any] = {
        "oamp_version": "1.0.0",
        "type": "knowledge_entry",
        "id": entry_id or str(uuid.uuid4()),
        "user_id": user_id,
        "category": category,
        "content": content,
        "confidence": confidence,
        "source": {
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
    if tags:
        entry["tags"] = tags
    if decay:
        entry["decay"] = decay
    if metadata:
        entry["metadata"] = metadata
    return entry


def make_user_model(
    user_id: str = "compliance-test-user",
    model_version: int = 1,
) -> dict[str, Any]:
    """Create a valid UserModel dict for testing."""
    return {
        "oamp_version": "1.0.0",
        "type": "user_model",
        "user_id": user_id,
        "model_version": model_version,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def make_knowledge_store(
    user_id: str = "compliance-test-user",
    entries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create a KnowledgeStore dict for testing."""
    return {
        "oamp_version": "1.0.0",
        "type": "knowledge_store",
        "user_id": user_id,
        "entries": entries or [],
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }