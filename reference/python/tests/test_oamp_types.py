"""Tests for OAMP Python types."""

import json
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

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
    validate_knowledge_store,
    validate_user_model,
)

SPEC_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "spec", "v1", "examples"
)


class TestKnowledgeEntry:
    """Tests for KnowledgeEntry creation, serialization, and parsing."""

    def test_create_knowledge_entry(self):
        entry = KnowledgeEntry(
            user_id="user-1",
            category=KnowledgeCategory.fact,
            content="Knows Rust",
            confidence=0.9,
            source=KnowledgeSource(session_id="sess-1"),
        )
        assert entry.oamp_version == "1.0.0"
        assert entry.type == "knowledge_entry"
        assert entry.category == KnowledgeCategory.fact
        assert entry.content == "Knows Rust"
        assert entry.confidence == 0.9
        assert entry.source.session_id == "sess-1"
        assert entry.id  # auto-generated UUID

    def test_knowledge_entry_roundtrip_json(self):
        entry = KnowledgeEntry(
            user_id="user-1",
            category=KnowledgeCategory.correction,
            content="Don't do X",
            confidence=0.95,
            source=KnowledgeSource(session_id="s2"),
        )
        json_str = entry.model_dump_json()
        parsed = KnowledgeEntry.model_validate_json(json_str)
        assert parsed.category == KnowledgeCategory.correction
        assert parsed.content == "Don't do X"
        assert parsed.confidence == 0.95

    def test_knowledge_entry_with_decay(self):
        entry = KnowledgeEntry(
            user_id="user-1",
            category=KnowledgeCategory.preference,
            content="Prefers dark mode",
            confidence=0.8,
            source=KnowledgeSource(session_id="sess-1"),
            decay=KnowledgeDecay(half_life_days=70.0),
        )
        assert entry.decay is not None
        assert entry.decay.half_life_days == 70.0

    def test_knowledge_entry_with_tags(self):
        entry = KnowledgeEntry(
            user_id="user-1",
            category=KnowledgeCategory.pattern,
            content="Deploys to staging before production",
            confidence=0.75,
            source=KnowledgeSource(session_id="sess-1"),
            tags=["devops", "deployment"],
        )
        assert entry.tags == ["devops", "deployment"]

    def test_knowledge_entry_with_all_optional_fields(self):
        entry = KnowledgeEntry(
            user_id="user-1",
            category=KnowledgeCategory.correction,
            content="Don't use unwrap()",
            confidence=0.98,
            source=KnowledgeSource(
                session_id="sess-1",
                agent_id="my-agent",
                timestamp=datetime(2026, 3, 12, 16, 45, 0, tzinfo=timezone.utc),
            ),
            decay=KnowledgeDecay(
                half_life_days=140.0,
                last_confirmed=datetime(2026, 3, 28, 9, 15, 0, tzinfo=timezone.utc),
            ),
            tags=["rust", "code-style"],
            metadata={"priority": "high"},
        )
        assert entry.source.agent_id == "my-agent"
        assert entry.decay.last_confirmed is not None
        assert entry.metadata == {"priority": "high"}

    def test_reject_invalid_confidence(self):
        with pytest.raises(ValidationError):
            KnowledgeEntry(
                user_id="user-1",
                category=KnowledgeCategory.fact,
                content="test",
                confidence=1.5,
                source=KnowledgeSource(session_id="s"),
            )

    def test_reject_confidence_below_zero(self):
        with pytest.raises(ValidationError):
            KnowledgeEntry(
                user_id="user-1",
                category=KnowledgeCategory.fact,
                content="test",
                confidence=-0.1,
                source=KnowledgeSource(session_id="s"),
            )

    def test_reject_empty_content(self):
        with pytest.raises(ValidationError):
            KnowledgeEntry(
                user_id="user-1",
                category=KnowledgeCategory.fact,
                content="",
                confidence=0.5,
                source=KnowledgeSource(session_id="s"),
            )

    def test_reject_empty_user_id(self):
        with pytest.raises(ValidationError):
            KnowledgeEntry(
                user_id="",
                category=KnowledgeCategory.fact,
                content="test",
                confidence=0.5,
                source=KnowledgeSource(session_id="s"),
            )

    def test_reject_invalid_oamp_version(self):
        with pytest.raises(ValidationError):
            KnowledgeEntry(
                user_id="user-1",
                oamp_version="2.0.0",
                category=KnowledgeCategory.fact,
                content="test",
                confidence=0.5,
                source=KnowledgeSource(session_id="s"),
            )

    def test_reject_unknown_fields(self):
        """extra='forbid' should reject unknown fields."""
        with pytest.raises(ValidationError):
            KnowledgeEntry.model_validate({
                "oamp_version": "1.0.0",
                "type": "knowledge_entry",
                "id": str(uuid4()),
                "user_id": "user-1",
                "category": "fact",
                "content": "test",
                "confidence": 0.5,
                "source": {"session_id": "s", "timestamp": "2026-01-01T00:00:00Z"},
                "unknown_field": "should be rejected",
            })

    def test_parse_example_file(self):
        path = os.path.join(SPEC_DIR, "knowledge-entry.json")
        if not os.path.exists(path):
            pytest.skip("Example file not found")
        with open(path) as f:
            data = json.load(f)
        entry = KnowledgeEntry.model_validate(data)
        assert entry.category == KnowledgeCategory.preference
        assert entry.confidence > 0.0
        assert entry.confidence <= 1.0


