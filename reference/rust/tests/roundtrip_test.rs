use oamp_types::*;

#[test]
fn test_knowledge_entry_roundtrip() {
    let entry = KnowledgeEntry::new("user-1", KnowledgeCategory::Fact, "Knows Rust", 0.9, "sess-1");
    let json = serde_json::to_string_pretty(&entry).unwrap();
    let parsed: KnowledgeEntry = serde_json::from_str(&json).unwrap();
    assert_eq!(parsed.category, KnowledgeCategory::Fact);
    assert_eq!(parsed.content, "Knows Rust");
    assert_eq!(parsed.confidence, 0.9);
}

#[test]
fn test_knowledge_store_roundtrip() {
    let entries = vec![
        KnowledgeEntry::new("user-1", KnowledgeCategory::Fact, "Fact 1", 0.8, "s1"),
        KnowledgeEntry::new("user-1", KnowledgeCategory::Correction, "Don't do X", 0.95, "s2"),
    ];
    let store = KnowledgeStore::new("user-1", entries);
    let json = serde_json::to_string_pretty(&store).unwrap();
    let parsed: KnowledgeStore = serde_json::from_str(&json).unwrap();
    assert_eq!(parsed.entries.len(), 2);
    assert_eq!(parsed.user_id, "user-1");
}

#[test]
fn test_user_model_roundtrip() {
    let mut model = UserModel::new("user-1");
    model.communication = Some(CommunicationProfile {
        verbosity: -0.5,
        formality: 0.3,
        prefers_examples: true,
        prefers_explanations: false,
        languages: vec!["en".into(), "ja".into()],
    });
    model.expertise.push(ExpertiseDomain {
        domain: "rust".into(),
        level: ExpertiseLevel::Expert,
        confidence: 0.95,
        evidence_sessions: vec!["s1".into()],
        last_observed: Some(chrono::Utc::now()),
    });

    let json = serde_json::to_string_pretty(&model).unwrap();
    let parsed: UserModel = serde_json::from_str(&json).unwrap();
    assert_eq!(parsed.expertise[0].level, ExpertiseLevel::Expert);
    assert_eq!(parsed.communication.unwrap().verbosity, -0.5);
}

#[test]
fn test_validation_valid_entry() {
    let entry = KnowledgeEntry::new("user-1", KnowledgeCategory::Fact, "Valid", 0.5, "sess-1");
    assert!(validate::validate_knowledge_entry(&entry).is_ok());
}

#[test]
fn test_validation_invalid_confidence() {
    let entry = KnowledgeEntry::new("user-1", KnowledgeCategory::Fact, "Test", 1.5, "sess-1");
    assert!(validate::validate_knowledge_entry(&entry).is_err());
}

#[test]
fn test_validation_empty_content() {
    let entry = KnowledgeEntry::new("user-1", KnowledgeCategory::Fact, "", 0.5, "sess-1");
    assert!(validate::validate_knowledge_entry(&entry).is_err());
}

#[test]
fn test_validation_valid_user_model() {
    let model = UserModel::new("user-1");
    assert!(validate::validate_user_model(&model).is_ok());
}

#[test]
fn test_validation_invalid_verbosity() {
    let mut model = UserModel::new("user-1");
    model.communication = Some(CommunicationProfile {
        verbosity: 2.0, // out of range
        ..Default::default()
    });
    assert!(validate::validate_user_model(&model).is_err());
}

#[test]
fn test_parse_example_knowledge_entry() {
    let json = std::fs::read_to_string("../../spec/v1/examples/knowledge-entry.json").unwrap();
    let entry: KnowledgeEntry = serde_json::from_str(&json).unwrap();
    assert_eq!(entry.category, KnowledgeCategory::Preference);
    assert!(entry.confidence > 0.0 && entry.confidence <= 1.0);
}

#[test]
fn test_parse_example_user_model() {
    let json = std::fs::read_to_string("../../spec/v1/examples/user-model.json").unwrap();
    let model: UserModel = serde_json::from_str(&json).unwrap();
    assert!(!model.expertise.is_empty());
    assert_eq!(model.expertise[0].level, ExpertiseLevel::Expert);
}
