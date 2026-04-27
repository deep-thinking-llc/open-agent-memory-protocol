"""Error response models for OAMP API."""

from __future__ import annotations

from fastapi import HTTPException
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response per OAMP spec Section 6.8."""

    error: str
    code: str


class OampError(HTTPException):
    """Base OAMP HTTP exception."""

    def __init__(self, status_code: int, error: str, code: str) -> None:
        self.error_msg = error
        self.error_code = code
        super().__init__(status_code=status_code, detail=ErrorResponse(error=error, code=code).model_dump())


def not_found(resource_type: str, resource_id: str) -> OampError:
    return OampError(404, f"{resource_type} not found: {resource_id}", "NOT_FOUND")


def validation_error(msg: str) -> OampError:
    return OampError(400, msg, "VALIDATION_ERROR")


def version_conflict(stored_version: int, attempted_version: int) -> OampError:
    return OampError(
        409,
        f"model_version {attempted_version} must be > {stored_version}",
        "VERSION_CONFLICT",
    )


def forbidden_patch(field: str) -> OampError:
    return OampError(400, f"Cannot patch field: {field}", "FORBIDDEN_PATCH")