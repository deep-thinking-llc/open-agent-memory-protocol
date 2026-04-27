"""Shared test fixtures for OAMP server tests."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from oamp_server import create_app, Settings


@pytest.fixture
def settings():
    """Settings with in-memory SQLite for testing."""
    return Settings(db_path=":memory:")


@pytest_asyncio.fixture
async def app(settings):
    """Create a fresh FastAPI app and initialize the repository."""
    app = create_app(settings)
    # Manually trigger lifespan startup
    async with app.router.lifespan_context(app):
        yield app


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
    """Factory fixture to create knowledge entry dicts."""

    def _make(
        user_id: str = "user-test",
        category: str = "fact",
        content: str = "Test knowledge content",
        confidence: float = 0.8,
        session_id: str = "sess-test-001",
    ) -> dict:
        return {
            "oamp_version": "1.0.0",
            "type": "knowledge_entry",
            "id": "550e8400-e29b-41d4-a716-446655440000",
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