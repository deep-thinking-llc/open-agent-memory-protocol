<div align="center">

# Open Agent Memory Protocol

### Your AI agent's memory should belong to you.

[![Spec Version](https://img.shields.io/badge/spec-v1.0.0-blue.svg)](spec/v1/oamp-v1.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Rust Crate](https://img.shields.io/crates/v/oamp-types.svg)](https://crates.io/crates/oamp-types)
[![npm Package](https://img.shields.io/npm/v/@deepthinking/oamp-types.svg)](https://www.npmjs.com/package/@deepthinking/oamp-types)
[![PyPI Package](https://img.shields.io/pypi/v/oamp-types.svg)](https://pypi.org/project/oamp-types/)
[![Go Reference](https://img.shields.io/badge/go-reference-blue.svg)](reference/go/)
[![Hex Package](https://img.shields.io/badge/hex-oamp__types-purple.svg)](https://hex.pm/packages/oamp_types)

[Specification](spec/v1/oamp-v1.md) | [Rust](reference/rust/) | [TypeScript](reference/typescript/) | [Python](reference/python/) | [Go](reference/go/) | [Elixir](reference/elixir/) | [Security Guide](docs/security-guide.md)

---

[中文](docs/README.zh.md) | [한국어](docs/README.ko.md) | [日本語](docs/README.ja.md) | [Bahasa Melayu](docs/README.ms.md)

</div>

## The Problem

Every AI agent stores memory differently. When you switch agents, you start from zero.

```
Agent A                          Agent B
  learns your preferences    →     knows nothing
  tracks your expertise      →     starts fresh  
  remembers corrections      →     repeats mistakes
  understands your workflow   →     generic responses
```

Your corrections, preferences, and expertise are locked in proprietary formats. **You lose weeks of context every time you switch.**

## The Solution

OAMP is an open standard that makes agent memory portable, private, and interoperable.

```
Agent A                          Agent B
  export as OAMP             →     import OAMP
  standard JSON format       →     instant context
  your data, your control    →     no vendor lock-in
```

---

## What's Inside

<table>
<tr>
<td width="50%">

### Knowledge Layer

Discrete facts your agent learns:

```json
{
  "category": "correction",
  "content": "Never use unwrap() — use ? operator",
  "confidence": 0.98
}
```

Four types: **fact** · **preference** · **pattern** · **correction**

</td>
<td width="50%">

### User Model Layer

A rich profile of who you are:

```json
{
  "expertise": [
    { "domain": "rust", "level": "expert" },
    { "domain": "react", "level": "novice" }
  ],
  "communication": { "verbosity": -0.6 }
}
```

Tracks: **expertise** · **communication style** · **corrections** · **preferences**

</td>
</tr>
</table>

---

## Privacy First

OAMP doesn't treat privacy as optional. These are **mandatory requirements** — not guidelines:

| Requirement | Detail |
|:---|:---|
| **Encryption at rest** | All stored data MUST be encrypted (AES-256-GCM recommended) |
| **User data ownership** | Full export MUST be supported — users own their memory |
| **Right to deletion** | Real deletion, not soft-delete. GDPR Article 17 compliant |
| **No content logging** | Implementations MUST NOT log knowledge content |
| **Provenance tracking** | Every entry records where and when it was learned |

---

## Quick Start

### Validate

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

let entry = KnowledgeEntry::new(
    "user-123",
    KnowledgeCategory::Correction,
    "Never use unwrap() — use ? operator instead",
    0.98,
    "session-42",
);

// Validate against spec
oamp_types::validate::validate_knowledge_entry(&entry)?;
```

### TypeScript

```bash
npm install @oamp/types
```

```typescript
import { KnowledgeEntry } from '@oamp/types';

const entry = KnowledgeEntry.parse(jsonData);
console.log(entry.category);   // "correction"
console.log(entry.confidence);  // 0.98
```

### Python

```bash
pip install oamp-types
```

```python
from oamp_types import (
    KnowledgeEntry, KnowledgeCategory, KnowledgeSource,
    validate_knowledge_entry,
)

entry = KnowledgeEntry(
    user_id="user-123",
    category=KnowledgeCategory.correction,
    content="Never use unwrap() — use ? operator instead",
    confidence=0.98,
    source=KnowledgeSource(session_id="session-42"),
)

# Validate
errors = validate_knowledge_entry(entry)

# Serialize to JSON (exclude null optional fields)
json_str = entry.model_dump_json(exclude_none=True)
```

### Go

```bash
go get github.com/deep-thinking-llc/oamp-go
```

```go
import oamp "github.com/deep-thinking-llc/oamp-go"

entry := oamp.NewKnowledgeEntry(
    "user-123",
    oamp.KnowledgeCategoryCorrection,
    "Never use unwrap() — use ? operator instead",
    0.98,
    "session-42",
)

// Validate
errors := oamp.ValidateKnowledgeEntry(entry)
```

### Elixir

```elixir
def deps do
  [{:oamp_types, "~> 1.0.0"}]
end
```

```elixir
alias OampTypes.Knowledge.Entry

entry = Entry.new(
  "user-123",
  :correction,
  "Never use unwrap() — use ? operator instead",
  0.98,
  "session-42"
)

# Validate
errors = OampTypes.Validate.validate_knowledge_entry(entry)

# JSON encode
json = Entry.to_json(entry)
```

### Reference Server

```bash
cd reference/server
pip install -e ".[dev]"
python -m oamp_server
```

OpenAPI docs at `http://localhost:8000/docs` — 12 endpoints for knowledge CRUD, user models, search, and bulk export/import.

---

```
spec/v1/
  oamp-v1.md              Authoritative specification (RFC 2119)
  *.schema.json            JSON Schema definitions (draft-2020-12)
  examples/                Valid example documents

proto/oamp/v1/             Protocol Buffer definitions

reference/
  rust/                    Rust crate: oamp-types
  typescript/              npm package: @oamp/types
  python/                  PyPI package: oamp-types
  go/                      Go module: oamp-go
  elixir/                  Hex package: oamp_types
  server/                  FastAPI reference backend

scripts/
  protoc-gen.sh            Generate code from protobuf definitions

validators/
  validate.sh              CLI document validator
  test-fixtures/            Valid + invalid test documents

docs/
  guide-for-agents.md      Implement OAMP in your agent
  guide-for-backends.md    Build an OAMP-compliant backend
  security-guide.md        Encryption, GDPR/CCPA, threat model
```

---

## Integrate OAMP

<table>
<tr>
<td width="50%">

### For Agent Developers

Add memory portability to your agent:

1. **Export** — map internal types to OAMP JSON
2. **Import** — parse OAMP JSON into internal types
3. **Validate** — ensure compliance with the schema

[Read the Agent Guide →](docs/guide-for-agents.md)

</td>
<td width="50%">

### For Backend Developers

Build an OAMP-compliant memory store:

- 10 REST endpoints (knowledge CRUD, user model, export/import)
- Encryption at rest (mandatory)
- Search (FTS, vector, or hybrid — your choice)

[Read the Backend Guide →](docs/guide-for-backends.md)

</td>
</tr>
</table>

---

## Specification

| | |
|:---|:---|
| **Current version** | v1.0.0 |
| **Schema format** | JSON Schema (draft-2020-12) + Protocol Buffers |
| **Compliance language** | RFC 2119 (MUST, SHOULD, MAY) |
| **Full spec** | [spec/v1/oamp-v1.md](spec/v1/oamp-v1.md) |

### Planned for v2.0

Based on community feedback:
- Session outcomes (structured task records)
- Skill metrics (execution statistics)
- Work patterns (activity timing, tool preferences)
- Streaming API for real-time memory sync

---

## Contributing

We welcome contributions:

1. Read the [spec](spec/v1/oamp-v1.md) before proposing changes
2. Add test fixtures for schema changes
3. Update both Rust and TypeScript reference implementations
4. Include all reference implementations (Rust, TypeScript, Python, Go, Elixir)
5. Follow existing code style

---

<div align="center">

### Contact

For questions, partnerships, or feedback

**contact@dthink.ai**

---

**MIT License** — [Deep Thinking](https://dthink.ai)

</div>
