# Open Agent Memory Protocol — Elixir Reference

Elixir types for the [Open Agent Memory Protocol (OAMP)](https://github.com/deep-thinking-llc/open-agent-memory-protocol) knowledge documents in v1.0.0, v1.1.0, and the additive v1.2.0 / v1.3.0 governed-memory draft lines.

## Installation

Add to your `mix.exs`:

```elixir
def deps do
  [
    {:oamp_types, "~> 1.0.0"}
  ]
end
```

Then fetch: `mix deps.get`

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
if errors == [] do
  IO.puts("Valid!")
else
  IO.inspect(errors)
end

# Encode to JSON
json = OampTypes.Knowledge.Entry.to_json(entry)

# Decode from JSON
decoded = OampTypes.Knowledge.Entry.from_json(json)

# Create a user model
model = OampTypes.UserModel.Model.new("user-123")

# Set communication profile
model = %{model | communication: %OampTypes.UserModel.CommunicationProfile{
  verbosity: -0.6,
  formality: 0.2,
  prefers_examples: true,
  prefers_explanations: false,
  languages: ["en", "ja"],
}}
```

## Governed Memory

`OampTypes.Knowledge.Entry` and `OampTypes.Knowledge.Store` accept the additive governed-memory fields reused by the v1.2 and v1.3 drafts:
- `provenance` for multi-source lineage
- `governance` for sensitivity classes, labels, and handling hints

Use `oamp_version: "1.2.0"` or `"1.3.0"` when producing governed-memory documents.

## Types

### `OampTypes.Knowledge.Entry` — a discrete piece of information about a user

| Field | Elixir Type | Required | Description |
|-------|-------------|----------|-------------|
| `oamp_version` | `String.t` | ✅ | Protocol version |
| `type` | `String.t` | ✅ | `"knowledge_entry"` |
| `id` | `String.t` | ✅ | UUID v4 (auto-generated) |
| `user_id` | `String.t` | ✅ | User identifier |
| `category` | `KnowledgeCategory` | ✅ | `:fact`, `:preference`, `:pattern`, `:correction` |
| `content` | `String.t` | ✅ | Natural language knowledge |
| `confidence` | `float` | ✅ | 0.0–1.0 |
| `source` | `KnowledgeSource.t` | ✅ | Provenance info |
| `provenance` | `Provenance.t \| nil` | ❌ | Extended multi-source lineage |
| `governance` | `Governance.t \| nil` | ❌ | Governed-memory metadata |
| `decay` | `KnowledgeDecay.t \| nil` | ❌ | Temporal decay params |
| `tags` | `[String.t]` | ❌ | Free-form tags |
| `metadata` | `map` | ❌ | Vendor extensions |

### `OampTypes.UserModel.Model` — structured understanding of a user

| Field | Elixir Type | Required | Description |
|-------|-------------|----------|-------------|
| `oamp_version` | `String.t` | ✅ | Protocol version |
| `type` | `String.t` | ✅ | `"user_model"` |
| `user_id` | `String.t` | ✅ | User identifier |
| `model_version` | `non_neg_integer` | ✅ | ≥ 1 |
| `updated_at` | `DateTime.t` | ✅ | Last update timestamp |
| `communication` | `CommunicationProfile.t \| nil` | ❌ | Communication preferences |
| `expertise` | `[ExpertiseDomain.t]` | ❌ | Domain expertise |
| `corrections` | `[Correction.t]` | ❌ | Agent corrections |
| `stated_preferences` | `[StatedPreference.t]` | ❌ | Declared preferences |
| `metadata` | `map` | ❌ | Vendor extensions |

### Enums

```elixir
@type knowledge_category :: :fact | :preference | :pattern | :correction
@type expertise_level :: :novice | :intermediate | :advanced | :expert
```

## Validation

All types include validation functions that return a list of error strings:

```elixir
errors = OampTypes.Validate.validate_knowledge_entry(entry)
errors = OampTypes.Validate.validate_knowledge_store(store)
errors = OampTypes.Validate.validate_user_model(model)
```

An empty list means valid. Validation checks:
- Required field presence
- Knowledge `oamp_version` is `"1.0.0"`, `"1.1.0"`, `"1.2.0"`, or `"1.3.0"`
- `confidence` in [0.0, 1.0]
- Communication profiles ranges
- Required `source.session_id`
- `provenance.sources` must be non-empty when present

## Server Integration

Use the SDK to construct documents, then send them to the reference server over HTTP:

```elixir
# POST a knowledge entry
json = OampTypes.Knowledge.Entry.to_json(entry)
{:ok, %Finch.Response{status: 201, body: body}} =
  Finch.build(:post, "http://localhost:8000/v1/knowledge",
    [{"content-type", "application/json"}],
    json
  )
  |> Finch.request(OampTypes.Finch)

# GET and decode
{:ok, %Finch.Response{status: 200, body: body}} =
  Finch.build(:get, "http://localhost:8000/v1/knowledge/#{entry.id}")
  |> Finch.request(OampTypes.Finch)

decoded = OampTypes.Knowledge.Entry.from_json(body)
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
cd reference/elixir
mix deps.get
mix test
```

## License

MIT
