use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

use super::knowledge::OAMP_VERSION;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ExpertiseLevel {
    Novice,
    Intermediate,
    Advanced,
    Expert,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommunicationProfile {
    pub verbosity: f32,      // -1.0 to 1.0
    pub formality: f32,      // -1.0 to 1.0
    pub prefers_examples: bool,
    pub prefers_explanations: bool,
    #[serde(default)]
    pub languages: Vec<String>,
}

impl Default for CommunicationProfile {
    fn default() -> Self {
        Self {
            verbosity: 0.0,
            formality: 0.0,
            prefers_examples: true,
            prefers_explanations: true,
            languages: vec!["en".to_string()],
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExpertiseDomain {
    pub domain: String,
    pub level: ExpertiseLevel,
    pub confidence: f32,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub evidence_sessions: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub last_observed: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Correction {
    pub what_agent_did: String,
    pub what_user_wanted: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub context: Option<String>,
    pub session_id: String,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatedPreference {
    pub key: String,
    pub value: String,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserModel {
    pub oamp_version: String,
    #[serde(rename = "type")]
    pub model_type: String,
    pub user_id: String,
    pub model_version: u64,
    pub updated_at: DateTime<Utc>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub communication: Option<CommunicationProfile>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub expertise: Vec<ExpertiseDomain>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub corrections: Vec<Correction>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub stated_preferences: Vec<StatedPreference>,
    #[serde(default, skip_serializing_if = "serde_json::Map::is_empty")]
    pub metadata: serde_json::Map<String, serde_json::Value>,
}

impl UserModel {
    pub fn new(user_id: &str) -> Self {
        Self {
            oamp_version: OAMP_VERSION.to_string(),
            model_type: "user_model".to_string(),
            user_id: user_id.to_string(),
            model_version: 1,
            updated_at: Utc::now(),
            communication: None,
            expertise: Vec::new(),
            corrections: Vec::new(),
            stated_preferences: Vec::new(),
            metadata: serde_json::Map::new(),
        }
    }
}
