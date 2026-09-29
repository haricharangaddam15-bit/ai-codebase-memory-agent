from pathlib import Path

from fastapi import APIRouter

from backend.app.agents.qa_agent import QAAgent
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
