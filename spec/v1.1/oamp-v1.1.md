# Open Agent Memory Protocol — Version 1.1.0

**Status:** Stable
**Date:** 2026-05-09
**Authors:** Deep Thinking LLC
**Supersedes:** None — extends v1.0.0 additively
**Repository:** `github.com/deep-thinking-llc/open-agent-memory-protocol`

---

## Abstract

OAMP v1.1 is a **strictly additive** minor version over v1.0.0. It defines two
OPTIONAL capabilities that v1.0 deliberately deferred to "future considerations":

- A **streaming subscription transport** that lets clients receive
  `KnowledgeEntry` and `UserModel` events in real time over WebSocket.
- A **bitemporal `as_of` query parameter** for read endpoints, allowing clients
  to query memory state as it existed at a past point in time.

A v1.1-conformant backend MUST still satisfy every v1.0 requirement. Both new
capabilities are advertised through a small **capabilities discovery endpoint**
so v1.0 clients remain interoperable. v1.1 introduces no breaking schema or
endpoint changes, and v1.0 clients remain wire-compatible with v1.1 backends.

The motivation for promoting these from "v2.0 scope" to v1.1 OPTIONAL is
practical: reference implementations (cosmictron, kizuna-mem) need both
capabilities to deliver useful product surfaces, and the absence of even an
OPTIONAL spec for them creates incompatible vendor extensions before the
ecosystem has a chance to align.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

---

## 1. Relationship to v1.0

v1.1 reuses **all** v1.0 schemas, endpoints, requirements, and semantics
without modification. Only the additions in §3 and §4 are new. Documents
SHOULD set `oamp_version` to `"1.1.0"` only when they exercise a v1.1-only
field; otherwise `"1.0.0"` remains correct and preferred for portability.

A v1.1 backend MUST accept documents with `oamp_version` of either `"1.0.0"`
or `"1.1.0"`. A v1.0 backend MUST reject `"1.1.0"` documents that contain
v1.1-only fields it does not understand (per v1.0 §10.2 — major version
compatibility rules); however, since v1.1 introduces no new top-level
required fields, a v1.0 backend SHOULD accept a `"1.1.0"` document that
contains only v1.0 fields, ignoring the version label.

---

## 2. Capabilities Discovery

v1.1 introduces a single new endpoint that lets clients discover which
OPTIONAL features a backend supports.

### 2.1 GET `/v1/capabilities`

Returns a JSON object describing the backend's protocol surface.

**Response:**

```json
{
  "oamp_version": "1.1.0",
  "capabilities": {
    "streaming": {
      "supported": true,
      "subprotocol": "oamp.v1",
      "endpoint": "/v1/stream",
      "event_types": ["knowledge_created", "knowledge_updated",
                      "knowledge_deleted", "user_model_updated"]
    },
    "as_of": {
      "supported": true,
      "endpoints": ["/v1/knowledge", "/v1/knowledge/{id}",
                    "/v1/user-model/{user_id}"],
      "min_resolution_ms": 1
    },
    "user_id_format": {
      "description": "tenant:node composite (e.g. '1:user')",
      "pattern": "^[0-9]+:.+$"
    },
    "id_preservation": "preserved",
    "content_types": ["application/json", "application/protobuf"],
    "auth_schemes": ["bearer"]
  }
}
```

**Requirements:**

- Backends advertising v1.1 MUST implement this endpoint.
- All `capabilities.*.supported` fields MUST be boolean.
- Clients SHOULD call this endpoint at most once per connection lifetime and
  cache the result.
- Backends MAY include vendor-specific keys under
  `capabilities.metadata` (object). Clients MUST tolerate unknown keys.

**`user_id_format` (REQUIRED):**

Backends MUST advertise their `user_id` encoding format so that clients
bridging multiple OAMP backends can pre-flight check compatibility before
attempting cross-backend import/export. The object contains:

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `description` | string | MUST | Human-readable description of the format (e.g., `"tenant:node composite (e.g. '1:user')"`, `"64-char lowercase hex Ed25519 public key"`). |
| `pattern` | string | MAY | ECMA-262 regex that matches valid `user_id` values for this backend. Clients MAY use this for pre-validation. |

