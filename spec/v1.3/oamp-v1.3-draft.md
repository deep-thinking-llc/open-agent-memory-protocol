# Open Agent Memory Protocol — Version 1.3.0 (Draft)

**Status:** Draft (proposed minor version)  
**Date:** 2026-05-07  
**Authors:** Deep Thinking LLC  
**Supersedes:** None — extends v1.0.0, v1.1.0, and v1.2.0 additively  
**Repository:** `github.com/deep-thinking-llc/open-agent-memory-protocol`

---

## Abstract

OAMP v1.3 is a **strictly additive** minor version over v1.0.0 and the
optional v1.1 and v1.2 draft features. It standardizes the **enforcement**
layer for governed memory introduced descriptively in v1.2.

v1.2 standardized:

- `governance.sensitivity_class`
- `governance.labels`
- `governance.handling`
- richer `provenance`
- governance capabilities discovery

v1.3 defines what a backend MUST do with those fields when multiple agents for
the same user access the same backend. It standardizes:

- portable agent grant claims
- hierarchical label-matching conventions
- read, write, import, export, and stream filtering rules
- existence hiding on agent surfaces
- agent-identity binding to provenance
- audit-log additions
- capabilities advertisement for enforcement support

v1.3 remains **omission-based**. It does **not** standardize portable withheld
or redacted result documents. That work remains deferred to the separate v2.0
track.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

---

## 1. Relationship To Earlier Versions

v1.3 reuses every v1.0 schema, endpoint, requirement, and semantic rule, plus
the optional v1.1 capabilities model and the additive v1.2 governed-memory
metadata model.

The only new wire-level additions in v1.3 are:

- OPTIONAL `capabilities.governance.enforcement` on `GET /v1/capabilities`
- a portable agent grant claim format for JWT claims or `OAMP-Grant`
- normative backend behavior that consumes the existing v1.2 `governance`
  fields

v1.3 introduces **no new `KnowledgeEntry` fields** and **no new
`KnowledgeStore` fields**.

Documents that only exercise v1.0-v1.2 entry/store fields MAY continue to use
`"1.2.0"` for `oamp_version`. Documents and responses that want to advertise
the v1.3 draft line MAY use `"1.3.0"`.

---

## 2. Scope Split

### 2.1 Standardized In v1.3

- portable per-agent grant claims
- hierarchical governance-label enforcement semantics
- operational meaning for v1.2 governance handling hints
- read filtering
- write rejection
- import rejection accounting
- export filtering and `oamp_export_full`
- stream filtering on v1.1 surfaces
- existence hiding on agent surfaces
- provenance binding to `oamp_agent_id`
- governance enforcement capabilities advertisement
- audit action names for grant and scope events

### 2.2 Explicitly deferred to v2.0

- standardized withheld or redacted result documents
- mixed result sets containing visible entries and withheld stubs
- portable `withholding_reason` semantics
- stream payloads that explicitly represent withheld knowledge
- a portable cross-backend authorization policy language

Implementations MUST NOT claim that v1.3 standardizes withheld or redacted stub
documents.

---

## 3. Operational Reuse Of v1.2 Governance Metadata

v1.3 adds **no new entry-level governance fields**. Instead it makes the v1.2
fields operational.

### 3.1 `governance.sensitivity_class`

The v1.2 enum is ordered:

`public < internal < confidential < restricted`

An agent grant carries `oamp_sensitivity_max`. Entries whose effective
`sensitivity_class` exceeds the grant ceiling are filtered or rejected.

When `governance` is absent, the effective class is `internal` for enforcement
purposes.

### 3.2 `governance.labels`

v1.3 introduces a hierarchical label convention used by enforcement.

- A label SHOULD be a dotted lowercase ASCII path matching
  `^[a-z][a-z0-9]*(\\.[a-z][a-z0-9_]*)*$`
- Hierarchical prefix matching applies
- A grant for `health` matches `health.condition` and
  `health.condition.diagnosis`

Reserved top-level labels for cross-vendor interoperability:

- `identity`
- `location`
- `health`
- `finance`
- `relationships`
- `work`
- `preferences`
- `creative`
- `beliefs`
- `behaviour`

Vendor-specific extensions SHOULD live under `x.<vendor>.<...>`.

Labels that do not match the hierarchical convention remain valid descriptive
v1.2 labels, but backends that enforce v1.3 SHOULD treat them as opaque exact
match values.

When `governance.labels` is absent or empty, the effective label set is
`["behaviour"]` for enforcement purposes.

### 3.3 `governance.handling`

The v1.2 `handling` hints become load-bearing in v1.3:

- `retrieval: "governed"` means read paths MUST apply grant filtering
- `retrieval: "ungoverned"` exempts the entry from read-path filtering
- `export: "governed"` means export paths MUST apply grant filtering
- `export: "ungoverned"` exempts the entry from export-path filtering
- `stream: "governed"` means v1.1 streaming paths MUST apply grant filtering
- `stream: "ungoverned"` exempts the entry from stream filtering

When `governance` is present and a handling value is omitted, the effective
default is `governed` for that surface.

---

## 4. Agent Grant Claims

### 4.1 JWT claim shape

When bearer authentication uses JWT, the token carries these additional claims:

```json
{
  "sub": "user-abc",
  "oamp_agent_id": "medical-assistant-v3",
  "oamp_grant_id": "grant-2026-05-07-001",
  "oamp_read_labels": ["health", "preferences"],
  "oamp_write_labels": ["health", "preferences"],
  "oamp_sensitivity_max": "restricted",
  "oamp_export_full": false,
  "exp": 1746662400
}
```

