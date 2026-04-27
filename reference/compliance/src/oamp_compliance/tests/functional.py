"""Functional endpoint tests for OAMP compliance.

Tests every endpoint defined in spec Section 6.
"""

from __future__ import annotations

from ..client import OAMPClient
from ..models import make_knowledge_entry, make_user_model, make_knowledge_store
from .utils import TestResult, new_id, registry


# ── Knowledge Entry Endpoints ───────────────────────────────────────


@registry.register("func", "FUNC-01", "POST /v1/knowledge — create valid entry, expect 201")
def test_create_knowledge(client: OAMPClient) -> TestResult:
    entry = make_knowledge_entry(entry_id=new_id())
    resp = client.create_knowledge(entry)
    if resp.status_code != 201:
        return TestResult("FUNC-01", "Create knowledge entry", TestResult.FAIL, str(resp.text))
    data = resp.json()
    if data.get("id") != entry["id"]:
        return TestResult("FUNC-01", "Create knowledge entry", TestResult.FAIL, "ID mismatch")
    return TestResult("FUNC-01", "Create knowledge entry", TestResult.PASS)


@registry.register("func", "FUNC-02", "POST /v1/knowledge — create with unknown metadata, expect 201")
def test_create_with_metadata(client: OAMPClient) -> TestResult:
    entry = make_knowledge_entry(entry_id=new_id(), metadata={"custom": "value"})
    resp = client.create_knowledge(entry)
    if resp.status_code != 201:
        return TestResult("FUNC-02", "Accept unknown metadata", TestResult.FAIL, str(resp.text))
    return TestResult("FUNC-02", "Accept unknown metadata", TestResult.PASS)


@registry.register("func", "FUNC-03", "GET /v1/knowledge/:id — retrieve existing entry, expect 200")
def test_get_knowledge(client: OAMPClient) -> TestResult:
    entry = make_knowledge_entry(entry_id=new_id())
    resp = client.create_knowledge(entry)
    if resp.status_code != 201:
        return TestResult("FUNC-03", "Retrieve entry", TestResult.FAIL, f"Create failed: {resp.text}")

    resp = client.get_knowledge(entry["id"])
    if resp.status_code != 200:
        return TestResult("FUNC-03", "Retrieve entry", TestResult.FAIL, str(resp.text))
    data = resp.json()
    if data.get("content") != entry["content"]:
        return TestResult("FUNC-03", "Retrieve entry", TestResult.FAIL, "Content mismatch")
    return TestResult("FUNC-03", "Retrieve entry", TestResult.PASS)


@registry.register("func", "FUNC-04", "GET /v1/knowledge/:id — non-existent ID, expect 404")
def test_get_nonexistent(client: OAMPClient) -> TestResult:
    resp = client.get_knowledge(new_id())
    if resp.status_code != 404:
        return TestResult("FUNC-04", "Non-existent entry (404)", TestResult.FAIL, str(resp.text))
    return TestResult("FUNC-04", "Non-existent entry (404)", TestResult.PASS)


@registry.register("func", "FUNC-05", "GET /v1/knowledge?query= — search, expect results")
def test_search(client: OAMPClient) -> TestResult:
    user_id = f"compliance-search-{new_id()[:8]}"
    entry = make_knowledge_entry(
        user_id=user_id, content="Rust programming compliance test", entry_id=new_id(),
    )
    resp = client.create_knowledge(entry)
    if resp.status_code != 201:
        return TestResult("FUNC-05", "Search", TestResult.FAIL, f"Create failed: {resp.text}")

    resp = client.list_knowledge(user_id=user_id, query="Rust")
    if resp.status_code != 200:
        return TestResult("FUNC-05", "Search", TestResult.FAIL, str(resp.text))
    results = resp.json()
    if not isinstance(results, list):
        return TestResult("FUNC-05", "Search", TestResult.FAIL, "Expected array response")
    return TestResult("FUNC-05", "Search", TestResult.PASS)


