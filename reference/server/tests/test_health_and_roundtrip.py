"""Tests for health check, spec example round-trips, and pre-populated E2E tests."""

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
    """Verify that spec examples can be stored, retrieved, and searched via the API."""

    async def test_knowledge_entry_spec_example(self, client):
        """POST then GET the spec example knowledge-entry.json."""
        path = SPEC_EXAMPLES / "knowledge-entry.json"
        if not path.exists():
            pytest.skip("spec example not found")

        entry = json.loads(path.read_text())

        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201, f"Create failed: {resp.json()}"

        resp = await client.get(f"/v1/knowledge/{entry['id']}")
        assert resp.status_code == 200
        data = resp.json()

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

        resp = await client.post("/v1/user-model", json=model)
        assert resp.status_code == 201, f"Create failed: {resp.json()}"

        resp = await client.get(f"/v1/user-model/{model['user_id']}")
        assert resp.status_code == 200
        data = resp.json()

        assert data["user_id"] == model["user_id"]
        assert data["model_version"] == model["model_version"]
        assert len(data["expertise"]) == 3
        assert data["communication"]["verbosity"] == -0.6

    async def test_knowledge_store_spec_example_import(self, client):
        """POST entries from knowledge-store.json via import, then list and search."""
        path = SPEC_EXAMPLES / "knowledge-store.json"
        if not path.exists():
            pytest.skip("spec example not found")

        store = json.loads(path.read_text())
        user_id = store["user_id"]

        resp = await client.post("/v1/import", json=store)
        assert resp.status_code == 200
        assert resp.json()["imported"] == 3

        # LIST
        resp = await client.get("/v1/knowledge", params={"user_id": user_id})
        assert resp.status_code == 200
        assert len(resp.json()) == 3

        # SEARCH for "unwrap" — should find the correction entry
        resp = await client.get(
            "/v1/knowledge",
            params={"query": "unwrap", "user_id": user_id},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestPrePopulatedE2E:
    """E2E tests using the populated_client fixture with pre-seeded data.

    Data: user-alice has 3 knowledge entries + 1 user model
          user-bob has 1 knowledge entry
    """

    async def test_list_alice_entries(self, populated_client):
        resp = await populated_client.get("/v1/knowledge", params={"user_id": "user-alice"})
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    async def test_list_bob_entries(self, populated_client):
        resp = await populated_client.get("/v1/knowledge", params={"user_id": "user-bob"})
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_search_alice_rust(self, populated_client):
        """Search for 'Rust' in alice's entries should match fact + correction."""
        resp = await populated_client.get(
            "/v1/knowledge",
            params={"user_id": "user-alice", "query": "Rust"},
        )
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) >= 1

    async def test_search_alice_unwrap(self, populated_client):
        resp = await populated_client.get(
            "/v1/knowledge",
            params={"user_id": "user-alice", "query": "unwrap"},
        )
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 1
        assert results[0]["category"] == "correction"

    async def test_get_alice_user_model(self, populated_client):
        resp = await populated_client.get("/v1/user-model/user-alice")
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "user-alice"

    async def test_export_alice(self, populated_client):
        resp = await populated_client.post("/v1/export", json={"user_id": "user-alice"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "user-alice"
        assert len(data["entries"]) == 3
        assert "metadata" in data
        assert "user_model" in data["metadata"]

    async def test_export_includes_user_model(self, populated_client):
        """Spec Section 6.4: export response includes User Model in metadata."""
        resp = await populated_client.post("/v1/export", json={"user_id": "user-alice"})
        data = resp.json()
        assert data["metadata"]["user_model"]["user_id"] == "user-alice"

    async def test_delete_alice_model_removes_everything(self, populated_client):
        """Deleting alice's user model should remove model + all knowledge."""
        resp = await populated_client.delete("/v1/user-model/user-alice")
        assert resp.status_code == 204

        # Model gone
        resp = await populated_client.get("/v1/user-model/user-alice")
        assert resp.status_code == 404

        # Knowledge gone
        resp = await populated_client.get("/v1/knowledge", params={"user_id": "user-alice"})
        assert resp.status_code == 200
        assert len(resp.json()) == 0

    async def test_bob_unaffected_by_alice_delete(self, populated_client):
        """Deleting alice's data should not affect bob's data."""
        await populated_client.delete("/v1/user-model/user-alice")

        resp = await populated_client.get("/v1/knowledge", params={"user_id": "user-bob"})
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_patch_alice_entry_confidence(self, populated_client):
        """PATCH confidence on one of alice's entries."""
        resp = await populated_client.patch(
            "/v1/knowledge/a0000001-e29b-41d4-a716-446655440001",
            json={"confidence": 0.99},
        )
        assert resp.status_code == 200
        assert resp.json()["confidence"] == 0.99

    async def test_import_export_cycle(self, populated_client):
        """Full E2E: export alice → delete everything → re-import → verify."""
        # Export first
        resp = await populated_client.post("/v1/export", json={"user_id": "user-alice"})
        assert resp.status_code == 200
        exported = resp.json()
        assert len(exported["entries"]) == 3

        # Delete all knowledge for alice
        for entry_id in ["a0000001-e29b-41d4-a716-446655440001",
                         "a0000002-e29b-41d4-a716-446655440002",
                         "a0000003-e29b-41d4-a716-446655440003"]:
            await populated_client.delete(f"/v1/knowledge/{entry_id}")

        # Verify empty
        resp = await populated_client.get("/v1/knowledge", params={"user_id": "user-alice"})
        assert len(resp.json()) == 0

        # Re-import
        import_payload = {
            "oamp_version": "1.0.0",
            "type": "knowledge_store",
            "user_id": "user-alice",
            "entries": exported["entries"],
        }
        resp = await populated_client.post("/v1/import", json=import_payload)
        assert resp.status_code == 200
        assert resp.json()["imported"] == 3

        # Verify restored
        resp = await populated_client.get("/v1/knowledge", params={"user_id": "user-alice"})
        assert len(resp.json()) == 3