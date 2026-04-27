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
| `GET` | `/v1/knowledge?user_id=...` | List entries for a user |
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
| `GET` | `/v1/export/{user_id}` | Export all knowledge as KnowledgeStore |
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

## Test Suite

59 tests covering:

- **CRUD operations**: Create, read, update, delete for knowledge entries and user models
- **Search**: FTS5 full-text search with Porter stemming, case-insensitive, scoped to user
- **Validation**: Error format (Section 6.8), forbidden PATCH fields, version conflicts
- **Bulk**: Export/import round-trips, spec example validation
- **Edge cases**: Empty stores, nonexistent resources, duplicate IDs

Run with:
```bash
PYTHONPATH=src pytest tests/ -v
```

## Phase Status

- [x] **Phase 1**: FastAPI skeleton, SQLite repo, Knowledge/UserModel CRUD
- [x] **Phase 2**: FTS5 search, bulk export/import, PATCH endpoint
- [ ] **Phase 3**: AES-256-GCM encryption at rest, key management
- [ ] **Phase 4**: Docker, performance benchmarks, compliance test integration