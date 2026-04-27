"""Tests for user model CRUD endpoints."""

from __future__ import annotations


class TestCreateUserModel:
    """POST /v1/user-model"""

    async def test_create_valid_model(self, client, make_user_model):
        model = make_user_model()
        resp = await client.post("/v1/user-model", json=model)
        assert resp.status_code == 201
        data = resp.json()
        assert data["user_id"] == model["user_id"]
        assert data["model_version"] == model["model_version"]

    async def test_create_with_communication(self, client, make_user_model):
        model = make_user_model()
        model["communication"] = {
            "verbosity": -0.6,
            "formality": 0.2,
            "prefers_examples": True,
            "prefers_explanations": False,
            "languages": ["en", "ja"],
        }
        resp = await client.post("/v1/user-model", json=model)
        assert resp.status_code == 201
        data = resp.json()
        assert data["communication"]["verbosity"] == -0.6
        assert data["communication"]["languages"] == ["en", "ja"]

    async def test_create_with_expertise(self, client, make_user_model):
        model = make_user_model()
        model["expertise"] = [
            {
                "domain": "rust",
                "level": "expert",
                "confidence": 0.95,
                "evidence_sessions": ["sess-001"],
                "last_observed": "2026-03-28T09:00:00Z",
            }
        ]
        resp = await client.post("/v1/user-model", json=model)
        assert resp.status_code == 201
        data = resp.json()
        assert len(data["expertise"]) == 1
        assert data["expertise"][0]["domain"] == "rust"


class TestGetUserModel:
    """GET /v1/user-model/:user_id"""

    async def test_get_existing_model(self, client, make_user_model):
        model = make_user_model()
        await client.post("/v1/user-model", json=model)
        resp = await client.get(f"/v1/user-model/{model['user_id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == model["user_id"]

    async def test_get_nonexistent_model(self, client):
        resp = await client.get("/v1/user-model/nonexistent-user")
        assert resp.status_code == 404


class TestDeleteUserModel:
    """DELETE /v1/user-model/:user_id"""

    async def test_delete_existing_model(self, client, make_user_model):
        model = make_user_model(user_id="user-delete")
        await client.post("/v1/user-model", json=model)
        resp = await client.delete(f"/v1/user-model/{model['user_id']}")
        assert resp.status_code == 204

        # Verify model is gone
        resp = await client.get(f"/v1/user-model/{model['user_id']}")
        assert resp.status_code == 404

    async def test_delete_also_removes_knowledge(self, client, make_user_model, make_knowledge_entry):
        """Spec Section 6.3: MUST delete all associated Knowledge Entries."""
        user_id = "user-delete-all"
        model = make_user_model(user_id=user_id)
        resp = await client.post("/v1/user-model", json=model)
        assert resp.status_code == 201

        # Create knowledge entries for this user
        uuids = [
            "e0000001-e29b-41d4-a716-446655440000",
            "e0000002-e29b-41d4-a716-446655440000",
            "e0000003-e29b-41d4-a716-446655440000",
        ]
        for i in range(3):
            entry = make_knowledge_entry(user_id=user_id)
            entry["id"] = uuids[i]
            resp = await client.post("/v1/knowledge", json=entry)
            assert resp.status_code == 201

        # Delete the user model — should remove everything
        resp = await client.delete(f"/v1/user-model/{user_id}")
        assert resp.status_code == 204

        # Verify knowledge is also gone
        resp = await client.get("/v1/knowledge", params={"user_id": user_id})
        assert resp.status_code == 200
        assert len(resp.json()) == 0

    async def test_delete_nonexistent_model(self, client):
        resp = await client.delete("/v1/user-model/nonexistent-user")
        assert resp.status_code == 404


class TestVersionMonotonicity:
    """POST /v1/user-model with version conflict"""

    async def test_update_with_higher_version(self, client, make_user_model):
        """Updating with model_version > stored should succeed."""
        model_v1 = make_user_model(user_id="user-version")
        await client.post("/v1/user-model", json=model_v1)

        model_v2 = make_user_model(user_id="user-version", model_version=2)
        resp = await client.post("/v1/user-model", json=model_v2)
        assert resp.status_code == 200
        assert resp.json()["model_version"] == 2

    async def test_update_with_same_version_fails(self, client, make_user_model):
        """Spec Section 5.1: MUST reject if model_version <= stored version."""
        model_v7 = make_user_model(user_id="user-conflict", model_version=7)
        await client.post("/v1/user-model", json=model_v7)

        model_v7_again = make_user_model(user_id="user-conflict", model_version=7)
        resp = await client.post("/v1/user-model", json=model_v7_again)
        assert resp.status_code == 409
        body = resp.json()
        assert body.get("code") == "VERSION_CONFLICT"

    async def test_update_with_lower_version_fails(self, client, make_user_model):
        model_v5 = make_user_model(user_id="user-conflict-low", model_version=5)
        await client.post("/v1/user-model", json=model_v5)

        model_v3 = make_user_model(user_id="user-conflict-low", model_version=3)
        resp = await client.post("/v1/user-model", json=model_v3)
        assert resp.status_code == 409