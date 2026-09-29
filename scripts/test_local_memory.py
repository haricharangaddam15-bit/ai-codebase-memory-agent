from backend.app.memory.local_store import LocalMemoryStore


def main() -> None:
    store = LocalMemoryStore()

    questions = [
        "Why did we choose FastAPI?",
        "backend framework decision",
        "Redis PostgreSQL",
    ]

    for question in questions:
        print()
        print("=" * 70)
        print(f"QUESTION: {question}")

        results = store.search(question)

        if not results:
            print("RESULT: NOT DOCUMENTED")
            continue

        for memory in results:
            print(f"TITLE: {memory.get('title')}")
            print(f"RATIONALE: {memory.get('rationale')}")
            print(
                "EVIDENCE:",
                memory.get("evidence", {}).get("quote"),
            )
            print(
                "SOURCE:",
                memory.get("evidence", {}).get("source_url"),
            )


if __name__ == "__main__":
    main()
