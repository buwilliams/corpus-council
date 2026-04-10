from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    error: str


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goal: str
    user_id: str
    conversation_id: str | None = None
    message: str
    mode: str | None = None


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    response: str
    goal: str
    conversation_id: str


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


class ConfigResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str


class ConfigWriteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str


class GoalsProcessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goals_processed: int


class GoalSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str


class GoalsListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goals: list[GoalSummary]
