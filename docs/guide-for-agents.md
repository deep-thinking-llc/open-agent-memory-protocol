# OAMP: Guide for Agent Implementors

## Overview

This guide explains how to add OAMP support to your AI agent framework. After implementing OAMP, your agent's memory will be portable — users can export it and import it into any other OAMP-compliant agent.

## What You Need to Implement

### 1. Export

Convert your agent's internal memory format to OAMP JSON documents.

**Minimum viable export:**
- Map your knowledge/facts/memories to `KnowledgeEntry` documents
- Set `category` based on the nature of each piece of knowledge
- Set `confidence` (even if you use a different internal scale — normalize to 0.0-1.0)
- Set `source.session_id` and `source.timestamp` for provenance

**Enhanced export (recommended):**
- Also export a `UserModel` with expertise domains and communication preferences
- Include `corrections` — these are the most valuable data for other agents

### 2. Import

Parse OAMP JSON documents into your agent's internal format.

**Key considerations:**
- Validate against the JSON Schema before processing
- Handle unknown categories gracefully (log a warning, skip the entry)
- Map OAMP `confidence` to your internal scoring system
- Preserve `source` metadata — don't claim imported knowledge as your own

### 3. Merge (Optional but Recommended)

When importing knowledge that conflicts with existing knowledge:
- **Confidence-based:** higher confidence wins
- **Recency-based:** more recent timestamp wins
- **Additive:** keep both, let the user resolve conflicts
- The spec does not mandate a merge strategy — choose what fits your agent's philosophy

## Example: Exporting from a Python Agent

```python
import json
from datetime import datetime, timezone

def export_to_oamp(agent_memories, user_id):
    entries = []
    for mem in agent_memories:
        entries.append({
            "oamp_version": "1.0.0",
            "type": "knowledge_entry",
            "id": str(uuid4()),
            "user_id": user_id,
            "category": map_category(mem.type),  # your mapping
            "content": mem.text,
            "confidence": mem.score / 100.0,  # normalize to 0-1
            "source": {
                "session_id": mem.session_id,
                "agent_id": "my-agent-v1",
                "timestamp": mem.created_at.isoformat(),
            },
        })
    
    return {
        "oamp_version": "1.0.0",
        "type": "knowledge_store",
        "user_id": user_id,
        "entries": entries,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "agent_id": "my-agent-v1",
    }
```

## Validation

Use the provided JSON Schema files to validate your output:

```bash
# CLI validator
./validators/validate.sh my-export.json

# Or in code (Rust)
use oamp_types::validate::validate_knowledge_entry;
let result = validate_knowledge_entry(&entry);

# Or in code (TypeScript)
import { KnowledgeEntry } from '@oamp/types';
KnowledgeEntry.parse(data); // throws on invalid
```

## Privacy Requirements

Your agent MUST:
- Encrypt exported OAMP documents if they contain sensitive content
- Include provenance (`source`) on every entry
- Never log the `content` field
- Support full export and deletion when the user requests it

See [security-guide.md](security-guide.md) for details.
