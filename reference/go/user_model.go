package oamp

import (
	"encoding/json"
	"fmt"
	"time"
)

// ExpertiseLevel represents the level of expertise in a domain.
type ExpertiseLevel string

const (
	ExpertiseLevelNovice       ExpertiseLevel = "novice"
	ExpertiseLevelIntermediate ExpertiseLevel = "intermediate"
	ExpertiseLevelAdvanced     ExpertiseLevel = "advanced"
	ExpertiseLevelExpert       ExpertiseLevel = "expert"
)

// ValidExpertiseLevels is the set of valid expertise levels.
var ValidExpertiseLevels = map[ExpertiseLevel]bool{
	ExpertiseLevelNovice:       true,
	ExpertiseLevelIntermediate: true,
	ExpertiseLevelAdvanced:     true,
	ExpertiseLevelExpert:       true,
}

// CommunicationProfile models how the user prefers to interact with agents.
type CommunicationProfile struct {
	Verbosity           float64  `json:"verbosity"`
	Formality           float64  `json:"formality"`
	PrefersExamples     bool     `json:"prefers_examples"`
	PrefersExplanations bool     `json:"prefers_explanations"`
	Languages           []string `json:"languages,omitempty"`
}

// ExpertiseDomain represents the user's demonstrated knowledge in a domain.
type ExpertiseDomain struct {
	Domain           string        `json:"domain"`
	Level            ExpertiseLevel `json:"level"`
	Confidence       float64       `json:"confidence"`
	EvidenceSessions []string      `json:"evidence_sessions,omitempty"`
	LastObserved     *time.Time    `json:"last_observed,omitempty"`
}

// Correction records an instance where the user corrected the agent.
type Correction struct {
	WhatAgentDid  string `json:"what_agent_did"`
	WhatUserWanted string `json:"what_user_wanted"`
	Context       *string `json:"context,omitempty"`
	SessionID     string `json:"session_id"`
	Timestamp     time.Time `json:"timestamp"`
}

// StatedPreference records a preference the user has explicitly declared.
type StatedPreference struct {
	Key       string    `json:"key"`
	Value     string    `json:"value"`
	Timestamp time.Time `json:"timestamp"`
}

// UserModel represents an agent's evolving structured understanding of a user.
type UserModel struct {
	OAMPVersion        string              `json:"oamp_version"`
	Type               string              `json:"type"`
	UserID             string              `json:"user_id"`
	ModelVersion       int                 `json:"model_version"`
	UpdatedAt          time.Time           `json:"updated_at"`
	Communication      *CommunicationProfile `json:"communication,omitempty"`
	Expertise         []ExpertiseDomain     `json:"expertise,omitempty"`
	Corrections       []Correction          `json:"corrections,omitempty"`
	StatedPreferences []StatedPreference    `json:"stated_preferences,omitempty"`
	Metadata          json.RawMessage      `json:"metadata,omitempty"`
}

// NewUserModel creates a new user model with sensible defaults.
func NewUserModel(userID string) *UserModel {
	return &UserModel{
		OAMPVersion:  OAMPVersion,
		Type:         "user_model",
		UserID:       userID,
		ModelVersion: 1,
		UpdatedAt:    time.Now().UTC(),
		Metadata:     json.RawMessage("{}"),
	}
}

// ValidateExpertiseLevel validates an ExpertiseLevel string.
func ValidateExpertiseLevel(s string) error {
	level := ExpertiseLevel(s)
	if !ValidExpertiseLevels[level] {
		return fmt.Errorf("invalid expertise level: %q (must be novice, intermediate, advanced, or expert)", s)
	}
	return nil
}