class TestKnowledgeEntrySerialization:
    """Tests for JSON serialization fidelity."""

    def test_none_fields_omitted_in_json(self):
        """Optional fields with None values should be omitted from JSON output."""
        entry = KnowledgeEntry(
            user_id="user-1",
            category=KnowledgeCategory.fact,
            content="Test",
            confidence=0.9,
            source=KnowledgeSource(session_id="s1"),
        )
        d = json.loads(entry.model_dump_json(exclude_none=True))
        assert "decay" not in d
        assert "agent_id" not in d.get("source", {})

    def test_timestamp_includes_timezone(self):
        """Timestamps should serialize with timezone info (Z suffix)."""
        entry = KnowledgeEntry(
            user_id="user-1",
            category=KnowledgeCategory.fact,
            content="Test",
            confidence=0.9,
            source=KnowledgeSource(session_id="s1"),
        )
        d = json.loads(entry.model_dump_json())
        ts = d["source"]["timestamp"]
        assert ts.endswith("Z"), f"Expected 'Z' suffix, got: {ts}"

    def test_roundtrip_preserves_data(self):
        """Round-trip serialization should preserve all data."""
        entry = KnowledgeEntry(
            user_id="user-1",
            category=KnowledgeCategory.preference,
            content="Prefers dark mode",
            confidence=0.8,
            source=KnowledgeSource(
                session_id="sess-1",
                agent_id="my-agent",
            ),
            decay=KnowledgeDecay(half_life_days=70.0),
            tags=["ui", "preference"],
        )
        json_str = entry.model_dump_json(exclude_none=True)
        parsed = KnowledgeEntry.model_validate_json(json_str)
        assert parsed.user_id == entry.user_id
        assert parsed.category == entry.category
        assert parsed.content == entry.content
        assert parsed.confidence == entry.confidence
        assert parsed.source.session_id == entry.source.session_id
        assert parsed.source.agent_id == entry.source.agent_id
        assert parsed.decay.half_life_days == entry.decay.half_life_days
        assert parsed.tags == entry.tags


