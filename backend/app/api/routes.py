from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")


@router.get("/status")
def status():
    return {
        "service": "ai-codebase-memory-agent",
        "status": "ready",
    }
