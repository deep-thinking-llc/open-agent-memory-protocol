# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] — 2026-05-09

Cross-impl interop verified 2026-05-09: kizuna-mem ↔ cosmictron, both
directions produce empty diffs against `spec/v1.2/examples/` and
`validators/test-fixtures/valid/`. Conformance pressure-test passed; v1.2
promoted from draft.

### Added (proposed, draft for community review)
- **`spec/v1.2/oamp-v1.2-governed-memory.md`** — design rationale for
  governed-memory standardization across OAMP backends used by `cosmictron`,
  `kizuna-mem`, `ultra`, and `toraeru`.
- **`spec/v1.2/oamp-v1.2.md`** — normative spec that ratifies the
  working split: v1.2 standardizes additive governance metadata, richer
  provenance, and discovery/filter semantics, while withheld/redacted result
  documents are explicitly deferred to a separate v2.0 design track.
- **Concrete v1.2 contract artifacts**:
  - `spec/v1.2/knowledge-entry.schema.json`
  - `spec/v1.2/knowledge-store.schema.json`
  - `spec/v1.2/openapi.yaml`
  - `spec/v1.2/examples/*`
- **Validator support for v1.2 documents** via `validators/validate.sh` and
  governed-memory fixtures under `validators/test-fixtures/`.
- **Reference TypeScript, Rust, Go, and Elixir support for the v1.2 draft path**:
  - all reference libraries now parse optional `governance` and `provenance`
  - round-trip tests cover governed-memory example documents across languages
- **Reference Python + server support for the v1.2 draft path**:
  - Python types now parse optional `governance` and `provenance`
  - reference server preserves governed-memory fields and advertises
    `/v1/capabilities`
  - governance-aware list/search filter keys are wired in the reference server
- **Compliance and interop follow-up artifacts**:
  - `spec/v2.0/oamp-v2.0-withheld-results-rfc.md`
  - `docs/governed-memory-interop-matrix.md`
  - canonical interop fixture pack under `spec/v1.2/examples/` and `validators/test-fixtures/valid/`

### Proposed scope
- Optional `governance` field on `KnowledgeEntry`
- Optional extended `provenance` field for multi-source lineage
- Capabilities advertisement for governance support
- Optional governance-aware filter keys

### Explicitly deferred
- Standard `withholding_reason`
- Standard redacted/withheld result documents
- Standard stream-level withheld event semantics
- Cross-backend authorization policy language

## [1.3.0-draft] — 2026-05-07

### Added (proposed, draft for community review)
- **`spec/v1.3/oamp-v1.3-draft.md`** — normative draft for governed-memory
  enforcement, reusing the v1.2 descriptive metadata model.
- **Concrete v1.3 contract artifacts**:
  - `spec/v1.3/knowledge-entry.schema.json`
  - `spec/v1.3/knowledge-store.schema.json`
  - `spec/v1.3/openapi.yaml`
  - `spec/v1.3/examples/*`
- **Validator support for `1.3.0` documents** via `validators/validate.sh` and
  new v1.3 fixtures.
- **Reference backend enforcement example**:
  - signed grant parsing via Bearer JWT or `OAMP-Grant`
  - omission-based read/export filtering
  - 404 existence hiding on agent get-by-id
  - write-scope rejection and import rejection counts
  - `/v1/capabilities` enforcement advertisement
- **Reference library compatibility updates**:
  - Python, TypeScript, Rust, and Go validators accept `1.3.0`
  - round-trip tests cover v1.3 fixtures

### Proposed scope
- Portable agent grant claims
- Hierarchical label matching for enforcement
- Read/write/import/export filtering rules
- Existence hiding on agent surfaces
- Enforcement capabilities advertisement

### Explicitly deferred
- Portable withheld/redacted result documents
- Portable `withholding_reason` envelopes
- Stream-level withheld event payloads

## [1.1.0] — 2026-05-09

### Added (proposed, draft for community review)
- **`spec/v1.1/oamp-v1.1.md`** — Strictly additive minor version
  introducing two OPTIONAL capabilities and a capabilities-discovery
  endpoint. No breaking changes; v1.0 clients remain wire-compatible.
- **Capabilities discovery endpoint** (`GET /v1/capabilities`) — lets
  clients learn which OPTIONAL features a backend supports, replacing
  vendor-extension sniffing.
- **Streaming subprotocol** (`oamp.v1` over WebSocket at `/v1/stream`) —
  push-based delivery of `knowledge_created` / `knowledge_updated` /
  `knowledge_deleted` / `user_model_updated` / `knowledge_snapshot`
  events, with subscription filters and at-most-once semantics.
  Privacy-preserving: `knowledge_deleted` frames carry only the entry
  id, never the deleted content.
- **Bitemporal `?as_of=<iso8601>`** query parameter on read endpoints
  (`/v1/knowledge`, `/v1/knowledge/{id}`, `/v1/user-model/{user_id}`)
  with response header `OAMP-As-Of` echoing the resolved timestamp and
  a `min_resolution_ms` advertisement in capabilities. Mutation
  endpoints reject `as_of` with `400 Bad Request`.
- **Reference implementation targets:** cosmictron and kizuna-mem are
  landing both OPTIONAL capabilities concurrently with the draft. They
  serve as the conformance pressure-test for v1.1; the draft will be
  revised if either implementation cannot land cleanly.

### Open questions for finalisation
- Subscription resumption (`since=<event_id>` on `subscribe`) — likely
  deferred to v2.0.
- Snapshot pagination — tentative `snapshot_chunk` frame when backends
  declare a `streaming.snapshot_max_entries` limit.
- gRPC streaming binding under `/proto/` — pending stabilised JSON
  shape.
- `valid_at` (world-time) queries — reserved but not standardised; v1.2
  or v2.0 work once ≥2 backends ship interoperable implementations.

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
