# Open Agent Memory Protocol -- Version 1.0.0

**Status:** Draft
**Date:** 2026-04-06
**Authors:** Deep Thinking
**Repository:** `github.com/deep-thinking-llc/open-agent-memory-protocol`

---

## Abstract

The Open Agent Memory Protocol (OAMP) defines a standard format for storing,
exchanging, and querying memory data between AI agents and memory backends. It
enables portability (users can export memory from one agent and import it into
another), backend interoperability (any OAMP-compliant backend works with any
OAMP-compliant agent), and privacy by default (encryption at rest, user data
ownership, and provenance tracking are mandatory).

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

---

## 1. Introduction and Motivation

AI agents increasingly maintain persistent memory about users: their preferences,
expertise, corrections, and behavioral patterns. Without a common interchange
format, this memory is locked to a single agent or backend, creating vendor
lock-in and preventing users from owning their own data.

OAMP addresses this by defining:

- A **JSON Schema** for the structure of agent memory documents
- A **REST API contract** for memory backends
- **Privacy requirements** that compliant implementations must meet
- **Reference implementations** in Rust and TypeScript

### 1.1 What OAMP Is

- A JSON schema defining the structure of agent memory documents
- A REST API contract for memory backends
- Reference implementations in Rust and TypeScript
- Privacy and security requirements that compliant implementations must meet

### 1.2 What OAMP Is Not

- A database or storage engine
- An agent framework
- A specific AI model or embedding format
- A transport protocol (OAMP uses HTTP/JSON, with optional protobuf)

### 1.3 Design Principles

- **Portability first.** Memory exported from one agent MUST be importable by any
  other compliant agent without transformation.
- **Privacy by default.** Encryption and provenance are not optional add-ons;
  they are normative requirements.
- **Adoption over completeness.** JSON over protobuf as the primary format.
  Optional fields over mandatory complexity. Underspecify search to allow
  backend choice.
- **Two-sided protocol.** OAMP serves both agent frameworks (producers/consumers)
  and memory backends (storage/retrieval). Both sides have normative requirements.

---

## 2. Terminology

- **Agent** -- a software system that interacts with users and maintains memory
  about them.
- **Backend** -- a storage service that persists OAMP documents and exposes the
  REST API defined in Section 6.
- **Knowledge Entry** -- a discrete piece of information an agent has learned
  about a user, represented as an OAMP document with `type: "knowledge_entry"`.
- **Knowledge Store** -- a collection of Knowledge Entries packaged for bulk
  export or import, represented as an OAMP document with
  `type: "knowledge_store"`.
- **User Model** -- an agent's evolving structured understanding of a user,
  represented as an OAMP document with `type: "user_model"`.
- **Confidence** -- a floating-point number in [0.0, 1.0] representing the
  agent's certainty in a piece of knowledge. 0.0 means no confidence; 1.0 means
  certain.
- **Provenance** -- the record of when and how a piece of knowledge was acquired
  (session, agent, timestamp).
- **Decay** -- the reduction of confidence over time as knowledge becomes stale.

---

## 3. Knowledge Entry

A Knowledge Entry represents a discrete piece of information an agent has learned
about a user.

### 3.1 Document Structure

```json
{
  "oamp_version": "1.0.0",
  "type": "knowledge_entry",
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "user_id": "user-123",
  "category": "preference",
  "content": "User prefers Rust over Python for systems programming",
  "confidence": 0.85,
  "source": {
    "session_id": "sess-2026-04-01-001",
    "agent_id": "my-agent-v1",
    "timestamp": "2026-04-01T14:30:00Z"
  },
  "decay": {
    "half_life_days": 70.0,
    "last_confirmed": "2026-04-01T14:30:00Z"
  },
  "tags": ["language", "preference"],
  "metadata": {}
}
```

### 3.2 Field Definitions

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `oamp_version` | string | MUST | Spec version as semver. For this version: `"1.0.0"`. |
| `type` | string | MUST | MUST be `"knowledge_entry"`. |
| `id` | string | MUST | UUID v4 unique identifier. MUST be globally unique. |
| `user_id` | string | MUST | Identifier of the user this knowledge belongs to. |
| `category` | string | MUST | One of: `"fact"`, `"preference"`, `"pattern"`, `"correction"`. See 3.4. |
| `content` | string | MUST | The knowledge itself in natural language. MUST NOT be empty. |
| `confidence` | number | MUST | Float in [0.0, 1.0]. See 3.5. |
| `source` | object | MUST | Provenance information. See 3.3. |
| `decay` | object | MAY | Temporal decay parameters. See 3.6. |
| `tags` | array of string | MAY | Free-form tags for filtering and grouping. |
| `metadata` | object | MAY | Vendor-specific extensions. Compliant implementations MUST NOT reject documents with unknown metadata fields. |

