# Open Agent Memory Protocol — TypeScript Reference

TypeScript types and validators for the [Open Agent Memory Protocol (OAMP)](https://github.com/deep-thinking-llc/open-agent-memory-protocol) v1.0.0.

Built on [Zod](https://zod.dev/) schemas for runtime validation with automatic TypeScript type inference.

## Installation

```bash
npm install @deepthinking/oamp-types
```

## Quick Start

```typescript
import { KnowledgeEntry, KnowledgeCategory, KnowledgeSource } from '@deepthinking/oamp-types';

// Create a knowledge entry with Zod validation
const entry = KnowledgeEntry.parse({
  oamp_version: '1.0.0',
  type: 'knowledge_entry',
  id: crypto.randomUUID(),
  user_id: 'user-alice-123',
  category: 'correction',
  content: 'Always use proper error handling, even in examples',
  confidence: 0.98,
  source: {
    session_id: 'sess-003',
    timestamp: new Date().toISOString(),
  },
});

// JSON-serialize (exclude unset optional fields)
const json = JSON.stringify(entry);
```

The `KnowledgeEntry.parse()` call validates at runtime (via Zod) and returns a typed object. If validation fails, Zod throws a `ZodError` with structured error messages.

## User Model Example

```typescript
import { UserModel, CommunicationProfile, ExpertiseLevel } from '@deepthinking/oamp-types';

const model = UserModel.parse({
  oamp_version: '1.0.0',
  type: 'user_model',
  user_id: 'user-alice-123',
  model_version: 7,
  updated_at: new Date().toISOString(),
  communication: {
    verbosity: -0.6,
    formality: 0.2,
    prefers_examples: true,
    prefers_explanations: false,
    languages: ['en', 'ja'],
  },
  expertise: [
    {
      domain: 'rust',
      level: 'expert',
      confidence: 0.95,
      evidence_sessions: ['sess-001'],
      last_observed: new Date().toISOString(),
    },
  ],
});
```

## Types

### `KnowledgeEntry` — a discrete piece of information about a user

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `oamp_version` | `string` | ✅ | Protocol version (default `"1.0.0"`) |
| `type` | `"knowledge_entry"` | ✅ | Document type discriminator |
| `id` | `string` | ✅ | UUID v4 |
| `user_id` | `string` | ✅ | User identifier |
| `category` | `KnowledgeCategory` | ✅ | `"fact"`, `"preference"`, `"pattern"`, `"correction"` |
| `content` | `string` | ✅ | Natural language knowledge |
| `confidence` | `number` | ✅ | 0.0–1.0 |
| `source` | `KnowledgeSource` | ✅ | Provenance info |
| `decay` | `KnowledgeDecay \| undefined` | ❌ | Temporal decay parameters |
| `tags` | `string[]` | ❌ | Free-form tags |
| `metadata` | `Record<string, unknown>` | ❌ | Vendor extensions |

### `UserModel` — structured understanding of a user

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `oamp_version` | `string` | ✅ | Protocol version |
| `type` | `"user_model"` | ✅ | Document type discriminator |
| `user_id` | `string` | ✅ | User identifier |
| `model_version` | `number` | ✅ | ≥ 1 |
| `updated_at` | `string` (ISO 8601) | ✅ | Last update timestamp |
| `communication` | `CommunicationProfile \| undefined` | ❌ | Communication preferences |
| `expertise` | `ExpertiseDomain[]` | ❌ | Domain expertise |
| `corrections` | `Correction[]` | ❌ | Agent corrections |
| `stated_preferences` | `StatedPreference[]` | ❌ | Declared preferences |
| `metadata` | `Record<string, unknown>` | ❌ | Vendor extensions |

### Enums

```typescript
enum KnowledgeCategory {
  Fact = "fact",
  Preference = "preference",
  Pattern = "pattern",
  Correction = "correction",
}

enum ExpertiseLevel {
  Novice = "novice",
  Intermediate = "intermediate",
  Advanced = "advanced",
  Expert = "expert",
}
```

## Validation

All schemas are built with Zod and validate on `parse()`. Validation catches:
- Required field presence
- `oamp_version` must be `"1.0.0"`
- `type` must match the expected discriminator
- `confidence` in [0.0, 1.0]
- UUID v4 format for `id`
- `verbosity` and `formality` in [-1.0, 1.0]
- Expertise confidence in [0.0, 1.0]
- Required `source.session_id`
- Unknown fields rejected (`z.object().strict()`)

```typescript
import { KnowledgeEntry } from '@deepthinking/oamp-types';

try {
  const entry = KnowledgeEntry.parse(data);
  // Valid — entry is fully typed
} catch (err) {
  if (err instanceof ZodError) {
    console.error(err.errors); // Structured validation errors
  }
}
```

## Server Integration

The OAMP reference server stores knowledge entries and user models over HTTP.
Use any HTTP client to POST and GET data:

```typescript
// POST a validated entry
const response = await fetch('http://localhost:8000/v1/knowledge', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(entry),
});

// GET and validate response
const response = await fetch('http://localhost:8000/v1/knowledge/' + entry.id);
const data = await response.json();
const fetched = KnowledgeEntry.parse(data); // Re-validate with Zod
```

The server encrypts all content fields at rest using AES-256-GCM (spec §8.1.1).
Encryption is transparent to the client — you send and receive plaintext JSON.

Key rotation (`POST /v1/admin/keys/rotate`), audit logging, and zeroization on
delete are also handled server-side without SDK involvement.

For a full server reference, see:
- [Server README](https://github.com/deep-thinking-llc/open-agent-memory-protocol/tree/main/reference/server)
- [Compliance Test Suite](https://github.com/deep-thinking-llc/open-agent-memory-protocol/tree/main/reference/compliance)

## License

MIT
