"""Tests for knowledge entry CRUD endpoints."""

from __future__ import annotations

import pytest


class TestCreateKnowledge:
    """POST /v1/knowledge"""

    async def test_create_valid_entry(self, client, make_knowledge_entry):
        entry = make_knowledge_entry()
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == entry["id"]
        assert data["user_id"] == entry["user_id"]
        assert data["category"] == entry["category"]
        assert data["content"] == entry["content"]
        assert data["confidence"] == entry["confidence"]

    async def test_create_with_optional_fields(self, client, make_knowledge_entry):
        entry = make_knowledge_entry()
        entry["decay"] = {"half_life_days": 70.0, "last_confirmed": "2026-04-01T14:30:00Z"}
        entry["tags"] = ["test", "automated"]
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201
        data = resp.json()
        assert data["decay"]["half_life_days"] == 70.0
        assert data["tags"] == ["test", "automated"]

    async def test_create_with_unknown_metadata(self, client, make_knowledge_entry):
        """Spec Section 9: MUST NOT reject documents with unknown metadata fields."""
        entry = make_knowledge_entry()
        entry["metadata"] = {"custom_key": "custom_value", "vendor_ext": 42}
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

    async def test_create_invalid_confidence(self, client, make_knowledge_entry):
        entry = make_knowledge_entry(confidence=1.5)
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 400

    async def test_create_empty_content(self, client, make_knowledge_entry):
        entry = make_knowledge_entry(content="")
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 400

    async def test_create_invalid_category(self, client, make_knowledge_entry):
        entry = make_knowledge_entry(category="unknown")
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 400

    async def test_create_missing_source(self, client, make_knowledge_entry):
        entry = make_knowledge_entry()
        del entry["source"]
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 400

    async def test_create_invalid_oamp_version(self, client, make_knowledge_entry):
        entry = make_knowledge_entry()
        entry["oamp_version"] = "2.0.0"
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 400


class TestGetKnowledge:
    """GET /v1/knowledge/:id"""

    async def test_get_existing_entry(self, client, make_knowledge_entry):
        entry = make_knowledge_entry()
        await client.post("/v1/knowledge", json=entry)
        resp = await client.get(f"/v1/knowledge/{entry['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == entry["id"]

    async def test_get_nonexistent_entry(self, client):
        resp = await client.get("/v1/knowledge/ nonexistent-id")
        assert resp.status_code == 404
        body = resp.json()
        assert "error" in body
        assert "code" in body


class TestDeleteKnowledge:
    """DELETE /v1/knowledge/:id"""

    async def test_delete_existing_entry(self, client, make_knowledge_entry):
        entry = make_knowledge_entry()
        await client.post("/v1/knowledge", json=entry)
        resp = await client.delete(f"/v1/knowledge/{entry['id']}")
        assert resp.status_code == 204

        # Verify it's gone
        resp = await client.get(f"/v1/knowledge/{entry['id']}")
        assert resp.status_code == 404

    async def test_delete_nonexistent_entry(self, client):
        resp = await client.delete("/v1/knowledge/nonexistent-id")
        assert resp.status_code == 404


class TestListKnowledge:
    """GET /v1/knowledge?user_id=..."""

    async def test_list_entries(self, client, make_knowledge_entry):
        # Create 3 entries for user-1
        uuids = [
            "11111111-1111-4111-a111-111111111111",
            "22222222-2222-4222-a222-222222222222",
            "33333333-3333-4333-a333-333333333333",
        ]
        for i in range(3):
            entry = make_knowledge_entry(user_id="user-1")
            entry["id"] = uuids[i]
            resp = await client.post("/v1/knowledge", json=entry)
            assert resp.status_code == 201

        # Create 1 entry for user-2
        entry2 = make_knowledge_entry(user_id="user-2")
        entry2["id"] = "44444444-4444-4444-a444-444444444444"
        resp = await client.post("/v1/knowledge", json=entry2)
        assert resp.status_code == 201

        # List user-1 should return 3
        resp = await client.get("/v1/knowledge", params={"user_id": "user-1"})
        assert resp.status_code == 200
        assert len(resp.json()) == 3

        # List user-2 should return 1
        resp = await client.get("/v1/knowledge", params={"user_id": "user-2"})
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_list_with_category_filter(self, client, make_knowledge_entry):
        uuids = [
            "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        ]
        for i, cat in enumerate(["fact", "preference", "correction"]):
            entry = make_knowledge_entry(user_id="user-filter", category=cat)
            entry["id"] = uuids[i]
            resp = await client.post("/v1/knowledge", json=entry)
            assert resp.status_code == 201, f"Failed to create {cat}: {resp.json()}"

        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-filter", "category": "fact"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["category"] == "fact"

    async def test_list_pagination(self, client, make_knowledge_entry):
        uuids = [
            "d0000000-d000-4d00-8d00-d00000000001",
            "d0000000-d000-4d00-8d00-d00000000002",
            "d0000000-d000-4d00-8d00-d00000000003",
            "d0000000-d000-4d00-8d00-d00000000004",
            "d0000000-d000-4d00-8d00-d00000000005",
        ]
        for i in range(5):
            entry = make_knowledge_entry(user_id="user-page")
            entry["id"] = uuids[i]
            resp = await client.post("/v1/knowledge", json=entry)
            assert resp.status_code == 201

        # Page 1: limit=2, offset=0
        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-page", "limit": 2, "offset": 0},
        )
        assert len(resp.json()) == 2

        # Page 2: limit=2, offset=2
        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-page", "limit": 2, "offset": 2},
        )
        assert len(resp.json()) == 2

        # Page 3: limit=2, offset=4
        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-page", "limit": 2, "offset": 4},
        )
        assert len(resp.json()) == 1