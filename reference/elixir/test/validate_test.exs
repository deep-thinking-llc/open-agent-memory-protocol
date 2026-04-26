defmodule OampTypes.ValidateTest do
  use ExUnit.Case, async: true

  alias OampTypes.Validate
  alias OampTypes.Knowledge.{Entry, Source}
  alias OampTypes.UserModel.{Model, CommunicationProfile, ExpertiseDomain}

  describe "validate_knowledge_entry/1" do
    test "valid entry has no errors" do
      entry = %Entry{
        id: "550e8400-e29b-41d4-a716-446655440000",
        user_id: "user-1",
        category: :fact,
        content: "test content",
        confidence: 0.8,
        source: %Source{session_id: "sess-1", timestamp: "2026-03-15T14:32:00Z"}
      }

      assert Validate.validate_knowledge_entry(entry) == []
    end

    test "invalid confidence produces error" do
      entry = %Entry{
        id: "550e8400-e29b-41d4-a716-446655440000",
        user_id: "user-1",
        category: :fact,
        content: "test",
        confidence: 1.5,
        source: %Source{session_id: "sess-1", timestamp: "2026-03-15T14:32:00Z"}
      }

      errors = Validate.validate_knowledge_entry(entry)
      assert length(errors) > 0
    end

    test "empty content produces error" do
      entry = %Entry{
        id: "550e8400-e29b-41d4-a716-446655440000",
        user_id: "user-1",
        category: :fact,
        content: "",
        confidence: 0.8,
        source: %Source{session_id: "sess-1", timestamp: "2026-03-15T14:32:00Z"}
      }

      errors = Validate.validate_knowledge_entry(entry)
      assert "content is required" in errors
    end

    test "invalid category produces error" do
      entry = %Entry{
        id: "550e8400-e29b-41d4-a716-446655440000",
        user_id: "user-1",
        category: :unknown,
        content: "test",
        confidence: 0.8,
        source: %Source{session_id: "sess-1", timestamp: "2026-03-15T14:32:00Z"}
      }

      errors = Validate.validate_knowledge_entry(entry)
      assert length(errors) > 0
    end
  end

  describe "validate_user_model/1" do
    test "valid model has no errors" do
      model = Model.new("user-1", updated_at: "2026-03-28T12:00:00Z")
      assert Validate.validate_user_model(model) == []
    end

    test "invalid verbosity produces error" do
      model = %Model{
        user_id: "user-1",
        model_version: 1,
        updated_at: "2026-03-28T12:00:00Z",
        communication: %CommunicationProfile{verbosity: 2.0, formality: 0.0}
      }

      errors = Validate.validate_user_model(model)
      assert length(errors) > 0
    end

    test "invalid model_version produces error" do
      model = %Model{user_id: "user-1", model_version: 0, updated_at: "2026-03-28T12:00:00Z"}

      errors = Validate.validate_user_model(model)
      assert length(errors) > 0
    end

    test "expertise with invalid confidence produces error" do
      model = %Model{
        user_id: "user-1",
        model_version: 1,
        updated_at: "2026-03-28T12:00:00Z",
        expertise: [
          %ExpertiseDomain{domain: "rust", level: :expert, confidence: 1.5}
        ]
      }

      errors = Validate.validate_user_model(model)
      assert length(errors) > 0
    end
  end
end