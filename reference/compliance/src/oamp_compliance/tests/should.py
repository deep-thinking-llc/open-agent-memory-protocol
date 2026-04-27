"""SHOULD requirement tests for OAMP compliance (spec §8.2).

These tests verify recommended requirements. Failing = compliant but not ideal.
"""

from __future__ import annotations

from ..client import OAMPClient
from ..models import make_knowledge_entry
from .utils import TestResult, new_id, registry


@registry.register("should", "SHOULD-01", "Audit logging — perform operations, verify audit_log entries")
def test_audit_logging(client: OAMPClient) -> TestResult:
    """Verify that operations are audit logged (spec §8.2.6)."""
    user_id = f"compliance-should-audit-{new_id()[:8]}"

    # Create entry
    entry = make_knowledge_entry(user_id=user_id, entry_id=new_id())
    resp = client.create_knowledge(entry)
    if resp.status_code != 201:
        return TestResult(
            "SHOULD-01", "Audit logging", TestResult.FAIL,
            f"Failed to create entry: {resp.status_code}",
        )

    # Check audit log
    resp = client.get_audit_log(user_id=user_id)
    if resp.status_code != 200:
        return TestResult(
            "SHOULD-01", "Audit logging", TestResult.FAIL,
            f"Audit endpoint returned {resp.status_code}",
        )
    logs = resp.json()
    if not logs:
        return TestResult(
            "SHOULD-01", "Audit logging", TestResult.FAIL,
            "No audit log entries found for operations",
        )

    create_actions = [l for l in logs if l.get("action") == "create"]
    if not create_actions:
        return TestResult(
            "SHOULD-01", "Audit logging", TestResult.FAIL,
            "No 'create' action in audit log",
        )

    # Delete and verify audit
    resp = client.delete_knowledge(entry["id"])
    if resp.status_code == 204:
        resp = client.get_audit_log(user_id=user_id)
        logs = resp.json()
        delete_actions = [l for l in logs if l.get("action") == "delete"]
        if not delete_actions:
            return TestResult(
                "SHOULD-01", "Audit logging", TestResult.FAIL,
                "No 'delete' action in audit log",
            )

    return TestResult("SHOULD-01", "Audit logging", TestResult.PASS)


@registry.register("should", "SHOULD-02", "Key rotation — rotate key, verify old data still readable")
def test_key_rotation(client: OAMPClient) -> TestResult:
    """Verify that key rotation works and old data remains readable."""
    user_id = f"compliance-rotate-{new_id()[:8]}"

    # Create entry with current key
    entry = make_knowledge_entry(user_id=user_id, entry_id=new_id())
    resp = client.create_knowledge(entry)
    if resp.status_code != 201:
        return TestResult(
            "SHOULD-02", "Key rotation", TestResult.FAIL,
            f"Failed to create entry: {resp.status_code}",
        )

    # Rotate key
    resp = client.rotate_key()
    if resp.status_code != 200:
        return TestResult(
            "SHOULD-02", "Key rotation", TestResult.FAIL,
            f"Key rotation returned {resp.status_code}: {resp.text}",
        )
    data = resp.json()
    if "key_id" not in data:
        return TestResult(
            "SHOULD-02", "Key rotation", TestResult.FAIL,
            "Key rotation response missing key_id",
        )

    # Old entry should still be readable
    resp = client.get_knowledge(entry["id"])
    if resp.status_code != 200:
        return TestResult(
            "SHOULD-02", "Key rotation", TestResult.FAIL,
            f"Old entry not readable after rotation: {resp.status_code}",
        )
    returned = resp.json()
    if returned.get("content") != entry["content"]:
        return TestResult(
            "SHOULD-02", "Key rotation", TestResult.FAIL,
            "Old entry content changed after key rotation",
        )

    # New entry should use new key
    entry2 = make_knowledge_entry(user_id=user_id, entry_id=new_id())
    resp = client.create_knowledge(entry2)
    if resp.status_code != 201:
        return TestResult(
            "SHOULD-02", "Key rotation", TestResult.FAIL,
            f"Failed to create entry after rotation: {resp.status_code}",
        )

    return TestResult("SHOULD-02", "Key rotation", TestResult.PASS)


@registry.register("should", "SHOULD-03", "Confidence decay — create entry with decay, verify reduced confidence")
def test_confidence_decay(client: OAMPClient) -> TestResult:
    """Skip — requires temporal simulation or server-side support."""
    return TestResult(
        "SHOULD-03",
        "Confidence decay",
        TestResult.SKIP,
        "Requires time-travel or server-side decay simulation. Manual verification recommended.",
    )