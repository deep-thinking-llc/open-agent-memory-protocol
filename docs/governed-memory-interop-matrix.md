# Governed Memory Interop Matrix

**Status:** In progress  
**Date:** 2026-05-09
**Related issue:** `#18`

This document tracks the minimum interop expectations for governed memory
across the current OAMP ecosystem:

- `cosmictron`
- `kizuna-mem`
- `ultra`
- `toraeru`

## Canonical Fixture Pack

Every backend pair or consumer path should be exercised with the same canonical
fixture set:

1. [spec/v1/examples/knowledge-entry.json](../spec/v1/examples/knowledge-entry.json)
2. [spec/v1.2/examples/knowledge-entry-governed.json](../spec/v1.2/examples/knowledge-entry-governed.json)
3. [spec/v1.2/examples/knowledge-entry-provenance.json](../spec/v1.2/examples/knowledge-entry-provenance.json)
4. [spec/v1.2/examples/knowledge-store-interop.json](../spec/v1.2/examples/knowledge-store-interop.json)
5. [spec/v1.2/examples/capabilities-governance.json](../spec/v1.2/examples/capabilities-governance.json)

Validator-ready copies live under `validators/test-fixtures/valid/` for
backends that want to reuse the same files in CI without bespoke setup.

## Invariants To Verify

- `governance.sensitivity_class` survives export/import unchanged
- `governance.labels` survive export/import unchanged
- `provenance.sources[]` survives export/import unchanged
- unsupported governance fields are tolerated rather than rejected
- capabilities discovery accurately reflects governance and provenance support
- lossy behavior is documented explicitly when a backend drops unsupported
  fields instead of preserving them opaquely

## Execution Checklist

A runnable implementation of this checklist lives at
[`scripts/interop-roundtrip.sh`](../scripts/interop-roundtrip.sh). The brief
to hand to a backend implementer is
[`docs/governed-memory-interop-agent-brief.md`](./governed-memory-interop-agent-brief.md).

For each producer/consumer pair:

1. Validate the fixture pack locally with the repo validator or equivalent.
2. Import `knowledge-store-interop.json` into the producer backend.
3. Export the same user scope from the producer backend.
4. Confirm the exported document still contains:
   - the untouched `v1.0.0` entry
   - the governed `v1.2.0` entry
   - the provenance-only `v1.2.0` entry
5. Import the producer export into the consumer backend.
6. Export the same user scope from the consumer backend.
7. Diff the producer and consumer exports for:
   - `governance.sensitivity_class`
   - `governance.labels`
   - `governance.handling`
   - `provenance.sources`
   - `provenance.derived`
8. Fetch `GET /v1/capabilities` from both backends and record whether:
   - `governance.supported` is accurate
   - `labels_supported` is accurate
   - `extended_provenance_supported` is accurate
   - governance filter keys are advertised truthfully
9. Record any intentional lossy behavior or unsupported fields in the matrix.

## Pairings

| Producer | Consumer | Direction type | Required checks | Status |
|----------|----------|----------------|-----------------|--------|
| `cosmictron` | `kizuna-mem` | backend -> backend | fixture pack, governance, provenance, capabilities | automated |
| `kizuna-mem` | `cosmictron` | backend -> backend | fixture pack, governance, provenance, capabilities | automated |
| `cosmictron` | `ultra` | backend -> mediated client | live create/get canary, governed response consumption, typed user-id negotiation | automated |
| `ultra` | `cosmictron` | mediated client -> backend | live create/get canary, governed request mapping, typed user-id negotiation | automated |
| `kizuna-mem` | `ultra` | backend -> mediated client | live create/get canary, governed response consumption, tenant-prefixed user-id handling | automated |
| `ultra` | `kizuna-mem` | mediated client -> backend | live create/get canary, governed request mapping, tenant-prefixed user-id handling | automated |
| `cosmictron` | `toraeru` | backend -> integrator | fixture pack, capabilities, fixture consumption | automated |
| `kizuna-mem` | `toraeru` | backend -> integrator | fixture pack, capabilities, fixture consumption | automated |

## Release-Blocking Minimum For `v1.2`

Before calling governed memory interoperable at `v1.2`, the ecosystem should
have at least:

- one automated backend-to-backend round-trip path using the canonical fixtures
- one consumer/integrator path through `toraeru`
- one mediated-client live-peer path through `ultra`
- documented handling for any intentional lossy cases

## Implemented Pairings

### `cosmictron -> kizuna-mem`

- Automated in `cosmictron` via `crates/cosmictron-oamp/tests/oamp_kizuna_mem_interop.rs`
- Uses the canonical `knowledge-store-interop.json` fixture, with the fixture
  user scope adapted to Kizuna's tenant-prefixed `user_id` shape
