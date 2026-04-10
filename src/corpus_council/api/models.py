from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    error: str


class ConversationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str
    message: str
    mode: Literal["sequential", "consolidated"] | None = None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response: str
    user_id: str


class CollectionStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str
    plan_id: str
    mode: Literal["sequential", "consolidated"] | None = None


class CollectionStartResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str
    session_id: str
    first_prompt: str


class CollectionRespondRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str
    session_id: str
    message: str
    mode: Literal["sequential", "consolidated"] | None = None


class CollectionRespondResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str
    session_id: str
    prompt: str | None
    status: Literal["active", "complete"]
    collected: dict[str, Any]


class CollectionStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str
    session_id: str
    status: str
    collected: dict[str, Any]
    created_at: str


class CorpusIngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str


class CorpusIngestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chunks_created: int
    files_processed: int


class CorpusEmbedResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vectors_created: int


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str
    goal: str
    mode: Literal["sequential", "consolidated"] | None = None


class QueryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response: str
    goal: str


class FileEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    type: Literal["file", "directory"]
    size: int | None  # None for directories


class DirectoryListingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["directory"]
    entries: list[FileEntry]


class FileContentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["file"]
    content: str


class FileRootsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    roots: list[str]


class FileWriteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str
