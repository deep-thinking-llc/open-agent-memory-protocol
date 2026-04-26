defmodule OampTypes.Knowledge do
  @moduledoc """
  Knowledge entry and store types for OAMP v1.
  """

  alias OampTypes.KnowledgeCategory

  # OAMP version is set in JSON encoding via OampTypes.oamp_version()

  defmodule Source do
    @moduledoc """
    Provenance information for a knowledge entry.
    """
    @enforce_keys [:session_id, :timestamp]
    defstruct [:session_id, :agent_id, :timestamp]

    @type t :: %__MODULE__{
      session_id: String.t(),
      agent_id: String.t() | nil,
      timestamp: String.t()
    }
  end

  defmodule Decay do
    @moduledoc """
    Temporal decay parameters for confidence.
    """
    defstruct [:half_life_days, :last_confirmed]

    @type t :: %__MODULE__{
      half_life_days: float() | nil,
      last_confirmed: String.t() | nil
    }
  end

  defmodule Entry do
    @moduledoc """
    A discrete piece of information an agent has learned about a user.
    """
    @enforce_keys [:id, :user_id, :category, :content, :confidence, :source]
    defstruct [
      :id,
      :user_id,
      :category,
      :content,
      :confidence,
      :source,
      :decay,
      tags: [],
      metadata: %{}
    ]

    @type t :: %__MODULE__{
      id: String.t(),
      user_id: String.t(),
      category: atom(),
      content: String.t(),
      confidence: float(),
      source: Source.t(),
      decay: Decay.t() | nil,
      tags: [String.t()],
      metadata: map()
    }

    @doc """
    Creates a new knowledge entry with sensible defaults.
    """
    def new(user_id, category, content, confidence, session_id, opts \\ []) do
      %__MODULE__{
        id: Keyword.get(opts, :id, generate_uuid()),
        user_id: user_id,
        category: category,
        content: content,
        confidence: confidence,
        source: %Source{
          session_id: session_id,
          agent_id: Keyword.get(opts, :agent_id),
          timestamp: Keyword.get(opts, :timestamp, DateTime.utc_now() |> DateTime.to_iso8601())
        },
        decay: Keyword.get(opts, :decay),
        tags: Keyword.get(opts, :tags, []),
        metadata: Keyword.get(opts, :metadata, %{})
      }
    end

    @doc """
    Encodes a knowledge entry to JSON.
    """
    def to_json(entry) do
      Jason.encode!(entry, pretty: true)
    end

    @doc """
    Decodes a knowledge entry from JSON.
    """
    def from_json(json) when is_binary(json) do
      case Jason.decode!(json) do
        %{"type" => "knowledge_entry"} = data -> from_map(data)
        data -> from_map(data)
      end
    end

    def from_map(data) do
      category =
        case Map.get(data, "category") do
          cat when is_atom(cat) -> cat
          cat when is_binary(cat) ->
            {:ok, atom} = KnowledgeCategory.from_string(cat)
            atom
        end

      source = %Source{
        session_id: data["source"]["session_id"],
        agent_id: data["source"]["agent_id"],
        timestamp: data["source"]["timestamp"]
      }

      decay =
        case data["decay"] do
          nil -> nil
          d ->
            %Decay{
              half_life_days: d["half_life_days"],
              last_confirmed: d["last_confirmed"]
            }
        end

      %__MODULE__{
        id: Map.get(data, "id", generate_uuid()),
        user_id: data["user_id"],
        category: category,
        content: data["content"],
        confidence: data["confidence"],
        source: source,
        decay: decay,
        tags: Map.get(data, "tags", []),
        metadata: Map.get(data, "metadata", %{})
      }
    end

    defp generate_uuid do
      import Bitwise
      <<a::32, b::16, c::16, d::16, e::48>> = :crypto.strong_rand_bytes(16)
      # Set version to 4 and variant to RFC 4122
      c_versioned = (c &&& 0x0FFF) ||| 0x4000
      d_varianted = (d &&& 0x3FFF) ||| 0x8000
      :io_lib.format("~8.16.0b-~4.16.0b-~4.16.0b-~4.16.0b-~12.16.0b", [a, b, c_versioned, d_varianted, e])
      |> to_string()
      |> String.downcase()
    end
  end

  defmodule Store do
    @moduledoc """
    A collection of knowledge entries for bulk export/import.
    """
    @enforce_keys [:user_id]
    defstruct [
      :user_id,
      entries: [],
      exported_at: nil,
      agent_id: nil
    ]

    @type t :: %__MODULE__{
      user_id: String.t(),
      entries: [Entry.t()],
      exported_at: String.t() | nil,
      agent_id: String.t() | nil
    }

    @doc """
    Creates a new knowledge store.
    """
    def new(user_id, entries \\ [], opts \\ []) do
      %__MODULE__{
        user_id: user_id,
        entries: entries,
        exported_at: Keyword.get(opts, :exported_at, DateTime.utc_now() |> DateTime.to_iso8601()),
        agent_id: Keyword.get(opts, :agent_id)
      }
    end

    @doc """
    Encodes a knowledge store to JSON.
    """
    def to_json(store) do
      Jason.encode!(store, pretty: true)
    end

    @doc """
    Decodes a knowledge store from JSON.
    """
    def from_json(json) when is_binary(json) do
      data = Jason.decode!(json)
      from_map(data)
    end

    def from_map(data) do
      entries =
        case data["entries"] do
          nil -> []
          entries -> Enum.map(entries, &Entry.from_map/1)
        end

      %__MODULE__{
        user_id: data["user_id"],
        entries: entries,
        exported_at: data["exported_at"],
        agent_id: data["agent_id"]
      }
    end
  end

  # Jason.Encoder implementations

  defimpl Jason.Encoder, for: Source do
    def encode(source, opts) do
      fields =
        [{"session_id", source.session_id}, {"timestamp", source.timestamp}] ++
          if(source.agent_id, do: [{"agent_id", source.agent_id}], else: [])

      Jason.Encode.map(fields |> Enum.into(%{}), opts)
    end
  end

  defimpl Jason.Encoder, for: Decay do
    def encode(decay, opts) do
      fields = []
      fields = if decay.half_life_days != nil, do: fields ++ [{"half_life_days", decay.half_life_days}], else: fields
      fields = if decay.last_confirmed != nil, do: fields ++ [{"last_confirmed", decay.last_confirmed}], else: fields

      Jason.Encode.map(fields |> Enum.into(%{}), opts)
    end
  end

  defimpl Jason.Encoder, for: Entry do
    def encode(entry, opts) do
      fields = %{
        "oamp_version" => OampTypes.oamp_version(),
        "type" => "knowledge_entry",
        "id" => entry.id,
        "user_id" => entry.user_id,
        "category" => KnowledgeCategory.to_string_value(entry.category),
        "content" => entry.content,
        "confidence" => entry.confidence,
        "source" => entry.source
      }

      fields = if entry.decay, do: Map.put(fields, "decay", entry.decay), else: fields
      fields = if entry.tags != [], do: Map.put(fields, "tags", entry.tags), else: fields
      fields = if entry.metadata != %{}, do: Map.put(fields, "metadata", entry.metadata), else: fields

      Jason.Encode.map(fields, opts)
    end
  end

  defimpl Jason.Encoder, for: Store do
    def encode(store, opts) do
      fields = %{
        "oamp_version" => OampTypes.oamp_version(),
        "type" => "knowledge_store",
        "user_id" => store.user_id,
        "entries" => store.entries,
        "exported_at" => store.exported_at
      }

      fields = if store.agent_id, do: Map.put(fields, "agent_id", store.agent_id), else: fields

      Jason.Encode.map(fields, opts)
    end
  end
end