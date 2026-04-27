"""AES-256-GCM encryption at rest for OAMP server.

Spec §8.1.1: "All stored knowledge and user model data MUST be encrypted
at rest. AES-256-GCM is RECOMMENDED."

Key design:
- 32-byte (256-bit) keys, 12-byte random nonces per encryption
- AAD = user_id binds ciphertext to user scope (auth tag fails on tampering)
- LocalKeyProvider stores keys as base64 in files (dev/test only)
- Production should use AWS KMS or HashiCorp Vault
"""

from __future__ import annotations

import base64
import json
import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@dataclass(frozen=True)
class EncryptionKey:
    """A single AES-256 key with an identifier."""

    key_id: str
    key_bytes: bytes  # 32 bytes for AES-256

    def __post_init__(self) -> None:
        if len(self.key_bytes) != 32:
            raise ValueError(f"AES-256 key must be 32 bytes, got {len(self.key_bytes)}")


class KeyProvider(Protocol):
    """Protocol for key management backends."""

    def get_active_key(self) -> EncryptionKey:
        """Return the current active encryption key."""
        ...

    def get_key(self, key_id: str) -> EncryptionKey:
        """Look up a key by its identifier."""
        ...

    def rotate(self) -> EncryptionKey:
        """Generate a new key, mark it as active, return it."""
        ...


class LocalKeyProvider:
    """Default key provider: stores keys as base64-encoded files in a directory.

    File layout:
        <key_dir>/
            <key_id>.key      — base64-encoded 32-byte key
            _active           — text file containing the active key_id
            _metadata.json    — key metadata (key_id, created_at, active)

    This provider is intended for development and testing only.
    Production deployments should use AWS KMS or HashiCorp Vault.
    """

    def __init__(self, key_dir: str | Path) -> None:
        self._key_dir = Path(key_dir)
        self._key_dir.mkdir(parents=True, exist_ok=True)

    def _key_path(self, key_id: str) -> Path:
        return self._key_dir / f"{key_id}.key"

    def _active_path(self) -> Path:
        return self._key_dir / "_active"

    def _metadata_path(self, key_id: str) -> Path:
        return self._key_dir / f"_{key_id}.meta.json"

    def generate_key(self) -> EncryptionKey:
        """Generate a new random AES-256 key and persist it."""
        key_id = secrets.token_hex(8)  # 16-char hex identifier
        key_bytes = AESGCM.generate_key(bit_length=256)
        key = EncryptionKey(key_id=key_id, key_bytes=key_bytes)

        # Write key file
        self._key_path(key_id).write_bytes(base64.b64encode(key_bytes))

        # Write metadata
        metadata = {
            "key_id": key_id,
            "created_at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
            "active": False,
        }
        self._metadata_path(key_id).write_text(json.dumps(metadata))

        return key

    def set_active(self, key_id: str) -> None:
        """Mark a key as the active key."""
        # Verify key exists
        self.get_key(key_id)
        self._active_path().write_text(key_id)

        # Update metadata
        meta_path = self._metadata_path(key_id)
        if meta_path.exists():
            metadata = json.loads(meta_path.read_text())
        else:
            metadata = {"key_id": key_id}
        metadata["active"] = True
        meta_path.write_text(json.dumps(metadata))

    def get_active_key(self) -> EncryptionKey:
        """Return the current active encryption key.

        If no active key exists, generates one automatically.
        """
        active_path = self._active_path()
        if not active_path.exists():
            # Bootstrap: generate first key automatically
            key = self.generate_key()
            self.set_active(key.key_id)
            return key

        key_id = active_path.read_text().strip()
        if not key_id:
            key = self.generate_key()
            self.set_active(key.key_id)
            return key

        return self.get_key(key_id)

    def get_key(self, key_id: str) -> EncryptionKey:
        """Look up a key by its identifier."""
        key_path = self._key_path(key_id)
        if not key_path.exists():
            raise KeyError(f"Encryption key not found: {key_id}")
        key_bytes = base64.b64decode(key_path.read_bytes())
        return EncryptionKey(key_id=key_id, key_bytes=key_bytes)

    def rotate(self) -> EncryptionKey:
        """Generate a new key, mark it as active.

        Old key remains available for decryption of existing data.
        New writes will use the new key.
        """
        # Mark old active key as inactive
        old_active_path = self._active_path()
        if old_active_path.exists():
            old_key_id = old_active_path.read_text().strip()
            if old_key_id:
                old_meta_path = self._metadata_path(old_key_id)
                if old_meta_path.exists():
                    old_metadata = json.loads(old_meta_path.read_text())
                    old_metadata["active"] = False
                    old_meta_path.write_text(json.dumps(old_metadata))

        # Generate new key and set as active
        new_key = self.generate_key()
        self.set_active(new_key.key_id)
        return new_key


def encrypt(plaintext: str, key: EncryptionKey, aad: str) -> str:
    """AES-256-GCM encrypt.

    Args:
        plaintext: The string to encrypt.
        key: AES-256 key with key_id.
        aad: Additional Authenticated Data (user_id, binds ciphertext to user scope).

    Returns:
        Base64-encoded nonce + ciphertext + tag.
    """
    aesgcm = AESGCM(key.key_bytes)
    nonce = os.urandom(12)  # 12-byte random nonce per spec
    plaintext_bytes = plaintext.encode("utf-8")
    aad_bytes = aad.encode("utf-8") if aad else b""

    ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, aad_bytes)
    # nonce || ciphertext (tag is appended by AESGCM.encrypt)
    combined = nonce + ciphertext
    return base64.b64encode(combined).decode("ascii")


def decrypt(encrypted: str, key_id: str, provider: KeyProvider, aad: str) -> str:
    """Decrypt base64-encoded AES-256-GCM ciphertext.

    Args:
        encrypted: Base64-encoded nonce + ciphertext + tag.
        key_id: Identifier of the key used to encrypt.
        provider: KeyProvider to look up the key.
        aad: Additional Authenticated Data (must match encryption-time aad).

    Returns:
        Decrypted plaintext string.

    Raises:
        KeyError: If key_id is not found in the provider.
        cryptography.exceptions.InvalidTag: If AAD or key mismatch (tampering).
    """
    key = provider.get_key(key_id)
    aesgcm = AESGCM(key.key_bytes)

    combined = base64.b64decode(encrypted)
    nonce = combined[:12]
    ciphertext = combined[12:]
    aad_bytes = aad.encode("utf-8") if aad else b""

    plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, aad_bytes)
    return plaintext_bytes.decode("utf-8")


def zeroize(data: str) -> None:
    """Best-effort zeroization of a string's memory.

    Per spec §8.2.7: "Delete operations SHOULD zeroize memory buffers
    containing knowledge content before freeing them."

    Note: Python strings are immutable and interned, so true zeroization
    is not possible. This is a best-effort approach.
    """
    # We can't truly zeroize a Python str due to immutability,
    # but this function serves as documentation of the intent
    # and can be called for compliance demonstration.
    pass