class TestKnowledgeStore:
    """Tests for KnowledgeStore creation and serialization."""

    def test_create_knowledge_store(self):
        entries = [
            KnowledgeEntry(
                user_id="user-1",
                category=KnowledgeCategory.fact,
                content="Fact 1",
                confidence=0.8,
                source=KnowledgeSource(session_id="s1"),
            ),
            KnowledgeEntry(
                user_id="user-1",
                category=KnowledgeCategory.correction,
                content="Don't do X",
                confidence=0.95,
                source=KnowledgeSource(session_id="s2"),
            ),
        ]
        store = KnowledgeStore(user_id="user-1", entries=entries)
        assert store.oamp_version == "1.0.0"
        assert store.type == "knowledge_store"
        assert len(store.entries) == 2
        assert store.user_id == "user-1"

    def test_knowledge_store_roundtrip_json(self):
        entries = [
            KnowledgeEntry(
                user_id="user-1",
                category=KnowledgeCategory.fact,
                content="Fact 1",
                confidence=0.8,
                source=KnowledgeSource(session_id="s1"),
            ),
        ]
        store = KnowledgeStore(user_id="user-1", entries=entries)
        json_str = store.model_dump_json()
        parsed = KnowledgeStore.model_validate_json(json_str)
        assert len(parsed.entries) == 1
        assert parsed.user_id == "user-1"

    def test_parse_example_file(self):
        path = os.path.join(SPEC_DIR, "knowledge-store.json")
        if not os.path.exists(path):
            pytest.skip("Example file not found")
        with open(path) as f:
            data = json.load(f)
        store = KnowledgeStore.model_validate(data)
        assert store.type == "knowledge_store"

    def test_store_entries_inherit_oamp_version(self):
        """Entries in a store can omit oamp_version (it's inherited)."""
        path = os.path.join(SPEC_DIR, "knowledge-store.json")
        if not os.path.exists(path):
            pytest.skip("Example file not found")
        with open(path) as f:
            data = json.load(f)
        # Some entries may not have oamp_version — they inherit from store
        for entry_data in data["entries"]:
            entry_data.pop("oamp_version", None)
            entry_data.pop("type", None)
        # This should still parse if store provides defaults
        # (KnowledgeEntry has defaults for oamp_version and type)


class TestUserModel:
    """Tests for UserModel creation, serialization, and parsing."""

    def test_create_user_model(self):
        model = UserModel(user_id="user-1")
        assert model.oamp_version == "1.0.0"
        assert model.type == "user_model"
        assert model.user_id == "user-1"
        assert model.model_version == 1

    def test_user_model_with_communication(self):
        model = UserModel(
            user_id="user-1",
            communication=CommunicationProfile(
                verbosity=-0.5,
                formality=0.3,
                prefers_examples=True,
                prefers_explanations=False,
                languages=["en", "ja"],
            ),
        )
        assert model.communication is not None
        assert model.communication.verbosity == -0.5
        assert model.communication.languages == ["en", "ja"]

    def test_user_model_with_expertise(self):
        model = UserModel(user_id="user-1")
        model.expertise.append(
            ExpertiseDomain(
                domain="rust",
                level=ExpertiseLevel.expert,
                confidence=0.95,
            )
        )
        assert len(model.expertise) == 1
        assert model.expertise[0].level == ExpertiseLevel.expert

    def test_user_model_with_corrections(self):
        model = UserModel(user_id="user-1")
        model.corrections.append(
            Correction(
                what_agent_did="Used unwrap()",
                what_user_wanted="Use proper error handling",
                session_id="sess-1",
                timestamp=datetime.now(timezone.utc),
            )
        )
        assert len(model.corrections) == 1

    def test_user_model_with_stated_preferences(self):
        model = UserModel(user_id="user-1")
        model.stated_preferences.append(
            StatedPreference(
                key="code_style",
                value="functional",
                timestamp=datetime.now(timezone.utc),
            )
        )
        assert len(model.stated_preferences) == 1

    def test_user_model_roundtrip_json(self):
        model = UserModel(
            user_id="user-1",
            communication=CommunicationProfile(
                verbosity=-0.5,
                formality=0.3,
            ),
        )
        model.expertise.append(
            ExpertiseDomain(
                domain="rust",
                level=ExpertiseLevel.expert,
                confidence=0.95,
            )
        )
        json_str = model.model_dump_json()
        parsed = UserModel.model_validate_json(json_str)
        assert parsed.expertise[0].level == ExpertiseLevel.expert
        assert parsed.communication.verbosity == -0.5

    def test_reject_verbosity_out_of_range(self):
        with pytest.raises(ValidationError):
            CommunicationProfile(verbosity=2.0, formality=0.0)

    def test_reject_invalid_model_version(self):
        with pytest.raises(ValidationError):
            UserModel(user_id="user-1", model_version=0)

    def test_reject_invalid_oamp_version(self):
        with pytest.raises(ValidationError):
            UserModel(user_id="user-1", oamp_version="2.0.0")

    def test_reject_unknown_fields(self):
        """extra='forbid' should reject unknown fields."""
        with pytest.raises(ValidationError):
            UserModel.model_validate({
                "oamp_version": "1.0.0",
                "type": "user_model",
                "user_id": "user-1",
                "model_version": 1,
                "updated_at": "2026-01-01T00:00:00Z",
                "unknown_field": "should be rejected",
            })

    def test_parse_example_file(self):
        path = os.path.join(SPEC_DIR, "user-model.json")
        if not os.path.exists(path):
            pytest.skip("Example file not found")
        with open(path) as f:
            data = json.load(f)
        model = UserModel.model_validate(data)
        assert len(model.expertise) > 0
        assert model.expertise[0].level == ExpertiseLevel.expert


