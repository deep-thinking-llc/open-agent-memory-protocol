from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ExpertiseLevel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EXPERTISE_LEVEL_UNSPECIFIED: _ClassVar[ExpertiseLevel]
    EXPERTISE_LEVEL_NOVICE: _ClassVar[ExpertiseLevel]
    EXPERTISE_LEVEL_INTERMEDIATE: _ClassVar[ExpertiseLevel]
    EXPERTISE_LEVEL_ADVANCED: _ClassVar[ExpertiseLevel]
    EXPERTISE_LEVEL_EXPERT: _ClassVar[ExpertiseLevel]
EXPERTISE_LEVEL_UNSPECIFIED: ExpertiseLevel
EXPERTISE_LEVEL_NOVICE: ExpertiseLevel
EXPERTISE_LEVEL_INTERMEDIATE: ExpertiseLevel
EXPERTISE_LEVEL_ADVANCED: ExpertiseLevel
EXPERTISE_LEVEL_EXPERT: ExpertiseLevel

class CommunicationProfile(_message.Message):
    __slots__ = ("verbosity", "formality", "prefers_examples", "prefers_explanations", "languages")
    VERBOSITY_FIELD_NUMBER: _ClassVar[int]
    FORMALITY_FIELD_NUMBER: _ClassVar[int]
    PREFERS_EXAMPLES_FIELD_NUMBER: _ClassVar[int]
    PREFERS_EXPLANATIONS_FIELD_NUMBER: _ClassVar[int]
    LANGUAGES_FIELD_NUMBER: _ClassVar[int]
    verbosity: float
    formality: float
    prefers_examples: bool
    prefers_explanations: bool
    languages: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, verbosity: _Optional[float] = ..., formality: _Optional[float] = ..., prefers_examples: bool = ..., prefers_explanations: bool = ..., languages: _Optional[_Iterable[str]] = ...) -> None: ...

class ExpertiseDomain(_message.Message):
    __slots__ = ("domain", "level", "confidence", "evidence_sessions", "last_observed")
    DOMAIN_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    EVIDENCE_SESSIONS_FIELD_NUMBER: _ClassVar[int]
    LAST_OBSERVED_FIELD_NUMBER: _ClassVar[int]
    domain: str
    level: ExpertiseLevel
    confidence: float
    evidence_sessions: _containers.RepeatedScalarFieldContainer[str]
    last_observed: str
    def __init__(self, domain: _Optional[str] = ..., level: _Optional[_Union[ExpertiseLevel, str]] = ..., confidence: _Optional[float] = ..., evidence_sessions: _Optional[_Iterable[str]] = ..., last_observed: _Optional[str] = ...) -> None: ...

class Correction(_message.Message):
    __slots__ = ("what_agent_did", "what_user_wanted", "context", "session_id", "timestamp")
    WHAT_AGENT_DID_FIELD_NUMBER: _ClassVar[int]
    WHAT_USER_WANTED_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    what_agent_did: str
    what_user_wanted: str
    context: str
    session_id: str
    timestamp: str
    def __init__(self, what_agent_did: _Optional[str] = ..., what_user_wanted: _Optional[str] = ..., context: _Optional[str] = ..., session_id: _Optional[str] = ..., timestamp: _Optional[str] = ...) -> None: ...

class StatedPreference(_message.Message):
    __slots__ = ("key", "value", "timestamp")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: str
    timestamp: str
    def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ..., timestamp: _Optional[str] = ...) -> None: ...

class UserModel(_message.Message):
    __slots__ = ("oamp_version", "type", "user_id", "model_version", "updated_at", "communication", "expertise", "corrections", "stated_preferences", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    OAMP_VERSION_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    MODEL_VERSION_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    COMMUNICATION_FIELD_NUMBER: _ClassVar[int]
    EXPERTISE_FIELD_NUMBER: _ClassVar[int]
    CORRECTIONS_FIELD_NUMBER: _ClassVar[int]
    STATED_PREFERENCES_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    oamp_version: str
    type: str
    user_id: str
    model_version: int
    updated_at: str
    communication: CommunicationProfile
    expertise: _containers.RepeatedCompositeFieldContainer[ExpertiseDomain]
    corrections: _containers.RepeatedCompositeFieldContainer[Correction]
    stated_preferences: _containers.RepeatedCompositeFieldContainer[StatedPreference]
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, oamp_version: _Optional[str] = ..., type: _Optional[str] = ..., user_id: _Optional[str] = ..., model_version: _Optional[int] = ..., updated_at: _Optional[str] = ..., communication: _Optional[_Union[CommunicationProfile, _Mapping]] = ..., expertise: _Optional[_Iterable[_Union[ExpertiseDomain, _Mapping]]] = ..., corrections: _Optional[_Iterable[_Union[Correction, _Mapping]]] = ..., stated_preferences: _Optional[_Iterable[_Union[StatedPreference, _Mapping]]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
