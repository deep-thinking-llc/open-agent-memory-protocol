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

---

## Separate Track: Verifiable Erasure (Research)

### Issue 9: Cryptographic proof of deletion

This is intentionally separate from the governed-memory and withheld-results
tracks. Current OAMP erasure is trust-based: the backend asserts that DELETE
removed the data, and conformance is checked via the audit log. This issue
tracks the open question of whether a future version of OAMP should offer a
way for a data subject to *cryptographically verify* that their data is no
longer present in the backend's current state.

Background note: `docs/security-guide.md` §4 "Verifiable Erasure
(Non-Normative — Future Work)" sketches the design tension with GDPR
Article 17 and names three candidate patterns.

Sequencing:

- **First iteration (v2.x earliest): crypto-shredded leaves.** Per-entry
  salts are destroyed on erasure; the leaf becomes a cryptographically
  unlinkable random value, and inclusion proofs for the remaining entries
  continue to verify. This composes with the existing zeroize-before-delete
  transaction (`docs/security-guide.md` §4) and uses commodity Merkle
  tooling, so it is a near-additive change rather than a new cryptosystem.
- **Distant follow-on: sparse Merkle exclusion proofs.** A separately
  advertised capability layered on top of the first iteration, once
  operational practice has answered the salt-custody and publication-cadence
  questions below. It offers stronger user-facing absence proofs but
  requires sparse-tree machinery and per-SDK non-membership verifiers.
- **Not on the path: per-user Merkle trees.** Considered and rejected
  because it loses cross-user verifiability for little implementation saving
  over crypto-shredded leaves.

Questions to resolve for the first iteration:

- Is the published root over crypto-shredded leaves GDPR-defensible in
  practice (the per-leaf hash is unlinkable once the salt is destroyed, but
  the publication mechanism still needs to be designed so the root itself
  does not accumulate as a permanent linkable artifact)?
- What salt-custody and salt-destruction guarantees does the spec need to
  require so that backups, restores, and replica catch-up cannot resurrect
  a destroyed salt?
- What publication cadence for the root is the minimum useful guarantee,
  and where should the root be published?
- What threat is the proof actually defending against, given the existing
  threat model already trusts the backend for deletion? (Working answer:
  silent non-compliance by the operator, and stale backups resurfacing
  deleted data as linkable PII.)
- Should this be a capability advertised via `/v1/capabilities`, a separate
  optional endpoint, or a major-version change?

Questions deferred until the distant follow-on is on the roadmap:

- For exclusion proofs, what publication cadence and client tooling would
  be expected of a conformant backend?
- Which sparse-tree construction (RFC 6962-style sorted, sparse Merkle,
  Verkle) is the right portable choice, and what does the per-SDK
  non-membership verifier surface look like?

Out of scope for v1.x. The first iteration would target v2.x at the
earliest; the sparse-Merkle follow-on is deliberately further out.
