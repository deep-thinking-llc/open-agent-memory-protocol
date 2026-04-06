use crate::{KnowledgeEntry, KnowledgeStore, UserModel};

/// Validate a KnowledgeEntry.
pub fn validate_knowledge_entry(entry: &KnowledgeEntry) -> Result<(), Vec<String>> {
    let mut errors = Vec::new();

    if entry.oamp_version.is_empty() {
        errors.push("oamp_version is required".into());
    }
    if entry.entry_type != "knowledge_entry" {
        errors.push(format!("type must be 'knowledge_entry', got '{}'", entry.entry_type));
    }
    if entry.id.is_empty() {
        errors.push("id is required".into());
    }
    if entry.user_id.is_empty() {
        errors.push("user_id is required".into());
    }
    if entry.content.is_empty() {
        errors.push("content is required".into());
    }
    if entry.confidence < 0.0 || entry.confidence > 1.0 {
        errors.push(format!("confidence must be 0.0-1.0, got {}", entry.confidence));
    }
    if entry.source.session_id.is_empty() {
        errors.push("source.session_id is required".into());
    }

    if errors.is_empty() { Ok(()) } else { Err(errors) }
}

/// Validate a KnowledgeStore.
pub fn validate_knowledge_store(store: &KnowledgeStore) -> Result<(), Vec<String>> {
    let mut errors = Vec::new();

    if store.oamp_version.is_empty() {
        errors.push("oamp_version is required".into());
    }
    if store.store_type != "knowledge_store" {
        errors.push(format!("type must be 'knowledge_store', got '{}'", store.store_type));
    }
    if store.user_id.is_empty() {
        errors.push("user_id is required".into());
    }

    if errors.is_empty() { Ok(()) } else { Err(errors) }
}

/// Validate a UserModel.
pub fn validate_user_model(model: &UserModel) -> Result<(), Vec<String>> {
    let mut errors = Vec::new();

    if model.oamp_version.is_empty() {
        errors.push("oamp_version is required".into());
    }
    if model.model_type != "user_model" {
        errors.push(format!("type must be 'user_model', got '{}'", model.model_type));
    }
    if model.user_id.is_empty() {
        errors.push("user_id is required".into());
    }

    // Validate communication ranges
    if let Some(ref comm) = model.communication {
        if comm.verbosity < -1.0 || comm.verbosity > 1.0 {
            errors.push(format!("verbosity must be -1.0 to 1.0, got {}", comm.verbosity));
        }
        if comm.formality < -1.0 || comm.formality > 1.0 {
            errors.push(format!("formality must be -1.0 to 1.0, got {}", comm.formality));
        }
    }

    // Validate expertise confidence
    for (i, exp) in model.expertise.iter().enumerate() {
        if exp.confidence < 0.0 || exp.confidence > 1.0 {
            errors.push(format!("expertise[{}].confidence must be 0.0-1.0, got {}", i, exp.confidence));
        }
    }

    if errors.is_empty() { Ok(()) } else { Err(errors) }
}
