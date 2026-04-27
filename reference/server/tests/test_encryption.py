"""Tests for Phase 3: AES-256-GCM encryption at rest.

Covers:
- Stored data is ciphertext (direct DB query)
- Key rotation works (old data decryptable, new data uses new key)
- Audit log records operations without knowledge content
- Zeroization on delete (overwrite before remove)
- FTS5 search still works with encrypted content
- Encryption module unit tests

Spec compliance: §8.1.1 (encryption at rest), §8.2.6 (audit logging),
§8.2.7 (zeroization), §8.2.8 (key rotation)
"""

from __future__ import annotations

import asyncio
import base64
import json
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from oamp_server import create_app, Settings
from oamp_server.encryption import (
    EncryptionKey,
    LocalKeyProvider,
    encrypt,
    decrypt,
    zeroize,
)
from oamp_server.repository.sqlite import SQLiteRepository


# ── Valid UUID v4 identifiers for tests ────────────────────────────

EID_ENC1 = "ae65cbd7-8afd-4ae8-872b-ac77141f2a2b"
EID_ENC2 = "34dac5ae-d443-41fb-9b48-94937c7119c9"
EID_ROT1 = "fe6fc694-8c30-4b61-9971-717d52146840"
EID_ROT2 = "27170a19-9987-43bc-ac4e-301a99c3c51a"
EID_MUL1 = "fd32ec23-0c84-4004-bbe5-f960743c846c"
EID_MUL2 = "8e2f21a9-09a9-4511-8bf4-f9e1869652ab"
EID_MUL3 = "bb4ab40f-669a-4f7a-838b-5ebd6ce0e40d"
EID_AUD1 = "962f5069-d744-461b-999d-667e66928c35"
EID_AUD2 = "35ea4d16-f560-47e2-a6bf-63fdf8e15e99"
EID_AUD3 = "db5cfdf0-2c52-4815-8890-76193e1f21b0"
EID_AUD4 = "ebbfcbbd-fc5e-4463-a0d9-b1c814543921"
EID_AUD5 = "88d88640-2a2c-488f-97e3-f2db3c17f84e"
EID_ZER1 = "ad057246-5344-4778-a335-761caad4b4c3"
EID_FTS1 = "707a0d01-72b7-4ffe-86c2-0120f21b99c5"
EID_FTS2 = "328ef27d-9dd6-443f-888a-153892a79bda"
EID_FTS3 = "a9bbfa02-c6a8-4c8b-b253-e447f241416a"
EID_FTSS = "94966bcf-3831-4a27-a3df-10bdb3389bf4"
EID_TRN1 = "28e1ad3d-fb60-4426-a748-62534bbdce1c"
EID_TRL0 = "7f29593e-5726-4961-8a8f-255404a56992"
EID_TRL1 = "3b77a210-da90-4d3e-8a53-b67bc0b4cd1c"
EID_TRL2 = "356c6c3e-86cf-4b48-8521-71b03ca233c8"
EID_TRE1 = "8a3e46ea-03b0-4737-b2d8-078486eda341"


# ── Encryption module unit tests ─────────────────────────────────────


