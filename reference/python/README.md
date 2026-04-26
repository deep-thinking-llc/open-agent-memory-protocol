# oamp-types

Python types for the [Open Agent Memory Protocol (OAMP)](https://github.com/deep-thinking-llc/open-agent-memory-protocol) v1.0.0.

Built on [Pydantic v2](https://docs.pydantic.dev/) for validation and serialization.

## Install

```bash
pip install oamp-types
```

## Quick Start

```python
from oamp_types import (
    KnowledgeEntry,
    KnowledgeCategory,
    KnowledgeSource,
    KnowledgeStore,
    UserModel,
    CommunicationProfile,
    ExpertiseDomain,
    ExpertiseLevel,
    Correction,
    StatedPreference,
    validate_knowledge_entry,
    validate_knowledge_store,
    validate_user_model,
)

# Create a knowledge entry
entry = KnowledgeEntry(
    user_id="user-123",
    category=KnowledgeCategory.correction,
    content="Never use unwrap() — use ? operator instead",
    confidence=0.98,
    source=KnowledgeSource(session_id="session-42"),
)

# Validate
errors = validate_knowledge_entry(entry)
assert len(errors) == 0

# Serialize to JSON (exclude null optional fields for spec compliance)
json_str = entry.model_dump_json(exclude_none=True)

# Parse from dict or JSON
parsed = KnowledgeEntry.model_validate_json(json_str)

# Create a user model
model = UserModel(user_id="user-123")
model.communication = CommunicationProfile(
    verbosity=-0.6,
    formality=0.3,
    prefers_examples=True,
    prefers_explanations=False,
    languages=["en", "de"],
)
model.expertise.append(
    ExpertiseDomain(
        domain="rust",
        level=ExpertiseLevel.expert,
        confidence=0.95,
    )
)

# Bulk export
store = KnowledgeStore(user_id="user-123", entries=[entry])
```

## Serialization

Pydantic models support multiple serialization modes:

```python
# Exclude None values (matches Rust's skip_serializing_if = "Option::is_none")
json_str = entry.model_dump_json(exclude_none=True)

# Include all fields (useful for debugging)
json_str = entry.model_dump_json()

# Python dict output
d = entry.model_dump(exclude_none=True)
```

**Note:** For spec-compliant output, use `exclude_none=True` to omit optional
fields that are not set (e.g., `decay`, `agent_id`). This matches the behavior
of the Rust and TypeScript reference implementations.

## Validation

Two levels of validation are provided:

### Pydantic field validators (automatic)

Creating or parsing models through Pydantic automatically validates:
- Required fields must be present
- `oamp_version` must be `"1.0.0"`
- `type` must match the expected document type
- `confidence` must be in [0.0, 1.0]
- String fields must not be empty where required
- Unknown fields are rejected (`extra = "forbid"`)
- Ranges like `verbosity` (-1.0 to 1.0) and `formality` (-1.0 to 1.0)

### Semantic validation functions (for data bypassing Pydantic)

```python
from oamp_types import validate_knowledge_entry, validate_knowledge_store, validate_user_model

# Returns list of error strings; empty list means valid
errors = validate_knowledge_entry(entry)
if errors:
    raise ValueError(f"Validation failed: {errors}")
```

These functions validate data that may have been constructed via
`model_construct()` or loaded from untrusted sources where Pydantic's
field validators were bypassed.

## API

### `KnowledgeEntry`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `oamp_version` | `str` | ✅ | Defaults to `"1.0.0"` |
| `type` | `str` | ✅ | Defaults to `"knowledge_entry"` |
| `id` | `str` | ✅ | UUID v4, auto-generated |
| `user_id` | `str` | ✅ | User identifier |
| `category` | `KnowledgeCategory` | ✅ | `fact`, `preference`, `pattern`, `correction` |
| `content` | `str` | ✅ | Natural language knowledge |
| `confidence` | `float` | ✅ | 0.0–1.0 |
| `source` | `KnowledgeSource` | ✅ | Provenance info |
| `decay` | `KnowledgeDecay \| None` | ❌ | Temporal decay params |
| `tags` | `list[str]` | ❌ | Free-form tags |
| `metadata` | `dict[str, Any]` | ❌ | Vendor extensions |

### `UserModel`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `oamp_version` | `str` | ✅ | Defaults to `"1.0.0"` |
| `type` | `str` | ✅ | Defaults to `"user_model"` |
| `user_id` | `str` | ✅ | User identifier |
| `model_version` | `int` | ✅ | ≥ 1, defaults to `1` |
| `updated_at` | `datetime` | ✅ | Auto-set to now (UTC) |
| `communication` | `CommunicationProfile \| None` | ❌ | Communication preferences |
| `expertise` | `list[ExpertiseDomain]` | ❌ | Domain expertise |
| `corrections` | `list[Correction]` | ❌ | Agent corrections |
| `stated_preferences` | `list[StatedPreference]` | ❌ | Declared preferences |
| `metadata` | `dict[str, Any]` | ❌ | Vendor extensions |

## Python Version

Requires Python ≥ 3.9. Uses `str, Enum` pattern for category/level enums
(available since Python 3.11 as `StrEnum`, backported for 3.9 compatibility).

## License

MIT