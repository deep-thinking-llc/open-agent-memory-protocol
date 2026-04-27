from typing import Any, Optional

from fastapi import APIRouter, Depends, Request

from ..encryption import KeyProvider
from ..middleware.audit import get_audit_log

router = APIRouter(tags=["Admin"])


def _get_key_provider(request: Request) -> KeyProvider:
    return request.app.state.key_provider


@router.post("/admin/keys/rotate")
async def rotate_key(
    request: Request,
    provider: KeyProvider = Depends(_get_key_provider),
) -> dict[str, Any]:
    """Rotate the active encryption key.

    Generates a new key and marks it as active. Existing data remains
    decryptable with the old key (stored key_id per row). New writes
    will use the new key.
    """
    new_key = provider.rotate()
    # Audit key rotation
    await request.app.state.repo.log_audit_event(
        "rotate_key",
        actor="system",
        detail=f"new_key_id:{new_key.key_id}",
    )
    return {
        "key_id": new_key.key_id,
        "message": "Encryption key rotated successfully. New writes will use this key.",
    }


@router.get("/admin/audit")
async def get_audit(
    request: Request,
    user_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Query audit log entries.

    Audit logs never contain knowledge content (spec §8.2.6).
    """
    db = request.app.state.repo._db
    entries = await get_audit_log(db, user_id=user_id, limit=limit, offset=offset)
    return entries