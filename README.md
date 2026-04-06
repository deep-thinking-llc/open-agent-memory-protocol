# Open Agent Memory Protocol (OAMP)

[中文](docs/README.zh.md) | [한국어](docs/README.ko.md) | [日本語](docs/README.ja.md) | [Bahasa Melayu](docs/README.ms.md)

**A standard for storing, exchanging, and querying memory data between AI agents and memory backends.**

OAMP enables AI agents to remember what they learn about users — and to share that memory portably across different agent frameworks and storage backends, with privacy and security built in from the ground up.

## Why OAMP?

Today, every AI agent framework stores user memory differently. When you switch agents, you lose everything the previous agent learned about you — your preferences, expertise, corrections, workflow patterns. OAMP solves this by defining:

- **A common format** for agent memory (JSON Schema + Protobuf)
- **A REST API contract** for memory backends
- **Privacy requirements** that every implementation must meet
- **Reference implementations** in Rust and TypeScript

### The Problem

- Agent A learns you prefer concise answers, are an expert in Rust, and never want `unwrap()` in code examples
- You switch to Agent B
- Agent B knows nothing about you — you start from zero
- Your corrections, preferences, and expertise are locked in Agent A's proprietary format

### The OAMP Solution

- Agent A exports your memory as an OAMP document (standard JSON)
- Agent B imports it
- Agent B immediately knows your preferences, expertise, and corrections
- No vendor lock-in. Your memory is yours.

## What OAMP Defines

### Knowledge Layer
Discrete facts an agent learns about you:

```json
{
  "type": "knowledge_entry",
  "category": "correction",
  "content": "Never use unwrap() — always use proper error handling with ? operator",
  "confidence": 0.98,
  "source": { "session_id": "sess-003", "timestamp": "2026-03-12T16:45:00Z" }
}
```

Four categories: **fact** (objective info), **preference** (how you like things), **pattern** (what you tend to do), **correction** (what you've told the agent to stop doing).

### User Model Layer
A richer profile of who you are:

```json
{
  "type": "user_model",
  "communication": { "verbosity": -0.6, "formality": 0.2 },
  "expertise": [
    { "domain": "rust", "level": "expert", "confidence": 0.95 },
    { "domain": "react", "level": "novice", "confidence": 0.60 }
  ],
  "corrections": [
    { "what_agent_did": "Used unwrap()", "what_user_wanted": "Use ? operator" }
  ]
}
```

### Privacy Requirements (Mandatory)

OAMP takes privacy seriously. Compliant implementations **MUST**:

- **Encrypt all data at rest** (AES-256-GCM recommended)
- **Support full data export** — users own their memory
- **Support full deletion** — real deletion, not soft-delete
- **Never log content** — IDs and categories only
- **Track provenance** — every entry records where it came from

## Repository Structure

```
open-agent-memory-protocol/
├── spec/v1/                    # Authoritative specification
│   ├── oamp-v1.md             # Human-readable spec (RFC 2119)
│   ├── *.schema.json          # JSON Schema (draft-2020-12)
│   └── examples/              # Valid example documents
├── proto/oamp/v1/             # Protocol Buffer definitions
├── reference/
│   ├── rust/                  # Rust crate: oamp-types
│   └── typescript/            # npm package: @oamp/types
├── validators/
│   ├── validate.sh            # CLI validator
│   └── test-fixtures/         # Valid + invalid test documents
└── docs/
    ├── guide-for-agents.md    # How to add OAMP to your agent
    ├── guide-for-backends.md  # How to build an OAMP backend
    └── security-guide.md      # Encryption, GDPR, threat model
```

## Quick Start

### Validate a document

```bash
./validators/validate.sh my-export.json
```

### Rust

```toml
[dependencies]
oamp-types = "1.0"
```

```rust
use oamp_types::{KnowledgeEntry, KnowledgeCategory};

// Create a knowledge entry
let entry = KnowledgeEntry::new(
    "user-123",
    KnowledgeCategory::Correction,
    "Never use unwrap() — use ? operator instead",
    0.98,
    "session-42",
);

// Serialize to OAMP JSON
let json = serde_json::to_string_pretty(&entry)?;

// Validate
oamp_types::validate::validate_knowledge_entry(&entry)?;
```

### TypeScript

```bash
npm install @oamp/types
```

```typescript
import { KnowledgeEntry } from '@oamp/types';

// Validate and parse an OAMP document
const entry = KnowledgeEntry.parse(jsonData);

// Type-safe access
console.log(entry.category); // "correction"
console.log(entry.confidence); // 0.98
```

## For Agent Developers

Want to add OAMP support to your agent? See the [Agent Guide](docs/guide-for-agents.md).

In short:
1. **Export** — map your internal memory types to OAMP JSON
2. **Import** — parse OAMP JSON into your internal types
3. **Validate** — use the JSON Schema or reference libraries to ensure compliance

## For Backend Developers

Want to build an OAMP-compliant memory backend? See the [Backend Guide](docs/guide-for-backends.md).

Your backend needs to implement 9 REST endpoints covering knowledge CRUD, user model storage, and bulk export/import.

## Specification

The full spec is at [spec/v1/oamp-v1.md](spec/v1/oamp-v1.md). It uses RFC 2119 language (MUST, SHOULD, MAY) to define compliance levels.

### Version

Current: **v1.0.0**

The spec is versioned semantically. Documents include an `oamp_version` field for forward compatibility.

### Future (v2.0)

Planned for v2.0 (based on community feedback):
- Session outcomes (structured task records)
- Skill metrics (execution statistics)
- Work patterns (activity timing, tool preferences)
- Streaming API for real-time memory sync

## Security

See the [Security Guide](docs/security-guide.md) for:
- Recommended cipher suites
- Key management patterns
- GDPR Article 17 / CCPA compliance mapping
- Threat model for memory interchange

## Contributing

We welcome contributions. Please:
1. Read the spec before proposing changes
2. Add test fixtures for any schema changes
3. Update both Rust and TypeScript reference implementations
4. Follow existing code style

## Contact

For questions, partnerships, or feedback:

**Email:** contact@dthink.ai

## License

MIT — see [LICENSE](LICENSE)
