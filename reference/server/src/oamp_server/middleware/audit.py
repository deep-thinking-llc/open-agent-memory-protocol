"""Audit logging middleware for OAMP server.

Per spec §8.2.6: "Operations on user data SHOULD be audit logged.
Audit logs MUST NOT contain knowledge content."

This middleware logs all CRUD operations with user_id and entry_id,
never logging content, tags, source, or any knowledge text.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import aiosqlite

# Audit log schema — separate from main data tables
AUDIT_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL,
    action      TEXT NOT NULL,
    user_id     TEXT NOT NULL,
    entry_id    TEXT,
    actor       TEXT,
    detail      TEXT
);
"""


async def init_audit_log(db: aiosqlite.Connection) -> None:
    """Create the audit_log table if it doesn't exist."""
    await db.executescript(AUDIT_SCHEMA)


async def log_audit(
    db: aiosqlite.Connection,
    action: str,
    user_id: str,
    entry_id: str | None = None,
    actor: str | None = None,
    detail: str | None = None,
) -> None:
    """Record an audit log entry.

    Args:
        db: Database connection.
        action: Operation type (create|read|update|delete|export|import|rotate_key).
        user_id: The user whose data is affected.
        entry_id: ID of the affected knowledge entry (if applicable).
        actor: Agent or system that initiated the action.
        detail: Additional detail that does NOT contain knowledge content.
    """
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        """INSERT INTO audit_log (timestamp, action, user_id, entry_id, actor, detail)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (now, action, user_id, entry_id, actor, detail),
    )
    await db.commit()


async def get_audit_log(
    db: aiosqlite.Connection,
    user_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Retrieve audit log entries."""
    if user_id:
        sql = (
            "SELECT id, timestamp, action, user_id, entry_id, actor, detail "
            "FROM audit_log WHERE user_id = ? ORDER BY id DESC LIMIT ? OFFSET ?"
        )
        params = (user_id, limit, offset)
    else:
        sql = (
            "SELECT id, timestamp, action, user_id, entry_id, actor, detail "
            "FROM audit_log ORDER BY id DESC LIMIT ? OFFSET ?"
        )
        params = (limit, offset)

    results: list[dict[str, Any]] = []
    async with db.execute(sql, params) as cursor:
        async for row in cursor:
            results.append({
                "id": row[0],
                "timestamp": row[1],
                "action": row[2],
                "user_id": row[3],
                "entry_id": row[4],
                "actor": row[5],
                "detail": row[6],
            })
    return results