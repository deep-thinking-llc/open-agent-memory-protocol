"""SQLite repository implementation with FTS5 search.

Phase 2: Real SQLite backend with async I/O, FTS5 full-text search,
bulk export/import support, and proper SQL schema.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

import aiosqlite
from oamp_types import KnowledgeEntry, KnowledgeStore, UserModel

from .base import Repository

SCHEMA = """
-- Knowledge entries table
CREATE TABLE IF NOT EXISTS knowledge_entries (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    confidence REAL NOT NULL,
    source_json TEXT NOT NULL,
    decay_json TEXT,
    tags_json TEXT,
    metadata_json TEXT,
    oamp_version TEXT NOT NULL DEFAULT '1.0.0',
    type TEXT NOT NULL DEFAULT 'knowledge_entry',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- User models table
CREATE TABLE IF NOT EXISTS user_models (
    user_id TEXT PRIMARY KEY,
    model_version INTEGER NOT NULL,
    oamp_version TEXT NOT NULL DEFAULT '1.0.0',
    type TEXT NOT NULL DEFAULT 'user_model',
    updated_at TEXT NOT NULL,
    communication_json TEXT,
    expertise_json TEXT,
    corrections_json TEXT,
    stated_preferences_json TEXT,
    metadata_json TEXT,
    created_at TEXT NOT NULL
);

-- FTS5 virtual table for knowledge content search (standalone, not content-sync)
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    entry_id,
    user_id,
    category,
    content,
    tokenize='porter'
);

