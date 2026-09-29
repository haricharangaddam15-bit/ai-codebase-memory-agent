from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.app.agents.qa_agent import QAAgent
from backend.app.agents.capture_agent import CaptureAgent
from backend.app.memory.capture_store import CaptureStore
from backend.app.schemas.capture import (
    CaptureCreateRequest,
    CaptureReviewRequest,
)
from backend.app.memory.local_store import LocalMemoryStore
from backend.app.schemas.qa import AskRequest, AskResponse


router = APIRouter(prefix="/api/v1")


MEMORY_FILE = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "memory"
    / "memories.json"
)

memory_store = LocalMemoryStore(str(MEMORY_FILE))
qa_agent = QAAgent(memory_store)
capture_agent = CaptureAgent()
CAPTURE_FILE = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "capture"
    / "drafts.json"
)
capture_store = CaptureStore(str(CAPTURE_FILE))


@router.get("/status")
def status():
    return {
        "service": "ai-codebase-memory-agent",
        "status": "ready",
    }


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    result = qa_agent.ask(
        question=request.question,
        memory_enabled=request.memory_enabled,
    )

    return AskResponse(
        question=result.question,
        answer=result.answer,
        documented=result.documented,
        memory_enabled=request.memory_enabled,
        memories=result.memories,
        citations=result.citations,
    )


@router.post("/capture/draft")
def create_capture_draft(request: CaptureCreateRequest):
    draft = capture_agent.draft(request.pr)

    if draft is None:
        raise HTTPException(
            status_code=422,
            detail=(
                "No evidence-backed decision could be captured "
                "from this merged PR."
            ),
        )

    capture_store.add(draft)

    return draft


@router.get("/capture/drafts")
def list_capture_drafts():
    return {
        "drafts": capture_store.load(),
    }


@router.post("/capture/drafts/{draft_id}/approve")
def approve_capture_draft(
    draft_id: str,
    request: CaptureReviewRequest,
):
    draft = capture_store.get(draft_id)

    if draft is None:
        raise HTTPException(
            status_code=404,
            detail="Capture draft not found.",
        )

    if draft.get("status") != "pending":
        raise HTTPException(
            status_code=409,
            detail="Capture draft has already been reviewed.",
        )

    memory = draft.get("memory", {})
    evidence = memory.get("evidence", {})

    if not evidence.get("quote", "").strip():
        raise HTTPException(
            status_code=422,
            detail="Cannot approve a memory without evidence.",
        )

    memories = memory_store.load()
    memories.append(memory)
    memory_store.save(memories)

    from datetime import datetime, timezone

    updated = capture_store.update(
        draft_id,
        {
            "status": "approved",
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_by": request.reviewer,
        },
    )

    return updated


@router.post("/capture/drafts/{draft_id}/reject")
def reject_capture_draft(
    draft_id: str,
    request: CaptureReviewRequest,
):
    draft = capture_store.get(draft_id)

    if draft is None:
        raise HTTPException(
            status_code=404,
            detail="Capture draft not found.",
        )

    if draft.get("status") != "pending":
        raise HTTPException(
            status_code=409,
            detail="Capture draft has already been reviewed.",
        )

    from datetime import datetime, timezone

    updated = capture_store.update(
        draft_id,
        {
            "status": "rejected",
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_by": request.reviewer,
        },
    )

    return updated
