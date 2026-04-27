# OAMP Compliance Test Suite

Automated test suite that verifies whether a backend implementation conforms to
the OAMP v1 specification. Point it at any running OAMP server and get a
compliance report.

## Quick Start

```bash
# Install
pip install -e .

# Run against a running server
oamp-compliance --url http://localhost:8000

# Run specific category
oamp-compliance --url http://localhost:8000 --category must
oamp-compliance --url http://localhost:8000 --category func

# Output formats
oamp-compliance --url http://localhost:8000 --format json
oamp-compliance --url http://localhost:8000 --format markdown
oamp-compliance --url http://localhost:8000 --format junit

# Write report to file
oamp-compliance --url http://localhost:8000 --format markdown --output compliance-report.md

# With authentication
oamp-compliance --url http://localhost:8000 --header "Authorization: Bearer $TOKEN"
```

## Test Categories

### MUST Requirements (12 tests) — spec §8.1

Failing any = non-compliant.

| ID | Requirement | Description |
|----|-------------|-------------|
| MUST-01 | Encryption at rest | Store entry, verify ciphertext (skip — requires DB access) |
| MUST-02 | Export completeness | Create entries, export, verify count |
| MUST-03 | Full data deletion | Delete user, verify all data removed |
| MUST-04 | No content in logs | Submit entry, check audit log for content |
| MUST-05 | Provenance required | POST without source.session_id, expect 400 |
| MUST-06 | Version monotonicity | POST v7 then v5, expect 409 |
| MUST-07 | Category validation | Invalid category, expect 400 |
| MUST-08 | Confidence range | confidence=1.5, expect 400 |
| MUST-09 | Error format | Verify `{error, code}` format |
| MUST-10 | Real deletion | Delete entry, GET returns 404 |
| MUST-11 | No silent discard | Import with merge conflict, verify reported |
| MUST-12 | Accept unknown metadata | POST with unknown fields, expect 201 |

### SHOULD Requirements (3 tests) — spec §8.2

Recommended. Failing = compliant but not ideal.

| ID | Requirement | Description |
|----|-------------|-------------|
| SHOULD-01 | Audit logging | Perform operations, verify audit log entries |
| SHOULD-02 | Key rotation | Rotate key, verify old data still readable |
| SHOULD-03 | Confidence decay | Requires time-travel simulation (skip) |

### Functional Tests (15 tests) — spec §6

Every endpoint exercised.

| ID | Endpoint | Description |
|----|----------|-------------|
| FUNC-01 | POST /v1/knowledge | Create valid entry, expect 201 |
| FUNC-02 | POST /v1/knowledge | Create with metadata, expect 201 |
| FUNC-03 | GET /v1/knowledge/:id | Retrieve existing entry, expect 200 |
| FUNC-04 | GET /v1/knowledge/:id | Non-existent ID, expect 404 |
| FUNC-05 | GET /v1/knowledge?query= | Search, expect results |
| FUNC-06 | GET /v1/knowledge?query=&user_id= | Search scoped to user |
| FUNC-07 | PATCH /v1/knowledge/:id | Update confidence, expect 200 |
| FUNC-08 | PATCH /v1/knowledge/:id | Forbidden field, expect 400 |
| FUNC-09 | DELETE /v1/knowledge/:id | Delete entry, expect 204 |
| FUNC-10 | POST /v1/user-model | Create model, expect 201 |
| FUNC-11 | POST /v1/user-model | Update with higher version, expect 200 |
| FUNC-12 | GET /v1/user-model/:user_id | Retrieve model, expect 200 |
| FUNC-13 | DELETE /v1/user-model/:user_id | Delete all, expect 204 |
| FUNC-14 | POST /v1/export | Export user data, expect KnowledgeStore |
| FUNC-15 | POST /v1/import | Import store, expect import summary |

## CI Integration

```yaml
- name: OAMP Compliance Test
  run: |
    cd reference/server && uvicorn oamp_server.main:create_app --factory &
    sleep 5
    pip install -e reference/compliance
    oamp-compliance --url http://localhost:8000 --format junit --output compliance-results.xml
    kill %1
```

## Architecture

```
reference/compliance/
├── pyproject.toml
├── README.md
├── src/
│   └── oamp_compliance/
│       ├── __init__.py
│       ├── runner.py          # CLI entry point
│       ├── client.py          # HTTP client for any OAMP server
│       ├── reporter.py        # Report generation (text/json/markdown/junit)
│       └── tests/
│           ├── __init__.py
│           ├── utils.py       # TestResult, registry, helpers
│           ├── must.py        # MUST requirement tests
│           ├── should.py      # SHOULD requirement tests
│           └── functional.py  # Endpoint functional tests
└── reports/
    └── .gitkeep
```

## License

MIT
