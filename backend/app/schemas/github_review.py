from pydantic import BaseModel, Field

from backend.app.schemas.review import PRReviewComment


class GitHubPRReviewRequest(BaseModel):
    repository: str = Field(min_length=1)
    pr_number: int = Field(gt=0)
    memory_enabled: bool = True


class GitHubPRReviewResponse(BaseModel):
    repository: str
    pr_number: int
    pr_title: str
    pr_url: str
    changed_files: list[str]
    reviewed: bool
    memory_enabled: bool
    comments: list[PRReviewComment]
