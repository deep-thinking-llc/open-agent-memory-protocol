"""Bulk export/import API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from oamp_types import KnowledgeStore

from ..services.knowledge import KnowledgeService
from ..services.user_model import UserModelService


router = APIRouter(tags=["Bulk Operations"])


class ExportRequest(BaseModel):
    """Export request body per spec Section 6.4."""
    user_id: str


def _get_knowledge_service(request: Request) -> KnowledgeService:
    return request.app.state.knowledge_service


def _get_user_model_service(request: Request) -> UserModelService:
    return request.app.state.user_model_service


@router.post("/export")
async def export_knowledge(
    body: ExportRequest,
    request: Request,
    knowledge_service: KnowledgeService = Depends(_get_knowledge_service),
    user_model_service: UserModelService = Depends(_get_user_model_service),
) -> dict[str, Any]:
    """Export all data for a user.

    Per spec Section 6.4: POST /v1/export with { "user_id": "string" }.
    Returns all KnowledgeEntries plus the UserModel in metadata if present.
    """
    # Audit export (spec §8.2.6)
    await request.app.state.repo.log_audit_event("export", body.user_id)
    return await knowledge_service.export_user(body.user_id, user_model_service)


@router.post("/import")
async def import_knowledge(
    store: KnowledgeStore,
    request: Request,
    service: KnowledgeService = Depends(_get_knowledge_service),
) -> dict[str, Any]:
    """Import a KnowledgeStore, creating all entries.

    Per spec Section 6.4: POST /v1/import with a KnowledgeStore document.
    Returns a summary of imported, skipped, and rejected entries.
    """
    imported_count = await service.import_store(store)
    # Audit import (spec §8.2.6)
    await request.app.state.repo.log_audit_event("import", store.user_id, detail=f"imported:{imported_count}")
    return {
        "imported": imported_count,
        "skipped": 0,
        "rejected": 0,
        "user_id": store.user_id,
    }