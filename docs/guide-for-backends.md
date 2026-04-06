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
- [ ] Search returns results ranked by relevance