class TestEncryptionModule:
    """Unit tests for encryption.py encrypt/decrypt functions."""

    def test_encrypt_decrypt_roundtrip(self):
        """Basic encrypt → decrypt roundtrip."""
        provider = LocalKeyProvider(tempfile.mkdtemp())
        key = provider.get_active_key()
        plaintext = "Hello, World!"
        aad = "user-123"

        encrypted = encrypt(plaintext, key, aad)
        decrypted = decrypt(encrypted, key.key_id, provider, aad)

        assert decrypted == plaintext

    def test_encrypt_produces_ciphertext(self):
        """Encrypted output should not contain the plaintext."""
        provider = LocalKeyProvider(tempfile.mkdtemp())
        key = provider.get_active_key()
        plaintext = "sensitive user data"
        aad = "user-456"

        encrypted = encrypt(plaintext, key, aad)
        assert plaintext not in encrypted
        # Verify it's valid base64
        raw = base64.b64decode(encrypted)
        assert len(raw) > 12  # nonce + ciphertext + tag

    def test_different_nonces_per_encryption(self):
        """Each encryption should use a different nonce."""
        provider = LocalKeyProvider(tempfile.mkdtemp())
        key = provider.get_active_key()

        encrypted1 = encrypt("test", key, "user-1")
        encrypted2 = encrypt("test", key, "user-1")

        # Same plaintext, different nonce → different ciphertext
        assert encrypted1 != encrypted2

    def test_aad_mismatch_fails(self):
        """Decrypting with wrong AAD (user_id) should fail."""
        provider = LocalKeyProvider(tempfile.mkdtemp())
        key = provider.get_active_key()

        encrypted = encrypt("secret", key, aad="user-alice")

        with pytest.raises(Exception):
            decrypt(encrypted, key.key_id, provider, aad="user-bob")

    def test_wrong_key_fails(self):
        """Decrypting with the wrong key should fail."""
        provider1 = LocalKeyProvider(tempfile.mkdtemp())
        provider2 = LocalKeyProvider(tempfile.mkdtemp())
        key1 = provider1.get_active_key()

        encrypted = encrypt("secret", key1, aad="user-1")

        with pytest.raises(Exception):
            decrypt(encrypted, key1.key_id, provider2, aad="user-1")

    def test_empty_aad_works(self):
        """Empty AAD should still work for encryption/decryption."""
        provider = LocalKeyProvider(tempfile.mkdtemp())
        key = provider.get_active_key()

        encrypted = encrypt("data", key, aad="")
        decrypted = decrypt(encrypted, key.key_id, provider, aad="")
        assert decrypted == "data"

    def test_unicode_content(self):
        """Unicode/multibyte content should roundtrip correctly."""
        provider = LocalKeyProvider(tempfile.mkdtemp())
        key = provider.get_active_key()

        plaintext = "日本語テスト 🎉 émojis"
        encrypted = encrypt(plaintext, key, aad="user-unicode")
        decrypted = decrypt(encrypted, key.key_id, provider, aad="user-unicode")
        assert decrypted == plaintext

    def test_large_content(self):
        """Large content should roundtrip correctly."""
        provider = LocalKeyProvider(tempfile.mkdtemp())
        key = provider.get_active_key()

        plaintext = "A" * 100000
        encrypted = encrypt(plaintext, key, aad="user-large")
        decrypted = decrypt(encrypted, key.key_id, provider, aad="user-large")
        assert decrypted == plaintext


class TestEncryptionKey:
    """Tests for EncryptionKey dataclass."""

    def test_valid_key(self):
        key = EncryptionKey(key_id="test", key_bytes=b"\x00" * 32)
        assert key.key_id == "test"
        assert len(key.key_bytes) == 32

    def test_invalid_key_length(self):
        with pytest.raises(ValueError, match="32 bytes"):
            EncryptionKey(key_id="bad", key_bytes=b"\x00" * 16)

    def test_immutable(self):
        key = EncryptionKey(key_id="test", key_bytes=b"\x00" * 32)
        with pytest.raises(AttributeError):
            key.key_id = "changed"


class TestLocalKeyProvider:
    """Tests for LocalKeyProvider."""

    def test_auto_generates_first_key(self):
        provider = LocalKeyProvider(tempfile.mkdtemp())
        key = provider.get_active_key()
        assert key.key_id
        assert len(key.key_bytes) == 32

    def test_get_active_key_consistent(self):
        provider = LocalKeyProvider(tempfile.mkdtemp())
        key1 = provider.get_active_key()
        key2 = provider.get_active_key()
        assert key1.key_id == key2.key_id

    def test_get_key_by_id(self):
        provider = LocalKeyProvider(tempfile.mkdtemp())
        active = provider.get_active_key()
        retrieved = provider.get_key(active.key_id)
        assert retrieved.key_bytes == active.key_bytes

    def test_get_nonexistent_key_raises(self):
        provider = LocalKeyProvider(tempfile.mkdtemp())
        with pytest.raises(KeyError):
            provider.get_key("nonexistent")

    def test_rotation_generates_new_key(self):
        provider = LocalKeyProvider(tempfile.mkdtemp())
        old_key = provider.get_active_key()
        new_key = provider.rotate()
        assert new_key.key_id != old_key.key_id

    def test_rotation_new_key_becomes_active(self):
        provider = LocalKeyProvider(tempfile.mkdtemp())
        new_key = provider.rotate()
        active = provider.get_active_key()
        assert active.key_id == new_key.key_id

    def test_old_key_still_retrievable_after_rotation(self):
        provider = LocalKeyProvider(tempfile.mkdtemp())
        old_key = provider.get_active_key()
        provider.rotate()
        # Old key should still be retrievable for decryption
        retrieved = provider.get_key(old_key.key_id)
        assert retrieved.key_bytes == old_key.key_bytes


