defmodule OampTypes do
  @moduledoc """
  Elixir types for the Open Agent Memory Protocol (OAMP) v1.

  OAMP defines a standard format for storing, exchanging, and querying
  memory data between AI agents and memory backends.
  """

  @oamp_version "1.0.0"

  @doc """
  Returns the current OAMP version.
  """
  def oamp_version, do: @oamp_version
end