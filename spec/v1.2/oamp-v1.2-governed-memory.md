# Open Agent Memory Protocol — Governed Memory for v1.2

**Status:** Stable
**Date:** 2026-05-09
**Authors:** Deep Thinking LLC
**Related implementations:** `cosmictron`, `kizuna-mem`, `ultra`, `toraeru`
**Depends on:** `spec/v1/oamp-v1.md`, `spec/v1.1/oamp-v1.1.md`

---

## 1. Why this exists

Multiple OAMP backends now need first-class governed memory:

- **kizuna-mem** needs enterprise-grade sensitivity classes, provenance-aware
  policy evaluation, and structured withholding reasons.
- **cosmictron** needs interoperable handling for policy-scoped memory and
  exported/imported governance metadata.
- **ultra** will consume and produce governed memory, so vendor-specific
  `metadata.*` blobs are no longer sufficient if we want backend portability.
- **toraeru** will integrate with OAMP and needs the same portable metadata
  contract rather than backend-specific governance payloads.

Today, OAMP v1.0/v1.1 can carry governed-memory data only as a vendor
extension inside `metadata`, and that is compliant. However:

1. there is no standard shape for governance metadata,
2. there is no standard capabilities advertisement for governed memory,
3. there is no portable representation of richer multi-source provenance,
4. there is no standard wire-level notion of “withheld” or “redacted stub”.

This proposal standardizes the first three as **additive v1.2 work** and
explicitly defers the fourth to **v2.0**, because the current v1.x schemas and
streaming payload rules do not allow a portable redacted stub without a
breaking change.

---

## 2. Recommendation Summary

### Standardize in v1.2

- Optional `governance` object on `KnowledgeEntry`
- Optional `provenance` extension object on `KnowledgeEntry`
- `GET /v1/capabilities` advertisement for governance support
- Optional governance-aware filter keys for search/streaming
- Compliance tests for governed-memory fields and round-trip tolerance

### Defer to v2.0

- Standardized redacted/withheld result documents
- Standardized REST response shapes that can mix visible entries and withheld stubs
- Standardized stream event types for withheld knowledge

---

## 3. Why withheld stubs are not a v1.2 change

This proposal intentionally does **not** standardize withheld stubs in v1.2.

Reasons:

1. In v1.0, `KnowledgeEntry.content` is required and MUST be a non-empty
   string.
2. Search/list responses are defined around arrays of `KnowledgeEntry`
   objects.
3. v1.1 streaming says `knowledge_created` and `knowledge_updated` carry a
   full `KnowledgeEntry`.

That means a portable “stub” such as:

```json
{
  "type": "knowledge_entry",
  "content": null,
  "withheld": true
}
```

is not valid in current v1.x schema terms. Making `content` optional or nullable
would be a breaking schema change, not an additive one.

So the correct standards split is:

- **v1.2:** standardize governance metadata and discovery
- **v2.0:** standardize withheld result semantics

Backends MAY continue to implement vendor-specific withholding behavior in
their own extensions until a v2.0 design lands.

---

## 4. Proposed v1.2 Additions

## 4.1 Optional `governance` field on `KnowledgeEntry`

Add a new OPTIONAL top-level field:

```json
{
  "governance": {
    "sensitivity_class": "confidential",
    "labels": ["finance", "hr"],
    "handling": {
      "retrieval": "governed",
      "export": "governed",
      "stream": "governed"
    }
  }
}
```

### Proposed field shape

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `governance` | object | MAY | Standard governed-memory metadata |
| `governance.sensitivity_class` | string | MUST if `governance` present | One of `public`, `internal`, `confidential`, `restricted` |
| `governance.labels` | array of string | MAY | Backend- or tenant-defined governance labels |
| `governance.handling` | object | MAY | Surface-specific governance hints |
| `governance.handling.retrieval` | string | MAY | `governed` or `ungoverned` |
| `governance.handling.export` | string | MAY | `governed` or `ungoverned` |
| `governance.handling.stream` | string | MAY | `governed` or `ungoverned` |

### Notes

- This field is **descriptive**, not a full policy language.
- It tells other backends and agents how the knowledge was classified.
- It does **not** standardize access-control evaluation rules.
- Backends MAY map richer local policy structures into `metadata` in addition
  to the standard `governance` field.

## 4.2 Optional extended `provenance` field on `KnowledgeEntry`

Keep `source` exactly as-is and add an OPTIONAL richer provenance structure:

```json
{
  "source": {
    "session_id": "sess-42",
    "timestamp": "2026-05-07T10:00:00Z"
  },
  "provenance": {
    "sources": [
      {
        "session_id": "sess-42",
        "timestamp": "2026-05-07T10:00:00Z",
        "agent_id": "agent-a",
        "turn_id": "turn-3"
      },
      {
        "session_id": "sess-43",
        "timestamp": "2026-05-08T09:00:00Z",
        "agent_id": "agent-a",
        "turn_id": "turn-7"
      }
    ],
    "derived": true
  }
}
```

### Proposed field shape

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `provenance` | object | MAY | Extended lineage metadata |
| `provenance.sources` | array | MUST if `provenance` present | Ordered evidence/source list |
| `provenance.sources[].session_id` | string | MUST | Source session identifier |
| `provenance.sources[].timestamp` | string | MUST | ISO 8601 acquisition time |
| `provenance.sources[].agent_id` | string | MAY | Source agent identifier |
| `provenance.sources[].turn_id` | string | MAY | Turn/message-local identifier |
| `provenance.derived` | boolean | MAY | Whether this entry was synthesized from multiple sources |

