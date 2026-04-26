# Open Agent Memory Protocol — Elixir Reference

Elixir types for the Open Agent Memory Protocol (OAMP) v1.

## Installation

Add to your `mix.exs`:

```elixir
def deps do
  [
    {:oamp_types, "~> 1.0.0"}
  ]
end
```

## Quick Start

```elixir
# Create a knowledge entry
entry = OampTypes.Knowledge.Entry.new(
  "user-123",
  :preference,
  "User prefers concise answers",
  0.85,
  "sess-001"
)

# Validate it
errors = OampTypes.Validate.validate_knowledge_entry(entry)

# Encode to JSON
json = OampTypes.Knowledge.Entry.to_json(entry)

# Decode from JSON
decoded = OampTypes.Knowledge.Entry.from_json(json)

# Create a user model
model = OampTypes.UserModel.Model.new("user-123")
```

## Running Tests

```bash
cd reference/elixir
mix deps.get
mix test
```

## Types

- `OampTypes.Knowledge.Entry` — a discrete piece of information about a user
- `OampTypes.Knowledge.Store` — bulk export/import collection
- `OampTypes.UserModel.Model` — structured understanding of a user
- `OampTypes.KnowledgeCategory` — enum: `:fact`, `:preference`, `:pattern`, `:correction`
- `OampTypes.ExpertiseLevel` — enum: `:novice`, `:intermediate`, `:advanced`, `:expert`

## Validation

All types include validation functions that return a list of error strings:

```elixir
errors = OampTypes.Validate.validate_knowledge_entry(entry)
errors = OampTypes.Validate.validate_knowledge_store(store)
errors = OampTypes.Validate.validate_user_model(model)
```