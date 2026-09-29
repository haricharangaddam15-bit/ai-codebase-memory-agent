from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    decision = "decision"
    rejected_approach = "rejected_approach"
    convention = "convention"
    bug_incident = "bug_incident"
    review_feedback_pattern = "review_feedback_pattern"
    tech_debt = "tech_debt"


class MemoryStatus(str, Enum):
    active = "active"
    superseded = "superseded"
    reverted = "reverted"


class Evidence(BaseModel):
    quote: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    source_type: str = "github"
    source_id: str = ""
    author: str = ""
    date: datetime | None = None


class DecisionMemory(BaseModel):
    memory_type: MemoryType
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    evidence: Evidence
    alternatives: list[str] = Field(default_factory=list)
    decided_by: str = ""
    module: str = ""
    file_paths: list[str] = Field(default_factory=list)
    status: MemoryStatus = MemoryStatus.active
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    superseded_by: str | None = None

    def validate_rationale(self) -> None:
        if not self.evidence.quote.strip():
            raise ValueError("Memory cannot be stored without evidence.")
