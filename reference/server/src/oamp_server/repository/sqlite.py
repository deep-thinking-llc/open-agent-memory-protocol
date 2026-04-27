"""SQLite repository implementation with FTS5 search and AES-256-GCM encryption.

Phase 3: All PII/content fields are encrypted at rest using AES-256-GCM.
Plaintext columns (user_id, category, confidence, id, timestamps) remain
unencrypted for querying/sorting. FTS5 indexes plaintext content at write
time for search functionality.

Spec §8.1.1: "All stored knowledge and user model data MUST be encrypted at rest."
Spec §8.2.6: "Audit logs MUST NOT contain knowledge content."
Spec §8.2.7: "Delete operations SHOULD zeroize memory buffers."
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, List, Optional

import aiosqlite
from oamp_types import KnowledgeEntry, KnowledgeStore, UserModel

from .base import Repository
from ..encryption import KeyProvider, LocalKeyProvider, encrypt, decrypt
from ..middleware.audit import log_audit, init_audit_log

SCHEMA = """
-- Knowledge entries table (Phase 3: encrypted columns)
CREATE TABLE IF NOT EXISTS knowledge_entries (
    id               TEXT PRIMARY KEY,
    user_id          TEXT NOT NULL,
    category         TEXT NOT NULL,
    confidence        REAL NOT NULL,
    oamp_version      TEXT NOT NULL DEFAULT '1.0.0',
    type              TEXT NOT NULL DEFAULT 'knowledge_entry',
    -- Encrypted columns (base64-encoded AES-256-GCM ciphertext)
    content_enc       TEXT NOT NULL,
    source_enc        TEXT NOT NULL,
    decay_enc         TEXT,
    tags_enc          TEXT,
    metadata_enc      TEXT,
    encryption_key_id TEXT NOT NULL,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);

-- User models table (Phase 3: encrypted columns)
CREATE TABLE IF NOT EXISTS user_models (
    user_id              TEXT PRIMARY KEY,
    model_version        INTEGER NOT NULL,
    oamp_version         TEXT NOT NULL DEFAULT '1.0.0',
    type                 TEXT NOT NULL DEFAULT 'user_model',
    updated_at           TEXT NOT NULL,
    -- Encrypted columns
    communication_enc    TEXT,
    expertise_enc        TEXT,
    corrections_enc       TEXT,
    stated_prefs_enc     TEXT,
    metadata_enc         TEXT,
    encryption_key_id    TEXT NOT NULL,
    created_at           TEXT NOT NULL
);

