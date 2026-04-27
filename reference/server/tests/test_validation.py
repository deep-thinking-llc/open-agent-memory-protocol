"""Tests for error handling compliance and PATCH endpoint.

Spec compliance: Section 6.2 (PATCH), Section 6.8 (Error Responses)
"""

from __future__ import annotations


class TestErrorFormat:
    """Spec Section 6.8: All errors MUST be JSON with 'error' and 'code'."""

    async def test_error_format_on_not_found(self, client):
        resp = await client.get("/v1/knowledge/nonexistent-id")
        assert resp.status_code == 404
        body = resp.json()
        assert "error" in body
        assert "code" in body
        assert isinstance(body["error"], str)
        assert isinstance(body["code"], str)

    async def test_error_format_on_validation_error(self, client, make_knowledge_entry):
        entry = make_knowledge_entry(confidence=5.0)
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 400
        body = resp.json()
        assert "error" in body
        assert "code" in body
        assert body["code"] == "VALIDATION_ERROR"

    async def test_error_format_on_version_conflict(self, client, make_user_model):
        model = make_user_model(user_id="user-err", model_version=3)
        await client.post("/v1/user-model", json=model)

        model_same = make_user_model(user_id="user-err", model_version=3)
        resp = await client.post("/v1/user-model", json=model_same)
        assert resp.status_code == 409
        body = resp.json()
        assert body["code"] == "VERSION_CONFLICT"

    async def test_error_format_on_duplicate_id(self, client, make_knowledge_entry):
        entry = make_knowledge_entry(entry_id="d0000001-e29b-41d4-a716-446655440001")
        await client.post("/v1/knowledge", json=entry)
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 409
        body = resp.json()
        assert "error" in body
        assert "code" in body

    async def test_error_format_on_forbidden_patch(self, client, make_knowledge_entry):
        entry = make_knowledge_entry()
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        resp = await client.patch(
            f"/v1/knowledge/{entry['id']}",
            json={"category": "preference"},  # category is forbidden to patch
        )
        assert resp.status_code == 400
        body = resp.json()
        assert body["code"] == "FORBIDDEN_PATCH"


class TestPatchKnowledge:
    """PATCH /v1/knowledge/:id — spec Section 6.2

    Only confidence, decay, and tags may be patched.
    Fields id, user_id, category, source are forbidden.
    """

    async def test_patch_confidence(self, client, make_knowledge_entry):
        entry = make_knowledge_entry()
        await client.post("/v1/knowledge", json=entry)

        resp = await client.patch(
            f"/v1/knowledge/{entry['id']}",
            json={"confidence": 0.95},
        )
        assert resp.status_code == 200
        assert resp.json()["confidence"] == 0.95

    async def test_patch_tags(self, client, make_knowledge_entry):
        entry = make_knowledge_entry()
        await client.post("/v1/knowledge", json=entry)

        resp = await client.patch(
            f"/v1/knowledge/{entry['id']}",
            json={"tags": ["updated", "tags"]},
        )
        assert resp.status_code == 200
        assert resp.json()["tags"] == ["updated", "tags"]

    async def test_patch_decay(self, client, make_knowledge_entry):
        entry = make_knowledge_entry()
        await client.post("/v1/knowledge", json=entry)

        resp = await client.patch(
            f"/v1/knowledge/{entry['id']}",
            json={"decay": {"half_life_days": 50.0, "last_confirmed": "2026-05-01T12:00:00Z"}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["decay"]["half_life_days"] == 50.0

    async def test_patch_forbidden_id(self, client, make_knowledge_entry):
        entry = make_knowledge_entry()
        await client.post("/v1/knowledge", json=entry)
        resp = await client.patch(
            f"/v1/knowledge/{entry['id']}",
            json={"id": "new-id"},
        )
        assert resp.status_code == 400

    async def test_patch_forbidden_user_id(self, client, make_knowledge_entry):
        entry = make_knowledge_entry()
        await client.post("/v1/knowledge", json=entry)
        resp = await client.patch(
            f"/v1/knowledge/{entry['id']}",
            json={"user_id": "different-user"},
        )
        assert resp.status_code == 400

    async def test_patch_forbidden_category(self, client, make_knowledge_entry):
        entry = make_knowledge_entry()
        await client.post("/v1/knowledge", json=entry)
        resp = await client.patch(
            f"/v1/knowledge/{entry['id']}",
            json={"category": "preference"},
        )
        assert resp.status_code == 400

    async def test_patch_forbidden_source(self, client, make_knowledge_entry):
        entry = make_knowledge_entry()
        await client.post("/v1/knowledge", json=entry)
        resp = await client.patch(
            f"/v1/knowledge/{entry['id']}",
            json={"source": {"session_id": "new-sess"}},
        )
        assert resp.status_code == 400

    async def test_patch_forbidden_content(self, client, make_knowledge_entry):
        """Content is immutable — should be forbidden to patch."""
        entry = make_knowledge_entry()
        await client.post("/v1/knowledge", json=entry)
        resp = await client.patch(
            f"/v1/knowledge/{entry['id']}",
            json={"content": "new content"},
        )
        assert resp.status_code == 400

    async def test_patch_nonexistent_entry(self, client):
        resp = await client.patch(
            "/v1/knowledge/nonexistent-id",
            json={"confidence": 0.5},
        )
        assert resp.status_code == 404