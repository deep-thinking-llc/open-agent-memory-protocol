# OAMP Reference Backend Server

FastAPI-based reference implementation of the Open Agent Memory Protocol backend API.

## Features

- **SQLite persistence** with async I/O via `aiosqlite`
- **FTS5 full-text search** with Porter stemming for knowledge entry queries
- **Version conflict detection** for User Model updates (monotonic `model_version`)
- **Bulk export/import** via `KnowledgeStore` format
- **OpenAPI/Swagger UI** auto-generated at `/docs`
- **JSON error responses** per spec Section 6.8

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the server
python -m oamp_server

# Or with custom settings
python -m oamp_server --host 127.0.0.1 --port 8080 --db-path ./data/oamp.db

# Run tests
PYTHONPATH=src pytest tests/ -v
```

## API Endpoints

### Knowledge Entries

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/knowledge` | Create a KnowledgeEntry (201) |
| `GET` | `/v1/knowledge?user_id=...` | List/search entries (`query=` for FTS5 search, `category=` filter, pagination) |
| `GET` | `/v1/knowledge/search?q=...&user_id=...` | Full-text search |
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

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |

## Architecture

```
src/oamp_server/
├── main.py              # FastAPI app factory, lifespan, error handlers
├── config.py            # Settings (env vars: OAMP_DB_PATH, OAMP_HOST, OAMP_PORT)
├── api/
│   ├── knowledge.py      # Knowledge CRUD + search endpoints
│   ├── user_model.py    # User model CRUD endpoints
│   ├── bulk.py          # Export/import endpoints
│   └── errors.py        # OampError, error response models
├── services/
│   ├── knowledge.py     # Knowledge business logic, validation
│   └── user_model.py    # User model business logic, version enforcement
├── repository/
│   ├── base.py          # Abstract Repository interface
│   └── sqlite.py        # SQLite + FTS5 implementation
└── middleware/
    └── __init__.py       # (future: auth, rate limiting)
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OAMP_DB_PATH` | `oamp.db` | SQLite database path (use `:memory:` for tests) |
| `OAMP_HOST` | `0.0.0.0` | Bind host |
| `OAMP_PORT` | `8000` | Bind port |
| `OAMP_LOG_LEVEL` | `info` | Log level |

## Test Suite (95 tests)

- **Knowledge CRUD** (20): create with all optionals, duplicate 409, get, delete + 204 empty body, list, pagination, category filter
- **FTS5 search** (6): Porter stemming, multi-word, case-insensitive, scoped, category filter, pagination, negative limit
- **User model CRUD** (12): 201 on create, 200 on update, version monotonicity (409), model_version >= 1, delete + remove knowledge
- **Validation & PATCH** (15): error format (Section 6.8), forbidden PATCH fields (id/user/category/source/content), duplicate ID 409, version conflict 409, 404 handling
- **Bulk export/import** (9): POST /v1/export, POST /v1/import, UserModel in metadata, skipped/rejected counts, spec examples
- **Health & spec round-trips** (14): health check, spec JSON files validated through API, pre-populated E2E scenarios, export/import cycle
- **SDK integration** (10): KnowledgeEntry round-trips (all categories, all optionals), UserModel round-trips (all expertise levels), KnowledgeStore import/export, validation alignment
- **Error compliance**: 409 duplicate, 409 version conflict, 400 validation, 404 not found, 204 delete, FORBIDDEN_PATCH

Run with:
```bash
PYTHONPATH=src pytest tests/ -v
```

## Phase Status

- [x] **Phase 1**: FastAPI skeleton, SQLite repo, Knowledge/UserModel CRUD
- [x] **Phase 2**: FTS5 search, bulk export/import, PATCH endpoint
- [ ] **Phase 3**: AES-256-GCM encryption at rest, key management
- [ ] **Phase 4**: Docker, performance benchmarks, compliance test integration