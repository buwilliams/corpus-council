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


class ConversationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response: str
    user_id: str


class CollectionStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str
    plan_id: str


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
