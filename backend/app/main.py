from fastapi import FastAPI

from backend.app.api.routes import router

app = FastAPI(
    title="AI Codebase Memory Agent",
    version="0.1.0",
    description="An AI agent that remembers why software decisions were made.",
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "name": "AI Codebase Memory Agent",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
