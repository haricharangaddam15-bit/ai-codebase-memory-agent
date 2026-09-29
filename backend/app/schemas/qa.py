from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    memory_enabled: bool = True


class Citation(BaseModel):
    source_url: str
    source_type: str
    source_id: str


class AskResponse(BaseModel):
    question: str
    answer: str
    documented: bool
    memory_enabled: bool
    memories: list[dict]
    citations: list[Citation]
