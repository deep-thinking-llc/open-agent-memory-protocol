defmodule OampTypes.ExpertiseLevelTest do
  use ExUnit.Case, async: true

  alias OampTypes.ExpertiseLevel

  test "valid levels are recognized" do
    for level <- ExpertiseLevel.valid_levels() do
      assert ExpertiseLevel.valid?(level)
    end
  end

  test "unknown level is invalid" do
    refute ExpertiseLevel.valid?(:guru)
  end

  test "to_string converts atoms to strings" do
    assert ExpertiseLevel.to_string_value(:novice) == "novice"
    assert ExpertiseLevel.to_string_value(:intermediate) == "intermediate"
    assert ExpertiseLevel.to_string_value(:advanced) == "advanced"
    assert ExpertiseLevel.to_string_value(:expert) == "expert"
  end

  test "from_string parses valid strings" do
    assert ExpertiseLevel.from_string("novice") == {:ok, :novice}
    assert ExpertiseLevel.from_string("expert") == {:ok, :expert}
  end

  test "from_string rejects invalid strings" do
    assert {:error, _} = ExpertiseLevel.from_string("guru")
  end
end