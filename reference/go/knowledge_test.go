package oamp

import (
	"encoding/json"
	"os"
	"testing"
)

func TestKnowledgeCategoryValues(t *testing.T) {
	categories := map[KnowledgeCategory]bool{
		KnowledgeCategoryFact:        true,
		KnowledgeCategoryPreference:  true,
		KnowledgeCategoryPattern:    true,
		KnowledgeCategoryCorrection: true,
	}
	for cat := range categories {
		if !ValidKnowledgeCategories[cat] {
			t.Errorf("category %q should be valid", cat)
		}
	}

	invalid := KnowledgeCategory("unknown")
	if ValidKnowledgeCategories[invalid] {
		t.Error("unknown category should not be valid")
	}
}

func TestNewKnowledgeEntry(t *testing.T) {
	entry := NewKnowledgeEntry("user-1", KnowledgeCategoryPreference, "test content", 0.8, "sess-1")

	if entry.OAMPVersion != OAMPVersion {
		t.Errorf("OAMPVersion = %q, want %q", entry.OAMPVersion, OAMPVersion)
	}
	if entry.Type != "knowledge_entry" {
		t.Errorf("Type = %q, want %q", entry.Type, "knowledge_entry")
	}
	if entry.UserID != "user-1" {
		t.Errorf("UserID = %q, want %q", entry.UserID, "user-1")
	}
	if entry.Category != KnowledgeCategoryPreference {
		t.Errorf("Category = %q, want %q", entry.Category, KnowledgeCategoryPreference)
	}
	if entry.Content != "test content" {
		t.Errorf("Content = %q, want %q", entry.Content, "test content")
	}
	if entry.Confidence != 0.8 {
		t.Errorf("Confidence = %f, want 0.8", entry.Confidence)
	}
	if entry.Source.SessionID != "sess-1" {
		t.Errorf("Source.SessionID = %q, want %q", entry.Source.SessionID, "sess-1")
	}
	if entry.ID == "" {
		t.Error("ID should not be empty")
	}
}

func TestNewKnowledgeStore(t *testing.T) {
	store := NewKnowledgeStore("user-1", []KnowledgeEntry{})

	if store.OAMPVersion != OAMPVersion {
		t.Errorf("OAMPVersion = %q, want %q", store.OAMPVersion, OAMPVersion)
	}
	if store.Type != "knowledge_store" {
		t.Errorf("Type = %q, want %q", store.Type, "knowledge_store")
	}
	if store.UserID != "user-1" {
		t.Errorf("UserID = %q, want %q", store.UserID, "user-1")
	}
	if store.ExportedAt.IsZero() {
		t.Error("ExportedAt should not be zero")
	}
}

func TestKnowledgeEntryRoundTrip(t *testing.T) {
	agentID := "my-agent"
	entry := &KnowledgeEntry{
		OAMPVersion: OAMPVersion,
		Type:        "knowledge_entry",
		ID:          "550e8400-e29b-41d4-a716-446655440000",
		UserID:      "user-alice-123",
		Category:    KnowledgeCategoryPreference,
		Content:     "User prefers concise answers",
		Confidence:  0.85,
		Source: KnowledgeSource{
			SessionID: "sess-001",
			AgentID:   &agentID,
			Timestamp:  parseTime("2026-03-15T14:32:00Z"),
		},
		Tags:     []string{"communication", "response-style"},
		Metadata: json.RawMessage("{}"),
	}

	data, err := json.Marshal(entry)
	if err != nil {
		t.Fatalf("Marshal: %v", err)
	}

	var parsed KnowledgeEntry
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("Unmarshal: %v", err)
	}

	if parsed.OAMPVersion != entry.OAMPVersion {
		t.Errorf("OAMPVersion mismatch: got %q, want %q", parsed.OAMPVersion, entry.OAMPVersion)
	}
	if parsed.Category != entry.Category {
		t.Errorf("Category mismatch: got %q, want %q", parsed.Category, entry.Category)
	}
	if parsed.Confidence != entry.Confidence {
		t.Errorf("Confidence mismatch: got %f, want %f", parsed.Confidence, entry.Confidence)
	}
	if parsed.Source.SessionID != entry.Source.SessionID {
		t.Errorf("Source.SessionID mismatch: got %q, want %q", parsed.Source.SessionID, entry.Source.SessionID)
	}
}

func TestParseKnowledgeEntryExample(t *testing.T) {
	data, err := os.ReadFile("../../spec/v1/examples/knowledge-entry.json")
	if err != nil {
		t.Skipf("example file not found: %v", err)
	}

	entry := MustParseKnowledgeEntry(data)
	if entry.OAMPVersion != "1.0.0" {
		t.Errorf("OAMPVersion = %q, want %q", entry.OAMPVersion, "1.0.0")
	}
	if entry.Type != "knowledge_entry" {
		t.Errorf("Type = %q, want %q", entry.Type, "knowledge_entry")
	}
	if entry.Category != KnowledgeCategoryPreference {
		t.Errorf("Category = %q, want %q", entry.Category, KnowledgeCategoryPreference)
	}
	if entry.Confidence != 0.85 {
		t.Errorf("Confidence = %f, want 0.85", entry.Confidence)
	}

	errors := ValidateKnowledgeEntry(entry)
	if len(errors) > 0 {
		t.Errorf("validation errors: %v", errors)
	}
}

func TestParseKnowledgeStoreExample(t *testing.T) {
	data, err := os.ReadFile("../../spec/v1/examples/knowledge-store.json")
	if err != nil {
		t.Skipf("example file not found: %v", err)
	}

	store := MustParseKnowledgeStore(data)
	if store.OAMPVersion != "1.0.0" {
		t.Errorf("OAMPVersion = %q, want %q", store.OAMPVersion, "1.0.0")
	}
	if store.Type != "knowledge_store" {
		t.Errorf("Type = %q, want %q", store.Type, "knowledge_store")
	}
	if len(store.Entries) != 3 {
		t.Errorf("len(Entries) = %d, want 3", len(store.Entries))
	}

	errors := ValidateKnowledgeStore(store)
	if len(errors) > 0 {
		t.Errorf("validation errors: %v", errors)
	}
}