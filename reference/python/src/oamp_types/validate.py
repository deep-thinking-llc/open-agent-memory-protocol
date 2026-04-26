"""Validation functions for OAMP types.

These functions perform semantic validation beyond what Pydantic
field validators cover. They return a list of error strings;
an empty list means the document is valid.

This is useful for validating data that bypasses Pydantic's
construction validation (e.g., data loaded via model_construct
or imported from untrusted sources).
"""

from __future__ import annotations

import re

from .knowledge import KnowledgeEntry, KnowledgeStore
from .user_model import UserModel

# Loose UUID v4 pattern for validation
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def validate_knowledge_entry(entry: KnowledgeEntry) -> list[str]:
    """Validate a KnowledgeEntry, returning a list of error strings."""
    errors: list[str] = []

    if not entry.oamp_version:
        errors.append("oamp_version is required")
    elif entry.oamp_version != "1.0.0":
        errors.append(f"oamp_version must be '1.0.0', got '{entry.oamp_version}'")

    if entry.type != "knowledge_entry":
        errors.append(f"type must be 'knowledge_entry', got '{entry.type}'")

    if not entry.id:
        errors.append("id is required")
    elif not _UUID_RE.match(entry.id):
        errors.append(f"id must be a valid UUID v4, got '{entry.id}'")

    if not entry.user_id:
        errors.append("user_id is required")

    if not entry.content:
        errors.append("content is required")

    if entry.confidence < 0.0 or entry.confidence > 1.0:
        errors.append(f"confidence must be 0.0-1.0, got {entry.confidence}")

    if not entry.source.session_id:
        errors.append("source.session_id is required")

    return errors


def validate_knowledge_store(store: KnowledgeStore) -> list[str]:
    """Validate a KnowledgeStore, returning a list of error strings."""
    errors: list[str] = []

    if not store.oamp_version:
        errors.append("oamp_version is required")
    elif store.oamp_version != "1.0.0":
        errors.append(f"oamp_version must be '1.0.0', got '{store.oamp_version}'")

    if store.type != "knowledge_store":
        errors.append(f"type must be 'knowledge_store', got '{store.type}'")

    if not store.user_id:
        errors.append("user_id is required")

    for i, entry in enumerate(store.entries):
        entry_errors = validate_knowledge_entry(entry)
        for err in entry_errors:
            errors.append(f"entries[{i}]: {err}")

    return errors


def validate_user_model(model: UserModel) -> list[str]:
    """Validate a UserModel, returning a list of error strings."""
    errors: list[str] = []

    if not model.oamp_version:
        errors.append("oamp_version is required")
    elif model.oamp_version != "1.0.0":
        errors.append(f"oamp_version must be '1.0.0', got '{model.oamp_version}'")

    if model.type != "user_model":
        errors.append(f"type must be 'user_model', got '{model.type}'")

    if not model.user_id:
        errors.append("user_id is required")

    if model.model_version < 1:
        errors.append(f"model_version must be >= 1, got {model.model_version}")

    # Validate communication ranges
    if model.communication is not None:
        comm = model.communication
        if comm.verbosity < -1.0 or comm.verbosity > 1.0:
            errors.append(f"verbosity must be -1.0 to 1.0, got {comm.verbosity}")
        if comm.formality < -1.0 or comm.formality > 1.0:
            errors.append(f"formality must be -1.0 to 1.0, got {comm.formality}")

    # Validate expertise confidence
    for i, exp in enumerate(model.expertise):
        if exp.confidence < 0.0 or exp.confidence > 1.0:
            errors.append(
                f"expertise[{i}].confidence must be 0.0-1.0, got {exp.confidence}"
            )

    return errors