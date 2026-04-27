# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Reference Backend Server** (`reference/server/`): FastAPI-based OAMP backend
  - 12 REST endpoints: Knowledge CRUD, search, user model CRUD, bulk export/import
  - SQLite persistence with `aiosqlite` async I/O
  - FTS5 full-text search with Porter stemming
  - Version conflict detection (monotonic `model_version`)
  - Spec-compliant error responses (Section 6.8)
  - Health check at `/health`
  - OpenAPI/Swagger UI at `/docs`
  - 59 tests covering CRUD, search, validation, bulk ops, spec round-trips
  - Server README with architecture docs and quick start
- CI workflow updated to include server test suite
- README updated with server section and quick start

## [1.0.1] - 2025-01-XX

### Added
- Initial v1.0.0 spec: KnowledgeEntry, KnowledgeStore, UserModel schemas
- JSON Schema definitions (draft-2020-12)
- Protocol Buffer definitions
- Rust reference implementation (oamp-types crate)
- TypeScript reference implementation (@oamp/types package)
- Python reference implementation (oamp-types package)
- Go reference implementation (oamp-go module)
- Elixir reference implementation (oamp_types Hex package)
- Protobuf code generation script (scripts/protoc-gen.sh)
- CI workflow with caching, Python version matrix, and all 5 language test suites
- Release automation workflow (publish to crates.io, npm, PyPI on tags)
- Root .gitignore (Python, Rust, TypeScript, Go, Elixir, IDE/OS files)
- Removed tracked Rust build artifacts from git
- Validator CLI and test fixtures
- Documentation: agent guide, backend guide, security guide
