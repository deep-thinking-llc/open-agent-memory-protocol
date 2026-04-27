# OAMP Reference Backend Server

FastAPI-based reference implementation of the Open Agent Memory Protocol backend API.

## Features

- **AES-256-GCM encryption at rest** (spec §8.1.1) — all PII/content fields encrypted with per-row key references
- **Key rotation** via `POST /v1/admin/keys/rotate` — new writes use the new key, old data decryptable with old key
- **Audit logging** (spec §8.2.6) — all CRUD operations logged without knowledge content
- **Zeroization** (spec §8.2.7) — encrypted columns overwritten before deletion
- **SQLite persistence** with async I/O via `aiosqlite`
- **FTS5 full-text search** with Porter stemming for knowledge entry queries
- **Version conflict detection** for User Model updates (monotonic `model_version`)
- **Bulk export/import** via `KnowledgeStore` format
- **OpenAPI/Swagger UI** auto-generated at `/docs`
- **JSON error responses** per spec Section 6.8

## Quick Start

```bash
# Install dependencies (includes cryptography>=42.0)
pip install -e ".[dev]"

# Run the server (auto-creates keys on first start)
python -m oamp_server

# Or with custom settings
python -m oamp_server --host 127.0.0.1 --port 8080 --db-path ./data/oamp.db

# Run tests (133 tests: 95 original + 38 encryption-specific)
PYTHONPATH=src pytest tests/ -v
```

## API Endpoints

### Knowledge Entries

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/knowledge` | Create a KnowledgeEntry (201) |
| `GET` | `/v1/knowledge?user_id=...` | List/search entries (`query=` for FTS5 search, `category=` filter, pagination) |
| `GET` | `/v1/knowledge/{entry_id}` | Get entry by ID |
| `PATCH` | `/v1/knowledge/{entry_id}` | Update confidence/tags/decay |
| `DELETE` | `/v1/knowledge/{entry_id}` | Delete entry (204) |

### User Models

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/user-model` | Create (201) or update (200) model |
| `GET` | `/v1/user-model/{user_id}` | Get model by user_id |
| `DELETE` | `/v1/user-model/{user_id}` | Delete model + all knowledge (204) |

### Bulk Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/export` | Export all knowledge as KnowledgeStore (includes UserModel in metadata) |
| `POST` | `/v1/import` | Import a KnowledgeStore |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/admin/keys/rotate` | Rotate encryption key — new key becomes active |
| `GET` | `/v1/admin/audit` | Query audit log entries (optional `user_id` filter) |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |

## Encryption Architecture

### Schema Design

All PII and knowledge content is encrypted at rest using AES-256-GCM. The schema separates plaintext columns (needed for querying/sorting) from encrypted columns:

**Knowledge entries:**
- Plaintext: `id`, `user_id`, `category`, `confidence`, `oamp_version`, `type`, timestamps
- Encrypted: `content_enc`, `source_enc`, `decay_enc`, `tags_enc`, `metadata_enc`

**User models:**
- Plaintext: `user_id`, `model_version`, `oamp_version`, `type`, timestamps
- Encrypted: `communication_enc`, `expertise_enc`, `corrections_enc`, `stated_prefs_enc`, `metadata_enc`

Each row stores an `encryption_key_id` referencing the key used for that row's encryption. This enables key rotation — old rows can be decrypted with their original key while new rows use the current key.

### Key Management

- **AAD (Additional Authenticated Data)** = `user_id` — binds ciphertext to user scope; tampering with `user_id` fails the auth tag
- **12-byte random nonce** per encryption operation
- **LocalKeyProvider** stores keys as base64-encoded files in a directory (dev/test only)
- Production deployments should use AWS KMS or HashiCorp Vault (configurable via `OAMP_ENCRYPTION_PROVIDER`)

### FTS5 Search Trade-off

Since content is encrypted in the main table, FTS5 indexes plaintext content at write time. The FTS5 virtual table itself is not encrypted — this is an accepted trade-off for Phase 3. The FTS5 index is ephemeral in memory for tests. Production deployments should encrypt the SQLite database at the filesystem level.

### Audit Logging

Per spec §8.2.6, all CRUD operations are logged to an `audit_log` table. The audit log **never** contains knowledge content, source, tags, or any PII — only the action, user_id, entry_id, timestamp, and actor.

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OAMP_DB_PATH` | `oamp.db` | SQLite database path (use `:memory:` for tests) |
| `OAMP_HOST` | `0.0.0.0` | Bind host |
| `OAMP_PORT` | `8000` | Bind port |
| `OAMP_LOG_LEVEL` | `info` | Log level |
| `OAMP_ENCRYPTION_KEY_DIR` | `./keys` | Directory for encryption key files |
| `OAMP_ENCRYPTION_PROVIDER` | `local` | Key provider: `local` (dev), `aws-kms`, `vault` (future) |
| `OAMP_AUDIT_LOG` | `true` | Enable/disable audit logging |

