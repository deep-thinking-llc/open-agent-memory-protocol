package oamp

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
)

// KnowledgeCategory represents the category of a knowledge entry.
type KnowledgeCategory string

const (
	KnowledgeCategoryFact       KnowledgeCategory = "fact"
	KnowledgeCategoryPreference KnowledgeCategory = "preference"
	KnowledgeCategoryPattern   KnowledgeCategory = "pattern"
	KnowledgeCategoryCorrection KnowledgeCategory = "correction"
)

// ValidKnowledgeCategories is the set of valid knowledge categories.
var ValidKnowledgeCategories = map[KnowledgeCategory]bool{
	KnowledgeCategoryFact:        true,
	KnowledgeCategoryPreference:  true,
	KnowledgeCategoryPattern:     true,
	KnowledgeCategoryCorrection:  true,
}

// KnowledgeSource records the provenance of a knowledge entry.
type KnowledgeSource struct {
	SessionID string    `json:"session_id"`
	AgentID   *string   `json:"agent_id,omitempty"`
	Timestamp time.Time `json:"timestamp"`
}

// KnowledgeDecay holds temporal decay parameters for confidence.
type KnowledgeDecay struct {
	HalfLifeDays  *float64   `json:"half_life_days,omitempty"`
	LastConfirmed *time.Time `json:"last_confirmed,omitempty"`
}

// KnowledgeEntry represents a discrete piece of information an agent has learned about a user.
type KnowledgeEntry struct {
	OAMPVersion string            `json:"oamp_version"`
	Type        string            `json:"type"`
	ID          string            `json:"id"`
	UserID      string            `json:"user_id"`
	Category    KnowledgeCategory `json:"category"`
	Content     string            `json:"content"`
	Confidence  float64           `json:"confidence"`
	Source      KnowledgeSource   `json:"source"`
	Decay       *KnowledgeDecay   `json:"decay,omitempty"`
	Tags        []string          `json:"tags,omitempty"`
	Metadata    json.RawMessage   `json:"metadata,omitempty"`
}

// NewKnowledgeEntry creates a new knowledge entry with sensible defaults.
func NewKnowledgeEntry(userID string, category KnowledgeCategory, content string, confidence float64, sessionID string) *KnowledgeEntry {
	return &KnowledgeEntry{
		OAMPVersion: OAMPVersion,
		Type:        "knowledge_entry",
		ID:          uuid.New().String(),
		UserID:      userID,
		Category:    category,
		Content:     content,
		Confidence:  confidence,
		Source: KnowledgeSource{
			SessionID: sessionID,
			Timestamp: time.Now().UTC(),
		},
		Tags:     []string{},
		Metadata: json.RawMessage("{}"),
	}
}

// KnowledgeStore is a collection document for bulk export and import.
type KnowledgeStore struct {
	OAMPVersion string            `json:"oamp_version"`
	Type        string            `json:"type"`
	UserID      string            `json:"user_id"`
	Entries     []KnowledgeEntry  `json:"entries"`
	ExportedAt  time.Time         `json:"exported_at"`
	AgentID     *string           `json:"agent_id,omitempty"`
}

// NewKnowledgeStore creates a new knowledge store.
func NewKnowledgeStore(userID string, entries []KnowledgeEntry) *KnowledgeStore {
	return &KnowledgeStore{
		OAMPVersion: OAMPVersion,
		Type:        "knowledge_store",
		UserID:      userID,
		Entries:     entries,
		ExportedAt:  time.Now().UTC(),
	}
}

// Validate validates a KnowledgeCategory string.
func ValidateKnowledgeCategory(s string) error {
	cat := KnowledgeCategory(s)
	if !ValidKnowledgeCategories[cat] {
		return fmt.Errorf("invalid knowledge category: %q (must be fact, preference, pattern, or correction)", s)
	}
	return nil
}