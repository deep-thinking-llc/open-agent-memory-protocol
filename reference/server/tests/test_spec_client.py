"""Spec-implementing client simulation tests.

These tests simulate exactly what a client implementing the OAMP specification
would do: load spec example JSON files, make HTTP calls to the server, and
verify responses match the spec-defined format and behavior.

Tests use only the HTTP API — no internal imports, exactly like a real client.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SPEC_EXAMPLES = Path(__file__).resolve().parents[3] / "spec" / "v1" / "examples"


class TestSpecClientKnowledgeLifecycle:
    """Full knowledge entry lifecycle as a spec-implementing client would call it.

    A real client would:
    1. POST a knowledge entry with the exact spec example format
    2. GET the entry and verify the full response matches what was sent
    3. Search for the entry by content
    4. PATCH confidence and verify
    5. DELETE the entry and verify 404 on subsequent GET
    """

    @pytest.mark.skipif(
        not (SPEC_EXAMPLES / "knowledge-entry.json").exists(),
        reason="spec example knowledge-entry.json not found",
    )
    async def test_full_knowledge_lifecycle_with_spec_example(self, client):
        """Complete CRUD lifecycle using the spec example JSON.

        Sequence: POST → GET → SEARCH → PATCH → GET (verify patch) → DELETE → GET (verify 404)
        """
        # ── Step 1: Load spec example ──
        raw_entry = json.loads((SPEC_EXAMPLES / "knowledge-entry.json").read_text())

        # ── Step 2: POST (Create) ──
        resp = await client.post("/v1/knowledge", json=raw_entry)
        assert resp.status_code == 201, f"Create failed: {resp.text}"
        created = resp.json()

        # Verify all top-level fields from spec example are preserved
        assert created["id"] == raw_entry["id"]
        assert created["user_id"] == raw_entry["user_id"]
        assert created["category"] == raw_entry["category"]
        assert created["content"] == raw_entry["content"]
        assert created["confidence"] == raw_entry["confidence"]
        assert created["oamp_version"] == raw_entry["oamp_version"]
        assert created["type"] == raw_entry["type"]

        # Verify nested source object
        assert created["source"]["session_id"] == raw_entry["source"]["session_id"]
        assert created["source"]["agent_id"] == raw_entry["source"]["agent_id"]
        assert "timestamp" in created["source"]

        # Verify nested decay object
        assert created["decay"]["half_life_days"] == raw_entry["decay"]["half_life_days"]
        assert "last_confirmed" in created["decay"]

        # Verify tags array
        assert created["tags"] == raw_entry["tags"]

        # Verify metadata
        assert created["metadata"] is not None

        # ── Step 3: GET (Read) ──
        resp = await client.get(f"/v1/knowledge/{raw_entry['id']}")
        assert resp.status_code == 200, f"Get failed: {resp.text}"
        fetched = resp.json()

        # Full field-by-field comparison
        assert fetched["id"] == raw_entry["id"]
        assert fetched["user_id"] == raw_entry["user_id"]
        assert fetched["category"] == raw_entry["category"]
        assert fetched["content"] == raw_entry["content"]
        assert fetched["confidence"] == raw_entry["confidence"]
        assert fetched["source"]["session_id"] == raw_entry["source"]["session_id"]
        assert fetched["tags"] == raw_entry["tags"]
        assert fetched["decay"]["half_life_days"] == raw_entry["decay"]["half_life_days"]

        # Spec mandates type and oamp_version in responses
        assert fetched["type"] == "knowledge_entry"
        assert fetched["oamp_version"] == "1.0.0"

        # ── Step 4: SEARCH ──
        # Search by a keyword in the content
        search_term = "concise"
        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": raw_entry["user_id"], "query": search_term},
        )
        assert resp.status_code == 200, f"Search failed: {resp.text}"
        search_results = resp.json()
        assert len(search_results) >= 1
        assert search_term in search_results[0]["content"]

        # ── Step 5: PATCH confidence ──
        resp = await client.patch(
            f"/v1/knowledge/{raw_entry['id']}",
            json={"confidence": 0.99},
        )
        assert resp.status_code == 200, f"Patch failed: {resp.text}"
        patched = resp.json()
        assert patched["confidence"] == 0.99
        # Verify other fields unchanged
        assert patched["content"] == raw_entry["content"]
        assert patched["user_id"] == raw_entry["user_id"]

        # ── Step 6: PATCH tags ──
        resp = await client.patch(
            f"/v1/knowledge/{raw_entry['id']}",
            json={"tags": ["updated-tag"]},
        )
        assert resp.status_code == 200
        assert resp.json()["tags"] == ["updated-tag"]

        # ── Step 7: DELETE ──
        resp = await client.delete(f"/v1/knowledge/{raw_entry['id']}")
        assert resp.status_code == 204, f"Delete failed: {resp.text}"
        # 204 must have empty body
        assert resp.content == b""

        # ── Step 8: GET after delete — must be 404 ──
        resp = await client.get(f"/v1/knowledge/{raw_entry['id']}")
        assert resp.status_code == 404, "Deleted entry should return 404"

        # Verify error response format (spec §6.8)
        error_body = resp.json()
        assert "error" in error_body
        assert "code" in error_body
        assert error_body["code"] == "NOT_FOUND"


class TestSpecClientUserModelLifecycle:
    """Full user model lifecycle as a spec-implementing client would call it."""

    @pytest.mark.skipif(
        not (SPEC_EXAMPLES / "user-model.json").exists(),
        reason="spec example user-model.json not found",
    )
    async def test_full_user_model_lifecycle_with_spec_example(self, client):
        """Full lifecycle using the spec example user-model.json.

        Sequence: POST (v1) → GET → POST (v2, expecting 200) → GET v2 → DELETE → GET (verify 404)
        """
        # ── Step 1: Load spec example ──
        raw_model = json.loads((SPEC_EXAMPLES / "user-model.json").read_text())
        user_id = raw_model["user_id"]

        # ── Step 2: POST (Create, expect 201) ──
        resp = await client.post("/v1/user-model", json=raw_model)
        assert resp.status_code == 201, f"Create failed: {resp.text}"
        created = resp.json()

        # Verify top-level fields
        assert created["user_id"] == user_id
        assert created["model_version"] == raw_model["model_version"]
        assert created["oamp_version"] == raw_model["oamp_version"]
        assert created["type"] == "user_model"

        # Verify communication profile
        assert created["communication"]["verbosity"] == raw_model["communication"]["verbosity"]
        assert created["communication"]["formality"] == raw_model["communication"]["formality"]
        assert created["communication"]["languages"] == raw_model["communication"]["languages"]

        # Verify expertise array (3 entries in spec example)
        assert len(created["expertise"]) == len(raw_model["expertise"])
        for i, exp in enumerate(raw_model["expertise"]):
            assert created["expertise"][i]["domain"] == exp["domain"]
            assert created["expertise"][i]["level"] == exp["level"]
            assert created["expertise"][i]["confidence"] == exp["confidence"]

        # Verify corrections
        assert len(created["corrections"]) == len(raw_model["corrections"])

        # Verify stated_preferences (2 entries in spec example)
        assert len(created["stated_preferences"]) == len(raw_model["stated_preferences"])

        # ── Step 3: GET ──
        resp = await client.get(f"/v1/user-model/{user_id}")
        assert resp.status_code == 200
        fetched = resp.json()
        assert fetched["user_id"] == user_id
        assert fetched["model_version"] == raw_model["model_version"]

        # ── Step 4: POST version 2 (Update, expect 200) ──
        model_v2 = dict(raw_model)
        model_v2["model_version"] = raw_model["model_version"] + 1
        model_v2["communication"] = {
            "verbosity": 0.0,
            "formality": 0.5,
            "prefers_examples": False,
            "prefers_explanations": True,
            "languages": ["en"],
        }
        resp = await client.post("/v1/user-model", json=model_v2)
        assert resp.status_code == 200, f"Update failed: {resp.text}"
        updated = resp.json()
        assert updated["model_version"] == raw_model["model_version"] + 1
        assert updated["communication"]["verbosity"] == 0.0

        # ── Step 5: POST same version (Version conflict, expect 409) ──
        resp = await client.post("/v1/user-model", json=model_v2)
        assert resp.status_code == 409, f"Expected 409 for same version, got {resp.status_code}"
        error_body = resp.json()
        assert error_body["code"] == "VERSION_CONFLICT"

        # ── Step 6: POST lower version (Version conflict, expect 409) ──
        model_lower = dict(raw_model)
        model_lower["model_version"] = 1
        resp = await client.post("/v1/user-model", json=model_lower)
        assert resp.status_code == 409

        # ── Step 7: DELETE ──
        resp = await client.delete(f"/v1/user-model/{user_id}")
        assert resp.status_code == 204
        assert resp.content == b""

        # ── Step 8: GET after delete — must be 404 ──
        resp = await client.get(f"/v1/user-model/{user_id}")
        assert resp.status_code == 404


class TestSpecClientImportExport:
    """Full import/export workflow as a spec-implementing client would call it."""

    @pytest.mark.skipif(
        not (SPEC_EXAMPLES / "knowledge-store.json").exists(),
        reason="spec example knowledge-store.json not found",
    )
    async def test_import_spec_store_then_export_roundtrip(self, client):
        """Import spec example → verify entries exist → export → verify data matches."""
        # ── Step 1: Load spec example ──
        store = json.loads((SPEC_EXAMPLES / "knowledge-store.json").read_text())
        user_id = store["user_id"]
        entry_count = len(store["entries"])

        # ── Step 2: Import ──
        resp = await client.post("/v1/import", json=store)
        assert resp.status_code == 200, f"Import failed: {resp.text}"
        import_result = resp.json()
        assert import_result["imported"] == entry_count
        assert import_result["user_id"] == user_id
        assert import_result["skipped"] == 0
        assert import_result["rejected"] == 0

        # ── Step 3: List entries — should show all imported ──
        resp = await client.get("/v1/knowledge", params={"user_id": user_id})
        assert resp.status_code == 200
        entries = resp.json()
        assert len(entries) == entry_count

        # Verify each entry from the store is present
        imported_ids = {e["id"] for e in entries}
        expected_ids = {e["id"] for e in store["entries"]}
        assert imported_ids == expected_ids

        # ── Step 4: Search across all entries ──
        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": user_id, "query": "unwrap"},
        )
        assert resp.status_code == 200
        # Should find the correction entry about unwrap()
        assert len(resp.json()) >= 1
        assert any("unwrap" in e["content"] for e in resp.json())

        # ── Step 5: Export — should get back the same entries ──
        resp = await client.post("/v1/export", json={"user_id": user_id})
        assert resp.status_code == 200
        exported = resp.json()
        assert exported["user_id"] == user_id
        assert len(exported["entries"]) == entry_count
        assert exported["oamp_version"] == "1.0.0"
        assert exported["type"] == "knowledge_store"
        assert "exported_at" in exported

        # ── Step 6: Export also returns metadata (with user_model if exists) ──
        assert "metadata" in exported
        # User model not created yet, so metadata should be empty
        # (We didn't create a user model in this test)

    @pytest.mark.skipif(
        not (SPEC_EXAMPLES / "knowledge-store.json").exists(),
        reason="spec example knowledge-store.json not found",
    )
    async def test_export_includes_user_model_when_present(self, client):
        """Export should include user model in metadata when it exists (spec §6.4)."""
        store = json.loads((SPEC_EXAMPLES / "knowledge-store.json").read_text())
        user_id = store["user_id"]

        # Import store
        await client.post("/v1/import", json=store)

        # Create a user model for this user
        user_model_data = json.loads((SPEC_EXAMPLES / "user-model.json").read_text())
        user_model_data["user_id"] = user_id
        user_model_data["model_version"] = 1
        resp = await client.post("/v1/user-model", json=user_model_data)
        assert resp.status_code == 201

        # Export should include user model in metadata
        resp = await client.post("/v1/export", json={"user_id": user_id})
        assert resp.status_code == 200
        exported = resp.json()
        assert "user_model" in exported["metadata"]
        assert exported["metadata"]["user_model"]["user_id"] == user_id
        assert exported["metadata"]["user_model"]["model_version"] == 1


class TestSpecClientSearch:
    """Search behavior exactly as a spec-implementing client expects."""

    async def test_search_with_pagination(self, client, make_knowledge_entry):
        """Search results should respect limit/offset pagination."""
        user_id = "user-spec-search-page"

        # Create 5 entries with searchable content
        entry_ids = [
            "33b6c9a2-ea6e-4a9c-8481-7071c59bb7cd",
            "a1e99253-4488-4ac8-8572-c452bffc42a1",
            "bd3e45ce-627a-4ddf-8fa7-adabab716240",
            "eb86b486-cca6-41f9-9667-57653fb0253d",
            "1663a0fe-5170-4af3-b00d-dd7ef598765f",
        ]
        for i in range(5):
            entry = make_knowledge_entry(
                user_id=user_id,
                content=f"Spec pagination search topic number {i}",
            )
            entry["id"] = entry_ids[i]
            resp = await client.post("/v1/knowledge", json=entry)
            assert resp.status_code == 201

        # Search with limit=2, offset=0
        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": user_id, "query": "topic", "limit": 2, "offset": 0},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

        # Search with limit=2, offset=2
        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": user_id, "query": "topic", "limit": 2, "offset": 2},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

        # Search with limit=2, offset=4 (should return 1)
        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": user_id, "query": "topic", "limit": 2, "offset": 4},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_search_no_results_returns_empty_array(self, client, make_knowledge_entry):
        """Search with no matches returns empty array (not 404)."""
        entry = make_knowledge_entry(
            user_id="user-spec-empty",
            content="Rust programming",
        )
        await client.post("/v1/knowledge", json=entry)

        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-spec-empty", "query": "quantum-computing"},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_search_multi_word_phrase(self, client, make_knowledge_entry):
        """Multi-word search queries should work (FTS5)."""
        entry = make_knowledge_entry(
            user_id="user-spec-phrase",
            content="Kubernetes deployment with Helm charts and monitoring",
        )
        entry["id"] = "05d6c808-0e5f-4a55-839e-dd573b83056e"
        await client.post("/v1/knowledge", json=entry)

        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-spec-phrase", "query": "Kubernetes Helm"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


class TestSpecClientListAndFilter:
    """List and filter behavior as a spec-implementing client expects."""

    async def test_list_across_multiple_categories(self, client, make_knowledge_entry):
        """List with category filter should only return matching entries."""
        user_id = "user-spec-filter"

        # Create entries across categories
        cat_ids = [
            "8922a97d-a0ec-4159-b10c-9ba30b70bdc7",
            "fd2695a4-e46a-466f-bc2b-7ea4c0305157",
            "1cae7aea-e3af-4da3-8dd6-d9ecac80e9a7",
        ]
        for i, cat in enumerate(["fact", "preference", "correction"]):
            entry = make_knowledge_entry(
                user_id=user_id,
                category=cat,
                content=f"Category {cat} entry",
            )
            entry["id"] = cat_ids[i]
            resp = await client.post("/v1/knowledge", json=entry)
            assert resp.status_code == 201

        # List all
        resp = await client.get("/v1/knowledge", params={"user_id": user_id})
        assert len(resp.json()) == 3

        # Filter by category
        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": user_id, "category": "fact"},
        )
        assert len(resp.json()) == 1
        assert resp.json()[0]["category"] == "fact"

    async def test_list_pagination_with_category_filter(self, client, make_knowledge_entry):
        """Pagination with category filter should work correctly."""
        user_id = "user-spec-cat-page"

        cat_page_ids = [
            "1027a626-35d1-489c-817c-c05ec58d1051",
            "9db4845b-0332-4e85-8c3b-13979ebc28a8",
            "f08e1b9a-fed8-4763-9917-cb3e9edcc1e2",
            "a81e1a56-f8ba-4ca2-adac-bd9100f1612e",
            "78c0c853-2d5d-46a2-b6ac-e13b880c51c6",
        ]
        for i in range(5):
            entry = make_knowledge_entry(
                user_id=user_id,
                category="fact",
                content=f"Fact entry {i}",
            )
            entry["id"] = cat_page_ids[i]
            resp = await client.post("/v1/knowledge", json=entry)
            assert resp.status_code == 201

        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": user_id, "category": "fact", "limit": 2, "offset": 0},
        )
        assert len(resp.json()) == 2

        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": user_id, "category": "fact", "limit": 2, "offset": 2},
        )
        assert len(resp.json()) == 2

        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": user_id, "category": "fact", "limit": 2, "offset": 4},
        )
        assert len(resp.json()) == 1


class TestSpecClientErrorHandling:
    """Error handling exactly as a spec-implementing client expects (spec §6.8)."""

    async def test_duplicate_id_returns_409_with_proper_format(self, client, make_knowledge_entry):
        """POST with existing ID returns 409 Conflict with proper error format."""
        entry = make_knowledge_entry(entry_id="3bb5f9af-37ec-4dd2-b777-ab040f608c9b")
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 409
        body = resp.json()
        assert "error" in body
        assert "code" in body
        assert body["code"] == "DUPLICATE_ID"

    async def test_invalid_category_returns_400(self, client, make_knowledge_entry):
        """Invalid category enum value returns 400."""
        entry = make_knowledge_entry(category="not-a-valid-category")
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 400
        body = resp.json()
        assert body["code"] == "VALIDATION_ERROR"

    async def test_forbidden_patch_field_returns_400(self, client, make_knowledge_entry):
        """PATCH on forbidden field returns 400 with FORBIDDEN_PATCH code."""
        entry = make_knowledge_entry()
        await client.post("/v1/knowledge", json=entry)

        resp = await client.patch(
            f"/v1/knowledge/{entry['id']}",
            json={"user_id": "different-user"},
        )
        assert resp.status_code == 400
        body = resp.json()
        assert body["code"] == "FORBIDDEN_PATCH"

    async def test_get_nonexistent_returns_404(self, client):
        """GET on non-existent entry returns 404 with NOT_FOUND code."""
        resp = await client.get(
            "/v1/knowledge/550e8400-e29b-41d4-a716-446655449999"
        )
        assert resp.status_code == 404
        body = resp.json()
        assert body["code"] == "NOT_FOUND"


class TestSpecClientMultiUserIsolation:
    """Multi-user data isolation as a spec-implementing client expects."""

    async def test_users_see_only_own_data(self, client, make_knowledge_entry):
        """Each user should only see their own entries."""
        # Create entries for user-a and user-b
        entry_a = make_knowledge_entry(
            user_id="user-spec-a",
            content="User A's private knowledge",
        )
        entry_a["id"] = "6b4a2ee5-1235-4b5b-852b-a183dd5c9b30"
        await client.post("/v1/knowledge", json=entry_a)

        entry_b = make_knowledge_entry(
            user_id="user-spec-b",
            content="User B's private knowledge",
        )
        entry_b["id"] = "7ac0d837-d1c8-4f6e-950b-ad1b03159901"
        await client.post("/v1/knowledge", json=entry_b)

        # User A lists - should only see A's entry
        resp = await client.get("/v1/knowledge", params={"user_id": "user-spec-a"})
        assert len(resp.json()) == 1
        assert resp.json()[0]["user_id"] == "user-spec-a"

        # User B lists - should only see B's entry
        resp = await client.get("/v1/knowledge", params={"user_id": "user-spec-b"})
        assert len(resp.json()) == 1
        assert resp.json()[0]["user_id"] == "user-spec-b"

        # Search scoped to user A should not find B's data
        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-spec-a", "query": "User B"},
        )
        assert len(resp.json()) == 0

    async def test_delete_user_removes_only_that_users_data(self, client, make_knowledge_entry, make_user_model):
        """Deleting a user model should not affect other users' data."""
        # Create data for user-a and user-b
        entry_a = make_knowledge_entry(
            user_id="user-spec-del-a",
            content="A's data",
        )
        entry_a["id"] = "5beb7404-3da9-4595-8d07-a508f4dae91c"
        await client.post("/v1/knowledge", json=entry_a)

        entry_b = make_knowledge_entry(
            user_id="user-spec-del-b",
            content="B's data",
        )
        entry_b["id"] = "36d26b84-c18c-4ec9-aa44-78df3cde9e2a"
        await client.post("/v1/knowledge", json=entry_b)

        model_b = make_user_model(user_id="user-spec-del-b")
        await client.post("/v1/user-model", json=model_b)

        # Delete user-b
        resp = await client.delete("/v1/user-model/user-spec-del-b")
        assert resp.status_code == 204

        # User A's data should still exist
        resp = await client.get("/v1/knowledge", params={"user_id": "user-spec-del-a"})
        assert len(resp.json()) == 1

        # User B's data should be gone
        resp = await client.get("/v1/knowledge", params={"user_id": "user-spec-del-b"})
        assert len(resp.json()) == 0