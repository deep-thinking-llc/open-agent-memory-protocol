# Open Agent Memory Protocol — Go Reference

Go types for the Open Agent Memory Protocol (OAMP) v1.

## Installation

```bash
go get github.com/deep-thinking-llc/oamp-go
```

## Quick Start

```go
package main

import (
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

    // Validate it
    errors := oamp.ValidateKnowledgeEntry(entry)
    if len(errors) > 0 {
        fmt.Printf("Validation errors: %v\n", errors)
    }

    // Create a user model
    model := oamp.NewUserModel("user-123")
    fmt.Printf("User model version: %d\n", model.ModelVersion)
}
```

## Running Tests

```bash
cd reference/go
go test ./... -v
```

## Types

- `KnowledgeEntry` — a discrete piece of information about a user
- `KnowledgeStore` — bulk export/import collection
- `UserModel` — structured understanding of a user
- `KnowledgeCategory` — enum: `fact`, `preference`, `pattern`, `correction`
- `ExpertiseLevel` — enum: `novice`, `intermediate`, `advanced`, `expert`

## Validation

All types include `Validate*` functions that return a `[]string` of error messages:

```go
errors := oamp.ValidateKnowledgeEntry(entry)
errors := oamp.ValidateKnowledgeStore(store)
errors := oamp.ValidateUserModel(model)
```