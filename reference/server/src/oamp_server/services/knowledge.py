"""Business logic for knowledge entry operations."""

from __future__ import annotations

from typing import Any, Optional

from oamp_types import KnowledgeEntry, KnowledgeStore, UserModel, validate_knowledge_entry

from ..api.errors import OampError, forbidden, not_found, validation_error, forbidden_patch
from ..auth import AgentGrantClaims
from ..repository.base import Repository


class KnowledgeService:
    """Service layer for knowledge entry operations."""

    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    async def create(self, entry: KnowledgeEntry, grant: AgentGrantClaims | None = None) -> KnowledgeEntry:
        """Create a new knowledge entry with validation."""
        if grant is not None and entry.user_id != grant.sub:
            raise forbidden("entry user_id exceeds grant subject", "SCOPE_DENIED_WRITE")
        self._enforce_write(entry, grant)
        errors = validate_knowledge_entry(entry)
        if errors:
            raise validation_error("; ".join(errors))
        return await self.repo.create_knowledge(entry)

    async def get(self, entry_id: str, grant: AgentGrantClaims | None = None) -> KnowledgeEntry:
        """Get a knowledge entry by ID."""
        entry = await self.repo.get_knowledge(entry_id)
        if entry is None:
            raise not_found("KnowledgeEntry", entry_id)
        if not self._can_read(entry, grant):
            await self.repo.log_audit_event(
                "scope_denied_read",
                user_id=entry.user_id,
                actor=grant.oamp_agent_id if grant else "direct-user",
                detail=f"grant:{grant.oamp_grant_id}" if grant else "direct-user",
            )
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

        Fields id, user_id, category, source, provenance, governance, content,
        oamp_version, and type are forbidden.
        """
        forbidden = {
            "id", "user_id", "category", "source", "provenance",
            "governance", "oamp_version", "type", "content",
        }
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
        sensitivity_classes: Optional[list[str]] = None,
        governance_labels: Optional[list[str]] = None,
        grant: AgentGrantClaims | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[KnowledgeEntry]:
        """List knowledge entries for a user."""
        if grant is not None and user_id != grant.sub:
            return []
        entries = await self.repo.list_knowledge(user_id, category, limit=10000, offset=0)
        return await self._apply_governance_filters(entries, sensitivity_classes, governance_labels, grant, limit, offset)

    async def search(
        self,
        query: str,
        user_id: str,
        category: Optional[str] = None,
        sensitivity_classes: Optional[list[str]] = None,
        governance_labels: Optional[list[str]] = None,
        grant: AgentGrantClaims | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[KnowledgeEntry]:
        """Search knowledge entries by text query."""
        if grant is not None and user_id != grant.sub:
            return []
        entries = await self.repo.search_knowledge(query, user_id, category, limit=10000, offset=0)
        return await self._apply_governance_filters(entries, sensitivity_classes, governance_labels, grant, limit, offset)

    async def export_user(
        self,
        user_id: str,
        user_model_service: Any,
        grant: AgentGrantClaims | None = None,
    ) -> dict[str, Any]:
        """Export all data for a user.

        Per spec Section 6.4: returns all KnowledgeEntries plus
        the UserModel in a metadata field if present.

        Returns a dict (not KnowledgeStore) because the export response
        adds a non-schema metadata field for the UserModel.
        """
        from datetime import datetime, timezone

        if grant is not None and user_id != grant.sub:
            entries: list[KnowledgeEntry] = []
        else:
            entries = await self.repo.list_knowledge(user_id, limit=10000)
        if grant is not None and not grant.oamp_export_full:
            before = len(entries)
            entries = [entry for entry in entries if self._can_export(entry, grant)]
            await self._log_scope_denied_if_needed(before, len(entries), user_id, grant)

        store_version = "1.3.0" if any(
            entry.governance is not None or entry.provenance is not None
            for entry in entries
        ) else "1.0.0"
        if store_version == "1.0.0" and grant is not None:
            store_version = "1.3.0"

        result: dict[str, Any] = {
            "oamp_version": store_version,
            "type": "knowledge_store",
            "user_id": user_id,
            "entries": [e.model_dump(mode="json", exclude_none=True) for e in entries],
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {},
        }

        # Include the User Model in metadata if present
        user_model = None if grant is not None and user_id != grant.sub else await user_model_service.repo.get_user_model(user_id)
        if user_model is not None:
            result["metadata"]["user_model"] = user_model.model_dump(mode="json", exclude_none=True)

        return result

    async def import_store(
        self,
        store: KnowledgeStore,
        grant: AgentGrantClaims | None = None,
    ) -> tuple[int, int]:
        """Import a KnowledgeStore, creating all allowed entries.

        Returns a tuple of (imported_count, rejected_count).
        """
        imported_count = 0
        rejected_count = 0
        for entry in store.entries:
            if grant is not None and entry.user_id != grant.sub:
                rejected_count += 1
                continue
            errors = validate_knowledge_entry(entry)
            if errors:
                raise validation_error(f"Entry {entry.id}: {'; '.join(errors)}")

            try:
                self._enforce_write(entry, grant)
            except OampError:
                rejected_count += 1
                continue

            await self.repo.create_knowledge(entry)
            imported_count += 1
        return imported_count, rejected_count

    @staticmethod
    def _sensitivity_rank(value: str) -> int:
        return {
            "public": 0,
            "internal": 1,
            "confidential": 2,
            "restricted": 3,
        }[value]

    @staticmethod
    def _label_matches(granted: str, label: str) -> bool:
        return label == granted or label.startswith(f"{granted}.")

    @staticmethod
    def _effective_sensitivity(entry: KnowledgeEntry) -> str:
        if entry.governance is None:
            return "internal"
        return entry.governance.sensitivity_class

    @staticmethod
    def _effective_labels(entry: KnowledgeEntry) -> list[str]:
        if entry.governance is None or not entry.governance.labels:
            return ["behaviour"]
        return entry.governance.labels

    @staticmethod
    def _handling_mode(entry: KnowledgeEntry, field: str) -> str:
        if entry.governance is None or entry.governance.handling is None:
            return "governed"
        value = getattr(entry.governance.handling, field)
        return value or "governed"

    def _can_read(self, entry: KnowledgeEntry, grant: AgentGrantClaims | None) -> bool:
        if grant is None:
            return True
        if entry.user_id != grant.sub:
            return False
        if self._handling_mode(entry, "retrieval") == "ungoverned":
            return True
        if self._sensitivity_rank(self._effective_sensitivity(entry)) > self._sensitivity_rank(grant.oamp_sensitivity_max):
            return False
        labels = self._effective_labels(entry)
        return any(
            self._label_matches(granted, label)
            for granted in grant.oamp_read_labels
            for label in labels
        )

    def _can_export(self, entry: KnowledgeEntry, grant: AgentGrantClaims | None) -> bool:
        if grant is None:
            return True
        if self._handling_mode(entry, "export") == "ungoverned":
            return True
        return self._can_read(entry, grant)

    def _enforce_write(self, entry: KnowledgeEntry, grant: AgentGrantClaims | None) -> None:
        if grant is None:
            return
        if not entry.source.agent_id or entry.source.agent_id != grant.oamp_agent_id:
            raise validation_error("source.agent_id must match oamp_agent_id for grant-bound writes")
        if self._sensitivity_rank(self._effective_sensitivity(entry)) > self._sensitivity_rank(grant.oamp_sensitivity_max):
            raise forbidden("entry sensitivity exceeds grant", "SCOPE_DENIED_WRITE")
        labels = self._effective_labels(entry)
        for label in labels:
            if not any(self._label_matches(granted, label) for granted in grant.oamp_write_labels):
                raise forbidden("entry labels exceed write grant", "SCOPE_DENIED_WRITE")

    async def _log_scope_denied_if_needed(
        self,
        before: int,
        after: int,
        user_id: str,
        grant: AgentGrantClaims | None,
    ) -> None:
        if grant is None or before == after:
            return
        await self.repo.log_audit_event(
            "scope_denied_read",
            user_id=user_id,
            actor=grant.oamp_agent_id,
            detail=f"grant:{grant.oamp_grant_id};requested:{','.join(grant.oamp_read_labels)}",
        )

    async def _apply_governance_filters(
        self,
        entries: list[KnowledgeEntry],
        sensitivity_classes: Optional[list[str]],
        governance_labels: Optional[list[str]],
        grant: AgentGrantClaims | None,
        limit: int,
        offset: int,
    ) -> list[KnowledgeEntry]:
        """Filter entries by optional governance metadata, then paginate."""
        filtered = [entry for entry in entries if self._can_read(entry, grant)]
        await self._log_scope_denied_if_needed(len(entries), len(filtered), entries[0].user_id if entries else "", grant)

        if sensitivity_classes:
            allowed = set(sensitivity_classes)
            filtered = [
                entry for entry in filtered
                if entry.governance is not None
                and entry.governance.sensitivity_class in allowed
            ]

        if governance_labels:
            requested = set(governance_labels)
            filtered = [
                entry for entry in filtered
                if entry.governance is not None
                and requested.intersection(entry.governance.labels)
            ]

        return filtered[offset:offset + limit]
