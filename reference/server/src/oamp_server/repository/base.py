"""Abstract repository interface for OAMP data persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from oamp_types import KnowledgeEntry, KnowledgeStore, UserModel


class Repository(ABC):
    """Abstract base class for OAMP data persistence."""

    # ── Knowledge Entries ─────────────────────────────

    @abstractmethod
    async def create_knowledge(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        """Store a new knowledge entry. Returns the stored entry."""
        ...

    @abstractmethod
    async def get_knowledge(self, entry_id: str) -> KnowledgeEntry | None:
        """Retrieve a knowledge entry by ID. Returns None if not found."""
        ...

    @abstractmethod
    async def delete_knowledge(self, entry_id: str) -> bool:
        """Delete a knowledge entry. Returns True if deleted, False if not found."""
        ...

    @abstractmethod
    async def update_knowledge(
        self, entry_id: str, updates: dict[str, Any]
    ) -> KnowledgeEntry | None:
        """Update specific fields on a knowledge entry. Returns updated entry or None."""
        ...

    @abstractmethod
    async def list_knowledge(
        self,
        user_id: str,
        category: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[KnowledgeEntry]:
        """List knowledge entries for a user, with optional category filter."""
        ...

    @abstractmethod
    async def count_knowledge(self, user_id: str) -> int:
        """Count knowledge entries for a user."""
        ...

    @abstractmethod
    async def search_knowledge(
        self,
        query: str,
        user_id: str,
        category: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[KnowledgeEntry]:
        """Search knowledge entries by text content."""
        ...

    # ── User Models ───────────────────────────────────

    @abstractmethod
    async def create_user_model(self, model: UserModel) -> UserModel:
        """Store a new user model. Returns the stored model."""
        ...

    @abstractmethod
    async def get_user_model(self, user_id: str) -> UserModel | None:
        """Retrieve a user model by user_id. Returns None if not found."""
        ...

    @abstractmethod
    async def update_user_model(self, model: UserModel) -> UserModel:
        """Update an existing user model. Returns the updated model."""
        ...

    @abstractmethod
    async def delete_user_model(self, user_id: str) -> bool:
        """Delete a user model and all associated knowledge entries."""
        ...