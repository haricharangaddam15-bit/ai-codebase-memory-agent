from backend.app.agents.extractor import (
    RuleBasedDecisionExtractor,
    memory_to_pretty_json,
)
from backend.app.schemas.ingestion import PRSource


def main():
    pr = PRSource(
        number=1,
        title="Architecture: choose FastAPI for backend",
        body="""\
## Decision

Use FastAPI as the backend framework for the AI Codebase Memory Agent.

## Why?

We considered Flask and FastAPI.

FastAPI was selected because the project needs typed request and
response models, asynchronous API endpoints, automatic OpenAPI
documentation, and strong integration with Pydantic.

## Alternatives considered

Flask was rejected because additional components would be needed
for validation and API schema generation.

FastAPI was accepted because these capabilities are built into the
framework and fit the architecture.
""",
        url="https://github.com/haricharangaddam15-bit/ai-codebase-memory-agent/pull/1",
        author="haricharangaddam15-bit",
        state="open",
        merged=False,
        changed_files=[
            "docs/architecture/backend-framework.md",
        ],
        comments=[],
    )

    extractor = RuleBasedDecisionExtractor()

    memories = extractor.extract(pr)

    print("===== EXTRACTION TEST =====")
    print(f"Memories extracted: {len(memories)}")
    print()

    for memory in memories:
        print(memory_to_pretty_json(memory))


if __name__ == "__main__":
    main()
