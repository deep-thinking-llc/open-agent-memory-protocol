defmodule OampTypes.KnowledgeCategoryTest do
  use ExUnit.Case, async: true

  alias OampTypes.KnowledgeCategory

  test "valid categories are recognized" do
    for cat <- KnowledgeCategory.valid_categories() do
      assert KnowledgeCategory.valid?(cat)
    end
  end

  test "unknown category is invalid" do
    refute KnowledgeCategory.valid?(:unknown)
    refute KnowledgeCategory.valid?("unknown")
  end

  test "to_string converts atoms to strings" do
    assert KnowledgeCategory.to_string_value(:fact) == "fact"
    assert KnowledgeCategory.to_string_value(:preference) == "preference"
    assert KnowledgeCategory.to_string_value(:pattern) == "pattern"
    assert KnowledgeCategory.to_string_value(:correction) == "correction"
  end

  test "from_string parses valid strings" do
    assert KnowledgeCategory.from_string("fact") == {:ok, :fact}
    assert KnowledgeCategory.from_string("preference") == {:ok, :preference}
    assert KnowledgeCategory.from_string("pattern") == {:ok, :pattern}
    assert KnowledgeCategory.from_string("correction") == {:ok, :correction}
  end

  test "from_string rejects invalid strings" do
    assert {:error, _} = KnowledgeCategory.from_string("unknown")
  end
end