-- FTS5 virtual table for knowledge content search
-- NOTE: FTS5 indexes plaintext content at write time for search.
-- The FTS5 index itself is not encrypted (a known trade-off for Phase 3).
-- The main knowledge_entries table stores encrypted content.
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    entry_id,
    user_id,
    category,
    content,
    tokenize='porter'
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_knowledge_user_id ON knowledge_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_user_category ON knowledge_entries(user_id, category);
"""


class SQLiteRepository(Repository):
    """SQLite-backed OAMP repository with FTS5 search and AES-256-GCM encryption.

    Uses aiosqlite for async I/O. Data is stored in a single .db file.
    Optional in-memory mode for testing.

    Encryption:
    - All PII/content columns are encrypted with AES-256-GCM before storage.
    - AAD = user_id binds ciphertext to user scope.
    - FTS5 indexes plaintext content for search (acceptable trade-off for Phase 3).
    - Key rotation supported: each row stores the key_id used for encryption.
    """

    def __init__(
        self,
        db_path: str = ":memory:",
        key_provider: Optional[KeyProvider] = None,
        audit_enabled: bool = True,
    ) -> None:
        self._db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None
        self._key_provider = key_provider
        self._audit_enabled = audit_enabled

    async def initialize(self) -> None:
        """Open the database and create tables."""
        self._db = await aiosqlite.connect(self._db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(SCHEMA)

        # Initialize audit log table if enabled
        if self._audit_enabled:
            await init_audit_log(self._db)

        await self._db.commit()

    async def close(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None

    def _ensure_connected(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("Repository not initialized. Call initialize() first.")
        return self._db

    def _get_key_provider(self) -> KeyProvider:
        if self._key_provider is not None:
            return self._key_provider
        raise RuntimeError("No key provider configured")

    @staticmethod
    def _now() -> str:
        """Return current UTC timestamp as ISO format string."""
        return datetime.now(timezone.utc).isoformat()

    async def _encrypt_field(self, plaintext: str, user_id: str) -> tuple[str, str]:
        """Encrypt a field value. Returns (ciphertext, key_id)."""
        provider = self._get_key_provider()
        key = provider.get_active_key()
        ciphertext = encrypt(plaintext, key, aad=user_id)
        return ciphertext, key.key_id

    async def _decrypt_field(self, ciphertext: str, key_id: str, user_id: str) -> str:
        """Decrypt a field value."""
        provider = self._get_key_provider()
        return decrypt(ciphertext, key_id, provider, aad=user_id)

    async def _audit(
        self,
        action: str,
        user_id: str | None = None,
        entry_id: str | None = None,
        detail: str | None = None,
        actor: str | None = None,
    ) -> None:
        """Log an audit event if audit logging is enabled."""
        if not self._audit_enabled or self._db is None:
            return
        await log_audit(
            self._db, action,
            user_id=user_id or "system",
            entry_id=entry_id, detail=detail, actor=actor,
        )

    async def log_audit_event(
        self,
        action: str,
        user_id: str | None = None,
        entry_id: str | None = None,
        detail: str | None = None,
        actor: str | None = None,
    ) -> None:
        """Public method to log an audit event from outside the repository."""
        await self._audit(action, user_id=user_id, entry_id=entry_id, detail=detail, actor=actor)

    # ── Knowledge Entries ─────────────────────────────

    async def create_knowledge(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        db = self._ensure_connected()
        now = self._now()
        category_val = entry.category.value if hasattr(entry.category, "value") else entry.category

        # Encrypt PII/content fields
        content_enc, key_id = await self._encrypt_field(entry.content, entry.user_id)
        source_json = json.dumps(entry.source.model_dump(mode="json", exclude_none=True)) if entry.source else "{}"
        source_enc, _ = await self._encrypt_field_with_key(source_json, entry.user_id, key_id)

        decay_json = json.dumps(entry.decay.model_dump(mode="json", exclude_none=True)) if entry.decay else None
        decay_enc = None
        if decay_json:
            decay_enc, _ = await self._encrypt_field_with_key(decay_json, entry.user_id, key_id)

        tags_json = json.dumps(entry.tags) if entry.tags else None
        tags_enc = None
        if tags_json:
            tags_enc, _ = await self._encrypt_field_with_key(tags_json, entry.user_id, key_id)

        metadata_json = json.dumps(entry.metadata) if entry.metadata else None
        metadata_enc = None
        if metadata_json:
            metadata_enc, _ = await self._encrypt_field_with_key(metadata_json, entry.user_id, key_id)

        # Delete existing if replacing (to keep FTS in sync)
        existing = await self.get_knowledge(entry.id)
        if existing is not None:
            await db.execute("DELETE FROM knowledge_entries WHERE id = ?", (entry.id,))
            await db.execute("DELETE FROM knowledge_fts WHERE entry_id = ?", (entry.id,))

        await db.execute(
            """INSERT INTO knowledge_entries
               (id, user_id, category, confidence, content_enc, source_enc,
                decay_enc, tags_enc, metadata_enc, oamp_version, type,
                encryption_key_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.id, entry.user_id, category_val, entry.confidence,
                content_enc, source_enc, decay_enc, tags_enc, metadata_enc,
                entry.oamp_version, entry.type, key_id, now, now,
            ),
        )
        # Insert into FTS index (plaintext for search)
        await db.execute(
            "INSERT INTO knowledge_fts (entry_id, user_id, category, content) VALUES (?, ?, ?, ?)",
            (entry.id, entry.user_id, category_val, entry.content),
        )
        await db.commit()

        # Audit log (no content logged)
        await self._audit("create", entry.user_id, entry.id, detail="knowledge_entry")

        return entry

    async def _encrypt_field_with_key(
        self, plaintext: str, user_id: str, key_id: str
    ) -> tuple[str, str]:
        """Encrypt a field using a specific key_id (for consistent key usage within a write)."""
        provider = self._get_key_provider()
        key = provider.get_key(key_id)
        ciphertext = encrypt(plaintext, key, aad=user_id)
        return ciphertext, key_id

    async def get_knowledge(self, entry_id: str) -> Optional[KnowledgeEntry]:
        db = self._ensure_connected()
        async with db.execute(
            "SELECT * FROM knowledge_entries WHERE id = ?", (entry_id,)
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        entry = await self._row_to_knowledge(row)

        # Audit log (no content logged)
        await self._audit("read", entry.user_id, entry_id, detail="knowledge_entry")

        return entry

    async def delete_knowledge(self, entry_id: str) -> bool:
        db = self._ensure_connected()

        # Get entry for audit and zeroization
        entry = await self.get_knowledge(entry_id)

        if entry is None:
            return False

        # Zeroization: overwrite encrypted columns with zeros before delete
        # per spec §8.2.7. All operations in a single transaction.
        await db.execute(
            """UPDATE knowledge_entries
               SET content_enc = 'ZEROED',
                   source_enc = 'ZEROED',
                   decay_enc = 'ZEROED',
                   tags_enc = 'ZEROED',
                   metadata_enc = 'ZEROED'
               WHERE id = ?""",
            (entry_id,),
        )
        # Delete from both tables
        await db.execute(
            "DELETE FROM knowledge_fts WHERE entry_id = ?", (entry_id,)
        )
        cursor = await db.execute(
            "DELETE FROM knowledge_entries WHERE id = ?", (entry_id,)
        )
        await db.commit()

        # Audit log
        await self._audit("delete", entry.user_id, entry_id, detail="knowledge_entry")

        return cursor.rowcount > 0

    async def update_knowledge(
        self, entry_id: str, updates: dict[str, Any]
    ) -> Optional[KnowledgeEntry]:
        db = self._ensure_connected()
        entry = await self.get_knowledge(entry_id)
        if entry is None:
            return None

        set_clauses = []
        values: list[Any] = []
        fts_dirty = False
        key_id = row_key_id = None

        # Get current key_id
        async with db.execute(
            "SELECT encryption_key_id FROM knowledge_entries WHERE id = ?", (entry_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                row_key_id = row["encryption_key_id"]

        for field, value in updates.items():
            if field == "confidence":
                set_clauses.append("confidence = ?")
                values.append(value)
            elif field == "tags":
                tags_json = json.dumps(value) if value else None
                if tags_json:
                    tags_enc, _ = await self._encrypt_field_with_key(tags_json, entry.user_id, row_key_id)
                    set_clauses.append("tags_enc = ?")
                    values.append(tags_enc)
                else:
                    set_clauses.append("tags_enc = ?")
                    values.append(None)
            elif field == "decay":
                decay_json = json.dumps(value) if value else None
                if decay_json:
                    decay_enc, _ = await self._encrypt_field_with_key(decay_json, entry.user_id, row_key_id)
                    set_clauses.append("decay_enc = ?")
                    values.append(decay_enc)
                else:
                    set_clauses.append("decay_enc = ?")
                    values.append(None)
            elif field == "metadata":
                metadata_json = json.dumps(value) if value else None
                if metadata_json:
                    metadata_enc, _ = await self._encrypt_field_with_key(metadata_json, entry.user_id, row_key_id)
                    set_clauses.append("metadata_enc = ?")
                    values.append(metadata_enc)
                else:
                    set_clauses.append("metadata_enc = ?")
                    values.append(None)
            elif field == "content":
                # Content updates via PATCH are blocked by the service layer,
                # but handle it for completeness
                content_enc, _ = await self._encrypt_field_with_key(value, entry.user_id, row_key_id)
                set_clauses.append("content_enc = ?")
                values.append(content_enc)
                fts_dirty = True
            # Skip forbidden/unknown fields silently

        if not set_clauses:
            return entry

        set_clauses.append("updated_at = ?")
        values.append(self._now())
        values.append(entry_id)

        await db.execute(
            f"UPDATE knowledge_entries SET {', '.join(set_clauses)} WHERE id = ?",
            values,
        )

        # Update FTS if content changed
        if fts_dirty:
            new_content = updates.get("content", entry.content)
            category_val = entry.category.value if hasattr(entry.category, "value") else entry.category
            await db.execute(
                "DELETE FROM knowledge_fts WHERE entry_id = ?", (entry_id,)
            )
            await db.execute(
                "INSERT INTO knowledge_fts (entry_id, user_id, category, content) VALUES (?, ?, ?, ?)",
                (entry_id, entry.user_id, category_val, new_content),
            )

        await db.commit()

        # Audit log
        await self._audit("update", entry.user_id, entry_id, detail="knowledge_entry")

        return await self._get_knowledge_no_audit(entry_id)

    async def _get_knowledge_no_audit(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get knowledge entry without logging an audit event (to avoid double-logging)."""
        db = self._ensure_connected()
        async with db.execute(
            "SELECT * FROM knowledge_entries WHERE id = ?", (entry_id,)
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        return await self._row_to_knowledge(row)

    async def list_knowledge(
        self,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[KnowledgeEntry]:
        db = self._ensure_connected()
        if category:
            query = "SELECT * FROM knowledge_entries WHERE user_id = ? AND category = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params: tuple = (user_id, category, limit, offset)
        else:
            query = "SELECT * FROM knowledge_entries WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params = (user_id, limit, offset)

        results: list[KnowledgeEntry] = []
        async with db.execute(query, params) as cursor:
            async for row in cursor:
                results.append(await self._row_to_knowledge(row))
        return results

    async def count_knowledge(self, user_id: str) -> int:
        db = self._ensure_connected()
        async with db.execute(
            "SELECT COUNT(*) FROM knowledge_entries WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
        return row[0]

    async def search_knowledge(
        self,
        query: str,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[KnowledgeEntry]:
        """FTS5-powered full-text search with Porter stemming.

        Falls back to LIKE search if FTS5 is unavailable or query is malformed.
        """
        try:
            return await self._fts5_search(query, user_id, category, limit, offset)
        except Exception:
            return await self._fallback_search(query, user_id, category, limit, offset)

    async def _fts5_search(
        self,
        query: str,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[KnowledgeEntry]:
        """Search using FTS5 MATCH with Porter stemming."""
        db = self._ensure_connected()
        # Escape special FTS5 characters for safety
        safe_query = query.replace('"', '""')

        if category:
            sql = """
                SELECT ke.* FROM knowledge_entries ke
                INNER JOIN knowledge_fts kft ON kft.entry_id = ke.id
                WHERE knowledge_fts MATCH ? AND kft.user_id = ? AND kft.category = ?
                ORDER BY ke.created_at DESC
                LIMIT ? OFFSET ?
            """
            params: tuple = (safe_query, user_id, category, limit, offset)
        else:
            sql = """
                SELECT ke.* FROM knowledge_entries ke
                INNER JOIN knowledge_fts kft ON kft.entry_id = ke.id
                WHERE knowledge_fts MATCH ? AND kft.user_id = ?
                ORDER BY ke.created_at DESC
                LIMIT ? OFFSET ?
            """
            params = (safe_query, user_id, limit, offset)

        results: list[KnowledgeEntry] = []
        async with db.execute(sql, params) as cursor:
            async for row in cursor:
                results.append(await self._row_to_knowledge(row))
        return results

    async def _fallback_search(
        self,
        query: str,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[KnowledgeEntry]:
        """Fallback: decrypt all entries and filter by content (slow but works)."""
        entries = await self.list_knowledge(user_id, category, limit=10000, offset=0)
        query_lower = query.lower()
        return [e for e in entries if query_lower in e.content.lower()][:limit]

    # ── User Models ───────────────────────────────────

    async def create_user_model(self, model: UserModel) -> UserModel:
        db = self._ensure_connected()
        now = self._now()

        # Encrypt PII fields
        comm_json = json.dumps(model.communication.model_dump(mode="json", exclude_none=True)) if model.communication else None
        exp_json = json.dumps([e.model_dump(mode="json", exclude_none=True) for e in model.expertise]) if model.expertise else None
        corr_json = json.dumps([c.model_dump(mode="json", exclude_none=True) for c in model.corrections]) if model.corrections else None
        pref_json = json.dumps([p.model_dump(mode="json", exclude_none=True) for p in model.stated_preferences]) if model.stated_preferences else None
        meta_json = json.dumps(model.metadata) if model.metadata else None

        # Get active key
        provider = self._get_key_provider()
        key = provider.get_active_key()
        key_id = key.key_id

        comm_enc = None
        if comm_json:
            comm_enc = encrypt(comm_json, key, aad=model.user_id)

        exp_enc = None
        if exp_json:
            exp_enc = encrypt(exp_json, key, aad=model.user_id)

        corr_enc = None
        if corr_json:
            corr_enc = encrypt(corr_json, key, aad=model.user_id)

        pref_enc = None
        if pref_json:
            pref_enc = encrypt(pref_json, key, aad=model.user_id)

        meta_enc = None
        if meta_json:
            meta_enc = encrypt(meta_json, key, aad=model.user_id)

        await db.execute(
            """INSERT OR REPLACE INTO user_models
               (user_id, model_version, oamp_version, type, updated_at,
                communication_enc, expertise_enc, corrections_enc,
                stated_prefs_enc, metadata_enc, encryption_key_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                model.user_id, model.model_version, model.oamp_version,
                model.type, model.updated_at, comm_enc, exp_enc,
                corr_enc, pref_enc, meta_enc, key_id, now,
            ),
        )
        await db.commit()

        # Audit log
        await self._audit("create", model.user_id, detail="user_model")

        return model

    async def get_user_model(self, user_id: str) -> Optional[UserModel]:
        db = self._ensure_connected()
        async with db.execute(
            "SELECT * FROM user_models WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        model = await self._row_to_user_model(row)

        # Audit log
        await self._audit("read", user_id, detail="user_model")

        return model

    async def update_user_model(self, model: UserModel) -> UserModel:
        return await self.create_user_model(model)

    async def delete_user_model(self, user_id: str) -> bool:
        db = self._ensure_connected()

        # Zeroize encrypted columns before delete (spec §8.2.7).
        # All operations in a single transaction.
        await db.execute(
            """UPDATE user_models
               SET communication_enc = 'ZEROED',
                   expertise_enc = 'ZEROED',
                   corrections_enc = 'ZEROED',
                   stated_prefs_enc = 'ZEROED',
                   metadata_enc = 'ZEROED'
               WHERE user_id = ?""",
            (user_id,),
        )
        # Delete knowledge entries and FTS entries for this user
        await db.execute(
            "DELETE FROM knowledge_fts WHERE user_id = ?", (user_id,)
        )
        await db.execute(
            "DELETE FROM knowledge_entries WHERE user_id = ?", (user_id,)
        )
        cursor = await db.execute(
            "DELETE FROM user_models WHERE user_id = ?", (user_id,)
        )
        await db.commit()

        # Audit log
        await self._audit("delete", user_id, detail="user_model")

        return cursor.rowcount > 0

    # ── Conversions ───────────────────────────────────

    async def _row_to_knowledge(self, row: aiosqlite.Row) -> KnowledgeEntry:
        """Convert a database row to a KnowledgeEntry, decrypting encrypted fields."""
        key_id = row["encryption_key_id"]
        user_id = row["user_id"]

        # Decrypt encrypted fields
        content = await self._decrypt_field(row["content_enc"], key_id, user_id)
        source_str = await self._decrypt_field(row["source_enc"], key_id, user_id)

        data: dict[str, Any] = {
            "id": row["id"],
            "user_id": user_id,
            "category": row["category"],
            "content": content,
            "confidence": row["confidence"],
            "oamp_version": row["oamp_version"],
            "type": row["type"],
            "source": json.loads(source_str) if source_str else {},
        }

        if row["decay_enc"]:
            decay_str = await self._decrypt_field(row["decay_enc"], key_id, user_id)
            data["decay"] = json.loads(decay_str)

        if row["tags_enc"]:
            tags_str = await self._decrypt_field(row["tags_enc"], key_id, user_id)
            data["tags"] = json.loads(tags_str)

        if row["metadata_enc"]:
            metadata_str = await self._decrypt_field(row["metadata_enc"], key_id, user_id)
            data["metadata"] = json.loads(metadata_str)

        return KnowledgeEntry.model_validate(data)

    async def _row_to_user_model(self, row: aiosqlite.Row) -> UserModel:
        """Convert a database row to a UserModel, decrypting encrypted fields."""
        key_id = row["encryption_key_id"]
        user_id = row["user_id"]

        data: dict[str, Any] = {
            "user_id": user_id,
            "model_version": row["model_version"],
            "oamp_version": row["oamp_version"],
            "type": row["type"],
            "updated_at": row["updated_at"],
        }

        if row["communication_enc"]:
            comm_str = await self._decrypt_field(row["communication_enc"], key_id, user_id)
            data["communication"] = json.loads(comm_str)

        if row["expertise_enc"]:
            exp_str = await self._decrypt_field(row["expertise_enc"], key_id, user_id)
            data["expertise"] = json.loads(exp_str)

        if row["corrections_enc"]:
            corr_str = await self._decrypt_field(row["corrections_enc"], key_id, user_id)
            data["corrections"] = json.loads(corr_str)

        if row["stated_prefs_enc"]:
            pref_str = await self._decrypt_field(row["stated_prefs_enc"], key_id, user_id)
            data["stated_preferences"] = json.loads(pref_str)

        if row["metadata_enc"]:
            meta_str = await self._decrypt_field(row["metadata_enc"], key_id, user_id)
            data["metadata"] = json.loads(meta_str)

        return UserModel.model_validate(data)