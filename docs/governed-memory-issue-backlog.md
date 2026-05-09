# Governed Memory Upstream Backlog

This backlog turns the governed-memory proposal into a reviewable upstream
sequence for OAMP.

Related drafts:

- `spec/v1.2/oamp-v1.2-governed-memory.md`
- `spec/v1.2/oamp-v1.2.md`
- `spec/v1.3/oamp-v1.3-draft.md`
- `spec/v2.0/oamp-v2.0-withheld-results-rfc.md`

---

## Phase 1: Scope Lock

### Issue 1: Approve the standards split

Decide and document:

- `v1.2` standardizes additive governed-memory metadata and richer provenance
- `v1.3` standardizes enforcement of that metadata at the agent boundary
- `v2.0` handles portable withheld/redacted result semantics

Why first:

- It prevents implementations from assuming stub semantics are part of the
  additive `v1.2` proposal.

---

## Phase 2: Schema And OpenAPI

### Issue 2: Add `governance` to `KnowledgeEntry`

Files:

- `spec/v1.2/knowledge-entry.schema.json`
- `spec/v1.2/knowledge-store.schema.json`
- `spec/v1.2/openapi.yaml`

Acceptance criteria:

- `governance` is OPTIONAL
- `sensitivity_class` is standardized
- free-form `labels` are supported
- no breaking changes to required v1.x fields

### Issue 3: Add extended `provenance`

Files:

- `spec/v1.2/knowledge-entry.schema.json`
- `spec/v1.2/openapi.yaml`

Acceptance criteria:

- existing `source` remains mandatory and unchanged
- new `provenance.sources[]` supports multi-source lineage
- import/export semantics are documented

---

## Phase 3: Capabilities And Discovery

### Issue 4: Advertise governance support in `/v1/capabilities`

Files:

- `spec/v1.2/oamp-v1.2-governed-memory.md`
- any consolidated capabilities spec text

Acceptance criteria:

- backends can advertise governance support
- supported sensitivity classes are discoverable
- support for labels and extended provenance is discoverable
- any non-standard withheld stub behavior is explicitly marked non-portable

### Issue 5: Standardize governance-aware filter keys

Acceptance criteria:

- define `sensitivity_class`
- define `governance_label`
- specify where filters apply and how unsupported filters are advertised

---

## Phase 4: Compliance And Reference Implementations

### Issue 6: Add compliance coverage

Files:

- `reference/compliance/README.md`
- `reference/compliance/src/oamp_compliance/tests/`

Acceptance criteria:

- create with `governance`
- create with extended `provenance`
- retrieve round-trip
- import/export preservation where supported
- capabilities reporting

### Issue 7: Update reference types and backend

Targets:

- Rust
- TypeScript
- Python
- Go
- Elixir
- reference server

Acceptance criteria:

- reference types parse and serialize new optional fields
- reference server preserves them
- no regression in v1.0/v1.1 behavior

---

## Separate Track: v2.0 Withheld Results RFC

### Issue 8: RFC for portable withheld/redacted result semantics

This is intentionally separate from the `v1.2` work.

Questions to resolve:

- Should withheld results be a new document type, a response envelope, or a
  major-version `KnowledgeEntry` change?
- How should `withholding_reason` be standardized?
- How should search/export/stream carry mixed visible and withheld results?
- How do we preserve privacy without destroying interoperability?
