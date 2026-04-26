defmodule OampTypes.UserModelTest do
  use ExUnit.Case, async: true

  alias OampTypes.UserModel.{Model, CommunicationProfile, ExpertiseDomain, Correction, StatedPreference}

  describe "new/2" do
    test "creates a user model with defaults" do
      model = Model.new("user-1")

      assert model.user_id == "user-1"
      assert model.model_version == 1
      assert model.communication == nil
      assert model.expertise == []
      assert model.corrections == []
      assert model.stated_preferences == []
    end
  end

  describe "JSON round-trip" do
    test "encodes and decodes a user model" do
      model = %Model{
        user_id: "user-alice-123",
        model_version: 7,
        updated_at: "2026-03-28T12:00:00Z",
        communication: %CommunicationProfile{
          verbosity: -0.6,
          formality: 0.2,
          prefers_examples: true,
          prefers_explanations: false,
          languages: ["en", "ja"]
        },
        expertise: [
          %ExpertiseDomain{
            domain: "rust",
            level: :expert,
            confidence: 0.95,
            evidence_sessions: ["sess-001", "sess-003"],
            last_observed: "2026-03-28T09:00:00Z"
          }
        ],
        corrections: [
          %Correction{
            what_agent_did: "Suggested using unwrap()",
            what_user_wanted: "Use proper error handling",
            context: "Rust code generation",
            session_id: "sess-003",
            timestamp: "2026-03-12T16:45:00Z"
          }
        ],
        stated_preferences: [
          %StatedPreference{key: "theme", value: "dark", timestamp: "2026-03-10T10:00:00Z"}
        ],
        metadata: %{}
      }

      json = Model.to_json(model)
      decoded = Model.from_json(json)

      assert decoded.user_id == "user-alice-123"
      assert decoded.model_version == 7
      assert decoded.communication.verbosity == -0.6
      assert decoded.communication.formality == 0.2
      assert length(decoded.expertise) == 1
      assert hd(decoded.expertise).domain == "rust"
      assert hd(decoded.expertise).level == :expert
      assert length(decoded.corrections) == 1
      assert length(decoded.stated_preferences) == 1
    end
  end

  describe "spec example parsing" do
    test "parses user-model.json from spec examples" do
      path = Path.join([__DIR__, "..", "..", "spec", "v1", "examples", "user-model.json"])

      if File.exists?(path) do
        model = Model.from_json(File.read!(path))

        assert model.user_id == "user-alice-123"
        assert model.model_version == 7
        assert model.communication != nil
        assert model.communication.verbosity == -0.6
        assert model.communication.formality == 0.2
        assert length(model.expertise) == 3
        assert length(model.corrections) == 1
        assert length(model.stated_preferences) == 2

        errors = OampTypes.Validate.validate_user_model(model)
        assert errors == []
      end
    end
  end
end