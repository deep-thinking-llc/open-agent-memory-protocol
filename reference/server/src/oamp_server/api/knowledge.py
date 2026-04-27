"""Knowledge entry API endpoints."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Request
from oamp_types import KnowledgeEntry

from ..services.knowledge import KnowledgeService


router = APIRouter(tags=["Knowledge"])


def _get_service(request: Request) -> KnowledgeService:
    return request.app.state.knowledge_service


@router.post("/knowledge", status_code=201)
async def create_knowledge(
    entry: KnowledgeEntry,
    service: KnowledgeService = Depends(_get_service),
) -> dict[str, Any]:
    """Store a new KnowledgeEntry."""
    result = await service.create(entry)
    return result.model_dump(mode="json", exclude_none=True)


# ── Search must come before {entry_id} to avoid path parameter collision ──


@router.get("/knowledge/search")
async def search_knowledge(
    q: str,
    user_id: str,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    service: KnowledgeService = Depends(_get_service),
) -> list[dict[str, Any]]:
    """Search knowledge entries by text query, scoped to a user."""
    entries = await service.search(q, user_id, category, limit, offset)
    return [e.model_dump(mode="json", exclude_none=True) for e in entries]


@router.get("/knowledge")
async def list_knowledge(
    user_id: str,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    service: KnowledgeService = Depends(_get_service),
) -> list[dict[str, Any]]:
    """List knowledge entries for a user, with optional category filter."""
    entries = await service.list_entries(user_id, category, limit, offset)
    return [e.model_dump(mode="json", exclude_none=True) for e in entries]


@router.get("/knowledge/{entry_id}")
async def get_knowledge(
    entry_id: str,
    service: KnowledgeService = Depends(_get_service),
) -> dict[str, Any]:
    """Retrieve a KnowledgeEntry by ID."""
    entry = await service.get(entry_id)
    return entry.model_dump(mode="json", exclude_none=True)


@router.delete("/knowledge/{entry_id}", status_code=204)
async def delete_knowledge(
    entry_id: str,
    service: KnowledgeService = Depends(_get_service),
) -> None:
    """Delete a KnowledgeEntry."""
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