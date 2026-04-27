"""MUST requirement tests for OAMP compliance (spec §8.1).

These tests verify mandatory requirements. Failing any = non-compliant.
"""

from __future__ import annotations

import uuid
from typing import Any

from ..client import OAMPClient
from ..models import make_knowledge_entry, make_user_model
from .utils import TestResult, assert_error_format, new_id, registry


@registry.register("must", "MUST-01", "Encryption at rest — store entry, verify ciphertext in DB")
def test_encryption_at_rest(client: OAMPClient) -> TestResult:
    """Skip — requires DB access (white-box mode)."""
    return TestResult(
        "MUST-01",
        "Encryption at rest",
        TestResult.SKIP,
        "Requires direct DB access to verify. Run in white-box mode with --db-path.",
    )


@registry.register("must", "MUST-02", "Export returns all data — create entries, export, verify count")
def test_export_completeness(client: OAMPClient) -> TestResult:
    """Verify that export returns all entries for a user."""
    user_id = f"compliance-export-{new_id()[:8]}"
    entry_count = 5

    # Create entries
    for i in range(entry_count):
        entry = make_knowledge_entry(
            user_id=user_id,
            content=f"Export test entry {i}",
            entry_id=new_id(),
        )
        resp = client.create_knowledge(entry)
        if resp.status_code != 201:
            return TestResult(
                "MUST-02", "Export returns all data", TestResult.FAIL,
                f"Failed to create entry {i}: {resp.status_code} {resp.text}",
            )

    # Export
    resp = client.export_data(user_id)
    if resp.status_code != 200:
        return TestResult(
            "MUST-02", "Export returns all data", TestResult.FAIL,
            f"Export returned {resp.status_code}: {resp.text}",
        )

    data = resp.json()
    if len(data.get("entries", [])) != entry_count:
        return TestResult(
            "MUST-02", "Export returns all data", TestResult.FAIL,
            f"Expected {entry_count} entries, got {len(data.get('entries', []))}",
        )

    return TestResult("MUST-02", "Export returns all data", TestResult.PASS)


@registry.register("must", "MUST-03", "Delete removes all data — delete user, verify zero rows")
def test_full_data_deletion(client: OAMPClient) -> TestResult:
    """Verify that deleting a user model removes all associated data."""
    user_id = f"compliance-delete-{new_id()[:8]}"

    # Create entries
    for i in range(3):
        entry = make_knowledge_entry(
            user_id=user_id,
            content=f"Delete test entry {i}",
            entry_id=new_id(),
        )
        resp = client.create_knowledge(entry)
        if resp.status_code != 201:
            return TestResult(
                "MUST-03", "Delete removes all data", TestResult.FAIL,
                f"Failed to create entry: {resp.status_code}",
            )

    # Create user model
    model = make_user_model(user_id=user_id)
    resp = client.create_user_model(model)
    if resp.status_code not in (200, 201):
        return TestResult(
            "MUST-03", "Delete removes all data", TestResult.FAIL,
            f"Failed to create user model: {resp.status_code}",
        )

    # Delete user
    resp = client.delete_user_model(user_id)
    if resp.status_code != 204:
        return TestResult(
            "MUST-03", "Delete removes all data", TestResult.FAIL,
            f"Delete returned {resp.status_code}, expected 204",
        )

    # Verify user model is gone
    resp = client.get_user_model(user_id)
    if resp.status_code != 404:
        return TestResult(
            "MUST-03", "Delete removes all data", TestResult.FAIL,
            f"User model still accessible after delete: {resp.status_code}",
        )

    # Verify knowledge entries are gone
    resp = client.list_knowledge(user_id)
    if resp.status_code != 200:
        return TestResult(
            "MUST-03", "Delete removes all data", TestResult.FAIL,
            f"List returned {resp.status_code}",
        )
    entries = resp.json()
    if len(entries) != 0:
        return TestResult(
            "MUST-03", "Delete removes all data", TestResult.FAIL,
            f"Found {len(entries)} entries after delete, expected 0",
        )

    return TestResult("MUST-03", "Delete removes all data", TestResult.PASS)


@registry.register("must", "MUST-04", "No content in logs — submit entry, check audit log for content")
def test_no_content_in_logs(client: OAMPClient) -> TestResult:
    """Verify that audit logs don't contain knowledge content (spec §8.2.6)."""
    user_id = f"compliance-audit-{new_id()[:8]}"
    sensitive_content = "COMPLIANCE_SECRET_CONTENT_98765"

    entry = make_knowledge_entry(
        user_id=user_id,
        content=sensitive_content,
        entry_id=new_id(),
    )
    resp = client.create_knowledge(entry)
    if resp.status_code != 201:
        return TestResult(
            "MUST-04", "No content in logs", TestResult.FAIL,
            f"Failed to create entry: {resp.status_code}",
        )

    # Query audit log
    resp = client.get_audit_log(user_id=user_id)
    if resp.status_code != 200:
        return TestResult(
            "MUST-04", "No content in logs", TestResult.FAIL,
            f"Audit endpoint returned {resp.status_code}: {resp.text}",
        )

    logs = resp.json()
    for log_entry in logs:
        for key, value in log_entry.items():
            if value is not None and isinstance(value, str) and sensitive_content in value:
                return TestResult(
                    "MUST-04", "No content in logs", TestResult.FAIL,
                    f"Audit log leaked content in field '{key}'",
                )

    return TestResult("MUST-04", "No content in logs", TestResult.PASS)


