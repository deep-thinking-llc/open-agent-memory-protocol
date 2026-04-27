"""OAMP Server package."""

from .main import create_app
from .config import Settings

__all__ = ["create_app", "Settings"]