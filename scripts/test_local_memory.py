from pathlib import Path

from backend.app.memory.local_store import LocalMemoryStore


ROOT = Path(__file__).resolve().parents[1]
MEMORY_FILE = ROOT / "data" / "memory" / "memories.json"


def main():
    store = LocalMemoryStore(str(MEMORY_FILE))

    questions = [
        "Why did we choose FastAPI?",
        "backend framework decision",
        "Why did we choose Redis?",
        "Redis PostgreSQL",
    ]

    for question in questions:
        print("=" * 70)
        print(f"QUESTION: {question}")

        results = store.search(question)

        if not results:
            print("RESULT: NOT DOCUMENTED")
            continue

        for memory in results:
            evidence = memory.get("evidence", {})

            print(f"TITLE: {memory.get('title')}")
            print(f"RATIONALE: {memory.get('rationale')}")
            print(f"EVIDENCE: {evidence.get('quote')}")
            print(f"SOURCE: {evidence.get('source_url')}")


if __name__ == "__main__":
    main()
