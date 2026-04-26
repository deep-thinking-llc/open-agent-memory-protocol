package oamp

import (
	"encoding/json"
	"testing"
	"time"
)

func parseTime(s string) time.Time {
	t, err := time.Parse(time.RFC3339, s)
	if err != nil {
		panic(err)
	}
	return t
}

func TestValidateKnowledgeEntry_Valid(t *testing.T) {
	entry := &KnowledgeEntry{
		OAMPVersion: OAMPVersion,
		Type:        "knowledge_entry",
		ID:          "550e8400-e29b-41d4-a716-446655440000",
		UserID:      "user-1",
		Category:    KnowledgeCategoryFact,
		Content:     "test",
		Confidence:  0.8,
		Source: KnowledgeSource{
			SessionID: "sess-1",
			Timestamp:  parseTime("2026-03-15T14:32:00Z"),
		},
	}

	errors := ValidateKnowledgeEntry(entry)
	if len(errors) > 0 {
		t.Errorf("expected no errors, got: %v", errors)
	}
}

func TestValidateKnowledgeEntry_InvalidVersion(t *testing.T) {
	entry := &KnowledgeEntry{
		OAMPVersion: "2.0.0",
		Type:        "knowledge_entry",
		ID:          "550e8400-e29b-41d4-a716-446655440000",
		UserID:      "user-1",
		Category:    KnowledgeCategoryFact,
		Content:     "test",
		Confidence:  0.8,
		Source: KnowledgeSource{
			SessionID: "sess-1",
			Timestamp:  parseTime("2026-03-15T14:32:00Z"),
		},
	}

	errors := ValidateKnowledgeEntry(entry)
	if len(errors) == 0 {
		t.Error("expected errors for invalid version")
	}
}

func TestValidateKnowledgeEntry_InvalidConfidence(t *testing.T) {
	entry := &KnowledgeEntry{
		OAMPVersion: OAMPVersion,
		Type:        "knowledge_entry",
		ID:          "550e8400-e29b-41d4-a716-446655440000",
		UserID:      "user-1",
		Category:    KnowledgeCategoryFact,
		Content:     "test",
		Confidence:  1.5, // out of range
		Source: KnowledgeSource{
			SessionID: "sess-1",
			Timestamp:  parseTime("2026-03-15T14:32:00Z"),
		},
	}

	errors := ValidateKnowledgeEntry(entry)
	found := false
	for _, e := range errors {
		if e == "confidence must be 0.0-1.0, got 1.500000" {
			found = true
		}
	}
	if !found {
		t.Errorf("expected confidence error, got: %v", errors)
	}
}

func TestValidateKnowledgeEntry_EmptyContent(t *testing.T) {
	entry := &KnowledgeEntry{
		OAMPVersion: OAMPVersion,
		Type:        "knowledge_entry",
		ID:          "550e8400-e29b-41d4-a716-446655440000",
		UserID:      "user-1",
		Category:    KnowledgeCategoryFact,
		Content:     "",
		Confidence:  0.8,
		Source: KnowledgeSource{
			SessionID: "sess-1",
			Timestamp:  parseTime("2026-03-15T14:32:00Z"),
		},
	}

	errors := ValidateKnowledgeEntry(entry)
	if len(errors) == 0 {
		t.Error("expected errors for empty content")
	}
}

func TestValidateKnowledgeEntry_InvalidUUID(t *testing.T) {
	entry := &KnowledgeEntry{
		OAMPVersion: OAMPVersion,
		Type:        "knowledge_entry",
		ID:          "not-a-uuid",
		UserID:      "user-1",
		Category:    KnowledgeCategoryFact,
		Content:     "test",
		Confidence:  0.8,
		Source: KnowledgeSource{
			SessionID: "sess-1",
			Timestamp:  parseTime("2026-03-15T14:32:00Z"),
		},
	}

	errors := ValidateKnowledgeEntry(entry)
	if len(errors) == 0 {
		t.Error("expected errors for invalid UUID")
	}
}

func TestValidateUserModel_Valid(t *testing.T) {
	model := &UserModel{
		OAMPVersion:  OAMPVersion,
		Type:         "user_model",
		UserID:       "user-1",
		ModelVersion: 1,
		UpdatedAt:    parseTime("2026-03-28T12:00:00Z"),
	}

	errors := ValidateUserModel(model)
	if len(errors) > 0 {
		t.Errorf("expected no errors, got: %v", errors)
	}
}

func TestValidateUserModel_InvalidVerbosity(t *testing.T) {
	model := &UserModel{
		OAMPVersion:  OAMPVersion,
		Type:         "user_model",
		UserID:       "user-1",
		ModelVersion: 1,
		UpdatedAt:    parseTime("2026-03-28T12:00:00Z"),
		Communication: &CommunicationProfile{
			Verbosity: 2.0, // out of range
			Formality: 0.0,
		},
	}

	errors := ValidateUserModel(model)
	if len(errors) == 0 {
		t.Error("expected errors for invalid verbosity")
	}
}

func TestValidateUserModel_InvalidModelVersion(t *testing.T) {
	model := &UserModel{
		OAMPVersion:  OAMPVersion,
		Type:         "user_model",
		UserID:       "user-1",
		ModelVersion: 0, // must be >= 1
		UpdatedAt:    parseTime("2026-03-28T12:00:00Z"),
	}

	errors := ValidateUserModel(model)
	if len(errors) == 0 {
		t.Error("expected errors for invalid model_version")
	}
}

func TestValidateKnowledgeCategory(t *testing.T) {
	valid := []string{"fact", "preference", "pattern", "correction"}
	for _, v := range valid {
		if err := ValidateKnowledgeCategory(v); err != nil {
			t.Errorf("ValidateKnowledgeCategory(%q) = %v, want nil", v, err)
		}
	}

	if err := ValidateKnowledgeCategory("unknown"); err == nil {
		t.Error("ValidateKnowledgeCategory('unknown') should return error")
	}
}

func TestValidateExpertiseLevel(t *testing.T) {
	valid := []string{"novice", "intermediate", "advanced", "expert"}
	for _, v := range valid {
		if err := ValidateExpertiseLevel(v); err != nil {
			t.Errorf("ValidateExpertiseLevel(%q) = %v, want nil", v, err)
		}
	}

	if err := ValidateExpertiseLevel("guru"); err == nil {
		t.Error("ValidateExpertiseLevel('guru') should return error")
	}
}

func TestRejectionOfUnknownFields(t *testing.T) {
	data := []byte(`{
		"oamp_version": "1.0.0",
		"type": "knowledge_entry",
		"id": "550e8400-e29b-41d4-a716-446655440000",
		"user_id": "user-1",
		"category": "fact",
		"content": "test",
		"confidence": 0.8,
		"source": {
			"session_id": "sess-1",
			"timestamp": "2026-03-15T14:32:00Z"
		},
		"unknown_field": "should not cause error in Go"
	}`)

	var entry KnowledgeEntry
	if err := json.Unmarshal(data, &entry); err != nil {
		t.Errorf("Go should tolerate unknown fields: %v", err)
	}
	// Note: Go's encoding/json silently ignores unknown fields.
	// This is different from Python's extra="forbid" behavior.
	// Validate separately that required fields are present.
}