from pydantic import BaseModel, Field


class PRSource(BaseModel):
    number: int
    title: str
    body: str = ""
    url: str
    author: str = ""
    state: str = ""
    merged: bool = False
    created_at: str = ""
    updated_at: str = ""
    changed_files: list[str] = Field(default_factory=list)
    comments: list[str] = Field(default_factory=list)


class IngestionResult(BaseModel):
    processed: int
    memories_created: int
    skipped: int
    errors: list[str] = Field(default_factory=list)