The `user_id` field in OAMP documents remains an opaque string (no format
constraint in the schema). The capabilities advertisement is for client-side
compatibility checking only. Clients that bridge backends with incompatible
`user_id` formats MUST transform `user_id` values during cross-backend
transfer (this is a client responsibility, not a backend responsibility).

**`id_preservation` (REQUIRED):**

A string indicating whether the backend preserves client-supplied entry IDs
during `POST /v1/import`. One of:

- `"preserved"` -- The backend stores and returns the client-supplied `id`
  unchanged. The `id_mappings` field in the import response will always be
  empty `{}`.
- `"regenerated"` -- The backend MAY assign new IDs to imported entries
  (e.g., deterministic derivation from internal keys). The `id_mappings`
  field in the import response MUST contain a mapping from each original ID
  to its new assigned ID.

Clients that bridge multiple OAMP backends and use entry IDs as join keys
MUST inspect `id_preservation` and, if `"regenerated"`, apply `id_mappings`
from the import response to maintain reference integrity.

### 2.2 v1.0 Backwards Compatibility

A v1.0 backend will return `404 Not Found` for `/v1/capabilities`. Clients
MUST treat this response as "backend is v1.0; no OPTIONAL capabilities
available" and fall back to REST-only behaviour. v1.0 backends also do not
advertise `user_id_format` or `id_preservation`; clients bridging multiple
backends MUST handle this gracefully (see §5).

### 2.3 Import Response Shape (Clarification of v1.0 §6.4)

v1.0 §6.4 defined `POST /v1/import` as returning "`200 OK` with a summary"
but did not pin the status code or response body shape. v1.1 mandates the
following:

**Status code:** `201 Created`. (Clients MUST also accept `200 OK` from
v1.0 backends for backward compatibility.)

**Response body:**

```json
{
  "imported": 5,
  "skipped": 0,
  "rejected": 0,
  "id_mappings": {
    "88f88510-928b-49d9-aff1-4f32acbf1f97": "a299eeae-39ac-4248-ae24-007302cb64fc"
  }
}
```

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `imported` | integer | MUST | Number of entries successfully imported. |
| `skipped` | integer | MUST | Number of entries skipped (e.g., duplicate with equal or higher confidence). |
| `rejected` | integer | MUST | Number of entries rejected due to validation errors. |
| `id_mappings` | object | MUST | Map of original ID to assigned ID. Empty `{}` if all IDs were preserved. See §2.4. |
| `rejections` | array | MAY | Detail on rejected entries. Each element: `{"id": "...", "reason": "..."}`. |

### 2.4 Entry ID Preservation on Import (Clarification of v1.0 §4.4)

Implementations MAY preserve or regenerate entry IDs during import, but
MUST communicate the outcome via the import response:

- **ID-preserving backends** (advertised as `id_preservation: "preserved"` in
  capabilities): store the client-supplied `id` unchanged. The `id_mappings`
  field in the import response MUST be `{}`.
- **ID-regenerating backends** (advertised as `id_preservation: "regenerated"`
  in capabilities): assign new IDs during import (e.g., via deterministic
  derivation). The `id_mappings` field in the import response MUST map every
  imported entry's original ID to its new assigned ID.

This accommodates both architectural patterns without requiring either to
change its internal design. Clients that depend on ID stability (e.g., agents
building memory graphs keyed on entry IDs) MUST inspect `id_mappings` and
update their references after import.

---

## 3. Streaming Transport (OPTIONAL)

### 3.1 Motivation

OAMP v1.0 is poll-based: clients learn about memory changes by re-issuing
search queries. For interactive agents, observability surfaces, and dashboards
this creates either high polling load or stale UI. v1.1 defines a WebSocket
subprotocol that lets clients subscribe to memory mutations as they occur.

This is OPTIONAL because (a) not every backend has a real-time event source,
and (b) the polling model in v1.0 remains correct and sufficient for batch
agents.

