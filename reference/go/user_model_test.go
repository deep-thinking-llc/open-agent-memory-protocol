package oamp

import (
	"encoding/json"
	"os"
	"testing"
)

func TestExpertiseLevelValues(t *testing.T) {
	levels := map[ExpertiseLevel]bool{
		ExpertiseLevelNovice:       true,
		ExpertiseLevelIntermediate: true,
		ExpertiseLevelAdvanced:     true,
		ExpertiseLevelExpert:       true,
	}
	for level := range levels {
		if !ValidExpertiseLevels[level] {
			t.Errorf("level %q should be valid", level)
		}
	}

	invalid := ExpertiseLevel("guru")
	if ValidExpertiseLevels[invalid] {
		t.Error("unknown level should not be valid")
	}
}

func TestNewUserModel(t *testing.T) {
	model := NewUserModel("user-1")

	if model.OAMPVersion != OAMPVersion {
		t.Errorf("OAMPVersion = %q, want %q", model.OAMPVersion, OAMPVersion)
	}
	if model.Type != "user_model" {
		t.Errorf("Type = %q, want %q", model.Type, "user_model")
	}
	if model.UserID != "user-1" {
		t.Errorf("UserID = %q, want %q", model.UserID, "user-1")
	}
	if model.ModelVersion != 1 {
		t.Errorf("ModelVersion = %d, want 1", model.ModelVersion)
	}
}

func TestUserModelRoundTrip(t *testing.T) {
	commVerbosity := -0.6
	commFormality := 0.2
	context := "Rust code generation"
	lastObserved := parseTime("2026-03-28T09:00:00Z")

	model := &UserModel{
		OAMPVersion:  OAMPVersion,
		Type:         "user_model",
		UserID:       "user-alice-123",
		ModelVersion: 7,
		UpdatedAt:    parseTime("2026-03-28T12:00:00Z"),
		Communication: &CommunicationProfile{
			Verbosity:           commVerbosity,
			Formality:           commFormality,
			PrefersExamples:     true,
			PrefersExplanations: false,
			Languages:           []string{"en", "ja"},
		},
		Expertise: []ExpertiseDomain{
			{
				Domain:           "rust",
				Level:            ExpertiseLevelExpert,
				Confidence:       0.95,
				EvidenceSessions: []string{"sess-001", "sess-003", "sess-005"},
				LastObserved:     &lastObserved,
			},
		},
		Corrections: []Correction{
			{
				WhatAgentDid:   "Suggested using unwrap() for quick prototyping",
				WhatUserWanted: "Always use proper error handling, even in examples",
				Context:        &context,
				SessionID:      "sess-003",
				Timestamp:      parseTime("2026-03-12T16:45:00Z"),
			},
		},
		StatedPreferences: []StatedPreference{
			{Key: "theme", Value: "dark", Timestamp: parseTime("2026-03-10T10:00:00Z")},
			{Key: "response-length", Value: "concise", Timestamp: parseTime("2026-03-15T14:00:00Z")},
		},
		Metadata: json.RawMessage("{}"),
	}

	data, err := json.Marshal(model)
	if err != nil {
		t.Fatalf("Marshal: %v", err)
	}

	var parsed UserModel
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("Unmarshal: %v", err)
	}

	if parsed.OAMPVersion != model.OAMPVersion {
		t.Errorf("OAMPVersion mismatch: got %q, want %q", parsed.OAMPVersion, model.OAMPVersion)
	}
	if parsed.UserID != model.UserID {
		t.Errorf("UserID mismatch: got %q, want %q", parsed.UserID, model.UserID)
	}
	if parsed.ModelVersion != model.ModelVersion {
		t.Errorf("ModelVersion mismatch: got %d, want %d", parsed.ModelVersion, model.ModelVersion)
	}
	if parsed.Communication == nil {
		t.Error("Communication should not be nil")
	}
	if len(parsed.Expertise) != 1 {
		t.Errorf("len(Expertise) = %d, want 1", len(parsed.Expertise))
	}
	if parsed.Expertise[0].Domain != "rust" {
		t.Errorf("Expertise[0].Domain = %q, want %q", parsed.Expertise[0].Domain, "rust")
	}
	if parsed.Expertise[0].Level != ExpertiseLevelExpert {
		t.Errorf("Expertise[0].Level = %q, want %q", parsed.Expertise[0].Level, ExpertiseLevelExpert)
	}
	if len(parsed.Corrections) != 1 {
		t.Errorf("len(Corrections) = %d, want 1", len(parsed.Corrections))
	}
	if len(parsed.StatedPreferences) != 2 {
		t.Errorf("len(StatedPreferences) = %d, want 2", len(parsed.StatedPreferences))
	}
}

func TestParseUserModelExample(t *testing.T) {
	data, err := os.ReadFile("../../spec/v1/examples/user-model.json")
	if err != nil {
		t.Skipf("example file not found: %v", err)
	}

	model := MustParseUserModel(data)
	if model.OAMPVersion != "1.0.0" {
		t.Errorf("OAMPVersion = %q, want %q", model.OAMPVersion, "1.0.0")
	}
	if model.Type != "user_model" {
		t.Errorf("Type = %q, want %q", model.Type, "user_model")
	}
	if model.UserID != "user-alice-123" {
		t.Errorf("UserID = %q, want %q", model.UserID, "user-alice-123")
	}
	if model.ModelVersion != 7 {
		t.Errorf("ModelVersion = %d, want 7", model.ModelVersion)
	}
	if model.Communication == nil {
		t.Error("Communication should not be nil")
	} else {
		if model.Communication.Verbosity != -0.6 {
			t.Errorf("Verbosity = %f, want -0.6", model.Communication.Verbosity)
		}
		if model.Communication.Formality != 0.2 {
			t.Errorf("Formality = %f, want 0.2", model.Communication.Formality)
		}
	}
	if len(model.Expertise) != 3 {
		t.Errorf("len(Expertise) = %d, want 3", len(model.Expertise))
	}
	if len(model.Corrections) != 1 {
		t.Errorf("len(Corrections) = %d, want 1", len(model.Corrections))
	}
	if len(model.StatedPreferences) != 2 {
		t.Errorf("len(StatedPreferences) = %d, want 2", len(model.StatedPreferences))
	}

	errors := ValidateUserModel(model)
	if len(errors) > 0 {
		t.Errorf("validation errors: %v", errors)
	}
}