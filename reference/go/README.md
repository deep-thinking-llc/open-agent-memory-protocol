# Open Agent Memory Protocol — Go Reference

Go types for the [Open Agent Memory Protocol (OAMP)](https://github.com/deep-thinking-llc/open-agent-memory-protocol) v1.0.0.

## Installation

The Go SDK lives in the main spec repository at `reference/go/`. To use it in your project:

```bash
# Clone the repo and vendor or use a replace directive
# The module path is github.com/deep-thinking-llc/oamp-go
```

## Quick Start

```go
package main

import (
    "encoding/json"
    "fmt"
    oamp "github.com/deep-thinking-llc/oamp-go"
)

func main() {
    // Create a knowledge entry
    entry := oamp.NewKnowledgeEntry(
        "user-123",
        oamp.KnowledgeCategoryPreference,
        "User prefers concise answers",
        0.85,
        "sess-001",
    )

    // Validate
    errors := oamp.ValidateKnowledgeEntry(entry)
    if len(errors) > 0 {
        fmt.Printf("Validation errors: %v\n", errors)
    }

    // Serialize to JSON
    json, _ := json.MarshalIndent(entry, "", "  ")
    fmt.Println(string(json))

    // Create a user model
    model := oamp.NewUserModel("user-123")
    model.Communication = &oamp.CommunicationProfile{
        Verbosity: -0.6,
        Formality: 0.2,
        PrefersExamples: true,
        PrefersExplanations: false,
        Languages: []string{"en", "ja"},
    }

    // Bulk export
    store := oamp.NewKnowledgeStore("user-123", []oamp.KnowledgeEntry{*entry})
}
```

## Types

### `KnowledgeEntry` — a discrete piece of information about a user

| Field | Go Type | Required | Description |
|-------|---------|----------|-------------|
| `OAMPVersion` | `string` | ✅ | Protocol version |
| `Type` | `string` | ✅ | `"knowledge_entry"` |
| `ID` | `string` | ✅ | UUID v4 (auto-generated) |
| `UserID` | `string` | ✅ | User identifier |
| `Category` | `KnowledgeCategory` | ✅ | Enum: `fact`, `preference`, `pattern`, `correction` |
| `Content` | `string` | ✅ | Natural language knowledge |
| `Confidence` | `float64` | ✅ | 0.0–1.0 |
| `Source` | `KnowledgeSource` | ✅ | Provenance info |
| `Decay` | `*KnowledgeDecay` | ❌ | Temporal decay params |
| `Tags` | `[]string` | ❌ | Free-form tags |
| `Metadata` | `map[string]any` | ❌ | Vendor extensions |

### `UserModel` — structured understanding of a user

| Field | Go Type | Required | Description |
|-------|---------|----------|-------------|
| `OAMPVersion` | `string` | ✅ | Protocol version |
| `Type` | `string` | ✅ | `"user_model"` |
| `UserID` | `string` | ✅ | User identifier |
| `ModelVersion` | `uint64` | ✅ | ≥ 1 |
| `UpdatedAt` | `time.Time` | ✅ | Last update timestamp |
| `Communication` | `*CommunicationProfile` | ❌ | Communication preferences |
| `Expertise` | `[]ExpertiseDomain` | ❌ | Domain expertise |
| `Corrections` | `[]Correction` | ❌ | Agent corrections |
| `StatedPreferences` | `[]StatedPreference` | ❌ | Declared preferences |
| `Metadata` | `map[string]any` | ❌ | Vendor extensions |

### Enums

```go
type KnowledgeCategory int
const (
    KnowledgeCategoryFact KnowledgeCategory = iota
    KnowledgeCategoryPreference
    KnowledgeCategoryPattern
    KnowledgeCategoryCorrection
)

type ExpertiseLevel int
const (
    ExpertiseLevelNovice ExpertiseLevel = iota
    ExpertiseLevelIntermediate
    ExpertiseLevelAdvanced
    ExpertiseLevelExpert
)
```

## Validation

All types include `Validate*` functions that return `[]string` of error messages:

```go
errors := oamp.ValidateKnowledgeEntry(entry)
errors := oamp.ValidateKnowledgeStore(store)
errors := oamp.ValidateUserModel(model)
```

An empty slice means valid. Validation checks:
- Required field presence
- `confidence` in [0.0, 1.0]
- Communication ranges (`verbosity`, `formality`) in [-1.0, 1.0]
- UUID validity
- Required nested fields

## Serialization

All types can be serialized to/from JSON using the standard `encoding/json` package:

```go
import "encoding/json"

// Serialize
json, err := json.Marshal(entry)

// Deserialize
var parsed oamp.KnowledgeEntry
err = json.Unmarshal(data, &parsed)
```

## Server Integration

Use the SDK to construct documents, then send them to the reference server over HTTP:

```go
import (
    "bytes"
    "encoding/json"
    "net/http"
)

// POST a knowledge entry
body, _ := json.Marshal(entry)
resp, _ := http.Post(
    "http://localhost:8000/v1/knowledge",
    "application/json",
    bytes.NewReader(body),
)
defer resp.Body.Close()

// GET a knowledge entry
resp, _ = http.Get("http://localhost:8000/v1/knowledge/" + entry.ID)
var fetched oamp.KnowledgeEntry
json.NewDecoder(resp.Body).Decode(&fetched)
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
cd reference/go
go test ./... -v
```

## License

MIT