### 3.2 Endpoint

A v1.1 backend with streaming support MUST expose:

- **URL:** `wss://{host}/v1/stream` (or `ws://` for non-TLS development)
- **Subprotocol:** `oamp.v1` (negotiated via standard WebSocket
  `Sec-WebSocket-Protocol` header)

If the client does not request `oamp.v1` in the subprotocol list, the
backend MUST refuse the upgrade with HTTP `400 Bad Request`.

### 3.3 Authentication

WebSocket upgrades MUST authenticate the same way the REST API does. Backends
SHOULD accept the bearer token via the `Authorization` header on the upgrade
request, and MAY accept it as a `?token=` query parameter for browser clients
that cannot set headers on a WebSocket upgrade. The chosen scheme MUST be
declared in `/v1/capabilities`.

### 3.4 Frame Format

All frames are **text frames** carrying a single JSON object. (Binary frames
are reserved for future protobuf-mode streaming and MUST NOT be used in v1.1.)

Every frame has the shape:

```json
{
  "oamp_version": "1.1.0",
  "type": "<frame_type>",
  "id": "<uuid_v4>",
  "ts": "<iso8601>",
  "payload": { ... }
}
```

`id` is a per-frame identifier the client uses to correlate replies; `ts`
is the backend's monotonic timestamp at the moment the frame was emitted.

### 3.5 Client → Server Frames

| `type`         | Purpose                                            |
|----------------|----------------------------------------------------|
| `subscribe`    | Open a subscription with filters.                  |
| `unsubscribe`  | Close a previously opened subscription.            |
| `ping`         | Liveness probe; backend MUST respond with `pong`.  |

**`subscribe` payload:**

```json
{
  "subscription_id": "<client-chosen-string>",
  "user_id": "user-123",
  "event_types": ["knowledge_created", "knowledge_updated"],
  "filters": {
    "category": ["preference", "correction"],
    "tags": ["language"]
  },
  "include_initial_snapshot": false
}
```

- `subscription_id` is client-chosen and MUST be unique per connection. The
  server uses it on every subsequent event and on the unsubscribe ack.
- `user_id` is REQUIRED. Backends MUST refuse cross-user subscriptions
  (return an `error` frame with code `"forbidden"`).
- `event_types` MAY be omitted to subscribe to all event types the backend
  supports.
- `filters` is OPTIONAL; recognised filter keys are listed in §3.7. Unknown
  filter keys MUST be ignored, not rejected.
- `include_initial_snapshot` (default `false`): if `true`, the backend MUST
  emit one `knowledge_snapshot` frame containing the current matching state
  before any live events flow.

### 3.6 Server → Client Frames

| `type`                | Purpose                                              |
|-----------------------|------------------------------------------------------|
| `subscribed`          | Acknowledge a subscription.                          |
| `unsubscribed`        | Acknowledge an unsubscription.                       |
| `knowledge_created`   | A new `KnowledgeEntry` was stored.                   |
| `knowledge_updated`   | An existing `KnowledgeEntry` was modified (PATCH).   |
| `knowledge_deleted`   | A `KnowledgeEntry` was permanently deleted.          |
| `knowledge_snapshot`  | One-shot snapshot for `include_initial_snapshot`.    |
| `user_model_updated`  | A `UserModel` row was updated.                       |
| `error`               | A protocol or application error.                     |
| `pong`                | Liveness reply.                                      |

**`knowledge_created` payload:**

```json
{
  "subscription_id": "<echoed-from-subscribe>",
  "entry": { /* full v1.0 KnowledgeEntry document */ }
}
```

`knowledge_updated` carries the **post-update** entry. `knowledge_deleted`
carries only `{ "subscription_id": "...", "id": "<uuid>", "user_id": "..." }`
to satisfy the v1.0 "no content in logs" rule even on the wire — the
deleted content MUST NOT be re-broadcast.

**`error` payload:**

```json
{
  "subscription_id": "<id-or-null>",
  "code": "forbidden | invalid | rate_limited | internal",
  "message": "human-readable",
  "retryable": false
}
```

