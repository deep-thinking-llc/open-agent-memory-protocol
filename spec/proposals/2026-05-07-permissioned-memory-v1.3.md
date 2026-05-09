# Proposal: OAMP Permissioned Memory (v1.3 enforcement companion to v1.2 governed metadata)

**Status:** Proposal draft, now superseded by `spec/v1.3/oamp-v1.3-draft.md`
**Target version:** v1.3 (additive over v1.0 / v1.1 / v1.2)
**Date:** 2026-05-07
**Authors:** Deep Thinking LLC
**Repository:** `github.com/deep-thinking-llc/open-agent-memory-protocol`
**Depends on:** `spec/v1/oamp-v1.md`, `spec/v1.1/oamp-v1.1.md`, `spec/v1.2/oamp-v1.2.md`, `spec/v1.2/oamp-v1.2-governed-memory.md`
**Related:** `spec/v2.0/oamp-v2.0-withheld-results-rfc.md`

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

---

## Abstract

OAMP v1.2 introduced standardized **descriptive** governed-memory metadata
(`governance.sensitivity_class`, `governance.labels`, `governance.handling`)
on `KnowledgeEntry`. The v1.2 draft is explicit that `governance` is
descriptive and "is not a portable policy engine"
(`spec/v1.2/oamp-v1.2.md` §3.1).

This proposal targets v1.3 and adds the **enforcement** layer that
operationalises v1.2's descriptive metadata. It defines a portable agent
identity and grant claim format, normative read/write/export/stream filtering
rules, an existence-hiding contract, and audit-log additions. It does not
introduce any new entry-level fields and does not duplicate v1.2 vocabulary;
it tells backends what to do with the v1.2 fields when an agent talks to
them.

The proposal is strictly additive under v1.0 §10.3. v1.0, v1.1, and v1.2
documents and clients remain wire-compatible. Backends that do not implement
enforcement advertise `governance.enforcement.supported: false` and behave
exactly as v1.2 specifies today. This proposal also does not standardise
withheld or redacted result documents; that work is owned by the v2.0 track
(`spec/v2.0/oamp-v2.0-withheld-results-rfc.md`). v1.3 enforcement
specifies **omission**, not redacted stubs.

---

## 1. Motivation

The v1.0 threat model (`docs/security-guide.md` §1) covers eight actor
classes. All of them assume the agent is either the legitimate user's agent
or an unauthorised attacker. v1.2 adds descriptive governance metadata but
is silent on what a backend must do when one of several legitimate agents
asks for a memory whose `governance.sensitivity_class` is too high for that
agent, or whose `governance.labels` are outside that agent's domain.

In practice this leaves a structural gap the moment a user runs more than
one OAMP-compliant agent against the same backend.

- **Cross-agent over-collection.** A coding agent authenticated for user `u`
  can issue `GET /v1/knowledge?user_id=u&query=health` and receive every
  health-related entry the user has ever told a different agent, even when
  those entries carry `governance.sensitivity_class: "confidential"` and
  `governance.labels: ["health"]`. v1.2 stores the labels; nothing in the
  spec requires the backend to act on them.
- **Vendor over-reach.** A general-purpose assistant from vendor X can read
  entries created by a specialised assistant from vendor Y, including
  entries the user told Y precisely because Y was trustworthy and X was
  not.
- **Prompt-injection blast radius.** When a single token grants total read
  access, a successful prompt injection against any agent leaks the entire
  memory store, not the slice that agent legitimately needed.
