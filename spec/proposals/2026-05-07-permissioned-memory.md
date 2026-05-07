# Proposal: OAMP Permissioned Memory (Per-Entry Sensitivity and Scope)

**Status:** Draft proposal for community review
**Target version:** v1.2 (additive over v1.0/v1.1)
**Date:** 2026-05-07
**Authors:** Deep Thinking LLC
**Repository:** `github.com/deep-thinking-llc/open-agent-memory-protocol`

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

---

## Abstract

OAMP v1.0 enforces user-level access control: an authenticated principal can
read any knowledge entry belonging to its `user_id`. This proposal adds
**per-entry permissioning** so that multiple agents serving the same user can
hold differently scoped views of that user's memory. A medical agent can read
health entries that a general-purpose chat agent cannot see at all, even though
both are authenticated for the same user.

The proposal is strictly additive under the v1.0 §10.3 minor-version evolution
rules. v1.0 and v1.1 documents and clients remain wire-compatible. Backends
that do not implement permissioning advertise `permissioning.supported: false`
via the v1.1 capabilities endpoint and behave exactly as today.

---

## 1. Motivation

The v1.0 threat model (`docs/security-guide.md` §1) covers eight actor
classes. All of them assume the agent is either the legitimate user's agent or
an unauthorised attacker. None of them addresses a class of threat that
becomes structural the moment a user runs more than one OAMP-compliant agent
against the same backend.

- **Cross-agent over-collection.** A coding agent authenticated for user `u`
  can issue `GET /v1/knowledge?user_id=u&query=health` and receive every
  health-related entry the user has ever told a different agent. The protocol
  does not prevent this; the security guide does not flag it.
- **Vendor over-reach.** A general-purpose assistant from vendor X can read
  entries created by a specialised assistant from vendor Y, including entries
  the user told Y precisely because Y was trustworthy and X was not.
- **Prompt-injection blast radius.** When a single token grants total read
  access, a successful prompt injection against any agent leaks the entire
  memory store, not the slice that agent legitimately needed.