### 3.7 Recognised Filter Keys

| Key        | Type            | Semantics                                  |
|------------|-----------------|--------------------------------------------|
| `category` | array of string | Match any of these v1.0 categories.        |
| `tags`     | array of string | Entry MUST contain at least one listed tag.|
| `min_confidence` | number    | Entry's `confidence` MUST be ≥ this value. |

Backends MAY support additional filter keys; they MUST be advertised in
`/v1/capabilities.streaming.filter_keys`.

### 3.8 Backpressure & Delivery

- The protocol is **at-most-once**. If the client cannot keep up, the backend
  MAY drop events and SHOULD emit a single `error` frame with code
  `"rate_limited"` and `retryable: true` to signal the gap. Clients that need
  exactly-once semantics MUST reconcile via `/v1/knowledge` polling.
- Backends MUST close the WebSocket after 60 seconds of no client traffic
  (no `ping`, no other frame). Clients SHOULD send `ping` every 30 seconds.
- Backends MUST tolerate at least 16 concurrent subscriptions per connection.

### 3.9 Privacy

The v1.0 §8 privacy rules apply to streamed content as if it were a REST
response:

- Knowledge content MUST NOT be logged on either side of the connection.
- `knowledge_deleted` frames MUST NOT include the deleted content.
- Subscriptions MUST be scoped to a single `user_id`. Multi-user fan-out
  is a v2.0 concern.

---

## 4. Bitemporal `as_of` Query Parameter (OPTIONAL)

### 4.1 Motivation

Many memory backends (cosmictron, kizuna-mem, others) already store
bitemporal data — a `valid_time` axis (when the fact was true in the world)
and an `ingest_time` axis (when the system learned the fact). v1.0 has no
way to ask "what did you know at time T?", which is needed for:

- Replay and debugging of agent decisions.
- Compliance audits ("what was on file when this decision was made?").
- Reverse-time-travel UIs in observability dashboards.

v1.1 defines a single, universally applicable query parameter that exposes
this storage capability without dictating internal representation.

### 4.2 Parameter

Backends with `as_of` support MUST accept the following query parameter on
the endpoints listed below:

```
?as_of=<iso8601-datetime>
```

Affected endpoints:

| Endpoint                          | Semantics with `as_of`                          |
|-----------------------------------|-------------------------------------------------|
| `GET /v1/knowledge?query=...`     | Search the index as it existed at `as_of`.      |
| `GET /v1/knowledge/{id}`          | Return the entry's state as of `as_of`.         |
| `GET /v1/user-model/{user_id}`    | Return the user model as of `as_of`.            |

The mutation endpoints (`POST`, `PATCH`, `DELETE`) MUST NOT accept `as_of`
and MUST respond with `400 Bad Request` if the parameter is supplied.

### 4.3 Semantics

Two semantic axes are possible. Backends MUST pick **ingest_time semantics**
by default: "show me the result that this same query would have returned if
issued at exactly `as_of`." This is the only universally well-defined
interpretation, and is what every known reference backend implements.

If a backend supports `valid_time` queries (the world-state axis), it MUST
expose them through a separate, explicitly named parameter (e.g.,
`?valid_at=`). v1.1 reserves `valid_at` for this purpose but does not
standardise it; that is v2.0 work.

### 4.4 Response Shape

The response body MUST be identical to the equivalent v1.0 response. v1.1
only changes which historical state the body describes.

A v1.1-aware backend SHOULD include a response header
`OAMP-As-Of: <iso8601>` echoing the timestamp it used. Clients MAY use
this to detect timestamp normalisation (e.g., the backend rounded to its
storage resolution).

### 4.5 Out-of-Range Timestamps

- An `as_of` in the future MUST be treated as `now`. The backend SHOULD
  set `OAMP-As-Of` to the actual resolved timestamp.
- An `as_of` before the user's first ingest event MUST return an empty
  result set (HTTP 200), not a 404.