| Claim | Requirement | Description |
|-------|-------------|-------------|
| `oamp_agent_id` | MUST | Stable identifier for the calling agent |
| `oamp_grant_id` | MUST | Stable identifier for the grant instance |
| `oamp_read_labels` | MUST | Labels the agent may read |
| `oamp_write_labels` | MUST | Labels the agent may write |
| `oamp_sensitivity_max` | MUST | Highest readable/writable sensitivity class |
| `oamp_export_full` | MAY | Whether full unfiltered export is authorized |

Empty `oamp_read_labels` means read-nothing.

### 4.2 `OAMP-Grant` header

For deployments that do not use JWT bearer tokens, the same claim object MAY be
conveyed in an `OAMP-Grant` header. The header value MUST be a compact JWS over
the claim object.

### 4.3 Provenance binding

When a write happens under a v1.3 grant, the backend MUST verify:

- `entry.source.agent_id == oamp_agent_id`, when `source.agent_id` is present

For entries with `provenance.sources[*].agent_id`, backends SHOULD validate each
listed `agent_id` against the calling grant or their local trust model.

---

## 5. Backend Enforcement Rules

A backend that advertises `governance.enforcement.supported: true` MUST apply
these rules.

### 5.1 Read filtering

An entry passes a governed read only if:

1. the effective retrieval handling is not exempt, and
2. at least one effective entry label is matched by some granted read label, and
3. the effective sensitivity class is less than or equal to
   `oamp_sensitivity_max`

Entries that fail MUST NOT appear in:

- `GET /v1/knowledge/{id}`
- `GET /v1/knowledge`
- search responses
- `POST /v1/export`
- v1.1 stream deliveries

### 5.2 Existence hiding

Out-of-scope entries MUST be hidden on agent surfaces.

- `GET /v1/knowledge/{id}` MUST return `404 Not Found`, not `403 Forbidden`,
  for an out-of-scope id
- filtered entries MUST NOT contribute to response totals

### 5.3 Write rejection

`POST /v1/knowledge` MUST be rejected with `403 Forbidden` if:

- the entry's effective labels are outside the write grant, or
- the entry's effective sensitivity class exceeds `oamp_sensitivity_max`, or
- `source.agent_id` conflicts with `oamp_agent_id`

### 5.4 Import rejection

`POST /v1/import` MUST reject entries that exceed the write grant and MUST count
them in the import response `rejected` field.

### 5.5 Export filtering

`POST /v1/export` MUST return only entries readable under the grant, unless
`oamp_export_full` is present and authorized under direct user authentication.

### 5.6 Stream filtering

If a backend supports v1.1 streaming, it MUST:

- omit `knowledge_created` and `knowledge_updated` for out-of-scope entries
- omit `knowledge_deleted` for entries the agent was not allowed to read

---

## 6. Capabilities Additions

v1.3 extends the v1.2 governance capabilities block:

```json
{
  "oamp_version": "1.3.0",
  "capabilities": {
    "governance": {
      "supported": true,
      "sensitivity_classes": ["public", "internal", "confidential", "restricted"],
      "labels_supported": true,
      "extended_provenance_supported": true,
      "withheld_stub_support": false,
      "enforcement": {
        "supported": true,
        "spec_version": "1.3.0",
        "label_hierarchy": "dotted-prefix",
        "reserved_top_level_labels": [
          "identity", "location", "health", "finance",
          "relationships", "work", "preferences",
          "creative", "beliefs", "behaviour"
        ],
        "grant_transport": ["jwt-claims", "oamp-grant-header"],
        "existence_hiding": true,
        "stream_filtering": true,
        "export_full_supported": true
      }
    }
  }
}
```

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `enforcement.supported` | boolean | MUST if `enforcement` present | Backend applies v1.3 enforcement rules |
| `enforcement.spec_version` | string | MUST | Implemented v1.3 spec line |
| `enforcement.label_hierarchy` | string | MUST | `dotted-prefix` for this draft |
| `enforcement.reserved_top_level_labels` | array of string | MUST | Reserved interoperable top-level labels |
| `enforcement.grant_transport` | array of string | MUST | Supported grant transport mechanisms |
| `enforcement.existence_hiding` | boolean | MUST | Whether out-of-scope ids are hidden as 404 |
| `enforcement.stream_filtering` | boolean | MUST | Whether v1.1 streams are filtered |
| `enforcement.export_full_supported` | boolean | MUST | Whether full export claims are honored |

---

## 7. Audit Log Additions

The audit action vocabulary gains:

- `grant_issue`
- `grant_revoke`
- `scope_denied_read`
- `scope_denied_write`

`scope_denied_read` MUST NOT log protected entry content and SHOULD avoid
logging filtered entry ids on agent surfaces.

---

## 8. Compatibility Rules

### 8.1 v1.3 backends

- MUST continue to accept v1.0, v1.1, and v1.2 documents
- MUST preserve v1.2 `governance` and `provenance`
- MUST advertise enforcement support accurately

### 8.2 v1.0-v1.2 clients

- MAY ignore the `governance.enforcement` block if they do not understand it
- MUST NOT infer portable withheld-result semantics from a `1.3.0` version
  string alone

### 8.3 Tokens without grants

On backends that enforce v1.3 for agent surfaces, a token that presents no
usable `oamp_read_labels` MUST be treated as read-nothing.

Deployments MAY still provide separate direct-user authentication paths outside
the portable grant format.

---

## 9. Schema And OpenAPI Artifacts

The v1.3 draft is represented by:

- `spec/v1.3/knowledge-entry.schema.json`
- `spec/v1.3/knowledge-store.schema.json`
- `spec/v1.3/openapi.yaml`

The entry and store schemas remain additive over v1.2. The main v1.3 novelty is
the enforcement-capabilities contract and the normative backend behavior defined
in this draft.
