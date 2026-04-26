# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Initial v1.0.0 spec: KnowledgeEntry, KnowledgeStore, UserModel schemas
- JSON Schema definitions (draft-2020-12)
- Protocol Buffer definitions
- Rust reference implementation (oamp-types crate)
- TypeScript reference implementation (@oamp/types package)
- Python reference implementation (oamp-types package)
- Go reference implementation (oamp-go module)
- Elixir reference implementation (oamp_types Hex package)
- Protobuf code generation script (scripts/protoc-gen.sh)
- CI workflow with caching, Python version matrix, and all 5 language test suites
- Release automation workflow (publish to crates.io, npm, PyPI on tags)
- Root .gitignore (Python, Rust, TypeScript, Go, Elixir, IDE/OS files)
- Removed tracked Rust build artifacts from git
- Validator CLI and test fixtures
- Documentation: agent guide, backend guide, security guide
