"""Business logic for knowledge entry operations."""

from __future__ import annotations

from typing import Any

from oamp_types import KnowledgeEntry, KnowledgeStore, validate_knowledge_entry

from ..api.errors import OampError, not_found, validation_error, forbidden_patch
from ..repository.base import Repository


class KnowledgeService:
    """Service layer for knowledge entry operations."""

    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    async def create(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        """Create a new knowledge entry with validation."""
        # Validate the entry
        errors = validate_knowledge_entry(entry)
        if errors:
            raise validation_error("; ".join(errors))

        # Store it
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

        Fields id, user_id, category, source are forbidden.
        """
        # Check for forbidden fields
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
        category: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[KnowledgeEntry]:
        """List knowledge entries for a user."""
        return await self.repo.list_knowledge(user_id, category, limit, offset)

    async def search(
        self,
        query: str,
        user_id: str,
        category: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[KnowledgeEntry]:
        """Search knowledge entries by text query."""
        return await self.repo.search_knowledge(query, user_id, category, limit, offset)

    async def export_user(self, user_id: str) -> KnowledgeStore:
        """Export all knowledge entries for a user as a KnowledgeStore."""
        from datetime import datetime, timezone

        entries = await self.repo.list_knowledge(user_id, limit=10000)
        store = KnowledgeStore(
            user_id=user_id,
            entries=entries,
            exported_at=datetime.now(timezone.utc),
        )
        return store

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