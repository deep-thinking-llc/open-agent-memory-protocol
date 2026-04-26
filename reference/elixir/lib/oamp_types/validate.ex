defmodule OampTypes.Validate do
  @moduledoc """
  Validation functions for OAMP types.

  These functions perform semantic validation and return a list of error
  strings. An empty list means the document is valid.
  """

  alias OampTypes.{KnowledgeCategory, ExpertiseLevel}
  alias OampTypes.Knowledge.{Entry, Store}
  alias OampTypes.UserModel.Model

  # OAMP version constant (for future version validation)
  # @oamp_version_val OampTypes.oamp_version()
  @uuid_regex ~r/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

  @doc """
  Validates a KnowledgeEntry, returning a list of error strings.
  """
  def validate_knowledge_entry(%Entry{} = entry) do
    errors = []

    errors = if entry.id == nil or entry.id == "",
      do: ["id is required" | errors], else: errors

    errors = if entry.id != nil and entry.id != "" and not Regex.match?(@uuid_regex, entry.id),
      do: ["id must be a valid UUID v4, got '#{entry.id}'" | errors], else: errors

    errors = if entry.user_id == nil or entry.user_id == "",
      do: ["user_id is required" | errors], else: errors

    errors = if not KnowledgeCategory.valid?(entry.category),
      do: ["invalid category: '#{entry.category}'" | errors], else: errors

    errors = if entry.content == nil or entry.content == "",
      do: ["content is required" | errors], else: errors

    errors = if entry.confidence == nil or entry.confidence < 0.0 or entry.confidence > 1.0,
      do: ["confidence must be 0.0-1.0, got #{entry.confidence}" | errors], else: errors

    errors = if entry.source == nil or entry.source.session_id == nil or entry.source.session_id == "",
      do: ["source.session_id is required" | errors], else: errors

    Enum.reverse(errors)
  end

  @doc """
  Validates a KnowledgeStore, returning a list of error strings.
  """
  def validate_knowledge_store(%Store{} = store) do
    errors = []

    errors = if store.user_id == nil or store.user_id == "",
      do: ["user_id is required" | errors], else: errors

    errors = if store.exported_at == nil,
      do: ["exported_at is required" | errors], else: errors

    entry_errors =
      store.entries
      |> Enum.with_index()
      |> Enum.flat_map(fn {entry, i} ->
        validate_knowledge_entry(entry)
        |> Enum.map(fn err -> "entries[#{i}]: #{err}" end)
      end)

    Enum.reverse(errors) ++ entry_errors
  end

  @doc """
  Validates a UserModel, returning a list of error strings.
  """
  def validate_user_model(%Model{} = model) do
    errors = []

    errors = if model.user_id == nil or model.user_id == "",
      do: ["user_id is required" | errors], else: errors

    errors = if model.model_version == nil or model.model_version < 1,
      do: ["model_version must be >= 1, got #{model.model_version}" | errors], else: errors

    errors = if model.updated_at == nil,
      do: ["updated_at is required" | errors], else: errors

    # Validate communication
    errors =
      if model.communication != nil do
        c = model.communication
        errs = []
        errs = if c.verbosity < -1.0 or c.verbosity > 1.0,
          do: ["verbosity must be -1.0 to 1.0, got #{c.verbosity}" | errs], else: errs
        errs = if c.formality < -1.0 or c.formality > 1.0,
          do: ["formality must be -1.0 to 1.0, got #{c.formality}" | errs], else: errs
        errs ++ errors
      else
        errors
      end

    # Validate expertise confidence
    expertise_errors =
      model.expertise
      |> Enum.with_index()
      |> Enum.flat_map(fn {exp, i} ->
        errs = []
        errs = if exp.confidence < 0.0 or exp.confidence > 1.0,
          do: ["expertise[#{i}].confidence must be 0.0-1.0, got #{exp.confidence}" | errs], else: errs
        errs = if not ExpertiseLevel.valid?(exp.level),
          do: ["expertise[#{i}]: invalid level '#{exp.level}'" | errs], else: errs
        errs
      end)

    Enum.reverse(errors) ++ expertise_errors
  end
end