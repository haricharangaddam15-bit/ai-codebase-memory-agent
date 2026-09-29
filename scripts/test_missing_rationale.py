from backend.app.agents.extractor import RuleBasedDecisionExtractor
from backend.app.schemas.ingestion import PRSource


def main():
    pr = PRSource(
        number=999,
        title="Architecture: choose Redis",
        body="""\
## Decision

We chose Redis.

No explanation was provided in this pull request.
""",
        url="https://github.com/haricharangaddam15-bit/ai-codebase-memory-agent/pull/999",
        author="haricharangaddam15-bit",
        changed_files=[
            "backend/app/services/cache.py",
        ],
    )

    extractor = RuleBasedDecisionExtractor()

    memories = extractor.extract(pr)

    print("===== MISSING RATIONALE TEST =====")
    print(f"Memories extracted: {len(memories)}")

    if memories:
        print("Rationale:", memories[0].rationale)
        print("Evidence:", memories[0].evidence.quote)
    else:
        print("No evidence-backed memory created.")


if __name__ == "__main__":
    main()
