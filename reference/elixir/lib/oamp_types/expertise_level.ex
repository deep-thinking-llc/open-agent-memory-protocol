defmodule OampTypes.ExpertiseLevel do
  @moduledoc """
  Level of expertise in a domain.

  Valid values: `:novice`, `:intermediate`, `:advanced`, `:expert`
  """

  @valid_levels [:novice, :intermediate, :advanced, :expert]

  @doc """
  Returns the list of valid expertise levels.
  """
  def valid_levels, do: @valid_levels

  @doc """
  Checks if the given atom is a valid expertise level.
  """
  def valid?(level) when level in @valid_levels, do: true
  def valid?(_), do: false

  @doc """
  Converts an expertise level atom to its string representation.
  """
  def to_string_value(:novice), do: "novice"
  def to_string_value(:intermediate), do: "intermediate"
  def to_string_value(:advanced), do: "advanced"
  def to_string_value(:expert), do: "expert"
  def to_string_value(other), do: Atom.to_string(other)

  @doc """
  Parses a string into an expertise level atom, or returns an error.
  """
  def from_string("novice"), do: {:ok, :novice}
  def from_string("intermediate"), do: {:ok, :intermediate}
  def from_string("advanced"), do: {:ok, :advanced}
  def from_string("expert"), do: {:ok, :expert}
  def from_string(other), do: {:error, "invalid expertise level: #{other}"}
end