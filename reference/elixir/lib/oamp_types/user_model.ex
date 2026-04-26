defmodule OampTypes.UserModel do
  @moduledoc """
  User model types for OAMP v1.
  """

  alias OampTypes.ExpertiseLevel

  :ok

  defmodule CommunicationProfile do
    @moduledoc """
    How the user prefers to interact with agents.
    """
    defstruct verbosity: 0.0, formality: 0.0, prefers_examples: true, prefers_explanations: true, languages: ["en"]

    @type t :: %__MODULE__{
      verbosity: float(),
      formality: float(),
      prefers_examples: boolean(),
      prefers_explanations: boolean(),
      languages: [String.t()]
    }

    def from_map(data) when is_map(data) do
      %__MODULE__{
        verbosity: data["verbosity"] || 0.0,
        formality: data["formality"] || 0.0,
        prefers_examples: Map.get(data, "prefers_examples", true),
        prefers_explanations: Map.get(data, "prefers_explanations", true),
        languages: Map.get(data, "languages", ["en"])
      }
    end
  end

  defmodule ExpertiseDomain do
    @moduledoc """
    The user's demonstrated knowledge in a domain.
    """
    @enforce_keys [:domain, :level, :confidence]
    defstruct [:domain, :level, :confidence, evidence_sessions: [], last_observed: nil]

    @type t :: %__MODULE__{
      domain: String.t(),
      level: atom(),
      confidence: float(),
      evidence_sessions: [String.t()],
      last_observed: String.t() | nil
    }

    def from_map(data) when is_map(data) do
      level =
        case Map.get(data, "level") do
          l when is_atom(l) -> l
          l when is_binary(l) ->
            {:ok, atom} = ExpertiseLevel.from_string(l)
            atom
        end

      %__MODULE__{
        domain: data["domain"],
        level: level,
        confidence: data["confidence"],
        evidence_sessions: Map.get(data, "evidence_sessions", []),
        last_observed: data["last_observed"]
      }
    end
  end

  defmodule Correction do
    @moduledoc """
    A record of the user correcting the agent's behavior.
    """
    @enforce_keys [:what_agent_did, :what_user_wanted, :session_id, :timestamp]
    defstruct [:what_agent_did, :what_user_wanted, :context, :session_id, :timestamp]

    @type t :: %__MODULE__{
      what_agent_did: String.t(),
      what_user_wanted: String.t(),
      context: String.t() | nil,
      session_id: String.t(),
      timestamp: String.t()
    }

    def from_map(data) when is_map(data) do
      %__MODULE__{
        what_agent_did: data["what_agent_did"],
        what_user_wanted: data["what_user_wanted"],
        context: data["context"],
        session_id: data["session_id"],
        timestamp: data["timestamp"]
      }
    end
  end

  defmodule StatedPreference do
    @moduledoc """
    A preference the user has explicitly declared.
    """
    @enforce_keys [:key, :value, :timestamp]
    defstruct [:key, :value, :timestamp]

    @type t :: %__MODULE__{
      key: String.t(),
      value: String.t(),
      timestamp: String.t()
    }

    def from_map(data) when is_map(data) do
      %__MODULE__{
        key: data["key"],
        value: data["value"],
        timestamp: data["timestamp"]
      }
    end
  end

  defmodule Model do
    @moduledoc """
    An agent's evolving structured understanding of a user.
    """
    @enforce_keys [:user_id]
    defstruct [
      :user_id,
      model_version: 1,
      updated_at: nil,
      communication: nil,
      expertise: [],
      corrections: [],
      stated_preferences: [],
      metadata: %{}
    ]

    @type t :: %__MODULE__{
      user_id: String.t(),
      model_version: non_neg_integer(),
      updated_at: String.t() | nil,
      communication: CommunicationProfile.t() | nil,
      expertise: [ExpertiseDomain.t()],
      corrections: [Correction.t()],
      stated_preferences: [StatedPreference.t()],
      metadata: map()
    }

    @doc """
    Creates a new user model with sensible defaults.
    """
    def new(user_id, opts \\ []) do
      %__MODULE__{
        user_id: user_id,
        model_version: Keyword.get(opts, :model_version, 1),
        updated_at: Keyword.get(opts, :updated_at, DateTime.utc_now() |> DateTime.to_iso8601()),
        communication: Keyword.get(opts, :communication),
        expertise: Keyword.get(opts, :expertise, []),
        corrections: Keyword.get(opts, :corrections, []),
        stated_preferences: Keyword.get(opts, :stated_preferences, []),
        metadata: Keyword.get(opts, :metadata, %{})
      }
    end

    @doc """
    Encodes a user model to JSON.
    """
    def to_json(model) do
      Jason.encode!(model, pretty: true)
    end

    @doc """
    Decodes a user model from JSON.
    """
    def from_json(json) when is_binary(json) do
      data = Jason.decode!(json)
      from_map(data)
    end

    def from_map(data) when is_map(data) do
      communication =
        case data["communication"] do
          nil -> nil
          c -> CommunicationProfile.from_map(c)
        end

      expertise =
        case data["expertise"] do
          nil -> []
          e -> Enum.map(e, &ExpertiseDomain.from_map/1)
        end

      corrections =
        case data["corrections"] do
          nil -> []
          c -> Enum.map(c, &Correction.from_map/1)
        end

      stated_preferences =
        case data["stated_preferences"] do
          nil -> []
          s -> Enum.map(s, &StatedPreference.from_map/1)
        end

      %__MODULE__{
        user_id: data["user_id"],
        model_version: Map.get(data, "model_version", 1),
        updated_at: data["updated_at"],
        communication: communication,
        expertise: expertise,
        corrections: corrections,
        stated_preferences: stated_preferences,
        metadata: Map.get(data, "metadata", %{})
      }
    end
  end

  # Jason.Encoder implementations

  defimpl Jason.Encoder, for: CommunicationProfile do
    def encode(profile, opts) do
      Jason.Encode.map(%{
        "verbosity" => profile.verbosity,
        "formality" => profile.formality,
        "prefers_examples" => profile.prefers_examples,
        "prefers_explanations" => profile.prefers_explanations,
        "languages" => profile.languages
      }, opts)
    end
  end

  defimpl Jason.Encoder, for: ExpertiseDomain do
    def encode(domain, opts) do
      fields = %{
        "domain" => domain.domain,
        "level" => ExpertiseLevel.to_string_value(domain.level),
        "confidence" => domain.confidence
      }

      fields = if domain.evidence_sessions != [], do: Map.put(fields, "evidence_sessions", domain.evidence_sessions), else: fields
      fields = if domain.last_observed != nil, do: Map.put(fields, "last_observed", domain.last_observed), else: fields

      Jason.Encode.map(fields, opts)
    end
  end

  defimpl Jason.Encoder, for: Correction do
    def encode(correction, opts) do
      fields = %{
        "what_agent_did" => correction.what_agent_did,
        "what_user_wanted" => correction.what_user_wanted,
        "session_id" => correction.session_id,
        "timestamp" => correction.timestamp
      }

      fields = if correction.context != nil, do: Map.put(fields, "context", correction.context), else: fields

      Jason.Encode.map(fields, opts)
    end
  end

  defimpl Jason.Encoder, for: StatedPreference do
    def encode(preference, opts) do
      Jason.Encode.map(%{
        "key" => preference.key,
        "value" => preference.value,
        "timestamp" => preference.timestamp
      }, opts)
    end
  end

  defimpl Jason.Encoder, for: Model do
    def encode(model, opts) do
      fields = %{
        "oamp_version" => OampTypes.oamp_version(),
        "type" => "user_model",
        "user_id" => model.user_id,
        "model_version" => model.model_version,
        "updated_at" => model.updated_at
      }

      fields = if model.communication != nil, do: Map.put(fields, "communication", model.communication), else: fields
      fields = if model.expertise != [], do: Map.put(fields, "expertise", model.expertise), else: fields
      fields = if model.corrections != [], do: Map.put(fields, "corrections", model.corrections), else: fields
      fields = if model.stated_preferences != [], do: Map.put(fields, "stated_preferences", model.stated_preferences), else: fields
      fields = if model.metadata != %{}, do: Map.put(fields, "metadata", model.metadata), else: fields

      Jason.Encode.map(fields, opts)
    end
  end
end