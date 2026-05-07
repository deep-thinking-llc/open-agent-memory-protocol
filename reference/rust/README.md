# Open Agent Memory Protocol — Rust Reference

Rust types for the [Open Agent Memory Protocol (OAMP)](https://github.com/deep-thinking-llc/open-agent-memory-protocol) knowledge documents in v1.0.0, v1.1.0, and the additive v1.2.0 / v1.3.0 governed-memory draft lines.

Built on `serde` for serialization, `chrono` for timestamps, and `uuid` for identifiers.

## Installation

```toml
[dependencies]
oamp-types = "1.0"
```

## Quick Start

```rust
use oamp_types::{KnowledgeEntry, KnowledgeCategory, KnowledgeStore, UserModel,
                 CommunicationProfile, ExpertiseLevel, ExpertiseDomain};

// Create a knowledge entry
let entry = KnowledgeEntry::new(
    "user-123",
    KnowledgeCategory::Correction,
    "Always use proper error handling, even in examples",
    0.98,
    "sess-003",
);

// Serialize to JSON (optional fields excluded when None)
let json = serde_json::to_string_pretty(&entry).unwrap();

// Deserialize from JSON
let parsed: KnowledgeEntry = serde_json::from_str(&json).unwrap();

// Create a user model
let mut model = UserModel::new("user-123");
model.communication = Some(CommunicationProfile {
    verbosity: -0.6,
    formality: 0.2,
    prefers_examples: true,
    prefers_explanations: false,
    languages: vec!["en".into(), "ja".into()],
});
model.expertise.push(ExpertiseDomain {
    domain: "rust".into(),
    level: ExpertiseLevel::Expert,
    confidence: 0.95,
    evidence_sessions: vec!["s1".into()],
    last_observed: None,
});

// Bulk export
let store = KnowledgeStore::new("user-123", vec![entry]);
```

## Governed Memory

`KnowledgeEntry` and `KnowledgeStore` now support the additive governed-memory fields reused by both the v1.2 and v1.3 drafts:
- `provenance` for multi-source lineage
- `governance` for sensitivity classes, labels, and handling hints

Set `entry.oamp_version = "1.2.0".to_string()` or `"1.3.0".to_string()` when producing governed-memory documents.

## Types

### `KnowledgeEntry` — a discrete piece of information about a user

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `oamp_version` | `String` | ✅ | Protocol version (default `"1.0.0"`) |
| `type` | `String` | ✅ | Discriminator, `"knowledge_entry"` |
| `id` | `String` | ✅ | UUID v4 (auto-generated in `new()`) |
| `user_id` | `String` | ✅ | User identifier |
| `category` | `KnowledgeCategory` | ✅ | Enum: `Fact`, `Preference`, `Pattern`, `Correction` |
| `content` | `String` | ✅ | Natural language knowledge |
| `confidence` | `f32` | ✅ | 0.0–1.0 |
| `source` | `KnowledgeSource` | ✅ | Provenance info (session_id, agent_id, timestamp) |
| `provenance` | `Option<Provenance>` | ❌ | Extended multi-source lineage |
| `governance` | `Option<Governance>` | ❌ | Governed-memory metadata |
| `decay` | `Option<KnowledgeDecay>` | ❌ | Temporal decay params |
| `tags` | `Vec<String>` | ❌ | Free-form tags |
| `metadata` | `serde_json::Map` | ❌ | Vendor extensions |

### `KnowledgeStore` — bulk export/import collection

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `oamp_version` | `String` | ✅ | Protocol version |
| `type` | `String` | ✅ | `"knowledge_store"` |
| `user_id` | `String` | ✅ | User identifier |
| `entries` | `Vec<KnowledgeEntry>` | ✅ | Collection of entries |
| `exported_at` | `DateTime<Utc>` | ✅ | Export timestamp |
| `agent_id` | `Option<String>` | ❌ | Exporting agent identifier |

### `UserModel` — structured understanding of a user

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `oamp_version` | `String` | ✅ | Protocol version |
| `type` | `String` | ✅ | `"user_model"` |
| `user_id` | `String` | ✅ | User identifier |
| `model_version` | `u64` | ✅ | ≥ 1 |
| `updated_at` | `DateTime<Utc>` | ✅ | Last update timestamp |
| `communication` | `Option<CommunicationProfile>` | ❌ | Communication preferences |
| `expertise` | `Vec<ExpertiseDomain>` | ❌ | Domain expertise |
| `corrections` | `Vec<Correction>` | ❌ | Agent corrections |
| `stated_preferences` | `Vec<StatedPreference>` | ❌ | Declared preferences |
| `metadata` | `serde_json::Map` | ❌ | Vendor extensions |

### Enums

```rust
#[derive(Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum KnowledgeCategory {
    Fact,
    Preference,
    Pattern,
    Correction,
}

#[derive(Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ExpertiseLevel {
    Novice,
    Intermediate,
    Advanced,
    Expert,
}
```

## Validation

The `validate` module provides functions that return `Result<(), Vec<String>>`:

```rust
use oamp_types::validate;

let entry = KnowledgeEntry::new("user-1", KnowledgeCategory::Fact, "Valid", 0.5, "sess-1");

match validate::validate_knowledge_entry(&entry) {
    Ok(()) => println!("Valid!"),
    Err(errors) => {
        for e in &errors {
            eprintln!("Validation error: {}", e);
        }
    }
}
```

Validation checks:
- Required fields are present
- knowledge `oamp_version` is `"1.0.0"`, `"1.1.0"`, `"1.2.0"`, or `"1.3.0"`
- `type` matches the expected discriminator
- `confidence` is in `[0.0, 1.0]`
- Communication profile ranges (`verbosity`, `formality`) are in `[-1.0, 1.0]`
- Expertise confidence is in `[0.0, 1.0]`
- Required nested fields (e.g. `source.session_id`)
- `provenance.sources` is non-empty when present

## Serialization

All types derive `Serialize` and `Deserialize` from serde. Optional fields use
`#[serde(skip_serializing_if = "Option::is_none")]` to produce spec-compliant
JSON output that omits unset optional fields.

```rust
// Serialize
let json = serde_json::to_string_pretty(&entry)?;

// Deserialize
let parsed: KnowledgeEntry = serde_json::from_str(&json)?;
```

## Server Integration

OAMP knowledge entries and user models are exchanged with a server over HTTP.
Use any HTTP client library (e.g. `reqwest`) to POST and GET data:

```rust
use oamp_types::KnowledgeEntry;

// POST a serialized entry
let json = serde_json::to_string(&entry)?;
let response = reqwest::Client::new()
    .post("http://localhost:8000/v1/knowledge")
    .header("Content-Type", "application/json")
    .body(json)
    .send()
    .await?;

// GET and deserialize the response
let response = reqwest::get(format!("http://localhost:8000/v1/knowledge/{}", entry.id)).await?;
let fetched: KnowledgeEntry = response.json().await?;
```

The server encrypts all content fields at rest using AES-256-GCM (spec §8.1.1).
Encryption is transparent to the client — you send and receive plaintext JSON.

Key rotation (`POST /v1/admin/keys/rotate`), audit logging, and zeroization on
delete are handled server-side without SDK involvement.

### Running the Reference Server

```bash
# From the reference/server/ directory
python -m oamp_server
# Or with Docker
docker compose up
```

For a full server reference, see:
- [Server README](https://github.com/deep-thinking-llc/open-agent-memory-protocol/tree/main/reference/server)
- [Compliance Test Suite](https://github.com/deep-thinking-llc/open-agent-memory-protocol/tree/main/reference/compliance)

## Tests

```bash
cd reference/rust
cargo test
```

Tests include round-trip serialization, validation, and parsing of spec example files.

## License

MIT