### 3.3 Source Object

The `source` object records the provenance of a Knowledge Entry.
Implementations MUST NOT create Knowledge Entries without a `source`.

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `session_id` | string | MUST | Identifier of the session where this was learned. |
| `timestamp` | string | MUST | ISO 8601 datetime when this was learned. |
| `agent_id` | string | MAY | Identifier of the agent that produced this knowledge. |

### 3.4 Category Definitions

The `category` field classifies the kind of knowledge. Compliant implementations
MUST use one of the four defined values and MUST NOT define additional categories
in v1.0 (use `tags` or `metadata` for vendor extensions).

- **`fact`** -- Objective information about the user's environment or context.
  Facts are not evaluative. Examples: "User works at Acme Corp", "Project uses
  PostgreSQL 15", "User is located in Berlin".

- **`preference`** -- A stated or inferred user preference about how the agent
  should behave or respond. Examples: "Prefers concise answers", "Likes dark
  mode", "Prefers Rust over Python".

- **`pattern`** -- A recurring behavioral pattern the agent has observed.
  Patterns are inferred from multiple observations, not a single event.
  Examples: "Deploys to staging before production", "Reviews PRs in the morning",
  "Asks for code review before merging".

- **`correction`** -- The user corrected the agent's behavior. This category
  is first-class data, not a side effect. Corrections are a primary learning
  signal. Examples: "Don't use `unwrap()`, use proper error handling",
  "Don't repeat context I already provided".

### 3.5 Confidence

The `confidence` field is a float in [0.0, 1.0]:

- `0.0` -- no confidence; this knowledge may be wrong
- `0.5` -- uncertain; roughly equal probability of being correct or incorrect
- `1.0` -- certain; the agent has strong evidence this is correct

Agents SHOULD calibrate confidence scores based on evidence. Stated facts from
users SHOULD have higher initial confidence than inferred patterns.

Corrections from users SHOULD be assigned confidence >= 0.9, as they represent
explicit user intent.

### 3.6 Confidence Decay

Knowledge becomes stale over time. Implementations SHOULD apply temporal decay:

```
confidence_t = confidence_0 * e^(-ln(2) / half_life_days * age_days)
```

Where:
- `confidence_0` is the confidence at the time of the last confirmation
- `half_life_days` is `decay.half_life_days`
- `age_days` is the number of days since `decay.last_confirmed`
  (or `source.timestamp` if `last_confirmed` is absent)

If `decay` is absent or `half_life_days` is `null`, no decay is applied.

Recommended default half-lives by category:
- `fact`: 365 days (facts change infrequently)
- `preference`: 70 days (preferences evolve)
- `pattern`: 90 days (patterns may shift with role/context changes)
- `correction`: no decay (corrections are persistent unless superseded)

---

## 4. Knowledge Store

A Knowledge Store is a collection document for bulk export and import. It allows
a complete memory snapshot to be moved between agents or backends.

### 4.1 Document Structure

```json
{
  "oamp_version": "1.0.0",
  "type": "knowledge_store",
  "user_id": "user-123",
  "entries": [...],
  "exported_at": "2026-04-06T10:00:00Z",
  "agent_id": "my-agent-v1"
}
```

### 4.2 Field Definitions

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `oamp_version` | string | MUST | Spec version. |
| `type` | string | MUST | MUST be `"knowledge_store"`. |
| `user_id` | string | MUST | User all entries belong to. |
| `entries` | array | MUST | Array of Knowledge Entry objects. MAY be empty. |
| `exported_at` | string | MUST | ISO 8601 timestamp of export. |
| `agent_id` | string | MAY | Exporting agent identifier. |

### 4.3 Entry Inheritance

Each entry in `entries` MUST be a valid Knowledge Entry object. Entries within
a Knowledge Store MAY omit `oamp_version` (they inherit from the store); however,
compliant importers MUST accept entries with or without `oamp_version`.

### 4.4 Merge Semantics

When importing a Knowledge Store into an existing backend:

- Entries with IDs that do not exist MUST be inserted.
- Entries with IDs that already exist: the spec RECOMMENDS confidence-based
  resolution (higher confidence wins). Implementations MAY define other merge
  strategies but MUST document them.