- Governance fields survive exactly across the handoff
- Kizuna currently canonicalizes detailed `provenance.sources[].session_id`
  and `timestamp` fields, while preserving `derived` and `turn_id`
- This is treated as an intentional lossy case because Kizuna now advertises
  `capabilities.governance.extended_provenance_supported=false`

### `kizuna-mem -> cosmictron`

- Automated in the same `cosmictron` canary
- `cosmictron` bulk import now accepts and preserves `1.3.0` governed-memory
  stores emitted by Kizuna, while continuing to advertise its own local
  implementation line separately
- `cosmictron` re-export preserves the Kizuna-emitted governed document exactly
  after timestamp formatting is normalized to semantic equality

### `kizuna-mem -> toraeru`

- Automated in `toraeru` via `crates/toraeru-skill-loader/tests/real_substrate.rs`
  behind the `kizuna-real-substrate` feature, with a CI helper script at
  `scripts/run-kizuna-real-substrate-canary.sh`
- Verified against a live Kizuna `v1.3.0` server on 2026-05-09
- Requires a Kizuna-compatible numeric provenance session id for the canary
  path because Kizuna's current internal provenance model canonicalizes session
  identifiers numerically when `extended_provenance_supported=false`
- Governance, confidence, top-level provenance, `metadata.toraeru.*`, and tags
  round-trip on that path
- `source.agent_id` remains optional and is currently omitted by Kizuna
- The canary now also acts as a truthfulness check: if Kizuna advertises
  `extended_provenance_supported=true`, the test requires
  `provenance.sources[].agent_id` to survive the round-trip
- Current Kizuna builds intentionally advertise
  `extended_provenance_supported=false` on this path because detailed
  provenance agent identity is not yet preserved

### `cosmictron -> ultra`

- Automated in `ultrasushitron` via
  `core/tests/cosmictron_oamp_real_peer_canary.rs`, with a runnable helper at
  `scripts/run-cosmictron-real-substrate-canary.sh`
- Verified against a live Cosmictron canary server on 2026-05-09
- Ultra accepts both legacy flat capability payloads and the standard nested
  `capabilities.governance.*` shape used by governed-memory backends
- Ultra consumes governed create/get responses from a real Cosmictron peer
- Ultra negotiates Cosmictron's typed-route `user_id` contract from
  `capabilities.user_id_format.description`

### `ultra -> cosmictron`

- Automated in the same Ultra live canary
- The canary now proved a real wire-shape bug fix: Ultra had to map its
  internal governed-memory create payload from `sensitivity` to OAMP
  `sensitivity_class` before Cosmictron would accept the entry
- Governed `governance` and portable `provenance` fields round-trip through
  real `POST /v1/oamp/knowledge` and `GET /v1/oamp/knowledge/{id}` calls

### `kizuna-mem -> ultra`

- Automated in `ultrasushitron` via
  `core/tests/cosmictron_oamp_real_peer_canary.rs`, with a runnable helper at
  `scripts/run-kizuna-real-substrate-canary.sh`
- Verified against a live Kizuna `v1.3.0` server on 2026-05-09
- Ultra consumes governed create/get responses from a real Kizuna peer
- Kizuna's advertised `extended_provenance_supported=false` remains accurate
  on this path; the canary requires governed labels and portable provenance
  fields that Kizuna claims to preserve

### `ultra -> kizuna-mem`

- Automated in the same Ultra live canary
- Ultra preserves Kizuna's tenant-prefixed `user_id` contract on `/v1/oamp/*`
- Governed `governance` and portable `provenance` fields round-trip through
  real `POST /v1/oamp/knowledge` and `GET /v1/oamp/knowledge/{id}` calls

### `cosmictron -> toraeru`

- Automated in `toraeru` via
  `crates/toraeru-skill-loader/tests/real_substrate.rs` behind the
  `kizuna-real-substrate` feature, with a CI helper script at
  `scripts/run-cosmictron-real-substrate-canary.sh`
- Verified against a live Cosmictron canary server on 2026-05-09
- Toraeru now probes `GET /v1/capabilities`, reads the advertised
  `capabilities.user_id_format` contract, and rewrites tenant-scoped opaque
  user ids to the stable 64-hex identity shape required by Cosmictron's typed
  `/v1/oamp/*` routes
- Governance, confidence, top-level provenance, `metadata.toraeru.*`, tags,
  and `source.agent_id` all round-trip on this path
- Cosmictron currently advertises `extended_provenance_supported=true` and the
  canary confirms detailed `provenance.sources[].agent_id` preservation

## Notes

- Portable withheld or redacted result semantics remain out of scope here until
  the separate `v2.0` RFC is resolved.
- This matrix should be updated as each backend lands real support or documents
  an intentional gap.
- `ultra` should be treated as a governed-memory client/mediator in this
  matrix, not as an OAMP substrate/backend.
