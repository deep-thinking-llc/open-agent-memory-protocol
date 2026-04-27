"""Business logic for user model operations."""

from __future__ import annotations

from oamp_types import UserModel, validate_user_model

from ..api.errors import not_found, validation_error, version_conflict
from ..repository.base import Repository


class UserModelService:
    """Service layer for user model operations."""

    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    async def create_or_update(self, model: UserModel) -> tuple[bool, UserModel]:
        """Create or update a user model with version enforcement.

        Per spec Section 5.1, model_version must be monotonically increasing.

        Returns (created, model) where created is True if this was a new model.
        """
        # Validate the model
        errors = validate_user_model(model)
        if errors:
            raise validation_error("; ".join(errors))

        existing = await self.repo.get_user_model(model.user_id)

        if existing is None:
            # New model
            result = await self.repo.create_user_model(model)
            return (True, result)
        else:
            # Update — enforce model_version monotonicity
            if model.model_version <= existing.model_version:
                raise version_conflict(existing.model_version, model.model_version)
            result = await self.repo.update_user_model(model)
            return (False, result)

    async def get(self, user_id: str) -> UserModel:
        """Get a user model by user_id."""
        model = await self.repo.get_user_model(user_id)
        if model is None:
            raise not_found("UserModel", user_id)
        return model

    async def delete(self, user_id: str) -> None:
        """Delete a user model and all associated knowledge entries.

        Per spec Section 6.3: MUST delete the complete User Model and
        all associated Knowledge Entries for the user.
        """
        deleted = await self.repo.delete_user_model(user_id)
        if not deleted:
            raise not_found("UserModel", user_id)