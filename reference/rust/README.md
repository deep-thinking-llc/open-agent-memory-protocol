# Open Agent Memory Protocol — Rust Reference

Rust types for the [Open Agent Memory Protocol (OAMP)](https://github.com/deep-thinking-llc/open-agent-memory-protocol) v1.0.0.

Built on `serde` for serialization, `chrono` for timestamps, and `uuid` for identifiers.

## Installation

```toml
[dependencies]
oamp-types = "1.0"
```

## Quick Start

```rust
use oamp_types::{KnowledgeEntry, KnowledgeCategory, KnowledgeStore, UserModel, CommunicationProfile, ExpertiseLevel, ExpertiseDomain};

fn main() {
    // Create a knowledge entry
    let entry = KnowledgeEntry::new(
        "user-123",
        KnowledgeCategory::Correction,
        "Always use proper error handling, even in examples",
        0.98,
        "sess-003",
    );

    // Serialize to JSON
    let json = serde_json::to_string_pretty(&entry).unwrap();
    println!("{}", json);

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

    // Create a knowledge store for bulk export
    let store = KnowledgeStore::new("user-123", vec![entry]);
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
- `oamp_version` is `"1.0.0"`
- `type` matches the expected document type
- `confidence` is in `[0.0, 1.0]`
- Communication profile ranges (`verbosity`, `formality`) are in `[-1.0, 1.0]`
- Expertise confidence is in `[0.0, 1.0]`
- Required nested fields (e.g. `source.session_id`)

## Types

### `KnowledgeEntry` — a discrete piece of information about a user

| Field       | Type                       | Required | Description                    |
|-------------|----------------------------|----------|--------------------------------|
| `oamp_version` | `String`                | ✅       | Protocol version               |
| `type`      | `String`                    | ✅       | Discriminator, `"knowledge_entry"` |
| `id`        | `String`                    | ✅       | UUID v4                        |
| `user_id`   | `String`                    | ✅       | User identifier                |
| `category`  | `KnowledgeCategory`         | ✅       | Enum: `Fact`, `Preference`, `Pattern`, `Correction` |
| `content`   | `String`                    | ✅       | Natural language knowledge      |
| `confidence`| `f32`                       | ✅       | 0.0–1.0                        |
| `source`    | `KnowledgeSource`           | ✅       | Provenance info                |
| `decay`     | `Option<KnowledgeDecay>`    | ❌       | Temporal decay params          |
| `tags`      | `Vec<String>`               | ❌       | Free-form tags                 |
| `metadata`  | `serde_json::Map`           | ❌       | Vendor extensions              |

### `KnowledgeStore` — bulk export/import collection

| Field       | Type                       | Required | Description               |
|-------------|----------------------------|----------|---------------------------|
| `oamp_version` | `String`                | ✅       | Protocol version          |
| `type`      | `String`                    | ✅       | `"knowledge_store"`       |
| `user_id`   | `String`                    | ✅       | User identifier           |
| `entries`   | `Vec<KnowledgeEntry>`       | ✅       | Collection of entries     |
| `exported_at` | `DateTime<Utc>`           | ✅       | Export timestamp          |
| `agent_id`  | `Option<String>`            | ❌       | Exporting agent           |

### `UserModel` — structured understanding of a user

| Field                 | Type                        | Required | Description            |
|-----------------------|-----------------------------|----------|------------------------|
| `oamp_version`        | `String`                    | ✅       | Protocol version       |
| `type`                | `String`                    | ✅       | `"user_model"`         |
| `user_id`             | `String`                    | ✅       | User identifier        |
| `model_version`       | `u64`                       | ✅       | ≥ 1                    |
| `updated_at`          | `DateTime<Utc>`             | ✅       | Last update timestamp  |
| `communication`       | `Option<CommunicationProfile>` | ❌    | Communication prefs    |
| `expertise`           | `Vec<ExpertiseDomain>`      | ❌       | Domain expertise       |
| `corrections`         | `Vec<Correction>`           | ❌       | Agent corrections      |
| `stated_preferences`  | `Vec<StatedPreference>`     | ❌       | Declared preferences   |
| `metadata`            | `serde_json::Map`           | ❌       | Vendor extensions      |

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

## Serialization

All types derive `Serialize` and `Deserialize` from serde. Optional fields use
`#[serde(skip_serializing_if = "Option::is_none")]` to produce spec-compliant JSON
output that omits unset optional fields.

```rust
// Serialize
let json = serde_json::to_string_pretty(&entry)?;

// Deserialize
let parsed: KnowledgeEntry = serde_json::from_str(&json)?;
```

## License

MIT