@registry.register("func", "FUNC-06", "GET /v1/knowledge?query=&user_id= — search scoped to user")
def test_search_scoped(client: OAMPClient) -> TestResult:
    user_a = f"compliance-scope-a-{new_id()[:8]}"
    user_b = f"compliance-scope-b-{new_id()[:8]}"

    entry_a = make_knowledge_entry(
        user_id=user_a, content="Only user A knows this fact", entry_id=new_id(),
    )
    entry_b = make_knowledge_entry(
        user_id=user_b, content="Only user B knows this fact", entry_id=new_id(),
    )
    for entry in [entry_a, entry_b]:
        resp = client.create_knowledge(entry)
        if resp.status_code != 201:
            return TestResult("FUNC-06", "User-scoped search", TestResult.FAIL, f"Create failed")

    # Search for user A's data
    resp = client.list_knowledge(user_id=user_a, query="fact")
    if resp.status_code != 200:
        return TestResult("FUNC-06", "User-scoped search", TestResult.FAIL, str(resp.text))
    results = resp.json()
    if not all(e.get("user_id") == user_a for e in results):
        return TestResult("FUNC-06", "User-scoped search", TestResult.FAIL, "Results leaked across users")
    return TestResult("FUNC-06", "User-scoped search", TestResult.PASS)


@registry.register("func", "FUNC-07", "PATCH /v1/knowledge/:id — update confidence, expect 200")
def test_patch_confidence(client: OAMPClient) -> TestResult:
    entry = make_knowledge_entry(entry_id=new_id())
    resp = client.create_knowledge(entry)
    if resp.status_code != 201:
        return TestResult("FUNC-07", "Update confidence", TestResult.FAIL, f"Create failed: {resp.text}")

    resp = client.update_knowledge(entry["id"], {"confidence": 0.95})
    if resp.status_code != 200:
        return TestResult("FUNC-07", "Update confidence", TestResult.FAIL, str(resp.text))
    data = resp.json()
    if data.get("confidence") != 0.95:
        return TestResult("FUNC-07", "Update confidence", TestResult.FAIL, "Confidence not updated")
    return TestResult("FUNC-07", "Update confidence", TestResult.PASS)


@registry.register("func", "FUNC-08", "PATCH /v1/knowledge/:id — patch forbidden field, expect 400")
def test_patch_forbidden(client: OAMPClient) -> TestResult:
    entry = make_knowledge_entry(entry_id=new_id())
    resp = client.create_knowledge(entry)
    if resp.status_code != 201:
        return TestResult("FUNC-08", "Reject forbidden patch", TestResult.FAIL, f"Create failed")

    resp = client.update_knowledge(entry["id"], {"user_id": "hacker"})
    if resp.status_code != 400:
        return TestResult("FUNC-08", "Reject forbidden patch", TestResult.FAIL,
                          f"Expected 400 for forbidden field, got {resp.status_code}")
    return TestResult("FUNC-08", "Reject forbidden patch", TestResult.PASS)


@registry.register("func", "FUNC-09", "DELETE /v1/knowledge/:id — delete entry, expect 204")
def test_delete_knowledge(client: OAMPClient) -> TestResult:
    entry = make_knowledge_entry(entry_id=new_id())
    resp = client.create_knowledge(entry)
    if resp.status_code != 201:
        return TestResult("FUNC-09", "Delete entry", TestResult.FAIL, f"Create failed")

    resp = client.delete_knowledge(entry["id"])
    if resp.status_code != 204:
        return TestResult("FUNC-09", "Delete entry", TestResult.FAIL, f"Expected 204, got {resp.status_code}")
    if resp.content != b"":
        return TestResult("FUNC-09", "Delete entry", TestResult.FAIL, "204 response must have empty body")
    return TestResult("FUNC-09", "Delete entry", TestResult.PASS)


# ── User Model Endpoints ────────────────────────────────────────────


@registry.register("func", "FUNC-10", "POST /v1/user-model — create model, expect 201")
def test_create_user_model(client: OAMPClient) -> TestResult:
    user_id = f"compliance-um-{new_id()[:8]}"
    model = make_user_model(user_id=user_id)
    resp = client.create_user_model(model)
    if resp.status_code != 201:
        return TestResult("FUNC-10", "Create user model", TestResult.FAIL, str(resp.text))
    return TestResult("FUNC-10", "Create user model", TestResult.PASS)


@registry.register("func", "FUNC-11", "POST /v1/user-model — update with higher version, expect 200")
def test_update_user_model(client: OAMPClient) -> TestResult:
    user_id = f"compliance-um-upd-{new_id()[:8]}"
    model = make_user_model(user_id=user_id, model_version=1)
    resp = client.create_user_model(model)
    if resp.status_code != 201:
        return TestResult("FUNC-11", "Update user model", TestResult.FAIL, f"Create failed")

    model_v2 = make_user_model(user_id=user_id, model_version=2)
    resp = client.create_user_model(model_v2)
    if resp.status_code != 200:
        return TestResult("FUNC-11", "Update user model", TestResult.FAIL,
                          f"Expected 200 for update, got {resp.status_code}")
    return TestResult("FUNC-11", "Update user model", TestResult.PASS)


