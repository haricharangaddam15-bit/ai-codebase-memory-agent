from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from backend.app.schemas.memory import DecisionMemory
from backend.app.schemas.ingestion import PRSource


class CaptureStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class CaptureDraft(BaseModel):
    id: str = Field(min_length=1)
    status: CaptureStatus = CaptureStatus.pending
    memory: DecisionMemory
    source_pr: PRSource
    created_at: datetime
    reviewed_at: datetime | None = None
    reviewed_by: str = ""


class CaptureCreateRequest(BaseModel):
    pr: PRSource


class CaptureReviewRequest(BaseModel):
    reviewer: str = Field(min_length=1)
