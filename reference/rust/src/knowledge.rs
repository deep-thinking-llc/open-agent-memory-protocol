use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

pub const OAMP_VERSION: &str = "1.0.0";

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum KnowledgeCategory {
    Fact,
    Preference,
    Pattern,
    Correction,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KnowledgeSource {
    pub session_id: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub agent_id: Option<String>,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KnowledgeDecay {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub half_life_days: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub last_confirmed: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KnowledgeEntry {
    pub oamp_version: String,
    #[serde(rename = "type")]
    pub entry_type: String,
    pub id: String,
    pub user_id: String,
    pub category: KnowledgeCategory,
    pub content: String,
    pub confidence: f32,
    pub source: KnowledgeSource,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub decay: Option<KnowledgeDecay>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub tags: Vec<String>,
    #[serde(default, skip_serializing_if = "serde_json::Map::is_empty")]
    pub metadata: serde_json::Map<String, serde_json::Value>,
}

impl KnowledgeEntry {
    pub fn new(
        user_id: &str,
        category: KnowledgeCategory,
        content: &str,
        confidence: f32,
        session_id: &str,
    ) -> Self {
        Self {
            oamp_version: OAMP_VERSION.to_string(),
            entry_type: "knowledge_entry".to_string(),
            id: Uuid::new_v4().to_string(),
            user_id: user_id.to_string(),
            category,
            content: content.to_string(),
            confidence,
            source: KnowledgeSource {
                session_id: session_id.to_string(),
                agent_id: None,
                timestamp: Utc::now(),
            },
            decay: None,
            tags: Vec::new(),
            metadata: serde_json::Map::new(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KnowledgeStore {
    pub oamp_version: String,
    #[serde(rename = "type")]
    pub store_type: String,
    pub user_id: String,
    pub entries: Vec<KnowledgeEntry>,
    pub exported_at: DateTime<Utc>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub agent_id: Option<String>,
}

impl KnowledgeStore {
    pub fn new(user_id: &str, entries: Vec<KnowledgeEntry>) -> Self {
        Self {
            oamp_version: OAMP_VERSION.to_string(),
            store_type: "knowledge_store".to_string(),
            user_id: user_id.to_string(),
            entries,
            exported_at: Utc::now(),
            agent_id: None,
        }
    }
}