@registry.register("func", "FUNC-12", "GET /v1/user-model/:user_id — retrieve model, expect 200")
def test_get_user_model(client: OAMPClient) -> TestResult:
    user_id = f"compliance-um-get-{new_id()[:8]}"
    model = make_user_model(user_id=user_id)
    client.create_user_model(model)

    resp = client.get_user_model(user_id)
    if resp.status_code != 200:
        return TestResult("FUNC-12", "Retrieve user model", TestResult.FAIL, str(resp.text))
    data = resp.json()
    if data.get("user_id") != user_id:
        return TestResult("FUNC-12", "Retrieve user model", TestResult.FAIL, "user_id mismatch")
    return TestResult("FUNC-12", "Retrieve user model", TestResult.PASS)


@registry.register("func", "FUNC-13", "DELETE /v1/user-model/:user_id — delete all, expect 204")
def test_delete_user_model(client: OAMPClient) -> TestResult:
    user_id = f"compliance-um-del-{new_id()[:8]}"
    model = make_user_model(user_id=user_id)
    client.create_user_model(model)

    # Also create some knowledge entries
    for i in range(3):
        entry = make_knowledge_entry(user_id=user_id, entry_id=new_id())
        client.create_knowledge(entry)

    resp = client.delete_user_model(user_id)
    if resp.status_code != 204:
        return TestResult("FUNC-13", "Delete user + all data", TestResult.FAIL,
                          f"Expected 204, got {resp.status_code}")
    if resp.content != b"":
        return TestResult("FUNC-13", "Delete user + all data", TestResult.FAIL,
                          "204 response must have empty body")

    # Verify all data is gone
    resp = client.get_user_model(user_id)
    if resp.status_code != 404:
        return TestResult("FUNC-13", "Delete user + all data", TestResult.FAIL,
                          "User model still exists after delete")
    resp = client.list_knowledge(user_id)
    entries = resp.json()
    if len(entries) != 0:
        return TestResult("FUNC-13", "Delete user + all data", TestResult.FAIL,
                          f"Knowledge entries still exist after delete: {len(entries)}")
    return TestResult("FUNC-13", "Delete user + all data", TestResult.PASS)


# ── Bulk Endpoints ──────────────────────────────────────────────────


@registry.register("func", "FUNC-14", "POST /v1/export — export user data, expect KnowledgeStore")
def test_export(client: OAMPClient) -> TestResult:
    user_id = f"compliance-export-{new_id()[:8]}"
    for i in range(3):
        entry = make_knowledge_entry(
            user_id=user_id, content=f"Export entry {i}", entry_id=new_id(),
        )
        client.create_knowledge(entry)

    resp = client.export_data(user_id)
    if resp.status_code != 200:
        return TestResult("FUNC-14", "Export", TestResult.FAIL, str(resp.text))
    data = resp.json()
    if data.get("type") != "knowledge_store":
        return TestResult("FUNC-14", "Export", TestResult.FAIL, f"Wrong type: {data.get('type')}")
    if len(data.get("entries", [])) != 3:
        return TestResult("FUNC-14", "Export", TestResult.FAIL,
                          f"Expected 3 entries, got {len(data.get('entries', []))}")
    return TestResult("FUNC-14", "Export", TestResult.PASS)


@registry.register("func", "FUNC-15", "POST /v1/import — import store, expect import summary")
def test_import(client: OAMPClient) -> TestResult:
    user_id = f"compliance-import-{new_id()[:8]}"
    entries = [
        make_knowledge_entry(user_id=user_id, content=f"Import entry {i}", entry_id=new_id())
        for i in range(3)
    ]
    store = make_knowledge_store(user_id=user_id, entries=entries)

    resp = client.import_data(store)
    if resp.status_code != 200:
        return TestResult("FUNC-15", "Import", TestResult.FAIL, str(resp.text))
    data = resp.json()
    if data.get("imported") != 3:
        return TestResult("FUNC-15", "Import", TestResult.FAIL,
                          f"Expected 3 imported, got {data.get('imported')}")
    if "skipped" not in data or "rejected" not in data:
        return TestResult("FUNC-15", "Import", TestResult.FAIL,
                          "Import response missing skipped/rejected fields")
    return TestResult("FUNC-15", "Import", TestResult.PASS)