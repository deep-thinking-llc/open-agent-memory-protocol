"""Knowledge entry API endpoints."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Request
from oamp_types import KnowledgeEntry

from ..api.errors import OampError, duplicate_id, not_found, validation_error, forbidden_patch
from ..services.knowledge import KnowledgeService


router = APIRouter(tags=["Knowledge"])


def _get_service(request: Request) -> KnowledgeService:
    return request.app.state.knowledge_service


@router.post("/knowledge", status_code=201)
async def create_knowledge(
    entry: KnowledgeEntry,
    service: KnowledgeService = Depends(_get_service),
) -> dict[str, Any]:
    """Store a new KnowledgeEntry.

    Per spec Section 6.2: POST /v1/knowledge.
    201 Created on success, 400 Bad Request on validation failure.
    409 Conflict if entry ID already exists.
    """
    # Check for duplicate ID
    existing = await service.repo.get_knowledge(entry.id)
    if existing is not None:
        raise duplicate_id("KnowledgeEntry", entry.id)

    result = await service.create(entry)
    return result.model_dump(mode="json", exclude_none=True)


@router.get("/knowledge")
async def list_or_search_knowledge(
    user_id: str,
    query: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    service: KnowledgeService = Depends(_get_service),
) -> list[dict[str, Any]]:
    """List or search knowledge entries for a user.

    Per spec Section 6.2 and 6.6:
    - Without `query`: list entries (with optional category filter)
    - With `query`: full-text search scoped to user_id

    Supports `?limit=` and `?offset=` pagination.
    """
    # Validate pagination bounds
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    if query:
        entries = await service.search(query, user_id, category, limit, offset)
    else:
        entries = await service.list_entries(user_id, category, limit, offset)

    return [e.model_dump(mode="json", exclude_none=True) for e in entries]


@router.get("/knowledge/{entry_id}")
async def get_knowledge(
    entry_id: str,
    service: KnowledgeService = Depends(_get_service),
) -> dict[str, Any]:
    """Retrieve a KnowledgeEntry by ID.

    Per spec Section 6.2: 200 OK or 404 Not Found.
    """
    entry = await service.get(entry_id)
    return entry.model_dump(mode="json", exclude_none=True)


@router.delete("/knowledge/{entry_id}", status_code=204)
async def delete_knowledge(
    entry_id: str,
    service: KnowledgeService = Depends(_get_service),
) -> None:
    """Delete a KnowledgeEntry.

    Per spec Section 6.2: 204 No Content. MUST permanently delete (not soft-delete).
    """
    await service.delete(entry_id)


@router.patch("/knowledge/{entry_id}")
async def update_knowledge(
    entry_id: str,
    updates: dict[str, Any],
    service: KnowledgeService = Depends(_get_service),
) -> dict[str, Any]:
    """Update allowed fields on a KnowledgeEntry.

    Per spec Section 6.2: only confidence, decay.last_confirmed, and tags
    may be patched. Fields id, user_id, category, and source are forbidden.
    """
    entry = await service.update(entry_id, updates)
    return entry.model_dump(mode="json", exclude_none=True)