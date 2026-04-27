"""OAMP v1 reference backend server configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    """Server configuration loaded from environment variables."""

    db_path: str = field(
        default_factory=lambda: os.environ.get(
            "OAMP_DB_PATH", "oamp.db"
        )
    )
    host: str = field(
        default_factory=lambda: os.environ.get("OAMP_HOST", "0.0.0.0")
    )
    port: int = field(
        default_factory=lambda: int(os.environ.get("OAMP_PORT", "8000"))
    )
    log_level: str = field(
        default_factory=lambda: os.environ.get("OAMP_LOG_LEVEL", "info")
    )
    max_page_size: int = 200
    default_page_size: int = 50

    # Encryption settings (Phase 3: spec §8.1.1)
    encryption_key_dir: str = field(
        default_factory=lambda: os.environ.get(
            "OAMP_ENCRYPTION_KEY_DIR", "./keys"
        )
    )
    encryption_provider: str = field(
        default_factory=lambda: os.environ.get(
            "OAMP_ENCRYPTION_PROVIDER", "local"
        )
    )
    audit_log: bool = field(
        default_factory=lambda: os.environ.get(
            "OAMP_AUDIT_LOG", "true"
        ).lower() in ("true", "1", "yes")
    )