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

  defmodule GovernanceHandling do
    @moduledoc """
    Surface-specific handling hints for governed memory.
    """
    defstruct [:retrieval, :export, :stream]

    @type t :: %__MODULE__{
      retrieval: String.t() | nil,
      export: String.t() | nil,
      stream: String.t() | nil
    }
  end

  defmodule Governance do
    @moduledoc """
    Standard governed-memory metadata.
    """
    @enforce_keys [:sensitivity_class]
    defstruct [:sensitivity_class, labels: [], handling: nil]

    @type t :: %__MODULE__{
      sensitivity_class: String.t(),
      labels: [String.t()],
      handling: GovernanceHandling.t() | nil
    }
  end

  defmodule ProvenanceSource do
    @moduledoc """
    Extended lineage record for multi-source provenance.
    """
    @enforce_keys [:session_id, :timestamp]
    defstruct [:session_id, :agent_id, :timestamp, :turn_id]

    @type t :: %__MODULE__{
      session_id: String.t(),
      agent_id: String.t() | nil,
      timestamp: String.t(),
      turn_id: String.t() | nil
    }
  end

  defmodule Provenance do
    @moduledoc """
    Extended provenance metadata for synthesized or multi-source memories.
    """
    @enforce_keys [:sources]
    defstruct [:derived, sources: []]

    @type t :: %__MODULE__{
      derived: boolean() | nil,
      sources: [ProvenanceSource.t()]
    }
  end

  defmodule Entry do
    @moduledoc """
    A discrete piece of information an agent has learned about a user.
    """
    @enforce_keys [:id, :user_id, :category, :content, :confidence, :source]
    defstruct [
      :oamp_version,
      :id,
      :user_id,
      :category,
      :content,
      :confidence,
      :source,
      :provenance,
      :governance,
      :decay,
      tags: [],
      metadata: %{}
    ]

    @type t :: %__MODULE__{
      oamp_version: String.t() | nil,
      id: String.t(),
      user_id: String.t(),
      category: atom(),
      content: String.t(),
      confidence: float(),
      source: Source.t(),
      provenance: Provenance.t() | nil,
      governance: Governance.t() | nil,
      decay: Decay.t() | nil,
      tags: [String.t()],
      metadata: map()
    }

    @doc """
    Creates a new knowledge entry with sensible defaults.
    """
    def new(user_id, category, content, confidence, session_id, opts \\ []) do
      %__MODULE__{
        oamp_version: Keyword.get(opts, :oamp_version, OampTypes.oamp_version()),
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
        provenance: Keyword.get(opts, :provenance),
        governance: Keyword.get(opts, :governance),
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

      provenance =
        case data["provenance"] do
          nil -> nil
          p ->
            %Provenance{
              derived: p["derived"],
              sources:
                Enum.map(p["sources"], fn source ->
                  %ProvenanceSource{
                    session_id: source["session_id"],
                    agent_id: source["agent_id"],
                    timestamp: source["timestamp"],
                    turn_id: source["turn_id"]
                  }
                end)
            }
        end

      governance =
        case data["governance"] do
          nil -> nil
          g ->
            handling =
              case g["handling"] do
                nil -> nil
                h ->
                  %GovernanceHandling{
                    retrieval: h["retrieval"],
                    export: h["export"],
                    stream: h["stream"]
                  }
              end

            %Governance{
              sensitivity_class: g["sensitivity_class"],
              labels: Map.get(g, "labels", []),
              handling: handling
            }
        end

      %__MODULE__{
        oamp_version: Map.get(data, "oamp_version", OampTypes.oamp_version()),
        id: Map.get(data, "id", generate_uuid()),
        user_id: data["user_id"],
        category: category,
        content: data["content"],
        confidence: data["confidence"],
        source: source,
        provenance: provenance,
        governance: governance,
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
      agent_id: nil,
      metadata: nil
    ]

    @type t :: %__MODULE__{
      user_id: String.t(),
      entries: [Entry.t()],
      exported_at: String.t() | nil,
      agent_id: String.t() | nil,
      metadata: map() | nil
    }

    @doc """
    Creates a new knowledge store.
    """
    def new(user_id, entries \\ [], opts \\ []) do
      %__MODULE__{
        user_id: user_id,
        entries: entries,
        exported_at: Keyword.get(opts, :exported_at, DateTime.utc_now() |> DateTime.to_iso8601()),
        agent_id: Keyword.get(opts, :agent_id),
        metadata: Keyword.get(opts, :metadata)
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
        agent_id: data["agent_id"],
        metadata: data["metadata"]
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
        "oamp_version" => entry.oamp_version || OampTypes.oamp_version(),
        "type" => "knowledge_entry",
        "id" => entry.id,
        "user_id" => entry.user_id,
        "category" => KnowledgeCategory.to_string_value(entry.category),
        "content" => entry.content,
        "confidence" => entry.confidence,
        "source" => entry.source
      }

      fields = if entry.decay, do: Map.put(fields, "decay", entry.decay), else: fields
      fields = if entry.provenance, do: Map.put(fields, "provenance", entry.provenance), else: fields
      fields = if entry.governance, do: Map.put(fields, "governance", entry.governance), else: fields
      fields = if entry.tags != [], do: Map.put(fields, "tags", entry.tags), else: fields
      fields = if entry.metadata != %{}, do: Map.put(fields, "metadata", entry.metadata), else: fields

      Jason.Encode.map(fields, opts)
    end
  end

  defimpl Jason.Encoder, for: GovernanceHandling do
    def encode(handling, opts) do
      fields = %{}
      fields = if handling.retrieval, do: Map.put(fields, "retrieval", handling.retrieval), else: fields
      fields = if handling.export, do: Map.put(fields, "export", handling.export), else: fields
      fields = if handling.stream, do: Map.put(fields, "stream", handling.stream), else: fields
      Jason.Encode.map(fields, opts)
    end
  end

  defimpl Jason.Encoder, for: Governance do
    def encode(governance, opts) do
      fields = %{"sensitivity_class" => governance.sensitivity_class}
      fields = if governance.labels != [], do: Map.put(fields, "labels", governance.labels), else: fields
      fields = if governance.handling, do: Map.put(fields, "handling", governance.handling), else: fields
      Jason.Encode.map(fields, opts)
    end
  end

  defimpl Jason.Encoder, for: ProvenanceSource do
    def encode(source, opts) do
      fields = %{
        "session_id" => source.session_id,
        "timestamp" => source.timestamp
      }

      fields = if source.agent_id, do: Map.put(fields, "agent_id", source.agent_id), else: fields
      fields = if source.turn_id, do: Map.put(fields, "turn_id", source.turn_id), else: fields
      Jason.Encode.map(fields, opts)
    end
  end

  defimpl Jason.Encoder, for: Provenance do
    def encode(provenance, opts) do
      fields = %{"sources" => provenance.sources}
      fields = if provenance.derived != nil, do: Map.put(fields, "derived", provenance.derived), else: fields
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
      fields = if store.metadata, do: Map.put(fields, "metadata", store.metadata), else: fields

      Jason.Encode.map(fields, opts)
    end
  end
end
