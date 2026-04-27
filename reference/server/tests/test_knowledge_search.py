"""Tests for search endpoint."""

from __future__ import annotations


class TestSearchKnowledge:
    """GET /v1/knowledge/search?q=...&user_id=..."""

    async def test_search_by_content(self, client, make_knowledge_entry):
        uuids = [
            "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        ]
        for i, (content, _) in enumerate([("Rust programming", 1), ("Python scripting", 2), ("Go concurrency", 3)]):
            entry = make_knowledge_entry(
                user_id="user-search",
                content=content,
            )
            entry["id"] = uuids[i]
            resp = await client.post("/v1/knowledge", json=entry)
            assert resp.status_code == 201

        resp = await client.get(
            "/v1/knowledge/search",
            params={"q": "Rust", "user_id": "user-search"},
        )
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 1
        assert "Rust" in results[0]["content"]

    async def test_search_case_insensitive(self, client, make_knowledge_entry):
        entry = make_knowledge_entry(user_id="user-ci", content="Concurrent Processing")
        await client.post("/v1/knowledge", json=entry)

        resp = await client.get(
            "/v1/knowledge/search",
            params={"q": "concurrent", "user_id": "user-ci"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_search_scoped_to_user(self, client, make_knowledge_entry):
        # User A has knowledge about Rust
        entry_a = make_knowledge_entry(user_id="user-a", content="Rust is great")
        entry_a["id"] = "f0000001-e29b-41d4-a716-446655440000"
        resp = await client.post("/v1/knowledge", json=entry_a)
        assert resp.status_code == 201

        # User B has knowledge about Rust too
        entry_b = make_knowledge_entry(user_id="user-b", content="Rust is fast")
        entry_b["id"] = "f0000002-e29b-41d4-a716-446655440000"
        resp = await client.post("/v1/knowledge", json=entry_b)
        assert resp.status_code == 201

        # Search user-a should only return user-a's entry
        resp = await client.get(
            "/v1/knowledge/search",
            params={"q": "Rust", "user_id": "user-a"},
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

        resp = await client.get(
            "/v1/knowledge/search",
            params={"q": "Rust", "user_id": "user-search-cat", "category": "fact"},
        )
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 1
        assert results[0]["category"] == "fact"

    async def test_search_no_results(self, client, make_knowledge_entry):
        entry = make_knowledge_entry(user_id="user-empty", content="Rust is great")
        await client.post("/v1/knowledge", json=entry)

        resp = await client.get(
            "/v1/knowledge/search",
            params={"q": "quantum computing", "user_id": "user-empty"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 0