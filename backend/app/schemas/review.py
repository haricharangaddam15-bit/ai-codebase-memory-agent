from pydantic import BaseModel, Field


class PRReviewRequest(BaseModel):
    diff: str = Field(min_length=1)
    memory_enabled: bool = True


class PRReviewComment(BaseModel):
    severity: str
    title: str
    body: str
    memory_title: str
    evidence_quote: str
    source_url: str
    source_type: str = "github"
    source_id: str = ""


class PRReviewResponse(BaseModel):
    reviewed: bool
    memory_enabled: bool
    comments: list[PRReviewComment]
