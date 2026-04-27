"""Tests for FTS5-specific search behavior."""

from __future__ import annotations


class TestFTS5Search:
    """FTS5 full-text search with Porter stemming."""

    async def test_search_porter_stemming(self, client, make_knowledge_entry):
        """FTS5 with Porter stemmer should match stemmed forms.

        E.g., searching 'programming' should find 'programs', 'programmed', etc.
        """
        entry = make_knowledge_entry(
            user_id="user-stem",
            content="The user programs in Rust and Go",
        )
        entry["id"] = "f0000001-e29b-41d4-a716-446655440001"
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        # Search with a different form of the word
        resp = await client.get(
            "/v1/knowledge/search",
            params={"q": "programming", "user_id": "user-stem"},
        )
        assert resp.status_code == 200
        results = resp.json()
        # Porter stemmer should match "programs" when searching "programming"
        assert len(results) >= 1

    async def test_search_multi_word_query(self, client, make_knowledge_entry):
        """Multi-word FTS5 queries should work."""
        entry = make_knowledge_entry(
            user_id="user-multi",
            content="Kubernetes deployment with Helm charts",
        )
        entry["id"] = "f0000002-e29b-41d4-a716-446655440002"
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        # Search with multiple words
        resp = await client.get(
            "/v1/knowledge/search",
            params={"q": "Kubernetes Helm", "user_id": "user-multi"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_search_partial_word(self, client, make_knowledge_entry):
        """Test that search works for exact word matches."""
        entry = make_knowledge_entry(
            user_id="user-partial",
            content="Docker container orchestration",
        )
        entry["id"] = "f0000003-e29b-41d4-a716-446655440003"
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        resp = await client.get(
            "/v1/knowledge/search",
            params={"q": "Docker", "user_id": "user-partial"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_search_returns_empty_for_no_match(self, client, make_knowledge_entry):
        """Search for something that doesn't exist returns empty list."""
        entry = make_knowledge_entry(
            user_id="user-no-match",
            content="PostgreSQL transaction isolation levels",
        )
        entry["id"] = "f0000004-e29b-41d4-a716-446655440004"
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        resp = await client.get(
            "/v1/knowledge/search",
            params={"q": "quantum entanglement", "user_id": "user-no-match"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 0

    async def test_search_with_pagination(self, client, make_knowledge_entry):
        """Search results should respect limit/offset."""
        for i in range(5):
            entry = make_knowledge_entry(
                user_id="user-search-page",
                content=f"Rust memory safety topic {i}",
            )
            entry["id"] = f"f{i+1:07d}-e29b-41d4-a716-446655440000"
            resp = await client.post("/v1/knowledge", json=entry)
            assert resp.status_code == 201

        # Limit to 2 results
        resp = await client.get(
            "/v1/knowledge/search",
            params={"q": "Rust", "user_id": "user-search-page", "limit": 2},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2