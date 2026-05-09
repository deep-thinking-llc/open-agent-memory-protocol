# Open Agent Memory Protocol — Version 1.2.0

**Status:** Stable  
**Date:** 2026-05-09  
**Authors:** Deep Thinking LLC  
**Supersedes:** None — extends v1.0.0 and v1.1.0 additively  
**Repository:** `github.com/deep-thinking-llc/open-agent-memory-protocol`

---

## Abstract

OAMP v1.2 is a **strictly additive** minor version over v1.0.0 and the
optional v1.1 draft features. It standardizes a portable shape for:

- governed-memory metadata on `KnowledgeEntry`,
- richer multi-source provenance on `KnowledgeEntry`,
- governance capability advertisement on `GET /v1/capabilities`, and
- governance-aware filter keys for search and streaming surfaces.

v1.2 intentionally does **not** standardize withheld or redacted result
documents. Those semantics require either a new response envelope or a breaking
change to the `KnowledgeEntry` contract, so they are explicitly deferred to a
separate v2.0 design track.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

---

## 1. Relationship to v1.0 and v1.1

v1.2 reuses all v1.0 schemas, endpoints, requirements, and semantics, plus the
optional v1.1 capabilities model, without changing any required field.

The only new wire-level additions are:

- OPTIONAL `governance` on `KnowledgeEntry`
- OPTIONAL `provenance` on `KnowledgeEntry`
- OPTIONAL `capabilities.governance` on `GET /v1/capabilities`
- OPTIONAL governance-aware filter keys

Documents SHOULD set `oamp_version` to `"1.2.0"` when they exercise a v1.2-only
field. Documents using only v1.0 fields MAY continue to use `"1.0.0"` for
maximum portability.

---

## 2. Scope Split

### 2.1 Standardized in v1.2

- portable governed-memory metadata
- portable richer provenance
- capabilities discovery for governed-memory support
- optional governance-aware filtering

### 2.2 Explicitly deferred to v2.0

- standardized withheld or redacted result documents
- mixed result sets containing visible entries and withheld stubs
- stream event payloads for withheld knowledge
- portable `withholding_reason` semantics
- standardized cross-backend authorization policy language

This split is normative for the v1.2 draft. Implementations MUST NOT claim that
withheld or redacted stubs are standardized by v1.2.

---

## 3. `KnowledgeEntry` Additions

### 3.1 Optional `governance`

`KnowledgeEntry` gains an OPTIONAL `governance` object:

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

#### Fields

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `governance` | object | MAY | Standard governed-memory metadata |
| `governance.sensitivity_class` | string | MUST if `governance` present | One of `public`, `internal`, `confidential`, `restricted` |
| `governance.labels` | array of string | MAY | Backend- or tenant-defined governance labels |
| `governance.handling` | object | MAY | Surface-specific handling hints |
| `governance.handling.retrieval` | string | MAY | `governed` or `ungoverned` |
| `governance.handling.export` | string | MAY | `governed` or `ungoverned` |
| `governance.handling.stream` | string | MAY | `governed` or `ungoverned` |

The `governance` object is descriptive. It is not a portable policy engine.

### 3.2 Optional `provenance`

`KnowledgeEntry` keeps the existing REQUIRED `source` object and adds an
OPTIONAL richer `provenance` object:

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

#### Fields

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `provenance` | object | MAY | Extended lineage metadata |
| `provenance.sources` | array | MUST if `provenance` present | Ordered evidence/source list |
| `provenance.sources[].session_id` | string | MUST | Source session identifier |
| `provenance.sources[].timestamp` | string | MUST | ISO 8601 acquisition time |
| `provenance.sources[].agent_id` | string | MAY | Source agent identifier |
| `provenance.sources[].turn_id` | string | MAY | Turn/message-local identifier |
| `provenance.derived` | boolean | MAY | Whether this entry was synthesized from multiple sources |

The existing `source` field remains the minimal provenance contract and MUST
still be present.

---

## 4. Capabilities Additions

v1.2 extends the v1.1 `GET /v1/capabilities` response with an OPTIONAL
`capabilities.governance` object:

```json
{
  "oamp_version": "1.2.0",
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

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `governance.supported` | boolean | MUST if `governance` present | Backend understands the standardized governance fields |
| `governance.sensitivity_classes` | array of string | MUST | Classes accepted by the backend |
| `governance.labels_supported` | boolean | MUST | Whether free-form labels are stored and preserved |
| `governance.extended_provenance_supported` | boolean | MUST | Whether `provenance` is stored and preserved |
| `governance.withheld_stub_support` | boolean | MUST | Whether the backend has any non-standard withheld behavior |

`withheld_stub_support` is informational only in v1.2 and MUST NOT be read as a
portable result-format guarantee.

---

## 5. Governance-Aware Filter Keys

Backends that already support query filters or streaming subscription filters
MAY advertise and accept these OPTIONAL governance-aware keys:

| Key | Type | Semantics |
|-----|------|-----------|
| `sensitivity_class` | array of string | Match entries whose `governance.sensitivity_class` is in the set |
| `governance_label` | array of string | Match entries containing at least one listed governance label |

For REST search endpoints, these MAY appear as repeated query parameters.
For streaming, these MAY appear in the `streaming.filter_keys` advertisement and
in subscription payloads.

Backends that do not index governance metadata MAY reject or ignore these keys,
but MUST advertise support accurately in capabilities.

---

## 6. Compatibility Rules

### 6.1 v1.2 backends

- MUST accept v1.0 and v1.1 documents.
- MUST preserve `governance` and `provenance` when supported.
- MUST continue tolerating unknown vendor-specific metadata extensions.

### 6.2 v1.0 and v1.1 clients

- MAY ignore `governance` and `provenance` if they do not understand them.
- MUST NOT assume withheld or redacted result semantics from a v1.2 version
  string alone.

### 6.3 Import and export

- Backends that support governed memory SHOULD preserve standardized
  `governance` and `provenance` across export and import.
- Backends that do not support governed memory SHOULD document whether those
  fields are preserved opaquely or dropped.

---

## 7. Schema And OpenAPI Artifacts

The v1.2 draft is represented by:

- `spec/v1.2/knowledge-entry.schema.json`
- `spec/v1.2/knowledge-store.schema.json`
- `spec/v1.2/openapi.yaml`

These artifacts are additive over `spec/v1/` and do not change the v1.0
required-field contract.
