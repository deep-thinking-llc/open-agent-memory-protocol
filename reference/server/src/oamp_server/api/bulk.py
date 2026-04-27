"""Bulk export/import API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from oamp_types import KnowledgeStore

from ..services.knowledge import KnowledgeService


router = APIRouter(tags=["Bulk Operations"])


def _get_service(request: Request) -> KnowledgeService:
    return request.app.state.knowledge_service


@router.get("/export/{user_id}")
async def export_knowledge(
    user_id: str,
    service: KnowledgeService = Depends(_get_service),
) -> dict[str, Any]:
    """Export all knowledge entries for a user as a KnowledgeStore.

    Per spec Section 7.1: MUST support bulk export of all knowledge entries.
    """
    store = await service.export_user(user_id)
    return store.model_dump(mode="json", exclude_none=True)


@router.post("/import")
async def import_knowledge(
    store: KnowledgeStore,
    service: KnowledgeService = Depends(_get_service),
) -> dict[str, Any]:
    """Import a KnowledgeStore, creating all entries.

    Per spec Section 7.2: MUST support bulk import of knowledge entries.
    Returns count of entries imported.
    """
    count = await service.import_store(store)
    return {
        "imported": count,
        "user_id": store.user_id,
    }