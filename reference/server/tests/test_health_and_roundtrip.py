"""Tests for health check and spec example round-trips."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SPEC_EXAMPLES = Path(__file__).resolve().parents[3] / "spec" / "v1" / "examples"


class TestHealthCheck:
    """GET /health"""

    async def test_health_check(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestSpecExampleRoundTrips:
    """Verify that spec examples can be stored and retrieved via the API."""

    async def test_knowledge_entry_spec_example(self, client):
        """POST then GET the spec example knowledge-entry.json."""
        path = SPEC_EXAMPLES / "knowledge-entry.json"
        if not path.exists():
            pytest.skip("spec example not found")

        entry = json.loads(path.read_text())

        # POST
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201, f"Create failed: {resp.json()}"

        # GET
        resp = await client.get(f"/v1/knowledge/{entry['id']}")
        assert resp.status_code == 200
        data = resp.json()

        # Verify round-trip (key fields)
        assert data["id"] == entry["id"]
        assert data["user_id"] == entry["user_id"]
        assert data["category"] == entry["category"]
        assert data["content"] == entry["content"]
        assert data["confidence"] == entry["confidence"]
        assert data["tags"] == entry["tags"]

    async def test_user_model_spec_example(self, client):
        """POST then GET the spec example user-model.json."""
        path = SPEC_EXAMPLES / "user-model.json"
        if not path.exists():
            pytest.skip("spec example not found")

        model = json.loads(path.read_text())

        # POST
        resp = await client.post("/v1/user-model", json=model)
        assert resp.status_code == 201, f"Create failed: {resp.json()}"

        # GET
        resp = await client.get(f"/v1/user-model/{model['user_id']}")
        assert resp.status_code == 200
        data = resp.json()

        # Verify round-trip (key fields)
        assert data["user_id"] == model["user_id"]
        assert data["model_version"] == model["model_version"]
        assert len(data["expertise"]) == 3
        assert data["communication"]["verbosity"] == -0.6

    async def test_knowledge_store_spec_example_import(self, client):
        """POST entries from knowledge-store.json, then list them."""
        path = SPEC_EXAMPLES / "knowledge-store.json"
        if not path.exists():
            pytest.skip("spec example not found")

        store = json.loads(path.read_text())
        user_id = store["user_id"]

        # POST each entry
        for entry in store["entries"]:
            resp = await client.post("/v1/knowledge", json=entry)
            assert resp.status_code == 201, f"Create failed for {entry['id']}: {resp.json()}"

        # LIST and verify count
        resp = await client.get("/v1/knowledge", params={"user_id": user_id})
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 3

        # SEARCH for "Rust" — should find entry about unwrap
        resp = await client.get(
            "/v1/knowledge/search",
            params={"q": "unwrap", "user_id": user_id},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1