defmodule OampTypes.KnowledgeCategory do
  @moduledoc """
  Category of a knowledge entry.

  Valid values: `:fact`, `:preference`, `:pattern`, `:correction`
  """

  @valid_categories [:fact, :preference, :pattern, :correction]

  @doc """
  Returns the list of valid knowledge categories.
  """
  def valid_categories, do: @valid_categories

  @doc """
  Checks if the given atom is a valid knowledge category.
  """
  def valid?(category) when category in @valid_categories, do: true
  def valid?(_), do: false

  @doc """
  Converts a knowledge category atom to its string representation.
  """
  def to_string_value(:fact), do: "fact"
  def to_string_value(:preference), do: "preference"
  def to_string_value(:pattern), do: "pattern"
  def to_string_value(:correction), do: "correction"
  def to_string_value(other), do: Atom.to_string(other)

  @doc """
  Parses a string into a knowledge category atom, or returns an error.
  """
  def from_string("fact"), do: {:ok, :fact}
  def from_string("preference"), do: {:ok, :preference}
  def from_string("pattern"), do: {:ok, :pattern}
  def from_string("correction"), do: {:ok, :correction}
  def from_string(other), do: {:error, "invalid knowledge category: #{other}"}
end