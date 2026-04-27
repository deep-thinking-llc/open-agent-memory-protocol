"""Business logic for knowledge entry operations."""

from __future__ import annotations

from typing import Any, Optional

from oamp_types import KnowledgeEntry, KnowledgeStore, UserModel, validate_knowledge_entry

from ..api.errors import OampError, not_found, validation_error, forbidden_patch
from ..repository.base import Repository


class KnowledgeService:
    """Service layer for knowledge entry operations."""

    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    async def create(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        """Create a new knowledge entry with validation."""
        errors = validate_knowledge_entry(entry)
        if errors:
            raise validation_error("; ".join(errors))
        return await self.repo.create_knowledge(entry)

    async def get(self, entry_id: str) -> KnowledgeEntry:
        """Get a knowledge entry by ID."""
        entry = await self.repo.get_knowledge(entry_id)
        if entry is None:
            raise not_found("KnowledgeEntry", entry_id)
        return entry

    async def delete(self, entry_id: str) -> None:
        """Delete a knowledge entry."""
        deleted = await self.repo.delete_knowledge(entry_id)
        if not deleted:
            raise not_found("KnowledgeEntry", entry_id)

    async def update(self, entry_id: str, updates: dict[str, Any]) -> KnowledgeEntry:
        """Update allowed fields on a knowledge entry.

        Per spec Section 6.2, only these fields may be patched:
        - confidence
        - decay (specifically decay.last_confirmed)
        - tags

        Fields id, user_id, category, source, content, oamp_version, type are forbidden.
        """
        forbidden = {"id", "user_id", "category", "source", "oamp_version", "type", "content"}
        for field in updates:
            if field in forbidden:
                raise forbidden_patch(field)

        entry = await self.repo.update_knowledge(entry_id, updates)
        if entry is None:
            raise not_found("KnowledgeEntry", entry_id)
        return entry

    async def list_entries(
        self,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[KnowledgeEntry]:
        """List knowledge entries for a user."""
        return await self.repo.list_knowledge(user_id, category, limit, offset)

    async def search(
        self,
        query: str,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[KnowledgeEntry]:
        """Search knowledge entries by text query."""
        return await self.repo.search_knowledge(query, user_id, category, limit, offset)

    async def export_user(
        self,
        user_id: str,
        user_model_service: Any,
    ) -> dict[str, Any]:
        """Export all data for a user.

        Per spec Section 6.4: returns all KnowledgeEntries plus
        the UserModel in a metadata field if present.

        Returns a dict (not KnowledgeStore) because the export response
        adds a non-schema metadata field for the UserModel.
        """
        from datetime import datetime, timezone

        entries = await self.repo.list_knowledge(user_id, limit=10000)

        result: dict[str, Any] = {
            "oamp_version": "1.0.0",
            "type": "knowledge_store",
            "user_id": user_id,
            "entries": [e.model_dump(mode="json", exclude_none=True) for e in entries],
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {},
        }

        # Include the User Model in metadata if present
        user_model = await user_model_service.repo.get_user_model(user_id)
        if user_model is not None:
            result["metadata"]["user_model"] = user_model.model_dump(mode="json", exclude_none=True)

        return result

    async def import_store(self, store: KnowledgeStore) -> int:
        """Import a KnowledgeStore, creating all entries.

        Returns the count of entries imported.
        """
        count = 0
        for entry in store.entries:
            # Validate each entry
            errors = validate_knowledge_entry(entry)
            if errors:
                raise validation_error(f"Entry {entry.id}: {'; '.join(errors)}")

            await self.repo.create_knowledge(entry)
            count += 1
        return count