- **Workforce compartmentalisation.** An employee using six AI tools cannot
  today be given a single backend with per-tool access control. The choice
  is six siloed memory stores (no consistency) or one shared store with no
  compartments (every tool reads every other tool's observations).

Encryption at rest (`docs/security-guide.md` §2) does not solve any of
these. Encryption protects against the database operator. It does nothing
against an agent that holds a valid token. v1.2 governance metadata
describes the policy. v1.3 makes it enforceable.

## 2. Non-goals

- Replacing the v1.0 user-scoping requirement. User-level scoping remains
  MUST. Per-agent enforcement is an additional layer, not a substitute.
- Defining new sensitivity values or new `governance` sub-fields. The v1.2
  enum and the v1.2 `labels` field are reused as-is.
- Defining a new authentication mechanism. JWT and mTLS remain the
  recommended schemes (`spec/v1/openapi.yaml` `securitySchemes`).
- Standardising withheld or redacted result documents. v1.3 enforcement is
  **omission-based**: filtered entries are absent from responses and
  invisible to the caller. The v2.0 track owns any future portable stub
  semantics (`spec/v2.0/oamp-v2.0-withheld-results-rfc.md`).
- Solving inference attacks across labels. The protocol cannot prevent an
  agent that legitimately reads `behaviour` from inferring health-adjacent
  facts; this is documented in §10.

## 3. Design overview

Three additions, all consuming v1.2 fields rather than introducing new ones:

1. **A portable agent grant claim format** that agent tokens carry, defining
   which sensitivity ceiling (using v1.2's `sensitivity_class` enum) and
   which `governance.labels` set the agent is permitted to read and write.
2. **A reserved hierarchical convention** for `governance.labels` values
   used by enforcement matchers, plus a reserved cross-vendor top-level
   vocabulary. v1.2 keeps `labels` free-form for descriptive use. v1.3
   defines the convention used when those labels drive enforcement.
3. **A normative enforcement rule** that backends advertising enforcement
   support MUST apply the grant filter to every read and write, and MUST
   hide the existence of out-of-scope entries.

## 4. Reuse of v1.2 metadata

This proposal adds **no new fields** on `KnowledgeEntry`. It uses the v1.2
fields with the following operational meanings.

### 4.1 `governance.sensitivity_class`

The v1.2 enum `public` < `internal` < `confidential` < `restricted` is
treated as a totally ordered ceiling. An agent token carries
`oamp_sensitivity_max`. Entries whose `sensitivity_class` exceeds the
agent's ceiling are filtered.

When `governance` is absent from an entry, the entry is treated as
`sensitivity_class: "internal"` for enforcement purposes. This default is
deliberately conservative; it fails closer to closed than to open without
breaking v1.0/v1.1 entries that simply have no governance metadata.

### 4.2 `governance.labels`

v1.2 defines `labels` as a free-form array of strings for descriptive use.
v1.3 introduces a hierarchical convention used by enforcement: a label
value is a dotted path of lowercase ASCII segments matching
`^[a-z][a-z0-9]*(\.[a-z][a-z0-9_]*)*$`. Hierarchical prefix matching
applies: a grant for `health` covers `health.condition` and
`health.condition.diagnosis`.

Reserved cross-vendor top-level labels (the interop layer):

| Top-level | Domain |
|-----------|--------|
| `identity` | Name, age, demographic facts |
| `location` | Where the user is, where they live |
| `health` | Medical, mental, fitness |
| `finance` | Income, accounts, transactions, holdings |
| `relationships` | Family, social, romantic |
| `work` | Employer, role, projects, expertise |
| `preferences` | Communication style, format, tone |
| `creative` | Writing, art, music, taste |
| `beliefs` | Political, religious, philosophical |
| `behaviour` | Patterns, habits, schedule |

Vendor-specific extensions live under `x.<vendor>.<...>` and MUST NOT be
required for cross-implementation interop. Labels that do not match the
hierarchical regex are valid descriptive labels under v1.2 but are treated
as opaque atoms for enforcement (no prefix matching). Backends that
advertise enforcement MUST document how they treat opaque labels; the
RECOMMENDED behaviour is exact match only.

When `governance.labels` is absent or empty on an entry, the entry is
treated as label `behaviour` for enforcement purposes. Agents that hold no
`oamp_read_labels` claim do not match `behaviour` either, by the
fail-closed rule in §11.

### 4.3 `governance.handling.retrieval`

v1.2 defines `handling.retrieval` as `governed` or `ungoverned`. This
proposal makes those values load-bearing.

- `retrieval: "governed"` (the default when `governance` is present) means
  the entry MUST be filtered through the calling token's grant.
- `retrieval: "ungoverned"` means the entry is exempt from grant filtering
  on read paths. It MAY still be filtered by the user-scoping rule
  (`spec/v1/oamp-v1.md` §6.4) and by `handling.export` /
  `handling.stream` rules on the corresponding surfaces.

Marking an entry `ungoverned` is the explicit user-authorised escape hatch
for "this is not sensitive, every agent can see it." It SHOULD only be
set on entries whose `sensitivity_class` is `public`. Backends MAY reject
ungoverned-retrieval on entries whose class is higher than `public` and
SHOULD log such combinations for review.

## 5. Agent identity and grant claims

### 5.1 Token claim format

When the bearer token is a JWT, it carries the following additional claims:

```json
{
  "sub": "user-abc",
  "oamp_agent_id": "medical-assistant-v3",
  "oamp_grant_id": "grant-2026-05-07-001",
  "oamp_read_labels":  ["health", "preferences"],
  "oamp_write_labels": ["health", "preferences"],
  "oamp_sensitivity_max": "restricted",
  "exp": 1746662400
}
```

| Claim | Semantics |
|-------|-----------|
| `oamp_agent_id` | Stable identifier for the agent. MUST match `source.agent_id` on writes. |
| `oamp_grant_id` | Stable identifier for this grant, used by the audit log and the revocation list. |
| `oamp_read_labels` | Hierarchical labels the agent may read. Empty array means read-nothing. |
| `oamp_write_labels` | Hierarchical labels the agent may write. SHOULD be a subset of `oamp_read_labels` unless the agent is explicitly write-only (e.g. ingest pipelines). |
| `oamp_sensitivity_max` | Highest `sensitivity_class` (per v1.2 enum) the agent may read or write. One of `public`, `internal`, `confidential`, `restricted`. |

For mTLS deployments the same claims are conveyed via a sidecar grant
object signed by the backend's authorisation key and presented in an
`OAMP-Grant` header. The header value is a compact JWS (RFC 7515) over the
claim object above.

A separate boolean claim `oamp_export_full` (default `false`) authorises
an unfiltered `POST /v1/export` for a principal acting under the user's
direct authentication. It MUST NOT be granted to long-lived agent tokens.

### 5.2 Issuance, refresh, and revocation

Grants are issued by the user's **authorisation point**, which in most
deployments is the backend itself acting on behalf of the user under their
direct authentication (passkey, OIDC, password). The signing key is the
backend's, not the user's. This proposal does not standardise the
issuance UI but does require:

- Grants MUST be revocable independently per `oamp_grant_id`. Revoking
  one grant MUST NOT revoke any other grant for the same agent or user.
- Grant changes MUST take effect on the next request issued under a token
  produced after the change. Backends SHOULD support short token TTLs
  (RECOMMENDED `≤ 1 hour` for agents whose `oamp_sensitivity_max` is
  `confidential` or `restricted`) plus a refresh flow.
- Backends MAY maintain a per-`oamp_grant_id` revocation list to invalidate
  unexpired tokens; if so, the list MUST be checked on every request.
- Backends MUST log grant issuance and revocation in the audit log per
  `docs/security-guide.md` §8 using the new actions defined in §9. The
  `detail` field MUST NOT contain the user's authentication credential.

## 6. Backend enforcement (normative)

A backend that advertises `governance.enforcement.supported: true` MUST:

1. **Filter reads.** For every read endpoint, evaluate each candidate
   entry `e` against the calling token. The entry passes the filter if
   and only if all of the following hold:
   - `e.governance.handling.retrieval` is not `"ungoverned"`, OR the
     entry bypass per §4.3 applies; AND
   - there exists a label in `e.governance.labels` (or the §4.2 default
     if absent) that is hierarchically prefixed by some label in
     `oamp_read_labels`; AND
   - `e.governance.sensitivity_class` is less than or equal to
     `oamp_sensitivity_max` per the §4.1 ordering.

   Entries that fail MUST NOT appear in the response and MUST NOT be
   counted in the response `total`.

2. **Hide existence.** Out-of-scope entries return as if they do not
   exist. `GET /v1/knowledge/{id}` for an out-of-scope id MUST return
   `404 Not Found`, not `403 Forbidden`. This prevents probing for the
   existence of restricted entries. Backends that expose admin or audit
   surfaces under direct user authentication MAY return 403 there;
   agent surfaces MUST NOT.

3. **Filter writes.** Reject `POST /v1/knowledge` with `403 Forbidden`
   if the entry's resolved `governance.labels` set is not a subset
   (under hierarchical matching) of `oamp_write_labels`, or if the
   entry's `governance.sensitivity_class` exceeds `oamp_sensitivity_max`.
   Default label/class assignment per §4.1, §4.2 happens before the
   check.

4. **Filter exports.** `POST /v1/export` returns only entries the
   calling token can read. The `oamp_export_full: true` claim is required
   for an unfiltered export and MUST be granted only under direct user
   authentication, never to a long-lived agent token. Entries with
   `governance.handling.export: "ungoverned"` MAY be returned without
   filtering on export surfaces; entries with `export: "governed"` (the
   default when `governance` is present) MUST be filtered.

5. **Filter streams.** v1.1 subscriptions MUST apply the same filter.
   `knowledge_created` and `knowledge_updated` events for out-of-scope
   entries MUST NOT be delivered. `knowledge_deleted` events for entries
   the agent could not previously read MUST NOT be delivered. Entries
   with `governance.handling.stream: "ungoverned"` are exempt; the
   default when `governance` is present is `governed`.

6. **Reject grant escalation.** A token MUST NOT be able to write or
   import an entry whose `governance.labels` or `sensitivity_class`
   exceeds its own grant. `POST /v1/import` MUST count out-of-scope
   entries in the `rejected` field of the import response
   (`spec/v1/oamp-v1.md` Appendix A.2).

7. **Bind agent identity to provenance.** When an agent writes an entry,
   the backend MUST verify `entry.source.agent_id == oamp_agent_id` and
   reject mismatches with `400 Bad Request`. For entries written with
   v1.2 `provenance.sources[*].agent_id`, the backend SHOULD verify
   each listed `agent_id` against the writing token's grant.

A backend that advertises `governance.enforcement.supported: false` MAY
accept and store v1.2 governance fields but MUST NOT claim filtering.
Mixed-environment clients MUST inspect capabilities before relying on
per-agent compartmentalisation.

## 7. Capabilities advertisement

This proposal extends the v1.2 `capabilities.governance` block with an
`enforcement` sub-block:

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
| `enforcement.supported` | boolean | MUST if `enforcement` present | Backend applies the §6 filter rules |
| `enforcement.spec_version` | string | MUST | Version of this proposal the backend implements |
| `enforcement.label_hierarchy` | string | MUST | `dotted-prefix` for the §4.2 convention; reserved for future schemes |
| `enforcement.reserved_top_level_labels` | array of string | MUST | Top-level labels the backend recognises hierarchically |
| `enforcement.grant_transport` | array of string | MUST | Subset of `["jwt-claims", "oamp-grant-header"]` |
| `enforcement.existence_hiding` | boolean | MUST | Whether out-of-scope ids return 404 (TRUE) or 403 (FALSE). 404 is RECOMMENDED for agent surfaces |
| `enforcement.stream_filtering` | boolean | MUST | Whether v1.1 subscriptions apply the filter |
| `enforcement.export_full_supported` | boolean | MUST | Whether the backend honours `oamp_export_full` claims |

`existence_hiding: false` is permitted for backends that want to surface
"you have N entries you cannot read" to UI clients running under direct
user authentication, but MUST NOT be used on agent surfaces because it
leaks per-label counts.

## 8. Worked example (non-normative)

A user `u-42` has three knowledge entries on a v1.3 backend:

```json
[
  { "id": "e1", "category": "fact", "content": "...",
    "governance": {
      "sensitivity_class": "restricted",
      "labels": ["health.condition"],
      "handling": { "retrieval": "governed" }
    } },
  { "id": "e2", "category": "preference", "content": "...",
    "governance": {
      "sensitivity_class": "internal",
      "labels": ["preferences"],
      "handling": { "retrieval": "governed" }
    } },
  { "id": "e3", "category": "pattern", "content": "...",
    "governance": {
      "sensitivity_class": "internal",
      "labels": ["work.code"],
      "handling": { "retrieval": "governed" }
    } }
]
```

Two agents are registered for `u-42`:

| Agent | `oamp_read_labels` | `oamp_sensitivity_max` |
|-------|--------------------|------------------------|
| `medical-assistant-v3` | `["health", "preferences"]` | `restricted` |
| `coding-assistant-v9`  | `["work", "preferences"]`   | `internal`   |

Both call `GET /v1/knowledge?user_id=u-42`.

`medical-assistant-v3` receives:

```json
{ "entries": [e1, e2], "total": 2, "limit": 50, "offset": 0 }
```

`coding-assistant-v9` receives:

```json
{ "entries": [e2, e3], "total": 2, "limit": 50, "offset": 0 }
```

Each agent's `total` reflects only its scoped view. Neither agent can
infer the existence of the other's entries from the response.
`GET /v1/knowledge/e1` from `coding-assistant-v9` returns
`404 Not Found`, not `403 Forbidden`.

If `coding-assistant-v9` attempts `POST /v1/knowledge` with
`governance.labels: ["health.condition"]`, the backend rejects with
`403 Forbidden` and audit-logs `scope_denied_write`.

## 9. Audit logging additions

Extend `audit_log.action` enum (per `docs/security-guide.md` §5) with:

| Action | Triggered by | `detail` field |
|--------|--------------|----------------|
| `grant_issue` | New grant issued | `oamp_grant_id`, `oamp_agent_id`, label set, sensitivity max, TTL |
| `grant_revoke` | Grant revoked | `oamp_grant_id`, `oamp_agent_id` |
| `scope_denied_read` | Read filtered out by enforcement | `oamp_agent_id`, `oamp_grant_id`, requested label set; aggregated, never per-entry |
| `scope_denied_write` | Write rejected by enforcement | `oamp_agent_id`, `oamp_grant_id`, attempted label set, attempted `sensitivity_class` |

The `scope_denied_read` action MUST NOT include the entry id of the
filtered entry. It records only the agent id, grant id, requested label
set, and timestamp, because logging the filtered entry id would leak
existence to anyone with log access (`spec/v1/oamp-v1.md` §8.1.3 — no
content in logs).

## 10. Threat model deltas

What this proposal closes:

- **Cross-agent over-collection.** Filtering happens at the storage layer,
  not the prompt layer. A clever prompt cannot retrieve out-of-scope
  entries because the agent's bearer token does not authorise them.
- **Vendor over-reach via shared backend.** Each vendor's agent gets only
  its granted slice.
- **Prompt-injection blast radius.** A compromised agent leaks at most
  its own grant.
- **Mis-attributed writes.** §6 rule 7 binds `source.agent_id` to the
  writing token's `oamp_agent_id`, preventing one agent from
  masquerading as another via the source field.

What it does not close:

- **Trusted-agent betrayal.** A scoped agent that legitimately reads
  `health` and then exfiltrates that data outside the protocol.
  Enforcement shrinks the radius; it does not eliminate trust in the
  agents the user has chosen. Pair with audit logging and outbound
  monitoring.
- **Inference attacks across labels.** An agent with `preferences` and
  `behaviour` may infer health-adjacent facts. The protocol cannot
  prevent inference. Users should be aware that low-sensitivity labels
  can leak signal about higher ones.
- **Authorisation-point compromise.** If the backend's grant-signing
  key leaks, all grants are forgeable. Treat that key with the same
  handling as the encryption key (`docs/security-guide.md` §3).
- **Withheld-stub leakage.** v1.3 enforcement omits filtered entries.
  Backends that wish to return explicit withheld stubs (cf.
  `spec/v2.0/oamp-v2.0-withheld-results-rfc.md`) MUST wait for the
  v2.0 envelope; emitting non-standard withheld stubs in v1.3 responses
  is out of scope and would conflict with `withheld_stub_support: false`
  in the v1.2 capability advertisement.

## 11. Backwards compatibility

- A v1.0/v1.1/v1.2 entry without `governance` is treated as
  `sensitivity_class: "internal"` and label `behaviour` for enforcement
  per §4.1, §4.2. v1.0/v1.1/v1.2 agents and backends that do not enforce
  ignore the absence and continue to work.
- Tokens without `oamp_read_labels` are treated as **fully scoped**
  (current v1.0/v1.1/v1.2 behaviour) on backends with
  `governance.enforcement.supported: false`, and as **read-nothing** on
  backends with `governance.enforcement.supported: true`. This
  deliberately fails closed: a pre-v1.3 token used against an enforcement
  backend gets nothing until upgraded, rather than silently inheriting
  full access.
- Capabilities discovery (v1.1 §2, extended by v1.2 §4 and this
  proposal §7) lets clients detect this transition before issuing reads.

## 12. Conformance summary

A v1.3-conformant backend that advertises
`governance.enforcement.supported: true` MUST:

- Continue to satisfy every v1.0, v1.1, and v1.2 requirement.
- Apply the read filter described in §6 rule 1 to every read endpoint,
  including list, get, search, export, and v1.1 streaming.
- Hide existence per §6 rule 2 (404 not 403 for out-of-scope ids on agent
  surfaces).
- Apply the write filter described in §6 rule 3 to `POST /v1/knowledge`.
- Reject import entries that exceed grant per §6 rule 6.
- Bind `source.agent_id` to the writing token's `oamp_agent_id` per §6
  rule 7.
- Treat tokens without `oamp_read_labels` as read-nothing.
- Emit the four new audit log actions described in §9.
- Advertise the `governance.enforcement` block per §7.

A v1.3-conformant backend that advertises
`governance.enforcement.supported: false` MUST:

- Continue to satisfy every v1.0, v1.1, and v1.2 requirement.
- Preserve `governance` and `provenance` on read and import per v1.2.
- NOT claim filtering. Clients depending on filtering MUST detect this
  via capabilities and refuse to share the backend across multiple
  agents.

## 13. Open questions

- **Hierarchical label semantics for negation.** Should `health.public`
  exist as an explicit "publishable health" label, or should
  `sensitivity_class` carry the publishability axis alone? The current
  draft uses `sensitivity_class` for publishability and `labels` for
  subject domain, which is cleaner but means the user cannot grant "all
  my health, but only the public bits" without per-entry sensitivity
  overrides.
- **Grant introspection.** Should agents be able to call
  `GET /v1/grants/self` to discover what they can read? Convenient for
  clients, but reveals the grant shape to a compromised agent.
- **Cross-backend label vocabulary governance.** v1.3 reserves a list.
  Beyond v1.3, additions to the reserved list need a process. Likely an
  IANA-style registry or a `RESERVED_LABELS.md` in this repo with a
  PR-and-vote rule.
- **Migration path.** When a backend turns on enforcement, every
  existing entry that lacks `governance` is treated as `internal` +
  `behaviour`. Bulk re-classify by category default, or require an
  explicit migration run that prompts the user to label legacy entries?
  The latter is more user-respecting; the former ships sooner.
- **Interaction with v2.0 withheld results.** When v2.0 lands, the v1.3
  omission rule will need a clear interop story with v2.0 stubs:
  presumably enforcement backends advertise both
  `governance.withheld_stub_support: true` (v2.0 capability) and
  `governance.enforcement.existence_hiding: true` (v1.3 capability),
  and clients pick behaviour based on whether they understand v2.0
  envelopes.

## 14. Implementation checklist

For backends adopting this proposal:

- [ ] Implement grant claim parsing for JWT and the `OAMP-Grant` header
- [ ] Add hierarchical label matching with the §4.2 convention
- [ ] Apply the read filter to all read paths, including `total` count
- [ ] Apply the filter to `POST /v1/export`, `POST /v1/import`, and v1.1
      streaming
- [ ] Implement the §4.3 `handling.retrieval` semantics including the
      `ungoverned` exemption
- [ ] Bind `source.agent_id` to the token per §6 rule 7
- [ ] Add the four new audit log actions per §9
- [ ] Advertise the `governance.enforcement` block per §7
- [ ] Decide existence-hiding policy and document it in deployment docs
- [ ] Define the grant lifecycle UX (issuance, revocation, TTL,
      `oamp_grant_id` allocation)
- [ ] Add cross-implementation conformance fixtures under
      `validators/test-fixtures/` covering filter, write rejection,
      404 existence-hiding, and import rejection counts

## References

- OAMP v1.0 Spec §8 (Privacy and Security Requirements), §10.3 (Field Evolution)
- OAMP v1.1 Draft §2 (Capabilities Discovery)
- OAMP v1.2 Draft §3 (`KnowledgeEntry` Additions: governance, provenance), §4 (Capabilities Additions)
- OAMP v1.2 Governed Memory Draft (kizuna-mem motivation, scope split)
- OAMP v2.0 Withheld Results RFC seed
- `docs/security-guide.md` §1 (Threat Model), §5 (No Content in Logs), §8 (Audit Logging), §12 (AI-Specific Threat Vectors)
- RFC 7519 (JSON Web Tokens)
- RFC 7515 (JSON Web Signature)
- RFC 8414 (OAuth 2.0 Authorization Server Metadata)
