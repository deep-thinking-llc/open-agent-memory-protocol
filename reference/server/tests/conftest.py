"""Shared test fixtures for OAMP server tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from oamp_server import create_app, Settings


@pytest.fixture
def key_dir(tmp_path):
    """Create a temporary directory for encryption keys."""
    keys = tmp_path / "keys"
    keys.mkdir()
    return str(keys)


@pytest.fixture
def settings(key_dir):
    """Settings with in-memory SQLite for testing and temp key dir."""
    return Settings(
        db_path=":memory:",
        encryption_key_dir=key_dir,
        audit_log=False,  # Disable audit for most tests
        governance_grant_secret="oamp-test-grant-secret-32bytes!!",
    )


@pytest_asyncio.fixture
async def app(settings):
    """Create a fresh FastAPI app and initialize the repository."""
    _app = create_app(settings)
    async with _app.router.lifespan_context(_app):
        yield _app


@pytest_asyncio.fixture
async def client(app):
    """Create an async HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def repo(app):
    """Get the repository from the app state."""
    return app.state.repo


@pytest.fixture
def make_knowledge_entry():
    """Factory fixture to create knowledge entry dicts.

    Each call with a different user_id gets the same base UUID.
    Tests MUST override `id` when creating multiple entries for the same user.
    """

    def _make(
        user_id: str = "user-test",
        category: str = "fact",
        content: str = "Test knowledge content",
        confidence: float = 0.8,
        session_id: str = "sess-test-001",
        entry_id: str = "550e8400-e29b-41d4-a716-446655440000",
    ) -> dict:
        return {
            "oamp_version": "1.0.0",
            "type": "knowledge_entry",
            "id": entry_id,
            "user_id": user_id,
            "category": category,
            "content": content,
            "confidence": confidence,
            "source": {
                "session_id": session_id,
                "timestamp": "2026-04-01T14:30:00Z",
            },
        }

    return _make


@pytest.fixture
def make_governed_knowledge_entry(make_knowledge_entry):
    """Factory fixture to create governed knowledge entries with governance metadata."""

    def _make(**kwargs) -> dict:
        entry = make_knowledge_entry(**kwargs)
        entry["oamp_version"] = "1.3.0"
        entry["provenance"] = {
            "sources": [
                {
                    "session_id": entry["source"]["session_id"],
                    "timestamp": entry["source"]["timestamp"],
                    "turn_id": "turn-1",
                }
            ],
            "derived": False,
        }
        entry["governance"] = {
            "sensitivity_class": "internal",
            "labels": ["finance", "ops"],
            "handling": {
                "retrieval": "governed",
                "export": "governed",
            },
        }
        return entry

    return _make


@pytest.fixture
def make_grant_headers(settings):
    """Create signed v1.3 grant headers for reference-server tests."""

    def _make(
        user_id: str = "user-test",
        agent_id: str = "coding-assistant-v9",
        grant_id: str = "grant-test-001",
        read_labels: list[str] | None = None,
        write_labels: list[str] | None = None,
        sensitivity_max: str = "internal",
        export_full: bool = False,
        use_authorization: bool = False,
    ) -> dict[str, str]:
        payload = {
            "sub": user_id,
            "oamp_agent_id": agent_id,
            "oamp_grant_id": grant_id,
            "oamp_read_labels": read_labels or [],
            "oamp_write_labels": write_labels or [],
            "oamp_sensitivity_max": sensitivity_max,
            "oamp_export_full": export_full,
        }
        token = jwt.encode(
            payload,
            settings.governance_grant_secret,
            algorithm=settings.governance_grant_algorithm,
        )
        if use_authorization:
            return {"Authorization": f"Bearer {token}"}
        return {"OAMP-Grant": token}

    return _make


@pytest.fixture
def make_user_model():
    """Factory fixture to create user model dicts."""

    def _make(
        user_id: str = "user-test",
        model_version: int = 1,
    ) -> dict:
        return {
            "oamp_version": "1.0.0",
            "type": "user_model",
            "user_id": user_id,
            "model_version": model_version,
            "updated_at": "2026-04-28T12:00:00Z",
        }

    return _make


@pytest_asyncio.fixture
async def populated_client(client, make_knowledge_entry, make_user_model):
    """Client with pre-populated data for E2E tests.

    Creates:
    - user-alice: 3 knowledge entries (fact, preference, correction) + a user model
    - user-bob: 1 knowledge entry (preference)
    """
    alice_entries = [
        make_knowledge_entry(
            user_id="user-alice", category="fact",
            content="Alice is a senior Rust engineer",
            entry_id="a0000001-e29b-41d4-a716-446655440001",
        ),
        make_knowledge_entry(
            user_id="user-alice", category="preference",
            content="Alice prefers concise answers",
            entry_id="a0000002-e29b-41d4-a716-446655440002",
        ),
        make_knowledge_entry(
            user_id="user-alice", category="correction",
            content="Never use unwrap() in Rust code",
            confidence=0.98,
            entry_id="a0000003-e29b-41d4-a716-446655440003",
        ),
    ]
    for entry in alice_entries:
        resp = await client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

    bob_entry = make_knowledge_entry(
        user_id="user-bob", category="preference",
        content="Bob prefers Python scripting",
        entry_id="b0000001-e29b-41d4-a716-446655440001",
    )
    resp = await client.post("/v1/knowledge", json=bob_entry)
    assert resp.status_code == 201

    alice_model = make_user_model(user_id="user-alice", model_version=1)
    resp = await client.post("/v1/user-model", json=alice_model)
    assert resp.status_code == 201

    yield client