- Implementations MUST NOT silently discard entries; any rejected entries SHOULD
  be reported in the import response.

---

## 5. User Model

The User Model represents an agent's evolving structured understanding of a user.
All sections beyond the envelope are independently optional -- an agent that only
tracks expertise MAY omit communication and corrections.

### 5.1 Envelope Fields

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `oamp_version` | string | MUST | Spec version. |
| `type` | string | MUST | MUST be `"user_model"`. |
| `user_id` | string | MUST | User identifier. |
| `model_version` | integer | MUST | Monotonically increasing version number. MUST be >= 1. |
| `updated_at` | string | MUST | ISO 8601 timestamp of last update. |
| `metadata` | object | MAY | Vendor-specific extensions. |

When storing a User Model, backends MUST reject updates where `model_version` is
less than or equal to the stored version (optimistic concurrency control).

### 5.2 Communication Section

The `communication` object models how the user prefers to interact with agents.
Scales are continuous rather than categorical to allow fine-grained modeling.

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `verbosity` | number | MAY | -1.0 (terse) to 1.0 (verbose). 0.0 = default. |
| `formality` | number | MAY | -1.0 (casual) to 1.0 (formal). 0.0 = default. |
| `prefers_examples` | boolean | MAY | User prefers code or worked examples. |
| `prefers_explanations` | boolean | MAY | User prefers explanations of reasoning. |
| `languages` | array of string | MAY | ISO 639-1 language codes (e.g., `["en", "de"]`). |

### 5.3 Expertise Section

The `expertise` array models the user's demonstrated knowledge across domains.
Each entry represents a single domain.

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `domain` | string | MUST | Expertise domain name (e.g., `"rust"`, `"kubernetes"`). |
| `level` | string | MUST | One of: `"novice"`, `"intermediate"`, `"advanced"`, `"expert"`. |
| `confidence` | number | MUST | Agent's confidence in this assessment, 0.0-1.0. |
| `evidence_sessions` | array of string | MAY | Session IDs where this expertise was observed. |
| `last_observed` | string | MAY | ISO 8601 datetime of most recent observation. |

### 5.4 Corrections Section

The `corrections` array is a first-class record of instances where the user
corrected the agent. This is a primary learning signal and SHOULD be preserved
indefinitely.

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `what_agent_did` | string | MUST | What the agent did that was incorrect. |
| `what_user_wanted` | string | MUST | What the user wanted instead. |
| `context` | string | MAY | When this correction applies (e.g., "only for architecture discussions"). |
| `session_id` | string | MUST | Session where the correction occurred. |
| `timestamp` | string | MUST | ISO 8601 datetime. |

### 5.5 Stated Preferences Section

The `stated_preferences` array records preferences the user has explicitly
declared. These carry higher weight than inferred knowledge because the user
actively stated them.

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `key` | string | MUST | Preference key (e.g., `"code_style"`, `"response_length"`). |
| `value` | string | MUST | Preference value. |
| `timestamp` | string | MUST | ISO 8601 datetime when stated. |

---

## 6. Backend REST API

### 6.1 Base URL

All endpoints are under `/v1/`. Backends MAY host at any base URL but MUST
preserve the `/v1/` path prefix to allow future versioning.

### 6.2 Knowledge Endpoints

```
POST   /v1/knowledge             -- store a KnowledgeEntry
GET    /v1/knowledge?query=      -- search knowledge (text query)
GET    /v1/knowledge/:id         -- retrieve by ID
DELETE /v1/knowledge/:id         -- delete
PATCH  /v1/knowledge/:id         -- update confidence, confirm
```

**POST /v1/knowledge**

Request body: a valid KnowledgeEntry document.
Success response: `201 Created` with the stored document (including any
backend-assigned fields).
On validation failure: `400 Bad Request` with a JSON error body.

**GET /v1/knowledge/:id**

Success response: `200 OK` with the KnowledgeEntry document.
If not found: `404 Not Found`.
Backends MUST verify that the authenticated user owns this entry. If the
requesting user does not own the entry, the backend MUST return `403 Forbidden`.
An optional `?user_id=` query parameter is RECOMMENDED for defense-in-depth
authorization verification.

**DELETE /v1/knowledge/:id**

Success response: `204 No Content`.
Backends MUST permanently delete the entry (not soft-delete).
Encrypted columns SHOULD be zeroized before deletion (spec §8.2.7).
Backends MUST verify that the authenticated user owns this entry.