## Architecture

```
src/oamp_server/
├── main.py              # FastAPI app factory, lifespan, error handlers
├── config.py            # Settings (env vars including encryption config)
├── encryption.py        # AES-256-GCM encrypt/decrypt, KeyProvider, LocalKeyProvider
├── __main__.py           # CLI entry point
├── api/
│   ├── knowledge.py      # Knowledge CRUD + search endpoints
│   ├── user_model.py     # User model CRUD endpoints
│   ├── bulk.py           # Export/import endpoints
│   ├── admin.py          # Key rotation + audit query endpoints
│   └── errors.py         # OampError, error response models
├── services/
│   ├── knowledge.py      # Knowledge business logic, validation
│   └── user_model.py    # User model business logic, version enforcement
├── repository/
│   ├── base.py           # Abstract Repository interface
│   └── sqlite.py         # SQLite + FTS5 + encryption implementation
└── middleware/
    ├── __init__.py        # Middleware package
    └── audit.py           # Audit logging (spec §8.2.6)
```

## Test Suite (133 tests)

- **Knowledge CRUD** (20): create with all optionals, duplicate 409, get, delete + 204 empty body, list, pagination, category filter
- **FTS5 search** (6): Porter stemming, multi-word, case-insensitive, scoped, category filter, pagination, negative limit
- **User model CRUD** (12): 201 on create, 200 on update, version monotonicity (409), model_version >= 1, delete + remove knowledge
- **Validation & PATCH** (15): error format (Section 6.8), forbidden PATCH fields (id/user/category/source/content), duplicate ID 409, version conflict 409, 404 handling
- **Bulk export/import** (9): POST /v1/export, POST /v1/import, UserModel in metadata, skipped/rejected counts, spec examples
- **Health & spec round-trips** (14): health check, spec JSON files validated through API, pre-populated E2E scenarios, export/import cycle
- **SDK integration** (10): KnowledgeEntry round-trips (all categories, all optionals), UserModel round-trips (all expertise levels), KnowledgeStore import/export, validation alignment
- **Encryption module** (11): encrypt/decrypt roundtrip, ciphertext verification, nonce uniqueness, AAD mismatch, key rotation, LocalKeyProvider
- **Stored data ciphertext** (3): DB query shows encrypted content, encrypted user model, plaintext fields queryable
- **Key rotation** (3): endpoint, old data decryptable, new data uses new key
- **Audit logging** (5): create/delete/update logged, no content leakage, entry_id tracked
- **Zeroization** (2): knowledge delete, user model delete
- **FTS5 with encryption** (2): search finds encrypted content, Porter stemming works
- **Encryption transparency** (4): API roundtrip, list/search, user model, export/import

Run with:
```bash
PYTHONPATH=src pytest tests/ -v
```

## Phase Status

- [x] **Phase 1**: FastAPI skeleton, SQLite repo, Knowledge/UserModel CRUD
- [x] **Phase 2**: FTS5 search, bulk export/import, PATCH endpoint
- [x] **Phase 3**: AES-256-GCM encryption at rest, key management, audit logging, zeroization
- [ ] **Phase 4**: Docker, performance benchmarks, compliance test integration