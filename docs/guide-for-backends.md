# OAMP: Guide for Backend Implementors

## Overview

This guide explains how to build an OAMP-compliant memory backend. After implementing the OAMP API, any OAMP-compliant agent can use your backend for persistent memory storage.

## API Endpoints

Your backend MUST implement these endpoints:

| Method | Path | Description |
|--------|------|-------------|
| POST | /v1/knowledge | Store a KnowledgeEntry |
| GET | /v1/knowledge?query= | Search knowledge |
| GET | /v1/knowledge/:id | Retrieve by ID |
| DELETE | /v1/knowledge/:id | Delete entry |
| PATCH | /v1/knowledge/:id | Update (confidence, confirm) |
| POST | /v1/user-model | Store/update UserModel |
| GET | /v1/user-model/:user_id | Retrieve UserModel |
| DELETE | /v1/user-model/:user_id | Delete all user data |
| POST | /v1/export | Export all user data |
| POST | /v1/import | Import OAMP document |

Your backend SHOULD also implement:

| Method | Path | Description |
|--------|------|-------------|
| POST | /v1/admin/keys/rotate | Rotate encryption key |
| GET | /v1/admin/audit | Query audit log |
| GET | /v1/capabilities | Advertise optional v1.1/v1.2/v1.3 support |
| GET | /health | Health check |

## Storage Requirements

### Encryption at Rest (MUST)

All stored data MUST be encrypted at rest. The spec recommends AES-256-GCM but does not mandate a specific cipher.

### Search (GET /v1/knowledge?query=)

The search endpoint accepts a text query and returns matching entries ranked by relevance. You choose the search implementation:
- Full-text search (FTS5, Elasticsearch)
- Vector/semantic search
- Hybrid (recommended)

The spec does not mandate a search algorithm.

### Content Negotiation

Support at minimum `application/json`. Optionally support `application/protobuf` for binary efficiency.

## Compliance Checklist

- [ ] All data encrypted at rest
- [ ] DELETE endpoints fully remove data (not soft-delete)
- [ ] Export endpoint returns ALL user data
- [ ] No knowledge content in server logs
- [ ] Every stored entry has provenance (source with session_id + timestamp)
- [ ] If you advertise v1.2 governance support, preserve `governance` and `provenance`
- [ ] If you advertise v1.3 enforcement support, apply the same grant filter to read, write, import, export, and stream paths
- [ ] If you advertise v1.3 enforcement support, hide out-of-scope IDs as `404` on agent surfaces
- [ ] Search returns results ranked by relevance
- [ ] All knowledge endpoints scoped to user_id (no cross-user leakage)
- [ ] Rate limiting on all endpoints
- [ ] TLS 1.2 minimum for production
- [ ] Audit logging enabled (SHOULD)

## Governed Memory Versions

- `v1.2` standardizes descriptive governed-memory metadata and richer provenance.
- `v1.3` standardizes enforcement of that metadata at the agent boundary.
- `v2.0` is still the home for portable withheld/redacted result semantics.

If your backend implements governed memory today, the recommended path is:

1. Preserve `governance` and `provenance` per `spec/v1.2/oamp-v1.2.md`
2. Advertise `capabilities.governance`
3. Add `capabilities.governance.enforcement` and enforce grant-based filtering per `spec/v1.3/oamp-v1.3-draft.md`