**PATCH /v1/knowledge/:id**

Allows partial update of `confidence`, `decay.last_confirmed`, and `tags`.
Implementations MUST NOT allow patching `id`, `user_id`, `category`, or `source`.
Backends MUST verify that the authenticated user owns this entry.

**GET /v1/knowledge?query=**

See Section 6.6 (Search).

### 6.3 User Model Endpoints

```
POST   /v1/user-model            -- store/update a UserModel
GET    /v1/user-model/:user_id   -- retrieve
DELETE /v1/user-model/:user_id   -- delete (full reset)
```

**POST /v1/user-model**

Request body: a valid UserModel document.
Success response: `200 OK` (update) or `201 Created` (new).
Backends MUST enforce `model_version` monotonicity (reject if new version <=
stored version with `409 Conflict`).

**DELETE /v1/user-model/:user_id**

MUST delete the complete User Model and all associated Knowledge Entries for
the user. MUST NOT be reversible (no soft-delete). Success response: `204 No Content`.

### 6.4 Bulk Endpoints

```
POST   /v1/export                -- export all data for a user as OAMP document
POST   /v1/import                -- import an OAMP document
```

**POST /v1/export**

Request body: `{ "user_id": "string" }`.
Response: a KnowledgeStore document containing all entries for the user, plus
the User Model in the `metadata` field (if present).

**POST /v1/import**

Request body: a KnowledgeStore document.
Response: `200 OK` with a summary of imported, skipped, and rejected entries.

### 6.5 Content Negotiation

Backends MUST support `application/json`. Support for other formats is OPTIONAL.

| Accept Header | Response Format |
|--------------|----------------|
| `application/json` (default) | JSON per schema |
| `application/protobuf` | Protobuf binary (OPTIONAL) |
| `application/json+oamp` | JSON with OAMP envelope metadata (OPTIONAL) |

### 6.6 Search

The `GET /v1/knowledge?query=` endpoint accepts a text query parameter.

- The spec does NOT mandate a specific search implementation (FTS, vector, hybrid).
  Backends choose their implementation.
- Results MUST be ranked by relevance (backend-defined).
- Results MUST be returned as a JSON array of KnowledgeEntry objects.
- List endpoints SHOULD support `?limit=` and `?offset=` parameters, or
  cursor-based pagination. The spec does not mandate a specific pagination style.
- Backends SHOULD support `?user_id=` to scope results to a single user.

### 6.7 Authentication

The spec does NOT define a specific authentication mechanism. Authentication is
deployment-specific. The security guide RECOMMENDS mTLS or Bearer tokens.
Backends MUST document their authentication requirements.

Regardless of the authentication mechanism, backends MUST enforce user-level
authorization: every API endpoint that returns or modifies knowledge data
MUST be scoped to the authenticated user. Cross-user access MUST be rejected
with `403 Forbidden`.

### 6.8 Error Responses

All error responses MUST be JSON objects with at least:

```json
{
  "error": "string describing the error",
  "code": "machine-readable error code"
}
```

Recommended error codes:

| Code | HTTP Status | When |
|------|-----------|------|
| `NOT_FOUND` | 404 | Resource does not exist |
| `VERSION_CONFLICT` | 409 | model_version not monotonically increasing |
| `VALIDATION_ERROR` | 400 | Field validation failure |
| `DUPLICATE_ID` | 409 | Entry with same ID already exists |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | User does not own this resource |
| `RATE_LIMITED` | 429 | Too many requests |

---

## 7. Content Negotiation

When an agent sends a request with `Accept: application/protobuf`, the backend
MAY respond with a protobuf-encoded binary message. The protobuf definitions
are provided in `proto/oamp/v1/` in the OAMP repository. The protobuf and JSON
representations MUST be semantically equivalent.

If a backend does not support protobuf, it MUST respond with `406 Not Acceptable`
rather than returning JSON with the wrong Content-Type.

---

## 8. Privacy and Security Requirements

### 8.1 MUST Requirements (Normative)

Implementations that violate these requirements MUST NOT claim OAMP compliance.

1. **Encryption at rest.** All stored knowledge and user model data MUST be
   encrypted at rest. AES-256-GCM is RECOMMENDED. Plaintext storage at rest
   is a compliance violation.

2. **User data ownership.** The `/v1/export` endpoint MUST return all data for
   a user without omission. The DELETE endpoints MUST permanently remove all
   user data. Soft-deletion (marking as deleted while retaining data) is NOT
   compliant.

