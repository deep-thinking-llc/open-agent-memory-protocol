#!/usr/bin/env bash
# Generate code from OAMP protobuf definitions.
#
# Prerequisites:
#   - protoc (protobuf compiler)
#   - protoc-gen-go (Go protobuf plugin)
#   - grpcio-tools (Python protobuf tools)
#   - protoc-gen-ts (TypeScript protobuf plugin)
#
# Usage:
#   ./scripts/protoc-gen.sh          # generate all languages
#   ./scripts/protoc-gen.sh go       # generate Go only
#   ./scripts/protoc-gen.sh python   # generate Python only
#   ./scripts/protoc-gen.sh ts       # generate TypeScript only

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROTO_DIR="${REPO_ROOT}/proto"

# Languages to generate (default: all)
LANGS="${*:-go python ts}"

echo "Generating protobuf code for: ${LANGS}"
echo "Proto dir: ${PROTO_DIR}"

for LANG in ${LANGS}; do
  case "${LANG}" in
    go)
      OUT_DIR="${REPO_ROOT}/reference/go/proto"
      mkdir -p "${OUT_DIR}/oamp/v1"
      echo "  → Go: ${OUT_DIR}/oamp/v1"
      protoc \
        --proto_path="${PROTO_DIR}" \
        --go_out="${OUT_DIR}" \
        --go_opt=paths=source_relative \
        "${PROTO_DIR}/oamp/v1/knowledge.proto" \
        "${PROTO_DIR}/oamp/v1/user_model.proto"
      ;;

    python)
      OUT_DIR="${REPO_ROOT}/reference/python/src/oamp_types/proto"
      mkdir -p "${OUT_DIR}/oamp/v1"
      echo "  → Python: ${OUT_DIR}/oamp/v1"
      python3 -m grpc_tools.protoc \
        --proto_path="${PROTO_DIR}" \
        --python_out="${OUT_DIR}" \
        --pyi_out="${OUT_DIR}" \
        "${PROTO_DIR}/oamp/v1/knowledge.proto" \
        "${PROTO_DIR}/oamp/v1/user_model.proto"
      # Fix Python imports to work with the package structure
      INIT_DIR="${OUT_DIR}/oamp/v1"
      touch "${OUT_DIR}/__init__.py" "${OUT_DIR}/oamp/__init__.py" "${INIT_DIR}/__init__.py"
      ;;

    ts)
      OUT_DIR="${REPO_ROOT}/reference/typescript/src/proto"
      mkdir -p "${OUT_DIR}/oamp/v1"
      echo "  → TypeScript: ${OUT_DIR}/oamp/v1"
      protoc \
        --proto_path="${PROTO_DIR}" \
        --ts_out="${OUT_DIR}" \
        "${PROTO_DIR}/oamp/v1/knowledge.proto" \
        "${PROTO_DIR}/oamp/v1/user_model.proto"
      ;;

    *)
      echo "  ⚠ Unknown language: ${LANG} (skipping)"
      ;;
  esac
done

echo "✅ Protobuf code generation complete"