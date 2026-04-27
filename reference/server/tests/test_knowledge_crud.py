"""E2E tests for knowledge entry CRUD + search endpoints.

Covers: POST /v1/knowledge, GET /v1/knowledge (list + search),
GET /v1/knowledge/:id, PATCH /v1/knowledge/:id, DELETE /v1/knowledge/:id

Spec compliance: Section 6.2 (Knowledge Endpoints), Section 6.6 (Search)
"""

from __future__ import annotations


class TestCreateKnowledge:
    """POST /v1/knowledge — spec Section 6.2"""

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

    async def test_create_duplicate_id_returns_409(self, client, make_knowledge_entry):
        """Second POST with same ID should return 409 Conflict."""
        entry = make_knowledge_entry(entry_id="d0000001-e29b-41d4-a716-446655440001")
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 409
        body = resp.json()
        assert "error" in body
        assert "code" in body

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

    async def test_create_negative_confidence(self, client, make_knowledge_entry):
        entry = make_knowledge_entry(confidence=-0.1)
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 400


class TestGetKnowledge:
    """GET /v1/knowledge/:id — spec Section 6.2"""

    async def test_get_existing_entry(self, client, make_knowledge_entry):
        entry = make_knowledge_entry()
        await client.post("/v1/knowledge", json=entry)
        resp = await client.get(f"/v1/knowledge/{entry['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == entry["id"]

    async def test_get_nonexistent_entry(self, client):
        resp = await client.get("/v1/knowledge/nonexistent-id")
        assert resp.status_code == 404
        body = resp.json()
        assert "error" in body
        assert "code" in body
        assert body["code"] == "NOT_FOUND"

    async def test_get_returns_full_entry(self, client, make_knowledge_entry):
        """GET should return all fields including optional ones."""
        entry = make_knowledge_entry()
        entry["tags"] = ["rust", "safety"]
        entry["decay"] = {"half_life_days": 35.0}
        await client.post("/v1/knowledge", json=entry)

        resp = await client.get(f"/v1/knowledge/{entry['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert "source" in data
        assert data["tags"] == ["rust", "safety"]


class TestDeleteKnowledge:
    """DELETE /v1/knowledge/:id — spec Section 6.2"""

    async def test_delete_existing_entry(self, client, make_knowledge_entry):
        """Spec: 204 No Content, MUST permanently delete (not soft-delete)."""
        entry = make_knowledge_entry()
        await client.post("/v1/knowledge", json=entry)
        resp = await client.delete(f"/v1/knowledge/{entry['id']}")
        assert resp.status_code == 204

        # Verify permanent deletion
        resp = await client.get(f"/v1/knowledge/{entry['id']}")
        assert resp.status_code == 404

    async def test_delete_nonexistent_entry(self, client):
        resp = await client.delete("/v1/knowledge/nonexistent-id")
        assert resp.status_code == 404

    async def test_delete_returns_empty_body(self, client, make_knowledge_entry):
        """Spec: 204 No Content should have empty body."""
        entry = make_knowledge_entry()
        await client.post("/v1/knowledge", json=entry)
        resp = await client.delete(f"/v1/knowledge/{entry['id']}")
        assert resp.status_code == 204
        assert resp.content == b""


class TestListKnowledge:
    """GET /v1/knowledge?user_id=... — spec Section 6.2 / 6.6"""

    async def test_list_entries(self, client, make_knowledge_entry):
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

        entry2 = make_knowledge_entry(user_id="user-2")
        entry2["id"] = "44444444-4444-4444-a444-444444444444"
        await client.post("/v1/knowledge", json=entry2)

        resp = await client.get("/v1/knowledge", params={"user_id": "user-1"})
        assert resp.status_code == 200
        assert len(resp.json()) == 3

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
            assert resp.status_code == 201

        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-filter", "category": "fact"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["category"] == "fact"

    async def test_list_pagination(self, client, make_knowledge_entry):
        uuids = [
            "d0000001-e29b-41d4-a716-446655440001",
            "d0000002-e29b-41d4-a716-446655440002",
            "d0000003-e29b-41d4-a716-446655440003",
            "d0000004-e29b-41d4-a716-446655440004",
            "d0000005-e29b-41d4-a716-446655440005",
        ]
        for i in range(5):
            entry = make_knowledge_entry(user_id="user-page")
            entry["id"] = uuids[i]
            resp = await client.post("/v1/knowledge", json=entry)
            assert resp.status_code == 201

        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-page", "limit": 2, "offset": 0},
        )
        assert len(resp.json()) == 2

        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-page", "limit": 2, "offset": 2},
        )
        assert len(resp.json()) == 2

        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-page", "limit": 2, "offset": 4},
        )
        assert len(resp.json()) == 1

    async def test_list_user_with_no_entries(self, client):
        """Listing for a non-existent user should return empty list."""
        resp = await client.get("/v1/knowledge", params={"user_id": "user-none"})
        assert resp.status_code == 200
        assert resp.json() == []