- **Workforce compartmentalisation.** An employee using six AI tools cannot
  today be given a single backend with per-tool access control. The choice is
  six siloed memory stores (no consistency) or one shared store with no
  compartments (every tool reads every other tool's observations).

Encryption at rest does not solve any of these. Encryption protects against
the database operator. It does nothing against an agent that holds a valid
token.

## 2. Non-goals

- Replacing the v1.0 user-scoping requirement. User-level scoping remains
  MUST. Permissioning is an additional layer, not a substitute.
- Defining a new authentication mechanism. JWT and mTLS remain the
  recommended schemes (`spec/v1/openapi.yaml` `securitySchemes`).
- Requiring all backends to support permissioning. It is OPTIONAL and
  capability-advertised.
- Specifying a UI for grant management. That is implementation territory.
- Solving inference attacks across scopes. The protocol cannot prevent an
  agent that legitimately reads `behaviour` from inferring health-adjacent
  facts; this is documented in §10.

## 3. Design overview

Three additions:

1. **Two OPTIONAL fields on `KnowledgeEntry`**: `sensitivity` (closed enum)
   and `scope` (string array drawn from a reserved vocabulary).
2. **A scope-grant claim format** that agent tokens carry, defining which
   sensitivity ceiling and which scope set the agent is permitted to read and
   write.
3. **A normative enforcement rule** that backends advertising permissioning
   support MUST apply the grant filter to every read and write, and MUST hide
   the existence of out-of-scope entries.

## 4. Schema additions

These fields conform to v1.0 §10.3 ("New OPTIONAL fields MAY be added in
minor versions").

### 4.1 `KnowledgeEntry.sensitivity` (OPTIONAL)

```json
"sensitivity": "personal"
```

| Value | Intended audience |
|-------|-------------------|
| `public` | Any agent with any grant for this user |
| `personal` | Default. Agents the user uses routinely. |
| `sensitive` | Agents the user has explicitly trusted with sensitive data |
| `restricted` | Domain-specialist agents only (e.g. medical, legal, financial) |

Sensitivity values are totally ordered: `public < personal < sensitive <
restricted`. Backends that do not implement permissioning MUST preserve the
field on read and import but MAY ignore it for filtering. Default when absent:
`personal`.

### 4.2 `KnowledgeEntry.scope` (OPTIONAL)

```json
"scope": ["health.condition", "health.medication"]
```

A scope is a dotted path drawn from a reserved top-level vocabulary. Values
are case-sensitive lowercase ASCII matching the regex
`^[a-z][a-z0-9]*(\.[a-z][a-z0-9_]*)*$`. Scopes are hierarchical: a grant for
`health` covers `health.condition` and `health.condition.diagnosis`. Multiple
scopes on a single entry are interpreted as union (the entry is in-scope for
any agent whose grant covers any listed scope).

Reserved top-level scopes (the cross-vendor interop layer):

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
required for cross-implementation interop. Default when absent:
`["preferences"]` for `category: preference`, otherwise `["behaviour"]`.

### 4.3 Schema impact

Both fields are additive, OPTIONAL in JSON Schema, and ignored by v1.0
validators. They appear on `KnowledgeEntry` and (for `sensitivity` only) on
`UserModel.communication`, `UserModel.expertise[*]`,
`UserModel.corrections[*]`, and `UserModel.stated_preferences[*]`. Both fields
are filter metadata and remain plaintext per the column-encryption strategy in
`docs/security-guide.md` §2; encrypting them would prevent backend-side
filtering without per-row decryption.

## 5. Agent identity and scope grants

### 5.1 Token claim format (normative for JWT, sidecar for mTLS)

When the bearer token is a JWT, it carries four additional claims:

```json
{
  "sub": "user-abc",
  "oamp_agent_id": "medical-assistant-v3",
  "oamp_read_scopes":  ["health", "preferences"],
  "oamp_write_scopes": ["health", "preferences"],
  "oamp_sensitivity_max": "restricted",
  "exp": 1746662400
}
```

| Claim | Semantics |
|-------|-----------|
| `oamp_agent_id` | Stable identifier for the agent. MUST match `source.agent_id` on writes. |
| `oamp_read_scopes` | Hierarchical scopes the agent may read. Empty array means read-nothing. |
| `oamp_write_scopes` | Hierarchical scopes the agent may write. SHOULD be a subset of `oamp_read_scopes` unless the agent is explicitly write-only (e.g. ingest pipelines). |
| `oamp_sensitivity_max` | Highest sensitivity tier the agent may read or write. One of `public`, `personal`, `sensitive`, `restricted`. |

For mTLS deployments the same claims are conveyed via a sidecar grant object
signed by the backend's authorisation key and presented in an `OAMP-Grant`
header. The header value is a compact JWS over the claim object above, with
the same semantics.

### 5.2 Issuance, refresh, and revocation

Grants are issued by the user's **authorisation point**, which in most
deployments is the backend itself acting on behalf of the user under their
direct authentication (passkey, OIDC, password). The signing key is the
backend's, not the user's. This proposal does not standardise the issuance UI
but does require:

- Grants MUST be revocable independently. Revoking `health` from one agent
  MUST NOT revoke any other agent's grant.
- Grant changes MUST take effect on the next request issued under a token
  produced after the change. Backends SHOULD support short token TTLs
  (RECOMMENDED `≤ 1 hour` for agents that read `sensitive` or `restricted`
  entries) plus a refresh flow.
- Backends MAY maintain a per-`oamp_agent_id` revocation list to invalidate
  unexpired tokens; if so, the list MUST be checked on every request.
- Backends MUST log grant issuance and revocation in the audit log per
  `docs/security-guide.md` §8 using the new actions defined in §9. The
  `detail` field MUST NOT contain the user's authentication credential.

## 6. Backend enforcement (normative)

A backend that advertises `permissioning.supported: true` MUST:

1. **Filter reads.** For every read endpoint, intersect each candidate
   entry's `scope` with the token's `oamp_read_scopes` (hierarchically) AND
   ensure entry `sensitivity ≤ oamp_sensitivity_max`. Entries that fail
   either check MUST NOT appear in the response and MUST NOT be counted in
   `total`.
2. **Hide existence.** Out-of-scope entries return as if they do not exist.
   The backend MUST NOT return 403 for an out-of-scope entry id; it MUST
   return 404. This prevents probing for the existence of restricted entries.
3. **Filter writes.** Reject `POST /v1/knowledge` with 403 if the entry's
   resolved scope set is not a subset of `oamp_write_scopes`, or if
   `sensitivity > oamp_sensitivity_max`. Default scope/sensitivity assignment
   (per §4.1, §4.2) happens before the check.
4. **Filter exports.** `POST /v1/export` returns only entries the calling
   token can read. A separate `oamp_export_full` claim (boolean) is required
   for an unfiltered export, and MUST be granted only to a principal acting
   under the user's direct authentication, never to a long-lived agent token.
5. **Filter streams.** v1.1 subscriptions MUST apply the same filter.
   `knowledge_created` events for out-of-scope entries MUST NOT be delivered.
   `knowledge_deleted` events for entries the agent could not previously read
   MUST NOT be delivered.
6. **Reject grant escalation.** A token MUST NOT be able to write an entry
   whose scope or sensitivity exceeds its own grant, even via `POST /v1/import`.
   Imported entries with out-of-scope `scope` or `sensitivity` MUST be
   rejected and counted in the `rejected` field of the import response.

A backend that advertises `permissioning.supported: false` MAY accept and
store the new fields but MUST NOT claim filtering. Mixed-environment clients
MUST inspect capabilities before relying on per-entry compartmentalisation.

## 7. Capabilities advertisement

Extend the v1.1 `/v1/capabilities` response with a `permissioning` block:

```json
{
  "oamp_version": "1.2.0",
  "capabilities": {
    "permissioning": {
      "supported": true,
      "scope_vocabulary_version": "1.0",
      "reserved_scopes": ["identity", "location", "health", "finance",
                          "relationships", "work", "preferences",
                          "creative", "beliefs", "behaviour"],
      "sensitivity_levels": ["public", "personal", "sensitive", "restricted"],
      "grant_transport": ["jwt-claims", "oamp-grant-header"],
      "existence_hiding": true,
      "stream_filtering": true
    }
  }
}
```

`existence_hiding: false` is permitted for backends that want to surface
"you have N entries you cannot read" to UI clients running under direct user
authentication, but is NOT RECOMMENDED for production agent traffic because
it leaks per-scope counts.

## 8. Worked example (non-normative)

A user `u-42` has three knowledge entries:

```json
[
  { "id": "e1", "category": "fact",       "content": "...",
    "scope": ["health.condition"], "sensitivity": "restricted" },
  { "id": "e2", "category": "preference", "content": "...",
    "scope": ["preferences"],      "sensitivity": "personal" },
  { "id": "e3", "category": "pattern",    "content": "...",
    "scope": ["work.code"],        "sensitivity": "personal" }
]
```

Two agents are registered:

| Agent | `oamp_read_scopes` | `oamp_sensitivity_max` |
|-------|--------------------|------------------------|
| `medical-assistant-v3` | `["health", "preferences"]` | `restricted` |
| `coding-assistant-v9`  | `["work", "preferences"]`   | `personal`   |

Both agents call `GET /v1/knowledge?user_id=u-42`.

`medical-assistant-v3` receives:

```json
{ "entries": [e1, e2], "total": 2, "limit": 50, "offset": 0 }
```

`coding-assistant-v9` receives:

```json
{ "entries": [e2, e3], "total": 2, "limit": 50, "offset": 0 }
```

Each agent's `total` reflects only its scoped view. Neither agent can infer
the existence of the other's entries from the response. A `GET
/v1/knowledge/e1` from `coding-assistant-v9` returns `404 Not Found`, not
`403 Forbidden`.

If `coding-assistant-v9` attempts `POST /v1/knowledge` with
`scope: ["health.condition"]`, the backend rejects with `403 Forbidden` and
audit-logs `scope_denied_write`.

## 9. Audit logging additions

Extend `audit_log.action` enum (per `docs/security-guide.md` §5) with:

| Action | Triggered by | `detail` field |
|--------|--------------|----------------|
| `grant_issue` | New scope grant issued | Agent id, scope set, sensitivity max, TTL |
| `grant_revoke` | Scope grant revoked | Agent id, revoked scopes |
| `scope_denied_read` | Read filtered out by scope | Agent id, requested scope set; aggregated, never per-entry |
| `scope_denied_write` | Write rejected by scope | Agent id, attempted scope set, attempted sensitivity |

The `scope_denied_read` action MUST NOT include the entry id of the filtered
entry. It records only the agent id, requested scope set, and timestamp,
because logging the filtered entry id would leak existence to anyone with log
access (cf. spec §8.1.3 — no content in logs).

## 10. Threat model deltas

What this proposal closes:

- **Cross-agent over-collection.** Filtering happens at the storage layer,
  not the prompt layer. A clever prompt cannot retrieve out-of-scope entries
  because the agent's bearer token does not authorise them.
- **Vendor over-reach via shared backend.** Each vendor's agent gets only its
  granted slice.
- **Prompt-injection blast radius.** A compromised agent leaks at most its
  own scope.

What it does not close:

- **Trusted-agent betrayal.** A scoped agent that legitimately reads `health`
  and then exfiltrates that data outside the protocol. Permissioning shrinks
  the radius; it does not eliminate trust in the agents the user has chosen.
  Pair with audit logging and outbound monitoring.
- **Inference attacks across scopes.** An agent with `preferences` and
  `behaviour` may infer health-adjacent facts. The protocol cannot prevent
  inference. Users should be aware that low-sensitivity scopes can leak
  signal about higher ones.
- **Authorisation-point compromise.** If the backend's grant-signing key
  leaks, all grants are forgeable. Treat that key with the same handling as
  the encryption key (`docs/security-guide.md` §3).

## 11. Backwards compatibility

- A v1.0/v1.1 entry without `sensitivity` or `scope` is treated as
  `personal` plus the category-default scope from §4.2. v1.0 agents and
  backends ignore the new fields and continue to work.
- Tokens without the `oamp_read_scopes` claim are treated as **fully scoped**
  (current v1.0 behaviour) on backends with `permissioning.supported: false`,
  and as **read-nothing** on backends with `permissioning.supported: true`.
  This deliberately fails closed: a v1.0 token used against a permissioning
  backend gets nothing until upgraded, rather than silently inheriting full
  access.
- Capabilities discovery (v1.1 §2) lets clients detect this transition before
  issuing reads.

## 12. Conformance summary

A v1.2-conformant backend that advertises `permissioning.supported: true`
MUST:

- Accept and persist the `sensitivity` and `scope` fields on `KnowledgeEntry`.
- Apply the read filter described in §6.1 to every read endpoint, including
  list, get, search, export, and v1.1 streaming.
- Hide existence per §6.2 (404 not 403 for out-of-scope ids).
- Apply the write filter described in §6.3 to `POST /v1/knowledge`.
- Reject import entries that exceed grant per §6.6.
- Treat tokens without `oamp_read_scopes` as read-nothing.
- Emit the four new audit log actions described in §9.
- Advertise the `permissioning` block in `/v1/capabilities` per §7.

A v1.2-conformant backend that advertises `permissioning.supported: false`
MUST:

- Continue to satisfy every v1.0 and v1.1 requirement.
- Preserve `sensitivity` and `scope` fields on read and import.
- NOT claim filtering. Clients depending on filtering MUST detect this via
  capabilities and refuse to share the backend across multiple agents.

## 13. Open questions

- **Hierarchical scope semantics for negation.** Should `health.public` exist
  as an explicit "publishable health" scope, or should sensitivity carry the
  publishability axis alone? The current draft uses sensitivity for
  publishability and scope for subject domain, which is cleaner but means
  the user cannot grant "all my health, but only the public bits" without
  per-entry sensitivity overrides.
- **Grant introspection.** Should agents be able to call `GET /v1/grants/self`
  to discover what they can read? Convenient for clients, but reveals the
  grant shape to a compromised agent.
- **Cross-backend scope vocabulary governance.** v1.2 reserves a list. Beyond
  v1.2, additions to the reserved list need a process. Likely an
  IANA-style registry or a `RESERVED_SCOPES.md` in this repo with a
  PR-and-vote rule.
- **Migration path.** When a backend turns on permissioning, every existing
  entry has no scope. Bulk-classify by category default, or require an
  explicit migration run that prompts the user to label legacy entries? The
  latter is more user-respecting; the former ships sooner.
- **Interaction with v2.0 roadmap items** (work patterns, session outcomes,
  skill metrics). Those will need scopes assigned at the moment they're added
  to the spec. Probably `behaviour`, `behaviour`, and `work` respectively.

## 14. Implementation checklist

For backends adopting this proposal:

- [ ] Add `sensitivity` and `scope` fields to JSON schemas (additive)
- [ ] Add equivalent fields to protobuf definitions under `proto/oamp/v1/`
- [ ] Implement grant claim parsing for JWT and the `OAMP-Grant` header
- [ ] Add scope/sensitivity filter to all read paths, including the `total`
      count
- [ ] Apply filter to `POST /v1/export`, `POST /v1/import`, and v1.1
      streaming
- [ ] Add the four new audit log actions per §9
- [ ] Advertise the `permissioning` block in `/v1/capabilities`
- [ ] Decide existence-hiding policy and document it in deployment docs
- [ ] Define the grant lifecycle UX (issuance, revocation, TTL)
- [ ] Add cross-implementation conformance fixtures under
      `validators/test-fixtures/`

## References

- OAMP v1.0 Spec §8 (Privacy and Security Requirements)
- OAMP v1.0 Spec §10.3 (Field Evolution)
- OAMP v1.1 Draft §2 (Capabilities Discovery)
- `docs/security-guide.md` §1 (Threat Model), §5 (No Content in Logs), §8
  (Audit Logging), §12 (AI-Specific Threat Vectors)
- RFC 7519 (JSON Web Tokens)
- RFC 7515 (JSON Web Signature)
- RFC 8414 (OAuth 2.0 Authorization Server Metadata)