@registry.register("must", "MUST-05", "Provenance required — POST without source.session_id, expect 400")
def test_provenance_required(client: OAMPClient) -> TestResult:
    """Verify that entries without source.session_id are rejected."""
    entry = make_knowledge_entry(entry_id=new_id())
    del entry["source"]["session_id"]
    resp = client.create_knowledge(entry)
    if resp.status_code != 400:
        return TestResult(
            "MUST-05", "Provenance required", TestResult.FAIL,
            f"Expected 400 for missing source.session_id, got {resp.status_code}",
        )
    assert_error_format(resp)
    return TestResult("MUST-05", "Provenance required", TestResult.PASS)


@registry.register("must", "MUST-06", "model_version monotonicity — POST v7 then v5, expect 409")
def test_version_monotonicity(client: OAMPClient) -> TestResult:
    """Verify that user model versions must increase monotonically."""
    user_id = f"compliance-version-{new_id()[:8]}"

    # Create v7
    model = make_user_model(user_id=user_id, model_version=7)
    resp = client.create_user_model(model)
    if resp.status_code != 201:
        return TestResult(
            "MUST-06", "Version monotonicity", TestResult.FAIL,
            f"Failed to create model v7: {resp.status_code}",
        )

    # Try v5 (lower)
    model_v5 = make_user_model(user_id=user_id, model_version=5)
    resp = client.create_user_model(model_v5)
    if resp.status_code != 409:
        return TestResult(
            "MUST-06", "Version monotonicity", TestResult.FAIL,
            f"Expected 409 for lower version, got {resp.status_code}",
        )
    assert_error_format(resp)
    body = resp.json()
    if body.get("code") != "VERSION_CONFLICT":
        return TestResult(
            "MUST-06", "Version monotonicity", TestResult.FAIL,
            f"Expected code VERSION_CONFLICT, got {body.get('code')}",
        )

    # Try v7 again (same)
    model_v7_again = make_user_model(user_id=user_id, model_version=7)
    resp = client.create_user_model(model_v7_again)
    if resp.status_code != 409:
        return TestResult(
            "MUST-06", "Version monotonicity", TestResult.FAIL,
            f"Expected 409 for same version, got {resp.status_code}",
        )

    return TestResult("MUST-06", "Version monotonicity", TestResult.PASS)


@registry.register("must", "MUST-07", "Category validation — POST with unknown category, expect 400")
def test_category_validation(client: OAMPClient) -> TestResult:
    """Verify that invalid category values are rejected."""
    entry = make_knowledge_entry(category="not-a-valid-category", entry_id=new_id())
    resp = client.create_knowledge(entry)
    if resp.status_code != 400:
        return TestResult(
            "MUST-07", "Category validation", TestResult.FAIL,
            f"Expected 400 for invalid category, got {resp.status_code}",
        )
    assert_error_format(resp)
    return TestResult("MUST-07", "Category validation", TestResult.PASS)


@registry.register("must", "MUST-08", "Confidence range — POST with confidence=1.5, expect 400")
def test_confidence_range(client: OAMPClient) -> TestResult:
    """Verify that out-of-range confidence values are rejected."""
    entry = make_knowledge_entry(confidence=1.5, entry_id=new_id())
    resp = client.create_knowledge(entry)
    if resp.status_code != 400:
        return TestResult(
            "MUST-08", "Confidence range", TestResult.FAIL,
            f"Expected 400 for confidence=1.5, got {resp.status_code}",
        )
    assert_error_format(resp)
    return TestResult("MUST-08", "Confidence range", TestResult.PASS)