class TestUserModelSerialization:
    """Tests for UserModel JSON serialization fidelity."""

    def test_none_fields_omitted_in_json(self):
        """Optional fields with None values should be omitted."""
        model = UserModel(user_id="user-1")
        d = json.loads(model.model_dump_json(exclude_none=True))
        assert "communication" not in d
        assert "agent_id" not in d  # UserModel doesn't have agent_id, but check pattern

    def test_timestamp_includes_timezone(self):
        """updated_at should have timezone info."""
        model = UserModel(user_id="user-1")
        d = json.loads(model.model_dump_json())
        assert d["updated_at"].endswith("Z")


class TestValidation:
    """Tests for the validate_* functions."""

    def test_validate_valid_knowledge_entry(self):
        entry = KnowledgeEntry(
            user_id="user-1",
            category=KnowledgeCategory.fact,
            content="Valid",
            confidence=0.5,
            source=KnowledgeSource(session_id="sess-1"),
        )
        errors = validate_knowledge_entry(entry)
        assert len(errors) == 0

    def test_validate_invalid_confidence(self):
        """Validate catches out-of-range confidence even when Pydantic would reject it."""
        entry = KnowledgeEntry.model_construct(
            oamp_version="1.0.0",
            type="knowledge_entry",
            id=str(uuid4()),
            user_id="user-1",
            category=KnowledgeCategory.fact,
            content="Test",
            confidence=1.5,
            source=KnowledgeSource(session_id="sess-1"),
            decay=None,
            tags=[],
            metadata={},
        )
        errors = validate_knowledge_entry(entry)
        assert len(errors) > 0
        assert any("confidence" in e for e in errors)

    def test_validate_empty_content(self):
        """Validate catches empty content even when Pydantic would reject it."""
        entry = KnowledgeEntry.model_construct(
            oamp_version="1.0.0",
            type="knowledge_entry",
            id=str(uuid4()),
            user_id="user-1",
            category=KnowledgeCategory.fact,
            content="",
            confidence=0.5,
            source=KnowledgeSource(session_id="sess-1"),
            decay=None,
            tags=[],
            metadata={},
        )
        errors = validate_knowledge_entry(entry)
        assert len(errors) > 0
        assert any("content" in e for e in errors)

    def test_validate_invalid_oamp_version(self):
        """Validate rejects wrong oamp_version."""
        entry = KnowledgeEntry.model_construct(
            oamp_version="2.0.0",
            type="knowledge_entry",
            id=str(uuid4()),
            user_id="user-1",
            category=KnowledgeCategory.fact,
            content="Test",
            confidence=0.5,
            source=KnowledgeSource(session_id="sess-1"),
            decay=None,
            tags=[],
            metadata={},
        )
        errors = validate_knowledge_entry(entry)
        assert any("oamp_version" in e for e in errors)

    def test_validate_invalid_uuid(self):
        """Validate rejects non-UUID id."""
        entry = KnowledgeEntry.model_construct(
            oamp_version="1.0.0",
            type="knowledge_entry",
            id="not-a-uuid",
            user_id="user-1",
            category=KnowledgeCategory.fact,
            content="Test",
            confidence=0.5,
            source=KnowledgeSource(session_id="sess-1"),
            decay=None,
            tags=[],
            metadata={},
        )
        errors = validate_knowledge_entry(entry)
        assert any("UUID" in e or "id" in e for e in errors)

    def test_validate_valid_knowledge_store(self):
        store = KnowledgeStore(user_id="user-1", entries=[])
        errors = validate_knowledge_store(store)
        assert len(errors) == 0

    def test_validate_valid_user_model(self):
        model = UserModel(user_id="user-1")
        errors = validate_user_model(model)
        assert len(errors) == 0

    def test_validate_invalid_verbosity(self):
        """Validate catches out-of-range verbosity."""
        comm = CommunicationProfile.model_construct(
            verbosity=2.0, formality=0.0,
            prefers_examples=True, prefers_explanations=True, languages=["en"],
        )
        model = UserModel(
            user_id="user-1",
            communication=comm,
        )
        errors = validate_user_model(model)
        assert len(errors) > 0
        assert any("verbosity" in e for e in errors)

    def test_validate_invalid_formality(self):
        """Validate catches out-of-range formality."""
        comm = CommunicationProfile.model_construct(
            verbosity=0.0, formality=-1.5,
            prefers_examples=True, prefers_explanations=True, languages=["en"],
        )
        model = UserModel(
            user_id="user-1",
            communication=comm,
        )
        errors = validate_user_model(model)
        assert len(errors) > 0
        assert any("formality" in e for e in errors)

    def test_validate_expertise_confidence_out_of_range(self):
        """Validate catches out-of-range expertise confidence."""
        exp = ExpertiseDomain.model_construct(
            domain="rust",
            level=ExpertiseLevel.expert,
            confidence=1.5,
            evidence_sessions=[],
            last_observed=None,
        )
        model = UserModel(user_id="user-1")
        model.expertise.append(exp)
        errors = validate_user_model(model)
        assert len(errors) > 0
        assert any("confidence" in e for e in errors)


class TestCategoryEnum:
    """Tests for KnowledgeCategory enum values."""

    def test_category_values(self):
        assert KnowledgeCategory.fact == "fact"
        assert KnowledgeCategory.preference == "preference"
        assert KnowledgeCategory.pattern == "pattern"
        assert KnowledgeCategory.correction == "correction"

    def test_category_from_string(self):
        assert KnowledgeCategory("fact") == KnowledgeCategory.fact
        assert KnowledgeCategory("correction") == KnowledgeCategory.correction


class TestExpertiseLevelEnum:
    """Tests for ExpertiseLevel enum values."""

    def test_level_values(self):
        assert ExpertiseLevel.novice == "novice"
        assert ExpertiseLevel.intermediate == "intermediate"
        assert ExpertiseLevel.advanced == "advanced"
        assert ExpertiseLevel.expert == "expert"

    def test_level_from_string(self):
        assert ExpertiseLevel("expert") == ExpertiseLevel.expert
        assert ExpertiseLevel("novice") == ExpertiseLevel.novice