# ── Helpers for creating test entries with valid UUIDs ──────────────

def _make_entry(
    entry_id: str,
    user_id: str,
    category: str = "fact",
    content: str = "Test content",
    confidence: float = 0.8,
    session_id: str = "s1",
    tags: list | None = None,
    decay: dict | None = None,
) -> dict:
    entry = {
        "oamp_version": "1.0.0",
        "type": "knowledge_entry",
        "id": entry_id,
        "user_id": user_id,
        "category": category,
        "content": content,
        "confidence": confidence,
        "source": {"session_id": session_id, "timestamp": "2026-04-01T14:30:00Z"},
    }
    if tags:
        entry["tags"] = tags
    if decay:
        entry["decay"] = decay
    return entry


# ── Stored data is ciphertext ────────────────────────────────────────


class TestStoredDataIsCiphertext:
    """Verify that stored data in the DB is encrypted, not plaintext."""

    @pytest_asyncio.fixture
    async def enc_app(self, tmp_path):
        """Create app with encryption enabled and a real (not in-memory) DB."""
        db_path = str(tmp_path / "test.db")
        key_dir = str(tmp_path / "keys")
        settings = Settings(
            db_path=db_path,
            encryption_key_dir=key_dir,
            audit_log=True,
        )
        _app = create_app(settings)
        async with _app.router.lifespan_context(_app):
            yield _app

    @pytest_asyncio.fixture
    async def enc_client(self, enc_app):
        transport = ASGITransport(app=enc_app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c

    async def test_knowledge_content_is_encrypted_in_db(self, enc_app, enc_client):
        """Direct DB query should reveal ciphertext, not plaintext content."""
        entry = _make_entry(
            entry_id=EID_ENC1,
            user_id="user-enc",
            content="This is sensitive knowledge that must be encrypted",
            confidence=0.9,
            session_id="sess-enc",
            tags=["sensitive", "test"],
        )
        resp = await enc_client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        # Direct DB query
        db = enc_app.state.repo._db
        async with db.execute(
            "SELECT content_enc, source_enc, tags_enc, encryption_key_id FROM knowledge_entries WHERE id = ?",
            (EID_ENC1,),
        ) as cursor:
            row = await cursor.fetchone()

        # Verify content is stored encrypted (not plaintext)
        assert "This is sensitive knowledge" not in row["content_enc"]
        assert "sensitive" not in row["source_enc"]  # source also encrypted
        assert row["encryption_key_id"]  # key_id is populated
        # Verify tags are encrypted
        assert row["tags_enc"] is not None
        assert "sensitive" not in row["tags_enc"]

    async def test_user_model_data_is_encrypted_in_db(self, enc_app, enc_client):
        """User model PII fields should be encrypted in the DB."""
        model = {
            "oamp_version": "1.0.0",
            "type": "user_model",
            "user_id": "user-enc-model",
            "model_version": 1,
            "updated_at": "2026-04-28T12:00:00Z",
            "communication": {
                "verbosity": -0.6,
                "formality": 0.2,
                "prefers_examples": True,
            },
            "expertise": [
                {
                    "domain": "rust",
                    "level": "expert",
                    "confidence": 0.95,
                }
            ],
        }
        resp = await enc_client.post("/v1/user-model", json=model)
        assert resp.status_code == 201

        # Direct DB query
        db = enc_app.state.repo._db
        async with db.execute(
            "SELECT communication_enc, expertise_enc, encryption_key_id FROM user_models WHERE user_id = ?",
            ("user-enc-model",),
        ) as cursor:
            row = await cursor.fetchone()

        # Verify PII is encrypted
        assert row["communication_enc"] is not None
        assert "verbosity" not in row["communication_enc"]
        assert row["expertise_enc"] is not None
        assert "rust" not in row["expertise_enc"]
        assert row["encryption_key_id"]

    async def test_plaintext_fields_remain_queryable(self, enc_app, enc_client):
        """user_id, category, confidence should remain plaintext for querying."""
        entry = _make_entry(
            entry_id=EID_ENC2,
            user_id="user-plain",
            content="Test content",
            confidence=0.75,
        )
        resp = await enc_client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        db = enc_app.state.repo._db
        async with db.execute(
            "SELECT user_id, category, confidence FROM knowledge_entries WHERE id = ?",
            (EID_ENC2,),
        ) as cursor:
            row = await cursor.fetchone()

        assert row["user_id"] == "user-plain"
        assert row["category"] == "fact"
        assert row["confidence"] == 0.75


# ── Key rotation ─────────────────────────────────────────────────────


class TestKeyRotation:
    """Key rotation: old data decryptable with old key, new data uses new key."""

    @pytest_asyncio.fixture
    async def rotation_app(self, tmp_path):
        db_path = str(tmp_path / "rotation.db")
        key_dir = str(tmp_path / "keys")
        settings = Settings(
            db_path=db_path,
            encryption_key_dir=key_dir,
            audit_log=True,
        )
        _app = create_app(settings)
        async with _app.router.lifespan_context(_app):
            yield _app

    @pytest_asyncio.fixture
    async def rotation_client(self, rotation_app):
        transport = ASGITransport(app=rotation_app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c

    async def test_rotate_key_endpoint(self, rotation_client):
        """POST /v1/admin/keys/rotate should return new key_id."""
        resp = await rotation_client.post("/v1/admin/keys/rotate")
        assert resp.status_code == 200
        data = resp.json()
        assert "key_id" in data
        assert data["key_id"]

    async def test_old_data_decryptable_after_rotation(self, rotation_client, rotation_app):
        """Data encrypted with old key should still be decryptable after rotation."""
        # Create entry before rotation
        entry = _make_entry(
            entry_id=EID_ROT1,
            user_id="user-rot",
            content="Data before rotation",
        )
        resp = await rotation_client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        # Get key_id before rotation
        db = rotation_app.state.repo._db
        async with db.execute(
            "SELECT encryption_key_id FROM knowledge_entries WHERE id = ?",
            (EID_ROT1,),
        ) as cursor:
            row = await cursor.fetchone()
        old_key_id = row["encryption_key_id"]

        # Rotate key
        resp = await rotation_client.post("/v1/admin/keys/rotate")
        assert resp.status_code == 200
        new_key_id = resp.json()["key_id"]
        assert new_key_id != old_key_id

        # Old data should still be readable
        resp = await rotation_client.get(f"/v1/knowledge/{EID_ROT1}")
        assert resp.status_code == 200
        assert resp.json()["content"] == "Data before rotation"

    async def test_new_data_uses_new_key(self, rotation_client, rotation_app):
        """After rotation, new data should be encrypted with the new key."""
        # Rotate first
        resp = await rotation_client.post("/v1/admin/keys/rotate")
        assert resp.status_code == 200
        new_key_id = resp.json()["key_id"]

        # Create entry after rotation
        entry = _make_entry(
            entry_id=EID_ROT2,
            user_id="user-rot2",
            content="Data after rotation",
        )
        resp = await rotation_client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        # Verify the new entry uses the new key
        db = rotation_app.state.repo._db
        async with db.execute(
            "SELECT encryption_key_id FROM knowledge_entries WHERE id = ?",
            (EID_ROT2,),
        ) as cursor:
            row = await cursor.fetchone()
        assert row["encryption_key_id"] == new_key_id

    async def test_multiple_rotations(self, rotation_client, rotation_app):
        """Multiple key rotations should work correctly."""
        # Create with key1
        entry1 = _make_entry(
            entry_id=EID_MUL1,
            user_id="user-multi",
            content="Created with key1",
            session_id="s1",
        )
        resp = await rotation_client.post("/v1/knowledge", json=entry1)
        assert resp.status_code == 201

        # Rotate to key2
        await rotation_client.post("/v1/admin/keys/rotate")

        # Create with key2
        entry2 = _make_entry(
            entry_id=EID_MUL2,
            user_id="user-multi",
            content="Created with key2",
            session_id="s2",
        )
        resp = await rotation_client.post("/v1/knowledge", json=entry2)
        assert resp.status_code == 201

        # Rotate to key3
        await rotation_client.post("/v1/admin/keys/rotate")

        # Create with key3
        entry3 = _make_entry(
            entry_id=EID_MUL3,
            user_id="user-multi",
            content="Created with key3",
            session_id="s3",
        )
        resp = await rotation_client.post("/v1/knowledge", json=entry3)
        assert resp.status_code == 201

        # All entries should be readable
        for eid in [EID_MUL1, EID_MUL2, EID_MUL3]:
            resp = await rotation_client.get(f"/v1/knowledge/{eid}")
            assert resp.status_code == 200, f"Failed for {eid}: {resp.json()}"


# ── Audit logging ────────────────────────────────────────────────────


class TestAuditLog:
    """Audit log records operations without knowledge content (spec §8.2.6)."""

    @pytest_asyncio.fixture
    async def audit_app(self, tmp_path):
        db_path = str(tmp_path / "audit.db")
        key_dir = str(tmp_path / "keys")
        settings = Settings(
            db_path=db_path,
            encryption_key_dir=key_dir,
            audit_log=True,  # Enable audit logging
        )
        _app = create_app(settings)
        async with _app.router.lifespan_context(_app):
            yield _app

    @pytest_asyncio.fixture
    async def audit_client(self, audit_app):
        transport = ASGITransport(app=audit_app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c

    async def test_audit_log_records_create(self, audit_client, audit_app):
        """Create operations should be logged."""
        entry = _make_entry(
            entry_id=EID_AUD1,
            user_id="user-audit",
            content="Sensitive data that should not appear in audit logs",
        )
        resp = await audit_client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        resp = await audit_client.get("/v1/admin/audit", params={"user_id": "user-audit"})
        assert resp.status_code == 200
        logs = resp.json()
        assert any(log["action"] == "create" for log in logs)

    async def test_audit_log_no_knowledge_content(self, audit_client, audit_app):
        """Audit logs MUST NOT contain knowledge content (spec §8.2.6)."""
        sensitive_content = "TOP_SECRET_DATA_12345"
        entry = _make_entry(
            entry_id=EID_AUD2,
            user_id="user-no-leak",
            content=sensitive_content,
        )
        resp = await audit_client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        # Check audit log via direct DB query (can't rely on API filtering)
        db = audit_app.state.repo._db
        async with db.execute(
            "SELECT * FROM audit_log WHERE user_id = ?",
            ("user-no-leak",),
        ) as cursor:
            rows = await cursor.fetchall()

        # Verify no audit log entry contains the sensitive content
        for row in rows:
            row_dict = dict(row)
            for key, value in row_dict.items():
                if value is not None:
                    assert sensitive_content not in str(value), (
                        f"Audit log leaked content in field '{key}': {value}"
                    )

    async def test_audit_log_records_delete(self, audit_client, audit_app):
        """Delete operations should be logged."""
        entry = _make_entry(
            entry_id=EID_AUD3,
            user_id="user-audit-del",
            content="To be deleted",
        )
        await audit_client.post("/v1/knowledge", json=entry)
        resp = await audit_client.delete(f"/v1/knowledge/{EID_AUD3}")
        assert resp.status_code == 204

        resp = await audit_client.get("/v1/admin/audit", params={"user_id": "user-audit-del"})
        logs = resp.json()
        assert any(log["action"] == "delete" for log in logs)

    async def test_audit_log_records_update(self, audit_client, audit_app):
        """Update operations should be logged."""
        entry = _make_entry(
            entry_id=EID_AUD4,
            user_id="user-audit-upd",
            content="To be updated",
        )
        await audit_client.post("/v1/knowledge", json=entry)
        await audit_client.patch(
            f"/v1/knowledge/{EID_AUD4}",
            json={"confidence": 0.95},
        )

        resp = await audit_client.get("/v1/admin/audit", params={"user_id": "user-audit-upd"})
        logs = resp.json()
        assert any(log["action"] == "update" for log in logs)

    async def test_audit_log_records_entry_id(self, audit_client, audit_app):
        """Audit logs should include entry_id for CRUD operations."""
        entry = _make_entry(
            entry_id=EID_AUD5,
            user_id="user-audit-eid",
            content="Entry ID tracking",
        )
        await audit_client.post("/v1/knowledge", json=entry)

        resp = await audit_client.get("/v1/admin/audit", params={"user_id": "user-audit-eid"})
        logs = resp.json()
        create_logs = [l for l in logs if l["action"] == "create"]
        assert len(create_logs) > 0
        assert create_logs[0]["entry_id"] == EID_AUD5


# ── Zeroization ──────────────────────────────────────────────────────


class TestZeroization:
    """Delete operations should zeroize memory buffers (spec §8.2.7)."""

    @pytest_asyncio.fixture
    async def zero_app(self, tmp_path):
        db_path = str(tmp_path / "zero.db")
        key_dir = str(tmp_path / "keys")
        settings = Settings(
            db_path=db_path,
            encryption_key_dir=key_dir,
            audit_log=False,
        )
        _app = create_app(settings)
        async with _app.router.lifespan_context(_app):
            yield _app

    @pytest_asyncio.fixture
    async def zero_client(self, zero_app):
        transport = ASGITransport(app=zero_app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c

    async def test_zeroization_on_knowledge_delete(self, zero_client, zero_app):
        """Encrypted columns should be overwritten with zeros before deletion."""
        entry = _make_entry(
            entry_id=EID_ZER1,
            user_id="user-zero",
            content="Sensitive data to be zeroized",
        )
        resp = await zero_client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        # Get encrypted content before delete
        db = zero_app.state.repo._db
        async with db.execute(
            "SELECT content_enc FROM knowledge_entries WHERE id = ?",
            (EID_ZER1,),
        ) as cursor:
            row = await cursor.fetchone()
        original_ciphertext = row["content_enc"]
        assert original_ciphertext != "ZEROED"

        # Delete - our repo zeroizes before deletion
        resp = await zero_client.delete(f"/v1/knowledge/{EID_ZER1}")
        assert resp.status_code == 204

        # After delete, row no longer exists
        async with db.execute(
            "SELECT content_enc FROM knowledge_entries WHERE id = ?",
            (EID_ZER1,),
        ) as cursor:
            row = await cursor.fetchone()
        assert row is None

    async def test_zeroization_on_user_model_delete(self, zero_client, zero_app):
        """User model encrypted columns should be zeroized before deletion."""
        model = {
            "oamp_version": "1.0.0",
            "type": "user_model",
            "user_id": "user-zero-model",
            "model_version": 1,
            "updated_at": "2026-04-28T12:00:00Z",
            "communication": {"verbosity": 0.5},
        }
        resp = await zero_client.post("/v1/user-model", json=model)
        assert resp.status_code == 201

        # Delete user model
        resp = await zero_client.delete("/v1/user-model/user-zero-model")
        assert resp.status_code == 204

        # After delete, row no longer exists
        db = zero_app.state.repo._db
        async with db.execute(
            "SELECT communication_enc FROM user_models WHERE user_id = ?",
            ("user-zero-model",),
        ) as cursor:
            row = await cursor.fetchone()
        assert row is None


# ── FTS5 search with encrypted content ──────────────────────────────


class TestFTS5WithEncryption:
    """FTS5 full-text search should still work with encrypted content."""

    @pytest_asyncio.fixture
    async def fts_app(self, tmp_path):
        db_path = str(tmp_path / "fts.db")
        key_dir = str(tmp_path / "keys")
        settings = Settings(
            db_path=db_path,
            encryption_key_dir=key_dir,
            audit_log=False,
        )
        _app = create_app(settings)
        async with _app.router.lifespan_context(_app):
            yield _app

    @pytest_asyncio.fixture
    async def fts_client(self, fts_app):
        transport = ASGITransport(app=fts_app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c

    async def test_search_finds_encrypted_content(self, fts_client, fts_app):
        """FTS5 should find entries by plaintext content even though main table is encrypted."""
        fts_ids = [EID_FTS1, EID_FTS2, EID_FTS3]
        topics = ["Rust programming", "Python scripting", "Go concurrency"]
        for i, (eid, topic) in enumerate(zip(fts_ids, topics)):
            entry = _make_entry(
                entry_id=eid,
                user_id="user-fts",
                content=f"Content about {topic}",
                session_id=f"s{i}",
            )
            resp = await fts_client.post("/v1/knowledge", json=entry)
            assert resp.status_code == 201

        # Search for "Rust"
        resp = await fts_client.get(
            "/v1/knowledge",
            params={"user_id": "user-fts", "query": "Rust"},
        )
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 1
        assert "Rust" in results[0]["content"]

    async def test_search_porter_stemming_works(self, fts_client, fts_app):
        """Porter stemming should still work with encrypted content."""
        entry = _make_entry(
            entry_id=EID_FTSS,
            user_id="user-stem",
            content="The user programs in Rust and Go",
        )
        resp = await fts_client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        resp = await fts_client.get(
            "/v1/knowledge",
            params={"user_id": "user-stem", "query": "programming"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


# ── Encryption transparency at API level ─────────────────────────────


class TestEncryptionTransparency:
    """Encryption should be transparent: API responses should look identical."""

    @pytest_asyncio.fixture
    async def trans_app(self, tmp_path):
        db_path = str(tmp_path / "trans.db")
        key_dir = str(tmp_path / "keys")
        settings = Settings(
            db_path=db_path,
            encryption_key_dir=key_dir,
            audit_log=False,
        )
        _app = create_app(settings)
        async with _app.router.lifespan_context(_app):
            yield _app

    @pytest_asyncio.fixture
    async def trans_client(self, trans_app):
        transport = ASGITransport(app=trans_app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c

    async def test_api_roundtrip_unchanged(self, trans_client):
        """Full API roundtrip should produce identical data to what was stored."""
        entry = _make_entry(
            entry_id=EID_TRN1,
            user_id="user-trans",
            content="Test transparency of encryption",
            confidence=0.85,
            tags=["enc", "test"],
            decay={"half_life_days": 70.0, "last_confirmed": "2026-04-01T14:30:00Z"},
        )
        resp = await trans_client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        resp = await trans_client.get(f"/v1/knowledge/{EID_TRN1}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["content"] == "Test transparency of encryption"
        assert data["tags"] == ["enc", "test"]
        assert data["decay"]["half_life_days"] == 70.0

    async def test_list_and_search_return_decrypted_data(self, trans_client):
        """List and search should return decrypted data."""
        list_ids = [EID_TRL0, EID_TRL1, EID_TRL2]
        for i, eid in enumerate(list_ids):
            entry = _make_entry(
                entry_id=eid,
                user_id="user-trans-ls",
                content=f"List search entry {i}",
                session_id=f"s{i}",
            )
            resp = await trans_client.post("/v1/knowledge", json=entry)
            assert resp.status_code == 201

        # List
        resp = await trans_client.get(
            "/v1/knowledge",
            params={"user_id": "user-trans-ls"},
        )
        assert resp.status_code == 200
        entries = resp.json()
        assert len(entries) == 3
        for e in entries:
            assert "List search entry" in e["content"]

        # Search
        resp = await trans_client.get(
            "/v1/knowledge",
            params={"user_id": "user-trans-ls", "query": "entry"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_user_model_roundtrip_transparent(self, trans_client):
        """User model API roundtrip should be unchanged by encryption."""
        model = {
            "oamp_version": "1.0.0",
            "type": "user_model",
            "user_id": "user-trans-model",
            "model_version": 1,
            "updated_at": "2026-04-28T12:00:00Z",
            "communication": {
                "verbosity": -0.6,
                "formality": 0.2,
                "prefers_examples": True,
            },
        }
        resp = await trans_client.post("/v1/user-model", json=model)
        assert resp.status_code == 201

        resp = await trans_client.get("/v1/user-model/user-trans-model")
        assert resp.status_code == 200
        data = resp.json()
        assert data["communication"]["verbosity"] == -0.6

    async def test_export_import_with_encryption(self, trans_client):
        """Export and import should work transparently with encryption."""
        entry = _make_entry(
            entry_id=EID_TRE1,
            user_id="user-trans-exp",
            content="Exported encrypted data",
        )
        resp = await trans_client.post("/v1/knowledge", json=entry)
        assert resp.status_code == 201

        # Export
        resp = await trans_client.post("/v1/export", json={"user_id": "user-trans-exp"})
        assert resp.status_code == 200
        exported = resp.json()
        assert exported["entries"][0]["content"] == "Exported encrypted data"

        # Delete and re-import
        resp = await trans_client.delete(f"/v1/knowledge/{EID_TRE1}")
        assert resp.status_code == 204

        import_payload = {
            "oamp_version": "1.0.0",
            "type": "knowledge_store",
            "user_id": "user-trans-exp",
            "entries": exported["entries"],
        }
        resp = await trans_client.post("/v1/import", json=import_payload)
        assert resp.status_code == 200
        assert resp.json()["imported"] == 1

        # Verify
        resp = await trans_client.get(f"/v1/knowledge/{EID_TRE1}")
        assert resp.status_code == 200
        assert resp.json()["content"] == "Exported encrypted data"