@registry.register("must", "MUST-09", "Error format — trigger any error, verify {error, code} format")
def test_error_format(client: OAMPClient) -> TestResult:
    """Verify that error responses follow the spec-defined format."""
    # Trigger 404
    resp = client.get_knowledge(new_id())
    if resp.status_code != 404:
        return TestResult(
            "MUST-09", "Error format", TestResult.FAIL,
            f"Expected 404, got {resp.status_code}",
        )
    try:
        assert_error_format(resp)
        body = resp.json()
        if body.get("code") != "NOT_FOUND":
            return TestResult(
                "MUST-09", "Error format", TestResult.FAIL,
                f"Expected code NOT_FOUND, got {body.get('code')}",
            )
    except AssertionError as e:
        return TestResult("MUST-09", "Error format", TestResult.FAIL, str(e))

    # Trigger 400
    entry = make_knowledge_entry(confidence=1.5, entry_id=new_id())
    resp = client.create_knowledge(entry)
    if resp.status_code != 400:
        return TestResult(
            "MUST-09", "Error format", TestResult.FAIL,
            f"Expected 400, got {resp.status_code}",
        )
    try:
        assert_error_format(resp)
    except AssertionError as e:
        return TestResult("MUST-09", "Error format", TestResult.FAIL, str(e))

    return TestResult("MUST-09", "Error format", TestResult.PASS)


@registry.register("must", "MUST-10", "Real deletion — delete entry, GET returns 404")
def test_real_deletion(client: OAMPClient) -> TestResult:
    """Verify that deletion is permanent (not soft-delete)."""
    entry = make_knowledge_entry(entry_id=new_id())
    resp = client.create_knowledge(entry)
    if resp.status_code != 201:
        return TestResult(
            "MUST-10", "Real deletion", TestResult.FAIL,
            f"Failed to create entry: {resp.status_code}",
        )

    entry_id = entry["id"]
    resp = client.delete_knowledge(entry_id)
    if resp.status_code != 204:
        return TestResult(
            "MUST-10", "Real deletion", TestResult.FAIL,
            f"Delete returned {resp.status_code}, expected 204",
        )

    # Must return 404, not 200 with tombstone data
    resp = client.get_knowledge(entry_id)
    if resp.status_code != 404:
        return TestResult(
            "MUST-10", "Real deletion", TestResult.FAIL,
            f"Expected 404 after delete, got {resp.status_code}. Soft-delete detected.",
        )

    return TestResult("MUST-10", "Real deletion", TestResult.PASS)


@registry.register("must", "MUST-11", "No silent discard — import with merge conflict, verify reported")
def test_no_silent_discard(client: OAMPClient) -> TestResult:
    """Verify that import doesn't silently discard entries (spec §6.4 merge semantics).

    When importing, entries with existing IDs must be reported, not silently dropped.
    """
    user_id = f"compliance-merge-{new_id()[:8]}"
    entry_id = new_id()

    # Create original entry
    entry = make_knowledge_entry(user_id=user_id, confidence=0.9, entry_id=entry_id)
    resp = client.create_knowledge(entry)
    if resp.status_code != 201:
        return TestResult(
            "MUST-11", "No silent discard", TestResult.FAIL,
            f"Failed to create entry: {resp.status_code}",
        )

    # Import a store with the same ID and lower confidence
    import_entry = make_knowledge_entry(
        user_id=user_id, confidence=0.3, entry_id=entry_id,
    )
    store = {
        "oamp_version": "1.0.0",
        "type": "knowledge_store",
        "user_id": user_id,
        "entries": [import_entry],
    }
    resp = client.import_data(store)
    if resp.status_code != 200:
        return TestResult(
            "MUST-11", "No silent discard", TestResult.FAIL,
            f"Import returned {resp.status_code}: {resp.text}",
        )

    result = resp.json()
    # The entry with the same ID but lower confidence should NOT be silently dropped.
    # The spec requires that rejected entries be reported.
    total_reported = result.get("imported", 0) + result.get("rejected", 0)
    if total_reported < 1:
        return TestResult(
            "MUST-11", "No silent discard", TestResult.FAIL,
            f"Import with duplicate ID: expected at least 1 entry reported, "
            f"got imported={result.get('imported')} rejected={result.get('rejected')}",
        )

    return TestResult("MUST-11", "No silent discard", TestResult.PASS)


@registry.register("must", "MUST-12", "Accept unknown metadata — POST with unknown metadata field, expect 201")
def test_accept_unknown_metadata(client: OAMPClient) -> TestResult:
    """Verify that the server accepts entries with unknown metadata fields (spec §9)."""
    entry = make_knowledge_entry(
        entry_id=new_id(),
        metadata={"custom_vendor_field": "should-be-accepted", "another_unknown": 42},
    )
    resp = client.create_knowledge(entry)
    if resp.status_code != 201:
        return TestResult(
            "MUST-12", "Accept unknown metadata", TestResult.FAIL,
            f"Expected 201 for entry with unknown metadata, got {resp.status_code}: {resp.text}",
        )
    # Verify the entry was stored and can be retrieved
    resp = client.get_knowledge(entry["id"])
    if resp.status_code != 200:
        return TestResult(
            "MUST-12", "Accept unknown metadata", TestResult.FAIL,
            f"Failed to retrieve entry: {resp.status_code}",
        )
    return TestResult("MUST-12", "Accept unknown metadata", TestResult.PASS)