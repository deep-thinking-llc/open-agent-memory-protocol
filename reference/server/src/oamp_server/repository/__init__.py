"""Repository implementations for OAMP data persistence."""

from .base import Repository
from .sqlite import SQLiteRepository

__all__ = ["Repository", "SQLiteRepository"]