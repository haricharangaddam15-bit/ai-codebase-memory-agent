import tempfile
from pathlib import Path

from backend.app.memory.local_store import LocalMemoryStore


def make_store():
    temp_dir = tempfile.TemporaryDirectory()
    path = Path(temp_dir.name) / "memories.json"
    store = LocalMemoryStore(str(path))

    store.save(
        [
            {
                "title": "Architecture: choose FastAPI for backend",
                "summary": "Backend framework decision.",
                "rationale": (
                    "FastAPI was selected because the project needs typed "
                    "request and response models and asynchronous API endpoints."
                ),
                "alternatives": [
                    "We considered Flask and FastAPI."
                ],
                "module": "docs/architecture",
                "file_paths": [
                    "docs/architecture/backend-framework.md"
                ],
                "status": "active",
                "evidence": {
                    "quote": (
                        "FastAPI was selected because the project needs typed "
                        "request and response models."
                    ),
                    "source_url": (
                        "https://github.com/haricharangaddam15-bit/"
                        "ai-codebase-memory-agent/pull/1"
                    ),
                    "source_type": "github_pr",
                    "source_id": "1",
                },
            },
            {
                "title": "Architecture: choose PostgreSQL",
                "summary": "Database decision.",
                "rationale": (
                    "because we need transactional consistency and typed "
                    "relational data."
                ),
                "alternatives": [],
                "module": "backend/db",
                "file_paths": [
                    "backend/db/database.py"
                ],
                "status": "active",
                "evidence": {
                    "quote": (
                        "We decided to use PostgreSQL because we need "
                        "transactional consistency and typed relational data."
                    ),
                    "source_url": "https://github.com/example/repo/pull/99",
                    "source_type": "github",
                    "source_id": "pr-99",
                },
            },
        ]
    )

    return temp_dir, store


def test_alternatives_query_prioritizes_alternatives_memory():
    temp_dir, store = make_store()

    try:
        results = store.search(
            "What alternatives were considered for the backend framework?"
        )

        assert results, "Expected at least one memory"
        assert (
            results[0]["title"]
            == "Architecture: choose FastAPI for backend"
        )
        assert results[0]["alternatives"] == [
            "We considered Flask and FastAPI."
        ]
    finally:
        temp_dir.cleanup()


def test_fastapi_query_still_returns_fastapi_first():
    temp_dir, store = make_store()

    try:
        results = store.search("Why did we choose FastAPI?")

        assert results, "Expected at least one memory"
        assert (
            results[0]["title"]
            == "Architecture: choose FastAPI for backend"
        )
    finally:
        temp_dir.cleanup()


def test_undocumented_technology_returns_no_memory():
    temp_dir, store = make_store()

    try:
        results = store.search("Why did we choose Redis?")

        assert results == []
    finally:
        temp_dir.cleanup()


def main():
    test_alternatives_query_prioritizes_alternatives_memory()
    test_fastapi_query_still_returns_fastapi_first()
    test_undocumented_technology_returns_no_memory()
    print("All memory retrieval regression tests passed.")


if __name__ == "__main__":
    main()
