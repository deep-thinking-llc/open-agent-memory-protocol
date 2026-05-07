"""Tests for the optional v1.3 governed-memory enforcement layer."""

from __future__ import annotations


class TestGovernanceEnforcement:
    async def test_list_filters_out_of_scope_entries(
        self,
        client,
        make_governed_knowledge_entry,
        make_grant_headers,
    ):
        health_entry = make_governed_knowledge_entry(
            user_id="user-governed",
            content="The user has a follow-up cardiology appointment.",
            entry_id="11111111-1111-4111-8111-111111111111",
        )
        health_entry["source"]["agent_id"] = "medical-assistant-v3"
        health_entry["governance"]["labels"] = ["health.condition"]
        health_entry["governance"]["sensitivity_class"] = "restricted"

        work_entry = make_governed_knowledge_entry(
            user_id="user-governed",
            content="The user is debugging a Zig storage issue.",
            entry_id="22222222-2222-4222-8222-222222222222",
        )
        work_entry["source"]["agent_id"] = "coding-assistant-v9"
        work_entry["governance"]["labels"] = ["work.code"]
        work_entry["governance"]["sensitivity_class"] = "internal"

        for entry in (health_entry, work_entry):
            resp = await client.post("/v1/knowledge", json=entry)
            assert resp.status_code == 201

        headers = make_grant_headers(
            user_id="user-governed",
            agent_id="coding-assistant-v9",
            read_labels=["work", "preferences"],
            write_labels=["work", "preferences"],
            sensitivity_max="internal",
        )
        resp = await client.get("/v1/knowledge", params={"user_id": "user-governed"}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == work_entry["id"]

    async def test_get_hides_out_of_scope_entry_as_404(
        self,
        client,
        make_governed_knowledge_entry,
        make_grant_headers,
    ):
        entry = make_governed_knowledge_entry(
            user_id="user-hidden",
            content="The user has a confidential diagnosis.",
            entry_id="33333333-3333-4333-8333-333333333333",
        )
        entry["source"]["agent_id"] = "medical-assistant-v3"
        entry["governance"]["labels"] = ["health.condition"]
        entry["governance"]["sensitivity_class"] = "restricted"
        create = await client.post("/v1/knowledge", json=entry)
        assert create.status_code == 201

        headers = make_grant_headers(
            user_id="user-hidden",
            agent_id="coding-assistant-v9",
            read_labels=["work"],
            write_labels=["work"],
            sensitivity_max="internal",
        )
        resp = await client.get(f"/v1/knowledge/{entry['id']}", headers=headers)
        assert resp.status_code == 404

    async def test_create_rejects_out_of_scope_write(
        self,
        client,
        make_governed_knowledge_entry,
        make_grant_headers,
    ):
        entry = make_governed_knowledge_entry(
            user_id="user-write",
            content="The user has a protected health note.",
            entry_id="44444444-4444-4444-8444-444444444444",
        )
        entry["source"]["agent_id"] = "coding-assistant-v9"
        entry["governance"]["labels"] = ["health.condition"]
        entry["governance"]["sensitivity_class"] = "restricted"

        headers = make_grant_headers(
            user_id="user-write",
            agent_id="coding-assistant-v9",
            read_labels=["work"],
            write_labels=["work"],
            sensitivity_max="internal",
        )
        resp = await client.post("/v1/knowledge", json=entry, headers=headers)
        assert resp.status_code == 403
        assert resp.json()["code"] == "SCOPE_DENIED_WRITE"

    async def test_export_filters_without_full_export_claim(
        self,
        client,
        make_governed_knowledge_entry,
        make_grant_headers,
    ):
        health_entry = make_governed_knowledge_entry(
            user_id="user-export",
            entry_id="55555555-5555-4555-8555-555555555555",
        )
        health_entry["source"]["agent_id"] = "medical-assistant-v3"
        health_entry["governance"]["labels"] = ["health.condition"]
        health_entry["governance"]["sensitivity_class"] = "restricted"

        work_entry = make_governed_knowledge_entry(
            user_id="user-export",
            entry_id="66666666-6666-4666-8666-666666666666",
        )
        work_entry["source"]["agent_id"] = "coding-assistant-v9"
        work_entry["governance"]["labels"] = ["work.code"]
        work_entry["governance"]["sensitivity_class"] = "internal"

        for entry in (health_entry, work_entry):
            resp = await client.post("/v1/knowledge", json=entry)
            assert resp.status_code == 201

        headers = make_grant_headers(
            user_id="user-export",
            agent_id="coding-assistant-v9",
            read_labels=["work"],
            write_labels=["work"],
            sensitivity_max="internal",
        )
        resp = await client.post("/v1/export", json={"user_id": "user-export"}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert [entry["id"] for entry in data["entries"]] == [work_entry["id"]]
        assert data["oamp_version"] == "1.3.0"

    async def test_import_counts_rejected_entries(
        self,
        client,
        make_governed_knowledge_entry,
        make_grant_headers,
    ):
        allowed = make_governed_knowledge_entry(
            user_id="user-import",
            entry_id="77777777-7777-4777-8777-777777777777",
        )
        allowed["source"]["agent_id"] = "coding-assistant-v9"
        allowed["governance"]["labels"] = ["work.code"]
        allowed["governance"]["sensitivity_class"] = "internal"

        denied = make_governed_knowledge_entry(
            user_id="user-import",
            entry_id="88888888-8888-4888-8888-888888888888",
        )
        denied["source"]["agent_id"] = "coding-assistant-v9"
        denied["governance"]["labels"] = ["health.condition"]
        denied["governance"]["sensitivity_class"] = "restricted"

        headers = make_grant_headers(
            user_id="user-import",
            agent_id="coding-assistant-v9",
            read_labels=["work"],
            write_labels=["work"],
            sensitivity_max="internal",
        )
        resp = await client.post(
            "/v1/import",
            json={
                "oamp_version": "1.3.0",
                "type": "knowledge_store",
                "user_id": "user-import",
                "entries": [allowed, denied],
                "exported_at": "2026-05-07T12:30:00Z",
                "agent_id": "coding-assistant-v9",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["imported"] == 1
        assert data["rejected"] == 1
