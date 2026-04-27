"""Shared test fixtures for OAMP server tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

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