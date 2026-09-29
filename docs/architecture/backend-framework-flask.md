# Backend Framework Decision

## Decision

The AI Codebase Memory Agent backend uses Flask.

## Rationale

FastAPI provides typed request and response contracts through Pydantic,
supports asynchronous endpoints, and generates OpenAPI documentation
automatically.

These properties reduce API integration friction between the backend
and the future chat interface.