- An `as_of` that the backend cannot resolve due to retention/snapshot
  expiry MUST return `409 Conflict` with `code: "as_of_expired"`.

### 4.6 Capabilities Advertisement

`/v1/capabilities.as_of.min_resolution_ms` MUST report the smallest time
delta the backend can resolve (e.g., snapshot interval). Clients SHOULD
NOT assume sub-millisecond resolution.

---

## 5. Compliance

A backend that claims **v1.1 conformance** MUST:

1. Satisfy every v1.0 mandatory requirement.
2. Implement `GET /v1/capabilities` returning truthful capability flags.
3. For each OPTIONAL capability it advertises (`streaming`, `as_of`):
   implement the full surface described in §3 or §4 respectively.
4. Reject unsupported OPTIONAL features with the documented HTTP/WebSocket
   error codes; never silently ignore.

A backend MAY claim v1.1 conformance with **zero OPTIONAL capabilities
supported**. This is useful: it signals to clients that the backend
understands the v1.1 vocabulary and will surface future OPTIONAL features
in `/v1/capabilities` rather than as undiscoverable extensions.

The validator at `/validators/validate.sh` will gain v1.1 fixtures in a
separate PR; v1.1 documents MUST validate against the v1.0 JSON Schemas
unchanged.

---

## 6. Migration Path for v1.0 Clients

A v1.0 client talking to a v1.1 backend continues to work without changes.
A v1.0 client wishing to opt into v1.1 features:

1. Issue `GET /v1/capabilities` and inspect the response.
2. If `streaming.supported`, open the WebSocket and follow §3.
3. If `as_of.supported`, append `?as_of=` to read requests where useful.

There is no need to bump `oamp_version` in stored documents. The version
string describes a document, not a session — a v1.1 client may store v1.0
documents perfectly well.

---

## 7. Open Questions for v1.1 Finalisation

These are tracked for community discussion before v1.1 is marked stable:

1. **Subscription resumption across reconnects.** Should clients be able
   to pass a `since=<event_id>` on `subscribe` to replay missed events?
   This requires backends to retain an event log; many do not. *Tentative
   answer:* leave to v2.0.
2. **Snapshot pagination.** A `knowledge_snapshot` frame for a user with
   100k entries is a single frame today. Should we mandate chunking?
   *Tentative answer:* mandate `snapshot_chunk` if backends report a
   `streaming.snapshot_max_entries` limit; otherwise single frame.
3. **`valid_at` standardisation.** Real demand from finance and compliance
   suggests `valid_at` is more useful than `as_of` for some workflows.
   *Tentative answer:* land `as_of` in v1.1, hold `valid_at` for v1.2 or
   v2.0 once ≥2 backends ship interoperable implementations.
4. **gRPC streaming.** Should the streaming subprotocol have a gRPC
   binding? *Tentative answer:* the `/proto/` directory will gain
   `service Stream { rpc Subscribe(stream SubscribeRequest) returns
   (stream Event); }` once the JSON shape is stable.

---

## Appendix A: Capabilities Schema

A JSON Schema for the `/v1/capabilities` response will be added at
`spec/v1.1/capabilities.schema.json` once §2 is finalised. The shape in §2.1
is the working definition.

## Appendix B: Reference Implementation Targets

Two reference backends will land v1.1 OPTIONAL capabilities concurrently
with this draft:

- **cosmictron** (Rust) — `/v1/capabilities`, `/v1/oamp/*` REST,
  `/v1/oamp/stream` WebSocket subprotocol, `?as_of=` on memory reads. See
  `cosmictron/docs/design/OAMP_TRANSPORT.md`.
- **kizuna-mem** (Zig core + Rust sidecar) — same surface; WebSocket
  served from the Rust sidecar. See
  `kizuna-dream/docs/design/OAMP_TRANSPORT.md` and
  `kizuna-dream/docs/design/WEBSOCKET_EVENT_STREAM.md`.

These implementations are the conformance pressure-test for the spec; if
either cannot land cleanly against this draft, the draft will be revised
before v1.1 is finalised.
