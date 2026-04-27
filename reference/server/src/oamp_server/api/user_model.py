"""User model API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from oamp_types import UserModel

from ..services.user_model import UserModelService


router = APIRouter(tags=["User Model"])


def _get_service(request: Request) -> UserModelService:
    return request.app.state.user_model_service


@router.post("/user-model")
async def create_or_update_user_model(
    model: UserModel,
    response: Response,
    service: UserModelService = Depends(_get_service),
) -> dict[str, Any]:
    """Store or update a UserModel.

    Returns 201 for new models, 200 for updates.
    Returns 409 if model_version <= stored version.
    """
    created, result = await service.create_or_update(model)
    if created:
        response.status_code = 201
    return result.model_dump(mode="json", exclude_none=True)


@router.get("/user-model/{user_id}")
async def get_user_model(
    user_id: str,
    service: UserModelService = Depends(_get_service),
) -> dict[str, Any]:
    """Retrieve a UserModel by user_id."""
    model = await service.get(user_id)
    return model.model_dump(mode="json", exclude_none=True)


@router.delete("/user-model/{user_id}", status_code=204)
async def delete_user_model(
    user_id: str,
    service: UserModelService = Depends(_get_service),
) -> None:
    """Delete a UserModel and all associated KnowledgeEntries."""
    await service.delete(user_id)