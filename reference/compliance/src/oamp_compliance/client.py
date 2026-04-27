"""HTTP client for OAMP backends.

Provides a thin wrapper around httpx to make API calls to any OAMP-compliant
server. All tests use this client — never make raw HTTP calls.
"""

from __future__ import annotations

from typing import Any

import httpx


class OAMPClient:
    """HTTP client for communicating with an OAMP backend server.

    Args:
        base_url: The root URL of the OAMP server (e.g. http://localhost:8000).
        headers: Optional additional headers (e.g. Authorization).
        timeout: Request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers=headers or {},
            timeout=timeout,
        )

    def close(self) -> None:
        self._client.close()

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    # ── Knowledge Endpoints ─────────────────────────────

    def create_knowledge(self, entry: dict[str, Any]) -> httpx.Response:
        """POST /v1/knowledge — Create a knowledge entry."""
        return self._client.post("/v1/knowledge", json=entry)

    def get_knowledge(self, entry_id: str) -> httpx.Response:
        """GET /v1/knowledge/{entry_id} — Retrieve by ID."""
        return self._client.get(f"/v1/knowledge/{entry_id}")

    def list_knowledge(
        self,
        user_id: str,
        query: str | None = None,
        category: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> httpx.Response:
        """GET /v1/knowledge — List or search entries."""
        params: dict[str, Any] = {"user_id": user_id, "limit": limit, "offset": offset}
        if query is not None:
            params["query"] = query
        if category is not None:
            params["category"] = category
        return self._client.get("/v1/knowledge", params=params)

    def update_knowledge(self, entry_id: str, updates: dict[str, Any]) -> httpx.Response:
        """PATCH /v1/knowledge/{entry_id} — Update fields."""
        return self._client.patch(f"/v1/knowledge/{entry_id}", json=updates)

    def delete_knowledge(self, entry_id: str) -> httpx.Response:
        """DELETE /v1/knowledge/{entry_id} — Delete an entry (permanent)."""
        return self._client.delete(f"/v1/knowledge/{entry_id}")

    # ── User Model Endpoints ────────────────────────────

    def create_user_model(self, model: dict[str, Any]) -> httpx.Response:
        """POST /v1/user-model — Create or update a user model."""
        return self._client.post("/v1/user-model", json=model)

    def get_user_model(self, user_id: str) -> httpx.Response:
        """GET /v1/user-model/{user_id} — Retrieve a user model."""
        return self._client.get(f"/v1/user-model/{user_id}")

    def delete_user_model(self, user_id: str) -> httpx.Response:
        """DELETE /v1/user-model/{user_id} — Delete a user model and all data."""
        return self._client.delete(f"/v1/user-model/{user_id}")

    # ── Bulk Endpoints ──────────────────────────────────

    def export_data(self, user_id: str) -> httpx.Response:
        """POST /v1/export — Export all data for a user."""
        return self._client.post("/v1/export", json={"user_id": user_id})

    def import_data(self, store: dict[str, Any]) -> httpx.Response:
        """POST /v1/import — Import a KnowledgeStore."""
        return self._client.post("/v1/import", json=store)

    # ── Admin Endpoints ─────────────────────────────────

    def rotate_key(self) -> httpx.Response:
        """POST /v1/admin/keys/rotate — Rotate encryption key."""
        return self._client.post("/v1/admin/keys/rotate")

    def get_audit_log(
        self,
        user_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> httpx.Response:
        """GET /v1/admin/audit — Query audit log."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if user_id is not None:
            params["user_id"] = user_id
        return self._client.get("/v1/admin/audit", params=params)

    # ── Health ──────────────────────────────────────────

    def health_check(self) -> httpx.Response:
        """GET /health — Health check."""
        return self._client.get("/health")