### Notes

- `source` remains mandatory and remains the minimal provenance contract.
- `provenance` is the richer interoperable lineage extension for backends that
  support merges, synthesis, or evidence chains.

## 4.3 Governance capabilities advertisement

Add an OPTIONAL `governance` object under `/v1/capabilities.capabilities`:

```json
{
  "capabilities": {
    "governance": {
      "supported": true,
      "sensitivity_classes": ["public", "internal", "confidential", "restricted"],
      "labels_supported": true,
      "extended_provenance_supported": true,
      "withheld_stub_support": false
    }
  }
}
```

### Proposed fields

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `governance.supported` | boolean | MUST if `governance` present | Backend understands the standardized governance fields |
| `governance.sensitivity_classes` | array of string | MUST | Classes accepted by the backend |
| `governance.labels_supported` | boolean | MUST | Whether free-form governance labels are stored/preserved |
| `governance.extended_provenance_supported` | boolean | MUST | Whether `provenance` is stored/preserved |
| `governance.withheld_stub_support` | boolean | MUST | Whether the backend has any non-standard withheld stub behavior |

`withheld_stub_support` is informational in v1.2 only. It does not imply a
standardized wire format.

## 4.4 Optional governance-aware filters

Where a backend supports filter advertisement, standardize these OPTIONAL keys:

| Key | Type | Semantics |
|-----|------|-----------|
| `sensitivity_class` | array of string | Match entries whose `governance.sensitivity_class` is in the set |
| `governance_label` | array of string | Match entries that contain at least one listed governance label |

This applies to:

- REST search, where supported by a backend-specific query model
- `streaming.filter_keys`, when streaming is supported

These keys are optional because not every backend indexes governance metadata.

---

## 5. Schema And OpenAPI Impact

This proposal requires a new minor-version schema because the current v1.0 JSON
Schema sets `additionalProperties: false` on `KnowledgeEntry` and
`KnowledgeStore` entry items.

So the v1.2 work must include:

- `spec/v1.2/knowledge-entry.schema.json`
- `spec/v1.2/knowledge-store.schema.json`
- `spec/v1.2/openapi.yaml`

with additive optional fields:

- `governance`
- `provenance`

No required fields change in v1.2.

---

## 6. Compatibility Rules

### v1.2 backend behavior

- MUST accept v1.0 and v1.1 documents.
- MUST preserve `governance` and `provenance` when provided, unless documented
  policy or storage constraints explicitly reject them.
- MUST ignore unknown additional vendor metadata as before.

### v1.0 / v1.1 client behavior

- A v1.0 or v1.1 client may ignore `governance` and `provenance` if it does not
  understand them.
- This is safe because both are OPTIONAL additive fields.

### Import/export expectations

- Backends that support governance SHOULD preserve standardized governance
  fields across export/import.
- Backends that do not support governance SHOULD still accept the document and
  either preserve the fields as opaque data or document that they are dropped.

---

## 7. Non-Goals For v1.2

The following are explicitly out of scope for this proposal:

- Standardized allow/deny policy language
- Cross-backend authorization semantics
- Standardized `withholding_reason`
- Standardized redacted `KnowledgeEntry` stub shape
- Multi-user subscription semantics

Those need either:

- a separate v2.0 design, or
- a new non-`KnowledgeEntry` response/event envelope that does not fit current
  v1.x expectations.

---

## 8. Compliance Additions

If v1.2 lands, add compliance cases for:

- `POST /v1/knowledge` accepts `governance`
- `POST /v1/knowledge` accepts `provenance`
- `GET /v1/knowledge/:id` round-trips standardized governance fields
- `POST /v1/import` preserves governance/provenance where supported
- `/v1/capabilities` advertises governance support accurately

Do **not** add withheld-stub compliance tests in v1.2.

---

## 9. Proposed Upstream Issue Breakdown

### Issue 1: Ratify governed-memory scope split

Decide and document:

- v1.2 standardizes governance metadata + discovery
- v2.0 handles withheld/redacted result semantics

### Issue 2: Add `governance` and `provenance` to v1.2 schema

Files:

- `spec/v1.2/knowledge-entry.schema.json`
- `spec/v1.2/knowledge-store.schema.json`
- `spec/v1.2/openapi.yaml`
- reference type libraries

### Issue 3: Capabilities advertisement and filter keys

Files:

- `spec/v1.2/oamp-v1.2.md`
- `spec/v1.2/openapi.yaml`
- v1.1 capabilities text if reused or superseded

### Issue 4: Compliance suite coverage

Files:

- `reference/compliance/README.md`
- `reference/compliance/src/oamp_compliance/tests/`

### Issue 5: Reference backend support

Files:

- `reference/server/`
- language reference types

### Issue 6: v2.0 RFC for withheld results

Open a separate design track for:

- non-breaking envelope options versus major-version schema changes
- REST semantics for withheld-by-policy
- stream semantics for withheld updates
- portability of `withholding_reason`

---

## 10. Recommendation

Adopt this proposal as the working direction:

1. standardize governed-memory metadata in v1.2,
2. standardize richer provenance in v1.2,
3. leave withholding/redaction semantics out of v1.2,
4. open a separate v2.0 RFC for portable withheld results.

That gives `cosmictron`, `kizuna-mem`, `ultra`, and `toraeru` a common
interoperable target now, without pretending that the current v1.x
`KnowledgeEntry` shape can already express every governed-memory behavior we
want.
