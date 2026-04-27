"""Shared test utilities for the compliance test suite."""

from __future__ import annotations

import uuid
from typing import Any


def new_id() -> str:
    """Generate a valid UUID v4."""
    return str(uuid.uuid4())


def assert_error_format(response: Any) -> None:
    """Assert that a response has the spec-defined error format (spec §6.8).

    All error responses MUST be JSON with 'error' (string) and 'code' (string).
    """
    body = response.json()
    assert isinstance(body, dict), f"Error body must be a dict, got {type(body)}"
    assert "error" in body, f"Error body missing 'error' field: {body}"
    assert "code" in body, f"Error body missing 'code' field: {body}"
    assert isinstance(body["error"], str), f"'error' must be a string, got {type(body['error'])}"
    assert isinstance(body["code"], str), f"'code' must be a string, got {type(body['code'])}"


class TestResult:
    """Result of a single compliance test."""

    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"

    def __init__(
        self,
        test_id: str,
        description: str,
        status: str = PASS,
        message: str = "",
    ) -> None:
        self.test_id = test_id
        self.description = description
        self.status = status
        self.message = message

    def to_dict(self) -> dict[str, str]:
        return {
            "test_id": self.test_id,
            "description": self.description,
            "status": self.status,
            "message": self.message,
        }

    def __repr__(self) -> str:
        icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⚠️"}.get(self.status, "?")
        return f"{icon} {self.test_id}: {self.description} ({self.status})"


class TestRegistry:
    """Registry of all compliance tests, organized by category."""

    def __init__(self) -> None:
        self.tests: list[tuple[str, str, callable]] = []

    def register(self, category: str, test_id: str, description: str) -> callable:
        """Decorator to register a test function."""
        def decorator(func: callable) -> callable:
            self.tests.append((category, test_id, description, func))
            return func
        return decorator

    def get_by_category(self, category: str) -> list[tuple[str, str, str, callable]]:
        """Get all tests in a category."""
        return [(c, tid, desc, fn) for c, tid, desc, fn in self.tests if c == category]

    def get_all(self) -> list[tuple[str, str, str, callable]]:
        """Get all registered tests."""
        return list(self.tests)

    def categories(self) -> list[str]:
        """Get unique category names."""
        return list({c for c, _, _, _ in self.tests})


# Global registry
registry = TestRegistry()