# Open Agent Memory Protocol (OAMP)

An open standard for storing, exchanging, and querying memory data between AI agents and memory backends.

## What is OAMP?

OAMP defines:

- **JSON schemas** for agent memory documents (knowledge entries, user models)
- **A REST API contract** for memory backends
- **Reference implementations** in Rust and TypeScript
- **Privacy and security requirements** that compliant implementations must meet

## Quick Start

```bash
# Validate a document against the schema
npm install -g ajv-cli
./validators/validate.sh spec/v1/examples/knowledge-entry.json

# Use from Rust
cargo add oamp-types

# Use from TypeScript
npm install @oamp/types
```

## Repository Structure

```
spec/v1/              -- JSON schemas and authoritative spec
proto/oamp/v1/        -- Protocol Buffer definitions
reference/rust/       -- Rust reference crate (oamp-types)
reference/typescript/ -- TypeScript reference package (@oamp/types)
validators/           -- CLI validator and test fixtures
docs/                 -- Guides for agents, backends, and security
```

## Spec Version

Current: **v1.0.0**

## License

Apache 2.0 -- see [LICENSE](LICENSE).
