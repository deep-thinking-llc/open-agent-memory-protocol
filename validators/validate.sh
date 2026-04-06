#!/bin/bash
# OAMP Document Validator
# Usage: ./validate.sh <document.json> [schema-name]
# schema-name: knowledge-entry, knowledge-store, user-model (auto-detected from "type" field)

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SPEC_DIR="$SCRIPT_DIR/../spec/v1"

if [ -z "$1" ]; then
    echo "Usage: $0 <document.json> [schema-name]"
    exit 1
fi

DOC="$1"
if [ ! -f "$DOC" ]; then
    echo "Error: File not found: $DOC"
    exit 1
fi

# Auto-detect schema from "type" field
if [ -z "$2" ]; then
    TYPE=$(python3 -c "import json; print(json.load(open('$DOC'))['type'])" 2>/dev/null || echo "")
    case "$TYPE" in
        knowledge_entry) SCHEMA="knowledge-entry" ;;
        knowledge_store) SCHEMA="knowledge-store" ;;
        user_model) SCHEMA="user-model" ;;
        *) echo "Error: Cannot detect type. Specify schema name."; exit 1 ;;
    esac
else
    SCHEMA="$2"
fi

SCHEMA_FILE="$SPEC_DIR/$SCHEMA.schema.json"
if [ ! -f "$SCHEMA_FILE" ]; then
    echo "Error: Schema not found: $SCHEMA_FILE"
    exit 1
fi

# Try ajv first, fall back to python
if command -v ajv &>/dev/null; then
    ajv validate -s "$SCHEMA_FILE" -d "$DOC" --spec=draft2020
elif command -v python3 &>/dev/null; then
    python3 -c "
import json, sys
try:
    from jsonschema import validate, Draft202012Validator
    with open('$SCHEMA_FILE') as sf, open('$DOC') as df:
        schema = json.load(sf)
        doc = json.load(df)
        Draft202012Validator(schema).validate(doc)
        print('Valid: $DOC matches $SCHEMA schema')
except ImportError:
    print('Warning: jsonschema not installed. Install: pip install jsonschema')
    sys.exit(1)
except Exception as e:
    print(f'Invalid: {e}')
    sys.exit(1)
"
else
    echo "Error: Neither ajv nor python3 available"
    exit 1
fi
