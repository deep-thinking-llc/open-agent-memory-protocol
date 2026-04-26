defmodule OampTypes.KnowledgeTest do
  use ExUnit.Case, async: true

  alias OampTypes.Knowledge.{Entry, Source, Decay, Store}

  describe "new/5" do
    test "creates a knowledge entry with defaults" do
      entry = Entry.new("user-1", :preference, "likes dark mode", 0.8, "sess-1")

      # oamp_version is added during JSON encoding
      json = Entry.to_json(entry)
      assert json =~ "\"oamp_version\": \"1.0.0\""
      assert json =~ "\"type\": \"knowledge_entry\""
      assert entry.user_id == "user-1"
      assert entry.category == :preference
      assert entry.content == "likes dark mode"
      assert entry.confidence == 0.8
      assert entry.source.session_id == "sess-1"
      assert entry.tags == []
      assert entry.decay == nil
    end
  end

  describe "JSON round-trip" do
    test "encodes and decodes a knowledge entry" do
      entry = %Entry{
        id: "550e8400-e29b-41d4-a716-446655440000",
        user_id: "user-alice-123",
        category: :preference,
        content: "User prefers concise answers",
        confidence: 0.85,
        source: %Source{
          session_id: "sess-001",
          agent_id: "my-agent",
          timestamp: "2026-03-15T14:32:00Z"
        },
        decay: %Decay{half_life_days: 140.0, last_confirmed: "2026-03-28T09:15:00Z"},
        tags: ["communication", "response-style"],
        metadata: %{}
      }

      json = Entry.to_json(entry)
      decoded = Entry.from_json(json)

      assert decoded.id == entry.id
      assert decoded.user_id == entry.user_id
      assert decoded.category == :preference
      assert decoded.content == entry.content
      assert decoded.confidence == entry.confidence
      assert decoded.source.session_id == "sess-001"
      assert decoded.source.agent_id == "my-agent"
      assert decoded.decay.half_life_days == 140.0
      assert decoded.tags == ["communication", "response-style"]
    end
  end

  describe "spec example parsing" do
    test "parses knowledge-entry.json from spec examples" do
      path = Path.join([__DIR__, "..", "..", "spec", "v1", "examples", "knowledge-entry.json"])

      if File.exists?(path) do
        entry = Entry.from_json(File.read!(path))

        # Verify round-trip: encode back and check oamp_version
        json = Entry.to_json(entry)
        assert json =~ "\"oamp_version\": \"1.0.0\""
        assert entry.category == :preference
        assert entry.confidence == 0.85
        assert entry.source.session_id == "sess-2026-03-15-001"

        errors = OampTypes.Validate.validate_knowledge_entry(entry)
        assert errors == []
      end
    end

    test "parses knowledge-store.json from spec examples" do
      path = Path.join([__DIR__, "..", "..", "spec", "v1", "examples", "knowledge-store.json"])

      if File.exists?(path) do
        store = Store.from_json(File.read!(path))

        assert store.user_id == "user-alice-123"
        assert length(store.entries) == 3

        errors = OampTypes.Validate.validate_knowledge_store(store)
        assert errors == []
      end
    end
  end

  describe "knowledge store" do
    test "creates a new store with defaults" do
      store = Store.new("user-1")

      assert store.user_id == "user-1"
      assert store.entries == []
      assert store.agent_id == nil
    end
  end
end