"""SDK integration tests: test the oamp-types Python package against the live server.

These tests verify that the SDK models serialize/deserialize correctly
through the full HTTP round-trip: SDK → JSON → API → DB → API → JSON → SDK.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from oamp_types import (
    KnowledgeCategory,
    KnowledgeEntry,
    KnowledgeSource,
    KnowledgeDecay,
    KnowledgeStore,
    CommunicationProfile,
    Correction,
    ExpertiseDomain,
    ExpertiseLevel,
    OAMP_VERSION,
    StatedPreference,
    UserModel,
    validate_knowledge_entry,
    validate_user_model,
)


class TestSDKKnowledgeRoundtrip:
    """Verify KnowledgeEntry SDK model survives POST → GET round-trip."""

    async def test_basic_knowledge_roundtrip(self, client):
        """Create via SDK, POST, GET, parse back via SDK."""
        entry = KnowledgeEntry(
            user_id="user-sdk",
            category=KnowledgeCategory.fact,
            content="SDK round-trip test",
            confidence=0.85,
            source=KnowledgeSource(session_id="sess-sdk-1"),
        )
        payload = json.loads(entry.model_dump_json(exclude_none=True))

        resp = await client.post("/v1/knowledge", json=payload)
        assert resp.status_code == 201

        resp = await client.get(f"/v1/knowledge/{entry.id}")
        assert resp.status_code == 200
        parsed = KnowledgeEntry.model_validate(resp.json())

        assert parsed.id == entry.id
        assert parsed.user_id == entry.user_id
        assert parsed.category == entry.category
        assert parsed.content == entry.content
        assert parsed.confidence == entry.confidence
        assert parsed.source.session_id == entry.source.session_id

    async def test_knowledge_with_all_optionals_roundtrip(self, client):
        """Full-featured KnowledgeEntry round-trip with decay, tags, metadata, agent_id."""
        entry = KnowledgeEntry(
            user_id="user-sdk-full",
            category=KnowledgeCategory.correction,
            content="Never use unwrap() in production Rust code",
            confidence=0.98,
            source=KnowledgeSource(
                session_id="sess-sdk-2",
                agent_id="ultrasushitron-v2",
                timestamp=datetime(2026, 3, 12, 16, 45, 0, tzinfo=timezone.utc),
            ),
            decay=KnowledgeDecay(
                half_life_days=140.0,
                last_confirmed=datetime(2026, 3, 28, 9, 15, 0, tzinfo=timezone.utc),
            ),
            tags=["rust", "code-style"],
            metadata={"priority": "high"},
        )
        payload = json.loads(entry.model_dump_json(exclude_none=True))

        resp = await client.post("/v1/knowledge", json=payload)
        assert resp.status_code == 201

        resp = await client.get(f"/v1/knowledge/{entry.id}")
        assert resp.status_code == 200
        parsed = KnowledgeEntry.model_validate(resp.json())

        assert parsed.source.agent_id == "ultrasushitron-v2"
        assert parsed.decay is not None
        assert parsed.decay.half_life_days == 140.0
        assert parsed.tags == ["rust", "code-style"]
        assert parsed.metadata == {"priority": "high"}

    async def test_all_categories_roundtrip(self, client):
        """Each KnowledgeCategory value should round-trip correctly."""
        for cat in KnowledgeCategory:
            entry = KnowledgeEntry(
                user_id="user-sdk-cats",
                category=cat,
                content=f"Test {cat.value} entry",
                confidence=0.5,
                source=KnowledgeSource(session_id=f"sess-{cat.value}"),
            )
            payload = json.loads(entry.model_dump_json(exclude_none=True))

            resp = await client.post("/v1/knowledge", json=payload)
            assert resp.status_code == 201, f"Failed for category {cat.value}"

            resp = await client.get(f"/v1/knowledge/{entry.id}")
            parsed = KnowledgeEntry.model_validate(resp.json())
            assert parsed.category == cat


class TestSDKUserModelRoundtrip:
    """Verify UserModel SDK model survives POST → GET round-trip."""

    async def test_basic_user_model_roundtrip(self, client):
        model = UserModel(user_id="user-sdk-model")
        payload = json.loads(model.model_dump_json(exclude_none=True))

        resp = await client.post("/v1/user-model", json=payload)
        assert resp.status_code == 201

        resp = await client.get(f"/v1/user-model/{model.user_id}")
        assert resp.status_code == 200
        parsed = UserModel.model_validate(resp.json())

        assert parsed.user_id == model.user_id
        assert parsed.model_version == 1
        assert parsed.oamp_version == OAMP_VERSION

    async def test_full_user_model_roundtrip(self, client):
        """UserModel with communication, expertise, corrections, preferences."""
        model = UserModel(user_id="user-sdk-full")
        model.communication = CommunicationProfile(
            verbosity=-0.6,
            formality=0.2,
            prefers_examples=True,
            prefers_explanations=False,
            languages=["en", "ja"],
        )
        model.expertise.append(
            ExpertiseDomain(
                domain="rust",
                level=ExpertiseLevel.expert,
                confidence=0.95,
                evidence_sessions=["sess-001"],
                last_observed=datetime(2026, 3, 28, 9, 0, 0, tzinfo=timezone.utc),
            )
        )
        model.corrections.append(
            Correction(
                what_agent_did="Suggested using unwrap()",
                what_user_wanted="Always use proper error handling",
                context="Rust code generation",
                session_id="sess-003",
                timestamp=datetime(2026, 3, 12, 16, 45, 0, tzinfo=timezone.utc),
            )
        )
        model.stated_preferences.append(
            StatedPreference(
                key="theme",
                value="dark",
                timestamp=datetime(2026, 3, 10, 10, 0, 0, tzinfo=timezone.utc),
            )
        )

        payload = json.loads(model.model_dump_json(exclude_none=True))
        resp = await client.post("/v1/user-model", json=payload)
        assert resp.status_code == 201

        resp = await client.get(f"/v1/user-model/{model.user_id}")
        parsed = UserModel.model_validate(resp.json())

        assert parsed.communication.verbosity == -0.6
        assert parsed.communication.languages == ["en", "ja"]
        assert len(parsed.expertise) == 1
        assert parsed.expertise[0].level == ExpertiseLevel.expert
        assert len(parsed.corrections) == 1
        assert parsed.corrections[0].context == "Rust code generation"
        assert len(parsed.stated_preferences) == 1

    async def test_all_expertise_levels_roundtrip(self, client):
        """Each ExpertiseLevel should survive the round-trip."""
        levels = list(ExpertiseLevel)
        for i, level in enumerate(levels):
            model = UserModel(user_id=f"user-sdk-level-{i}")
            model.expertise.append(
                ExpertiseDomain(
                    domain=f"domain-{i}",
                    level=level,
                    confidence=0.5,
                )
            )
            payload = json.loads(model.model_dump_json(exclude_none=True))
            resp = await client.post("/v1/user-model", json=payload)
            assert resp.status_code == 201

            resp = await client.get(f"/v1/user-model/{model.user_id}")
            parsed = UserModel.model_validate(resp.json())
            assert parsed.expertise[0].level == level


class TestSDKKnowledgeStoreRoundtrip:
    """Verify KnowledgeStore import/export with SDK models."""

    async def test_import_via_sdk_store(self, client):
        """Build a KnowledgeStore via SDK, import it, verify entries."""
        entries = [
            KnowledgeEntry(
                user_id="user-sdk-store",
                category=KnowledgeCategory.fact,
                content=f"SDK store entry {i}",
                confidence=0.8,
                source=KnowledgeSource(session_id=f"_sess-store-{i}"),
            )
            for i in range(3)
        ]
        store = KnowledgeStore(user_id="user-sdk-store", entries=entries)
        payload = json.loads(store.model_dump_json())

        resp = await client.post("/v1/import", json=payload)
        assert resp.status_code == 200
        assert resp.json()["imported"] == 3

    async def test_export_parsed_as_sdk_store(self, client, make_knowledge_entry):
        """Export produces data where entries can be parsed by SDK KnowledgeEntry."""
        entry = make_knowledge_entry(user_id="user-sdk-export")
        entry["id"] = "sdk00001-e29b-41d4-a716-446655440001"
        await client.post("/v1/knowledge", json=entry)

        resp = await client.post("/v1/export", json={"user_id": "user-sdk-export"})
        assert resp.status_code == 200
        data = resp.json()

        # Verify entries can be parsed by SDK
        for entry_data in data["entries"]:
            parsed = KnowledgeEntry.model_validate(entry_data)
            assert parsed.user_id == "user-sdk-export"


class TestSDKValidation:
    """Verify that SDK validate_* functions match server validation."""

    async def test_sdk_validates_before_post(self, client):
        """Entries that pass SDK validation should also pass server validation."""
        entry = KnowledgeEntry(
            user_id="user-sdk-valid",
            category=KnowledgeCategory.fact,
            content="Valid entry",
            confidence=0.8,
            source=KnowledgeSource(session_id="sess-valid"),
        )
        errors = validate_knowledge_entry(entry)
        assert len(errors) == 0

        payload = json.loads(entry.model_dump_json(exclude_none=True))
        resp = await client.post("/v1/knowledge", json=payload)
        assert resp.status_code == 201

    async def test_sdk_validates_user_model_before_post(self, client):
        """UserModels that pass SDK validation should also pass server validation."""
        model = UserModel(user_id="user-sdk-um-valid")
        errors = validate_user_model(model)
        assert len(errors) == 0

        payload = json.loads(model.model_dump_json(exclude_none=True))
        resp = await client.post("/v1/user-model", json=payload)
        assert resp.status_code == 201


class TestSDKSpecExamplesAgainstServer:
    """Load spec example JSON files, validate via SDK, POST to server, GET back."""

    async def test_spec_knowledge_entry_e2e(self, client):
        path = __import__("pathlib").Path(__file__).resolve().parents[3] / "spec" / "v1" / "examples" / "knowledge-entry.json"
        if not path.exists():
            pytest.skip("spec example not found")

        data = json.loads(path.read_text())

        # SDK validate
        entry = KnowledgeEntry.model_validate(data)
        errors = validate_knowledge_entry(entry)
        assert len(errors) == 0

        # POST
        resp = await client.post("/v1/knowledge", json=data)
        assert resp.status_code == 201

        # GET and SDK parse
        resp = await client.get(f"/v1/knowledge/{entry.id}")
        parsed = KnowledgeEntry.model_validate(resp.json())
        assert parsed.category == entry.category

    async def test_spec_user_model_e2e(self, client):
        path = __import__("pathlib").Path(__file__).resolve().parents[3] / "spec" / "v1" / "examples" / "user-model.json"
        if not path.exists():
            pytest.skip("spec example not found")

        data = json.loads(path.read_text())

        # SDK validate
        model = UserModel.model_validate(data)
        errors = validate_user_model(model)
        assert len(errors) == 0

        # POST
        resp = await client.post("/v1/user-model", json=data)
        assert resp.status_code == 201

        # GET and SDK parse
        resp = await client.get(f"/v1/user-model/{model.user_id}")
        parsed = UserModel.model_validate(resp.json())
        assert len(parsed.expertise) == 3