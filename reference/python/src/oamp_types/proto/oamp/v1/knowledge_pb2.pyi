from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class KnowledgeCategory(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    KNOWLEDGE_CATEGORY_UNSPECIFIED: _ClassVar[KnowledgeCategory]
    KNOWLEDGE_CATEGORY_FACT: _ClassVar[KnowledgeCategory]
    KNOWLEDGE_CATEGORY_PREFERENCE: _ClassVar[KnowledgeCategory]
    KNOWLEDGE_CATEGORY_PATTERN: _ClassVar[KnowledgeCategory]
    KNOWLEDGE_CATEGORY_CORRECTION: _ClassVar[KnowledgeCategory]
KNOWLEDGE_CATEGORY_UNSPECIFIED: KnowledgeCategory
KNOWLEDGE_CATEGORY_FACT: KnowledgeCategory
KNOWLEDGE_CATEGORY_PREFERENCE: KnowledgeCategory
KNOWLEDGE_CATEGORY_PATTERN: KnowledgeCategory
KNOWLEDGE_CATEGORY_CORRECTION: KnowledgeCategory

class KnowledgeSource(_message.Message):
    __slots__ = ("session_id", "agent_id", "timestamp")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    agent_id: str
    timestamp: str
    def __init__(self, session_id: _Optional[str] = ..., agent_id: _Optional[str] = ..., timestamp: _Optional[str] = ...) -> None: ...

class KnowledgeDecay(_message.Message):
    __slots__ = ("half_life_days", "last_confirmed")
    HALF_LIFE_DAYS_FIELD_NUMBER: _ClassVar[int]
    LAST_CONFIRMED_FIELD_NUMBER: _ClassVar[int]
    half_life_days: float
    last_confirmed: str
    def __init__(self, half_life_days: _Optional[float] = ..., last_confirmed: _Optional[str] = ...) -> None: ...

class KnowledgeEntry(_message.Message):
    __slots__ = ("oamp_version", "type", "id", "user_id", "category", "content", "confidence", "source", "decay", "tags", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    OAMP_VERSION_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    DECAY_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    oamp_version: str
    type: str
    id: str
    user_id: str
    category: KnowledgeCategory
    content: str
    confidence: float
    source: KnowledgeSource
    decay: KnowledgeDecay
    tags: _containers.RepeatedScalarFieldContainer[str]
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, oamp_version: _Optional[str] = ..., type: _Optional[str] = ..., id: _Optional[str] = ..., user_id: _Optional[str] = ..., category: _Optional[_Union[KnowledgeCategory, str]] = ..., content: _Optional[str] = ..., confidence: _Optional[float] = ..., source: _Optional[_Union[KnowledgeSource, _Mapping]] = ..., decay: _Optional[_Union[KnowledgeDecay, _Mapping]] = ..., tags: _Optional[_Iterable[str]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class KnowledgeStore(_message.Message):
    __slots__ = ("oamp_version", "type", "user_id", "entries", "exported_at", "agent_id")
    OAMP_VERSION_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    EXPORTED_AT_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    oamp_version: str
    type: str
    user_id: str
    entries: _containers.RepeatedCompositeFieldContainer[KnowledgeEntry]
    exported_at: str
    agent_id: str
    def __init__(self, oamp_version: _Optional[str] = ..., type: _Optional[str] = ..., user_id: _Optional[str] = ..., entries: _Optional[_Iterable[_Union[KnowledgeEntry, _Mapping]]] = ..., exported_at: _Optional[str] = ..., agent_id: _Optional[str] = ...) -> None: ...
