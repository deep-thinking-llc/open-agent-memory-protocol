"""Tests for bulk export/import endpoints."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SPEC_EXAMPLES = Path(__file__).resolve().parents[3] / "spec" / "v1" / "examples"


class TestExportKnowledge:
    """GET /v1/export/:user_id"""

    async def test_export_empty_user(self, client):
        """Export for user with no entries returns empty store."""
        resp = await client.get("/v1/export/user-nonexistent")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "user-nonexistent"
        assert data["entries"] == []
        assert data["type"] == "knowledge_store"

    async def test_export_after_create(self, client, make_knowledge_entry):
        """Export after creating entries returns them."""
        uuids = [
            "a0000001-e29b-41d4-a716-446655440001",
            "a0000002-e29b-41d4-a716-446655440002",
        ]
        for i in range(2):
            entry = make_knowledge_entry(user_id="user-export")
            entry["id"] = uuids[i]
            resp = await client.post("/v1/knowledge", json=entry)
            assert resp.status_code == 201

        resp = await client.get("/v1/export/user-export")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "user-export"
        assert len(data["entries"]) == 2
        assert data["type"] == "knowledge_store"
        assert data["oamp_version"] == "1.0.0"
        assert "exported_at" in data

    async def test_export_only_includes_user_entries(self, client, make_knowledge_entry):
        """Export should only include entries for the specified user."""
        # Create entries for two different users
        entry_a = make_knowledge_entry(user_id="user-export-a")
        entry_a["id"] = "b0000001-e29b-41d4-a716-446655440001"
        await client.post("/v1/knowledge", json=entry_a)

        entry_b = make_knowledge_entry(user_id="user-export-b")
        entry_b["id"] = "b0000002-e29b-41d4-a716-446655440002"
        await client.post("/v1/knowledge", json=entry_b)

        # Export user-a should only contain user-a's entry
        resp = await client.get("/v1/export/user-export-a")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["entries"]) == 1
        assert data["entries"][0]["user_id"] == "user-export-a"


class TestImportKnowledge:
    """POST /v1/import"""

    async def test_import_valid_store(self, client, make_knowledge_entry):
        """Import a KnowledgeStore and verify entries are created."""
        # Build a store with 3 entries
        entries = []
        uuids = [
            "c0000001-e29b-41d4-a716-446655440001",
            "c0000002-e29b-41d4-a716-446655440002",
            "c0000003-e29b-41d4-a716-446655440003",
        ]
        for i in range(3):
            entry = make_knowledge_entry(
                user_id="user-import",
                category=["fact", "preference", "correction"][i],
                content=f"Imported entry {i + 1}",
            )
            entry["id"] = uuids[i]
            entries.append(entry)

        store = {
            "oamp_version": "1.0.0",
            "type": "knowledge_store",
            "user_id": "user-import",
            "entries": entries,
        }

        resp = await client.post("/v1/import", json=store)
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"] == 3
        assert data["user_id"] == "user-import"

        # Verify entries are retrievable
        resp = await client.get("/v1/knowledge", params={"user_id": "user-import"})
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    async def test_import_empty_store(self, client):
        """Import an empty store returns 0."""
        store = {
            "oamp_version": "1.0.0",
            "type": "knowledge_store",
            "user_id": "user-import-empty",
            "entries": [],
        }
        resp = await client.post("/v1/import", json=store)
        assert resp.status_code == 200
        assert resp.json()["imported"] == 0

    async def test_import_invalid_entry_in_store(self, client):
        """Import with invalid entry returns validation error."""
        store = {
            "oamp_version": "1.0.0",
            "type": "knowledge_store",
            "user_id": "user-import-err",
            "entries": [
                {
                    "oamp_version": "1.0.0",
                    "type": "knowledge_entry",
                    "id": "d0000001-e29b-41d4-a716-446655440001",
                    "user_id": "user-import-err",
                    "category": "fact",
                    "content": "Valid entry",
                    "confidence": 0.8,
                    "source": {"session_id": "s1", "timestamp": "2026-04-01T14:30:00Z"},
                },
                {
                    "oamp_version": "1.0.0",
                    "type": "knowledge_entry",
                    "id": "d0000002-e29b-41d4-a716-446655440002",
                    "user_id": "user-import-err",
                    "category": "invalid_category",  # Invalid!
                    "content": "Bad entry",
                    "confidence": 0.8,
                    "source": {"session_id": "s2", "timestamp": "2026-04-01T14:30:00Z"},
                },
            ],
        }
        resp = await client.post("/v1/import", json=store)
        assert resp.status_code == 400

    async def test_import_then_export_roundtrip(self, client, make_knowledge_entry):
        """Import a store, then export should return the same entries."""
        entries = []
        uuids = [
            "e0000001-e29b-41d4-a716-446655440001",
            "e0000002-e29b-41d4-a716-446655440002",
        ]
        for i in range(2):
            entry = make_knowledge_entry(
                user_id="user-rt",
                content=f"Round-trip entry {i + 1}",
            )
            entry["id"] = uuids[i]
            entries.append(entry)

        store = {
            "oamp_version": "1.0.0",
            "type": "knowledge_store",
            "user_id": "user-rt",
            "entries": entries,
        }

        # Import
        resp = await client.post("/v1/import", json=store)
        assert resp.status_code == 200
        assert resp.json()["imported"] == 2

        # Export
        resp = await client.get("/v1/export/user-rt")
        assert resp.status_code == 200
        exported = resp.json()
        assert len(exported["entries"]) == 2
        exported_ids = {e["id"] for e in exported["entries"]}
        assert exported_ids == {uuids[0], uuids[1]}

    async def test_import_spec_knowledge_store_example(self, client):
        """Import the spec example knowledge-store.json."""
        path = SPEC_EXAMPLES / "knowledge-store.json"
        if not path.exists():
            pytest.skip("spec example not found")

        store = json.loads(path.read_text())

        resp = await client.post("/v1/import", json=store)
        assert resp.status_code == 200
        assert resp.json()["imported"] == 3

        # Verify via list
        resp = await client.get("/v1/knowledge", params={"user_id": store["user_id"]})
        assert resp.status_code == 200
        assert len(resp.json()) == 3