3. **No content in logs.** Implementations MUST NOT log knowledge content,
   user model field values, or correction text. Logging entry IDs, categories,
   timestamps, and metadata keys is permitted.

4. **Provenance tracking.** Every KnowledgeEntry MUST have a `source` object
   with `session_id` and `timestamp`. Agents MUST NOT create anonymous
   knowledge entries (entries without provenance).

### 8.2 SHOULD Requirements (Recommended)

5. **Confidence decay.** Implementations SHOULD apply temporal decay to
   confidence scores using the formula in Section 3.6.

6. **Audit logging.** Operations on user data SHOULD be audit logged, recording
   who accessed what and when. Audit logs MUST NOT contain knowledge content
   (see requirement 3).

7. **Secure deletion.** Delete operations SHOULD zeroize memory buffers
   containing knowledge content before freeing them.

### 8.3 Companion Guidance (Non-Normative)

The `docs/security-guide.md` provides:

- Recommended cipher suites and key sizes
- Key management patterns (per-user keys, key rotation)
- GDPR Article 17 (right to erasure) compliance mapping
- CCPA compliance considerations
- Threat model: export file interception, import poisoning, session replay

---

## 9. Agent Interface

Agents that produce or consume OAMP documents MUST implement:

- **Export** -- Serialize internal memory to valid OAMP documents. All exported
  documents MUST pass validation against the JSON Schema in `spec/v1/`.

- **Import** -- Deserialize OAMP documents into internal format. Agents MUST
  accept documents that are valid per the JSON Schema and MUST NOT reject valid
  documents due to unknown `metadata` fields.

- **Merge** -- Handle conflicts when importing knowledge that overlaps with
  existing knowledge. The spec RECOMMENDS confidence-based resolution (higher
  confidence wins). Agents MAY implement other strategies but MUST document them.

---

## 10. Versioning Policy

### 10.1 Version Field

The `oamp_version` field uses semantic versioning (semver). The current version
is `"1.0.0"`.

### 10.2 Compatibility Rules

- Implementations MUST reject documents with an unsupported major version
  (e.g., a v1.0 implementation receiving a `"2.0.0"` document MUST reject it
  with a clear error).
- Implementations SHOULD accept documents with a higher minor version, ignoring
  unknown optional fields (forward compatibility).
- Implementations MUST accept documents with any patch version within the same
  minor version.

### 10.3 Field Evolution

- New REQUIRED fields MAY only be added in major versions.
- New OPTIONAL fields MAY be added in minor versions.
- Fields MAY NOT be removed in minor or patch versions.

---

## 11. Future Considerations (v2.0 Scope)

The following are deliberately excluded from v1.0 as too implementation-specific
or requiring more community input. They MAY be added in v2.0 or explored via the
`metadata` field in v1.0:

- **Work patterns** -- active hours, common task types, tool preferences.
  v1.0 agents MAY store these in `metadata`.

- **Activity timing** -- hour-of-day and day-of-week behavioral patterns.
  Relevant for scheduling-aware agents.

- **Session outcomes** -- structured records of what was accomplished in each
  session. Useful for agents that manage long-running projects.

- **Skill metrics** -- execution statistics for reusable skills or workflows.
  Too implementation-specific without broader community input.

Community feedback on these areas should be directed to the OAMP GitHub
repository's discussion board.

---

## Appendix A: Compliance Checklist

### Agent Compliance

- [ ] Exports produce valid OAMP documents (validated against JSON Schema)
- [ ] All exported KnowledgeEntries have `source.session_id` and `source.timestamp`
- [ ] Import accepts all valid OAMP documents (including unknown `metadata`)
- [ ] Merge strategy is documented
- [ ] No knowledge content logged

### Backend Compliance

- [ ] All ten REST endpoints implemented
- [ ] Data encrypted at rest
- [ ] `/v1/export` returns all user data
- [ ] DELETE endpoints perform permanent deletion
- [ ] `model_version` monotonicity enforced
- [ ] No knowledge content in logs
- [ ] User-level authorization enforced on all endpoints
- [ ] Error responses follow Section 6.8 format

---

## Appendix B: JSON Schema Locations

| Document Type | Schema |
|--------------|--------|
| KnowledgeEntry | `spec/v1/knowledge-entry.schema.json` |
| KnowledgeStore | `spec/v1/knowledge-store.schema.json` |
| UserModel | `spec/v1/user-model.schema.json` |

All schemas use JSON Schema draft-2020-12.