class TestSearchKnowledge:
    """GET /v1/knowledge?user_id=...&query=... — spec Section 6.6"""

    async def test_search_by_content(self, client, make_knowledge_entry):
        uuids = [
            "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        ]
        for i, content in enumerate(["Rust programming", "Python scripting", "Go concurrency"]):
            entry = make_knowledge_entry(user_id="user-search", content=content)
            entry["id"] = uuids[i]
            resp = await client.post("/v1/knowledge", json=entry)
            assert resp.status_code == 201

        # Spec: query= parameter for search
        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-search", "query": "Rust"},
        )
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 1
        assert "Rust" in results[0]["content"]

    async def test_search_case_insensitive(self, client, make_knowledge_entry):
        entry = make_knowledge_entry(user_id="user-ci", content="Concurrent Processing")
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-ci", "query": "concurrent"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_search_scoped_to_user(self, client, make_knowledge_entry):
        entry_a = make_knowledge_entry(user_id="user-a", content="Rust is great")
        entry_a["id"] = "f0000001-e29b-41d4-a716-446655440001"
        resp = await client.post("/v1/knowledge", json=entry_a)
        assert resp.status_code == 201

        entry_b = make_knowledge_entry(user_id="user-b", content="Rust is fast")
        entry_b["id"] = "f0000002-e29b-41d4-a716-446655440002"
        resp = await client.post("/v1/knowledge", json=entry_b)
        assert resp.status_code == 201

        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-a", "query": "Rust"},
        )
        results = resp.json()
        assert len(results) == 1
        assert results[0]["user_id"] == "user-a"

    async def test_search_with_category_filter(self, client, make_knowledge_entry):
        uuids = [
            "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        ]
        for i, cat in enumerate(["fact", "preference"]):
            entry = make_knowledge_entry(
                user_id="user-search-cat",
                category=cat,
                content=f"This is a {cat} about Rust",
            )
            entry["id"] = uuids[i]
            resp = await client.post("/v1/knowledge", json=entry)
            assert resp.status_code == 201

        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-search-cat", "query": "Rust", "category": "fact"},
        )
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 1
        assert results[0]["category"] == "fact"

    async def test_search_no_results(self, client, make_knowledge_entry):
        entry = make_knowledge_entry(user_id="user-empty", content="Rust is great")
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-empty", "query": "quantum computing"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 0

    async def test_search_porter_stemming(self, client, make_knowledge_entry):
        """FTS5 Porter stemmer: searching 'programming' should match 'programs'."""
        entry = make_knowledge_entry(
            user_id="user-stem",
            content="The user programs in Rust and Go",
        )
        entry["id"] = "fa000001-e29b-41d4-a716-446655440001"
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-stem", "query": "programming"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_search_multi_word_query(self, client, make_knowledge_entry):
        """FTS5 multi-word queries should work."""
        entry = make_knowledge_entry(
            user_id="user-multi",
            content="Kubernetes deployment with Helm charts",
        )
        entry["id"] = "fa000002-e29b-41d4-a716-446655440002"
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-multi", "query": "Kubernetes Helm"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_search_pagination(self, client, make_knowledge_entry):
        """Search results should respect limit/offset."""
        for i in range(5):
            entry = make_knowledge_entry(
                user_id="user-search-page",
                content=f"Rust memory safety topic {i}",
            )
            entry["id"] = f"f{i+1:07d}-e29b-41d4-a716-446655440000"
            resp = await client.post("/v1/knowledge", json=entry)
            assert resp.status_code == 201

        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-search-page", "query": "Rust", "limit": 2},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    async def test_list_with_negative_limit_clamped(self, client, make_knowledge_entry):
        """Negative limit should be clamped to valid range."""
        entry = make_knowledge_entry(user_id="user-clamp")
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        resp = await client.get(
            "/v1/knowledge",
            params={"user_id": "user-clamp", "limit": -5},
        )
        assert resp.status_code == 200