-- Index for fast user_id lookups
CREATE INDEX IF NOT EXISTS idx_knowledge_user_id ON knowledge_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_user_category ON knowledge_entries(user_id, category);
"""


class SQLiteRepository(Repository):
    """SQLite-backed OAMP repository with FTS5 search.

    Uses aiosqlite for async I/O. Data is stored in a single .db file.
    Optional in-memory mode for testing.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Open the database and create tables."""
        self._db = await aiosqlite.connect(self._db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(SCHEMA)
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

    @staticmethod
    def _now() -> str:
        """Return current UTC timestamp as ISO format string."""
        return datetime.now(timezone.utc).isoformat()

    # ── Knowledge Entries ─────────────────────────────

    async def create_knowledge(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        db = self._ensure_connected()
        now = self._now()
        category_val = entry.category.value if hasattr(entry.category, "value") else entry.category
        source_json = json.dumps(entry.source.model_dump(mode="json", exclude_none=True)) if entry.source else "{}"
        decay_json = json.dumps(entry.decay.model_dump(mode="json", exclude_none=True)) if entry.decay else None
        tags_json = json.dumps(entry.tags) if entry.tags else None
        metadata_json = json.dumps(entry.metadata) if entry.metadata else None

        # Delete existing if replacing (to keep FTS in sync)
        existing = await self.get_knowledge(entry.id)
        if existing is not None:
            await db.execute("DELETE FROM knowledge_entries WHERE id = ?", (entry.id,))

        await db.execute(
            """INSERT INTO knowledge_entries
               (id, user_id, category, content, confidence, source_json,
                decay_json, tags_json, metadata_json, oamp_version, type,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.id, entry.user_id, category_val, entry.content,
                entry.confidence, source_json, decay_json, tags_json,
                metadata_json, entry.oamp_version, entry.type, now, now,
            ),
        )
        # Insert into FTS index
        await db.execute(
            "INSERT INTO knowledge_fts (entry_id, user_id, category, content) VALUES (?, ?, ?, ?)",
            (entry.id, entry.user_id, category_val, entry.content),
        )
        await db.commit()
        return entry

    async def get_knowledge(self, entry_id: str) -> Optional[KnowledgeEntry]:
        db = self._ensure_connected()
        async with db.execute(
            "SELECT * FROM knowledge_entries WHERE id = ?", (entry_id,)
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_knowledge(row)

    async def delete_knowledge(self, entry_id: str) -> bool:
        db = self._ensure_connected()
        # Delete from FTS first
        await db.execute(
            "DELETE FROM knowledge_fts WHERE entry_id = ?", (entry_id,)
        )
        cursor = await db.execute(
            "DELETE FROM knowledge_entries WHERE id = ?", (entry_id,)
        )
        await db.commit()
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

        for field, value in updates.items():
            if field == "confidence":
                set_clauses.append("confidence = ?")
                values.append(value)
            elif field == "tags":
                set_clauses.append("tags_json = ?")
                values.append(json.dumps(value))
            elif field == "decay":
                set_clauses.append("decay_json = ?")
                values.append(json.dumps(value) if value else None)
            elif field == "metadata":
                set_clauses.append("metadata_json = ?")
                values.append(json.dumps(value) if value else None)
            elif field == "content":
                set_clauses.append("content = ?")
                values.append(value)
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
            # Get the new content value
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
        return await self.get_knowledge(entry_id)

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
                results.append(self._row_to_knowledge(row))
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
                results.append(self._row_to_knowledge(row))
        return results

    async def _fallback_search(
        self,
        query: str,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[KnowledgeEntry]:
        """Fallback LIKE search when FTS5 fails."""
        db = self._ensure_connected()
        pattern = f"%{query}%"
        if category:
            sql = "SELECT * FROM knowledge_entries WHERE user_id = ? AND category = ? AND content LIKE ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params: tuple = (user_id, category, pattern, limit, offset)
        else:
            sql = "SELECT * FROM knowledge_entries WHERE user_id = ? AND content LIKE ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params = (user_id, pattern, limit, offset)

        results: list[KnowledgeEntry] = []
        async with db.execute(sql, params) as cursor:
            async for row in cursor:
                results.append(self._row_to_knowledge(row))
        return results

    # ── User Models ───────────────────────────────────

    async def create_user_model(self, model: UserModel) -> UserModel:
        db = self._ensure_connected()
        now = self._now()
        comm_json = json.dumps(model.communication.model_dump(mode="json", exclude_none=True)) if model.communication else None
        exp_json = json.dumps([e.model_dump(mode="json", exclude_none=True) for e in model.expertise]) if model.expertise else None
        corr_json = json.dumps([c.model_dump(mode="json", exclude_none=True) for c in model.corrections]) if model.corrections else None
        pref_json = json.dumps([p.model_dump(mode="json", exclude_none=True) for p in model.stated_preferences]) if model.stated_preferences else None
        meta_json = json.dumps(model.metadata) if model.metadata else None

        await db.execute(
            """INSERT OR REPLACE INTO user_models
               (user_id, model_version, oamp_version, type, updated_at,
                communication_json, expertise_json, corrections_json,
                stated_preferences_json, metadata_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                model.user_id, model.model_version, model.oamp_version,
                model.type, model.updated_at, comm_json, exp_json,
                corr_json, pref_json, meta_json, now,
            ),
        )
        await db.commit()
        return model

    async def get_user_model(self, user_id: str) -> Optional[UserModel]:
        db = self._ensure_connected()
        async with db.execute(
            "SELECT * FROM user_models WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_user_model(row)

    async def update_user_model(self, model: UserModel) -> UserModel:
        return await self.create_user_model(model)

    async def delete_user_model(self, user_id: str) -> bool:
        db = self._ensure_connected()
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
        return cursor.rowcount > 0

    # ── Conversions ───────────────────────────────────

    @staticmethod
    def _row_to_knowledge(row: aiosqlite.Row) -> KnowledgeEntry:
        """Convert a database row to a KnowledgeEntry."""
        data: dict[str, Any] = {
            "id": row["id"],
            "user_id": row["user_id"],
            "category": row["category"],
            "content": row["content"],
            "confidence": row["confidence"],
            "oamp_version": row["oamp_version"],
            "type": row["type"],
            "source": json.loads(row["source_json"]) if row["source_json"] else {},
        }
        if row["decay_json"]:
            data["decay"] = json.loads(row["decay_json"])
        if row["tags_json"]:
            data["tags"] = json.loads(row["tags_json"])
        if row["metadata_json"]:
            data["metadata"] = json.loads(row["metadata_json"])
        return KnowledgeEntry.model_validate(data)

    @staticmethod
    def _row_to_user_model(row: aiosqlite.Row) -> UserModel:
        """Convert a database row to a UserModel."""
        data: dict[str, Any] = {
            "user_id": row["user_id"],
            "model_version": row["model_version"],
            "oamp_version": row["oamp_version"],
            "type": row["type"],
            "updated_at": row["updated_at"],
        }
        if row["communication_json"]:
            data["communication"] = json.loads(row["communication_json"])
        if row["expertise_json"]:
            data["expertise"] = json.loads(row["expertise_json"])
        if row["corrections_json"]:
            data["corrections"] = json.loads(row["corrections_json"])
        if row["stated_preferences_json"]:
            data["stated_preferences"] = json.loads(row["stated_preferences_json"])
        if row["metadata_json"]:
            data["metadata"] = json.loads(row["metadata_json"])
        return UserModel.model_validate(data)