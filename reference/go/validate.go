package oamp

import (
	"encoding/json"
	"fmt"
	"regexp"
)

// uuidPattern matches a UUID v4 string.
var uuidPattern = regexp.MustCompile(`^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$`)

// ValidateKnowledgeEntry validates a KnowledgeEntry and returns a list of errors.
func ValidateKnowledgeEntry(e *KnowledgeEntry) []string {
	var errors []string

	if e.OAMPVersion == "" {
		errors = append(errors, "oamp_version is required")
	} else if e.OAMPVersion != OAMPVersion {
		errors = append(errors, fmt.Sprintf("oamp_version must be %q, got %q", OAMPVersion, e.OAMPVersion))
	}

	if e.Type != "knowledge_entry" {
		errors = append(errors, fmt.Sprintf("type must be %q, got %q", "knowledge_entry", e.Type))
	}

	if e.ID == "" {
		errors = append(errors, "id is required")
	} else if !uuidPattern.MatchString(e.ID) {
		errors = append(errors, fmt.Sprintf("id must be a valid UUID v4, got %q", e.ID))
	}

	if e.UserID == "" {
		errors = append(errors, "user_id is required")
	}

	if !ValidKnowledgeCategories[e.Category] {
		errors = append(errors, fmt.Sprintf("invalid category: %q", e.Category))
	}

	if e.Content == "" {
		errors = append(errors, "content is required")
	}

	if e.Confidence < 0 || e.Confidence > 1 {
		errors = append(errors, fmt.Sprintf("confidence must be 0.0-1.0, got %f", e.Confidence))
	}

	if e.Source.SessionID == "" {
		errors = append(errors, "source.session_id is required")
	}

	if e.Source.Timestamp.IsZero() {
		errors = append(errors, "source.timestamp is required")
	}

	if e.Decay != nil && e.Decay.HalfLifeDays != nil && *e.Decay.HalfLifeDays <= 0 {
		errors = append(errors, "decay.half_life_days must be positive")
	}

	return errors
}

// ValidateKnowledgeStore validates a KnowledgeStore and returns a list of errors.
func ValidateKnowledgeStore(s *KnowledgeStore) []string {
	var errors []string

	if s.OAMPVersion == "" {
		errors = append(errors, "oamp_version is required")
	} else if s.OAMPVersion != OAMPVersion {
		errors = append(errors, fmt.Sprintf("oamp_version must be %q, got %q", OAMPVersion, s.OAMPVersion))
	}

	if s.Type != "knowledge_store" {
		errors = append(errors, fmt.Sprintf("type must be %q, got %q", "knowledge_store", s.Type))
	}

	if s.UserID == "" {
		errors = append(errors, "user_id is required")
	}

	if s.ExportedAt.IsZero() {
		errors = append(errors, "exported_at is required")
	}

	for i, entry := range s.Entries {
		for _, err := range ValidateKnowledgeEntry(&entry) {
			errors = append(errors, fmt.Sprintf("entries[%d]: %s", i, err))
		}
	}

	return errors
}

// ValidateUserModel validates a UserModel and returns a list of errors.
func ValidateUserModel(m *UserModel) []string {
	var errors []string

	if m.OAMPVersion == "" {
		errors = append(errors, "oamp_version is required")
	} else if m.OAMPVersion != OAMPVersion {
		errors = append(errors, fmt.Sprintf("oamp_version must be %q, got %q", OAMPVersion, m.OAMPVersion))
	}

	if m.Type != "user_model" {
		errors = append(errors, fmt.Sprintf("type must be %q, got %q", "user_model", m.Type))
	}

	if m.UserID == "" {
		errors = append(errors, "user_id is required")
	}

	if m.ModelVersion < 1 {
		errors = append(errors, fmt.Sprintf("model_version must be >= 1, got %d", m.ModelVersion))
	}

	if m.UpdatedAt.IsZero() {
		errors = append(errors, "updated_at is required")
	}

	if m.Communication != nil {
		c := m.Communication
		if c.Verbosity < -1 || c.Verbosity > 1 {
			errors = append(errors, fmt.Sprintf("verbosity must be -1.0 to 1.0, got %f", c.Verbosity))
		}
		if c.Formality < -1 || c.Formality > 1 {
			errors = append(errors, fmt.Sprintf("formality must be -1.0 to 1.0, got %f", c.Formality))
		}
	}

	for i, exp := range m.Expertise {
		if exp.Confidence < 0 || exp.Confidence > 1 {
			errors = append(errors, fmt.Sprintf("expertise[%d].confidence must be 0.0-1.0, got %f", i, exp.Confidence))
		}
		if !ValidExpertiseLevels[exp.Level] {
			errors = append(errors, fmt.Sprintf("expertise[%d]: invalid level %q", i, exp.Level))
		}
	}

	return errors
}

// MustParseKnowledgeEntry parses JSON into a KnowledgeEntry, panicking on error.
// Useful for tests.
func MustParseKnowledgeEntry(data []byte) *KnowledgeEntry {
	var entry KnowledgeEntry
	if err := json.Unmarshal(data, &entry); err != nil {
		panic(err)
	}
	return &entry
}

// MustParseKnowledgeStore parses JSON into a KnowledgeStore, panicking on error.
func MustParseKnowledgeStore(data []byte) *KnowledgeStore {
	var store KnowledgeStore
	if err := json.Unmarshal(data, &store); err != nil {
		panic(err)
	}
	return &store
}

// MustParseUserModel parses JSON into a UserModel, panicking on error.
func MustParseUserModel(data []byte) *UserModel {
	var model UserModel
	if err := json.Unmarshal(data, &model); err != nil {
		panic(err)
	}
	return &model
}