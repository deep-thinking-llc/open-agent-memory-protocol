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